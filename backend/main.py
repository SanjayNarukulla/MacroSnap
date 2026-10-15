import os
import time
from dotenv import load_dotenv
load_dotenv()
import base64
import uuid
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE, SUMMARY_PROMPT

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
MODEL_NAME = "gemini-3.5-flash-lite"

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# in-memory session store: session_id -> {chat, name, messages}
sessions = {}


class OnboardRequest(BaseModel):
    name: str

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


@app.post("/onboard")
def onboard(req: OnboardRequest):
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")

    session_id = str(uuid.uuid4())
    chat = gemini_client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )
    welcome = WELCOME_MESSAGE.format(name=req.name.strip())
    sessions[session_id] = {
        "chat": chat,
        "name": req.name.strip(),
        "messages": [{"role": "assistant", "kind": "text", "content": welcome}],
    }
    return {"session_id": session_id, "welcome": welcome}


@app.post("/chat")
def chat(req: ChatRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

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

    session["messages"].extend(user_messages)

    answer = ask_gemini(session["chat"], parts)
    session["messages"].append({"role": "assistant", "kind": "text", "content": answer})

    return {"reply": answer, "user_messages": user_messages}


@app.post("/send-telegram")
def send_telegram(req: TelegramRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    summary = ask_gemini(session["chat"], [SUMMARY_PROMPT])

    text = f"Hey {session['name']}! Here's your MacroSnap daily summary:\n\n{summary}"
    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
    )
    if not resp.ok:
        raise HTTPException(status_code=500, detail=resp.text)
    return {"ok": True}
