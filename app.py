from google import genai
from google.genai import types
import streamlit as st 
import time

import requests

from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE, WHATSAPP_SUMMARY_PROMPT

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key = GEMINI_API_KEY)

gemini_client = get_gemini_client()
MODEL_NAME = "gemini-3.5-flash-lite"

def send_telegram(name, summary):
    text = f"Hey {name}! Here's your MacroSnap daily summary:\n\n{summary}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    if resp.ok:
        return True, None
    return False, resp.text



def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):
    st.session_state.messages.append({
        "role": role,
        "kind": kind,
        "content": content
    })
    render_message(st.session_state.messages[-1])

# def ask_gemini(parts):
#     try:
#         return st.session_state.chat.send_message(parts).text
#     except Exception as error:
#         return f"Sorry, something went wrong: {error}"
def ask_gemini(parts):
    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = st.session_state.chat.send_message(parts)
            return response.text

        except Exception as error:
            error_message = str(error)

            if "503" in error_message or "UNAVAILABLE" in error_message:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue

            return f"Sorry, something went wrong: {error_message}"

    return "Sorry, the AI service is temporarily unavailable. Please try again."
# st.title("MacroSnap")
# st.caption("Snap")

#step 1: onboarding (username and phone)

if 'onboarded' not in st.session_state:
    st.title("MacroSnap")
    st.caption("Snap")

    with st.form("onboarding_form"):
        name = st.text_input("Your name")
        submitted = st.form_submit_button("Let's go")

    if submitted:
        if not name.strip():
            st.warning("Please enter your name")

        else:
            st.session_state.name = name.strip()
            #activate my ai
            st.session_state.chat = gemini_client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            st.session_state.messages = [{
                "role": "assistant",
                "kind": "text",
                "content": WELCOME_MESSAGE.format(name=name.strip())
            }]
            st.session_state.onboarded = True
            st.rerun()

    st.stop()

#create chat interface

header_col, button_col = st.columns([5,2], vertical_alignment="center")

with header_col:
    st.title("MacroSnap")

with button_col:
    send_disabled = not any(m["role"] == "user" for m in st.session_state.messages)
    if st.button("Send to Telegram", disabled=send_disabled, use_container_width=True):
        with st.spinner("Summarizing your day..."):
            summary = ask_gemini([WHATSAPP_SUMMARY_PROMPT])
        success, info = send_telegram(st.session_state.name, summary)
        if success:
            st.toast("Summary sent to Telegram! ✅")
        else:
            st.toast(f"Failed: {info}", icon="🚨")
        
st.caption(f"Logged in as {st.session_state.name}")

for message in st.session_state.messages:
    render_message(message)


user_input = st.chat_input(
    "Ask a question, or attach a photo of your meal",
    accept_file = True,
    file_type=["jpg", "jpeg", "png"]
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user","image",photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes,mime_type=photo.type))

    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        parts.append("What is this meal? Give me the calories and macros")

    with st.spinner("Crunching the numbers..."):
        answer = ask_gemini(parts)
    add_message("assistant","text", answer)
    