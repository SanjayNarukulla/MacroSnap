import os
import asyncio
import time
import base64
import uuid
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from google import genai
from google.genai import types

from database import users_col, sessions_col, messages_col
from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE, SUMMARY_PROMPT
from auth import hash_password, verify_password, create_token, decode_token, bearer_scheme

app = FastAPI()

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
MODEL_NAME = "gemini-3.5-flash"

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# in-memory Gemini chat objects: session_id -> chat
gemini_chats = {}


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChatRequest(BaseModel):
    session_id: str
    text: str = ""
    image_base64: str = ""
    image_mime: str = ""

class TelegramRequest(BaseModel):
    session_id: str


def ask_gemini(chat, parts):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return chat.send_message(parts).text
        except Exception as e:
            err = str(e)
            if "503" in err or "UNAVAILABLE" in err:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
            raise HTTPException(status_code=500, detail=err)
    raise HTTPException(status_code=503, detail="AI service temporarily unavailable")


async def run_gemini(chat, parts):
    return await asyncio.get_event_loop().run_in_executor(None, ask_gemini, chat, parts)


async def create_session(user_id: str, name: str) -> dict:
    session_id = str(uuid.uuid4())
    await sessions_col.insert_one({
        "_id": session_id,
        "user_id": user_id,
        "name": name,
        "created_at": datetime.now(timezone.utc),
    })
    chat = gemini_client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )
    gemini_chats[session_id] = chat

    welcome = WELCOME_MESSAGE.format(name=name)
    await messages_col.insert_one({
        "_id": str(uuid.uuid4()),
        "session_id": session_id,
        "role": "assistant",
        "kind": "text",
        "content": welcome,
        "created_at": datetime.now(timezone.utc),
    })
    return {"session_id": session_id, "welcome": welcome}


@app.post("/register")
async def register(req: RegisterRequest):
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing = await users_col.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user_id = str(uuid.uuid4())
    await users_col.insert_one({
        "_id": user_id,
        "name": req.name.strip(),
        "email": req.email,
        "hashed_password": hash_password(req.password),
        "created_at": datetime.now(timezone.utc),
    })

    token = create_token(user_id)
    session = await create_session(user_id, req.name.strip())
    return {"token": token, "name": req.name.strip(), **session}


@app.post("/login")
async def login(req: LoginRequest):
    user = await users_col.find_one({"email": req.email})
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user["_id"])
    session = await create_session(user["_id"], user["name"])
    return {"token": token, "name": user["name"], **session}


@app.get("/me")
async def me(user_id: str = Security(decode_token)):
    user = await users_col.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session = await sessions_col.find_one({"user_id": user_id}, sort=[("created_at", -1)])
    if not session:
        raise HTTPException(status_code=404, detail="No session found")
    messages = await messages_col.find({"session_id": session["_id"]}).sort("created_at", 1).to_list(None)
    return {
        "name": user["name"],
        "session_id": session["_id"],
        "messages": [{"role": m["role"], "kind": m["kind"], "content": m["content"]} for m in messages],
    }


@app.post("/chat")
async def chat(req: ChatRequest, user_id: str = Security(decode_token)):
    session = await sessions_col.find_one({"_id": req.session_id, "user_id": user_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if req.session_id not in gemini_chats:
        chat_obj = gemini_client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        )
        gemini_chats[req.session_id] = chat_obj

    parts = []
    user_messages = []

    if req.image_base64:
        image_bytes = base64.b64decode(req.image_base64)
        parts.append(types.Part.from_bytes(data=image_bytes, mime_type=req.image_mime))
        user_messages.append({"role": "user", "kind": "image", "content": req.image_base64})

    if req.text:
        parts.append(req.text)
        user_messages.append({"role": "user", "kind": "text", "content": req.text})
    elif req.image_base64:
        parts.append("What is this meal? Give me the calories and macros")

    now = datetime.now(timezone.utc)
    if user_messages:
        await messages_col.insert_many([
            {"_id": str(uuid.uuid4()), "session_id": req.session_id, "created_at": now, **msg}
            for msg in user_messages
        ])

    answer = await run_gemini(gemini_chats[req.session_id], parts)
    await messages_col.insert_one({
        "_id": str(uuid.uuid4()),
        "session_id": req.session_id,
        "role": "assistant",
        "kind": "text",
        "content": answer,
        "created_at": datetime.now(timezone.utc),
    })

    return {"reply": answer, "user_messages": user_messages}


@app.post("/send-telegram")
async def send_telegram(req: TelegramRequest, user_id: str = Security(decode_token)):
    session = await sessions_col.find_one({"_id": req.session_id, "user_id": user_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await messages_col.find(
        {"session_id": req.session_id, "role": "user", "kind": "text"}
    ).sort("created_at", 1).to_list(None)

    if not messages:
        raise HTTPException(status_code=400, detail="No meals logged yet")

    meal_log = "\n".join([f"- {m['content']}" for m in messages])
    prompt = f"{SUMMARY_PROMPT}\n\nMeals logged today:\n{meal_log}"

    try:
        one_shot = gemini_client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        )
        summary = await run_gemini(one_shot, [prompt])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")

    text = f"Hey {session['name']}! Here's your MacroSnap daily summary:\n\n{summary}"
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
        )
        if not resp.ok:
            raise HTTPException(status_code=500, detail=f"Telegram error: {resp.text}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")

    return {"ok": True}
