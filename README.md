# 🥗 MacroSnap — AI Vision Nutrition Chatbot

MacroSnap is a full-stack AI-powered nutrition assistant. Users can snap a photo of their meal or describe what they ate, and the app estimates calories, protein, carbs, and fat using Google Gemini's multimodal AI. At the end of the day, a personalized nutrition summary is sent directly to the user's Telegram.

**Live Demo**
- Frontend: https://macrosnap.vercel.app
- Backend API: https://macrosnap-v9ik.onrender.com

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Architecture](#architecture)
4. [Project Structure](#project-structure)
5. [Getting Started](#getting-started)
6. [Backend Setup](#backend-setup)
7. [Frontend Setup](#frontend-setup)
8. [Environment Variables](#environment-variables)
9. [API Reference](#api-reference)
10. [Deployment](#deployment)
11. [How It Works](#how-it-works)

---

## Features

- Register and login with email and password (JWT authentication)
- Chat with an AI nutrition buddy via text or meal photo
- Drag and drop image upload or click to attach
- Real-time calorie and macro estimates (protein, carbs, fat)
- Persistent chat history stored in MongoDB
- Daily nutrition summary sent to Telegram with one click
- Responsive dark UI built with Tailwind CSS
- Typing indicator while AI is responding
- Auto-scroll to latest message

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | FastAPI, Python 3.14 |
| AI | Google Gemini API (gemini-3.5-flash) |
| Database | MongoDB Atlas (via Motor async driver) |
| Auth | JWT (python-jose), bcrypt password hashing |
| Messaging | Telegram Bot API |
| Deployment | Render (backend), Vercel (frontend) |

---

## Architecture

```
React (Vite + Tailwind)
        │
        │  REST API (JSON)
        ▼
FastAPI (Python)
        │
        ├──► Google Gemini API  (multimodal AI)
        ├──► MongoDB Atlas      (users, sessions, messages)
        └──► Telegram Bot API   (daily summary delivery)
```

---

## Project Structure

```
macrosnap/
├── backend/
│   ├── main.py            # FastAPI app, all endpoints
│   ├── auth.py            # JWT creation, verification, bcrypt
│   ├── database.py        # MongoDB Motor async client
│   ├── prompts.py         # Gemini system prompt, welcome message, summary prompt
│   ├── requirements.txt   # Python dependencies
│   ├── Procfile           # Render start command
│   └── .env               # Local secrets (not committed)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                      # Root component, auth state
│   │   ├── components/
│   │   │   ├── Onboarding.jsx           # Login / Register form
│   │   │   └── Chat.jsx                 # Chat UI, image upload, Telegram button
│   │   ├── index.css                    # Tailwind directives
│   │   └── main.jsx                     # React entry point
│   ├── .env                             # Local API URL
│   ├── .env.production                  # Production API URL (Render)
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── render.yaml            # Render deployment config
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB Atlas account (free tier works)
- Google AI Studio API key
- Telegram Bot token and chat ID

### Clone the repo

```bash
git clone https://github.com/SanjayNarukulla/MacroSnap.git
cd MacroSnap
```

---

## Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Fill in your secrets (see Environment Variables section)

# Run the server
python -m uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`

API docs available at `http://localhost:8000/docs`

---

## Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env

# Run the dev server
npm run dev
```

Frontend runs at `http://localhost:5173`

---

## Environment Variables

### Backend (`backend/.env`)

```env
GEMINI_API_KEY=your_google_gemini_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
MONGODB_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/macrosnap
JWT_SECRET=your_random_secret_key
ALLOWED_ORIGINS=http://localhost:5173
```

### Frontend (`frontend/.env`)

```env
VITE_API_URL=http://localhost:8000
```

### How to get each key

**Gemini API Key**
1. Go to https://aistudio.google.com/app/apikey
2. Create a new API key

**Telegram Bot Token**
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the steps
3. Copy the token provided

**Telegram Chat ID**
1. Message your bot once
2. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Find `"chat": {"id": ...}` in the response

**MongoDB URI**
1. Go to https://mongodb.com/atlas and create a free cluster
2. Click Connect → Drivers → copy the connection string
3. Replace `<password>` with your database user password

**JWT Secret**
Any long random string, e.g. `openssl rand -hex 32`

---

## API Reference

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Create account, returns JWT + session |
| POST | `/login` | Login, returns JWT + session |
| GET | `/me` | Get current user + chat history (requires token) |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Send text or image, get macro estimate (requires token) |
| POST | `/send-telegram` | Generate summary and send to Telegram (requires token) |

### Request Examples

**Register**
```json
POST /register
{
  "name": "Sanjay",
  "email": "sanjay@example.com",
  "password": "secret123"
}
```

**Chat with text**
```json
POST /chat
Authorization: Bearer <token>
{
  "session_id": "uuid",
  "text": "I had a chicken rice bowl"
}
```

**Chat with image**
```json
POST /chat
Authorization: Bearer <token>
{
  "session_id": "uuid",
  "text": "",
  "image_base64": "<base64 encoded image>",
  "image_mime": "image/jpeg"
}
```

**Send Telegram summary**
```json
POST /send-telegram
Authorization: Bearer <token>
{
  "session_id": "uuid"
}
```

---

## Deployment

### Backend on Render

1. Go to https://render.com and sign in with GitHub
2. Click New → Web Service
3. Connect the `MacroSnap` repo
4. Set Root Directory to `backend`
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
7. Add all environment variables from the list above
8. Click Deploy

### Frontend on Vercel

1. Go to https://vercel.com and sign in with GitHub
2. Click Add New Project → Import `MacroSnap`
3. Set Root Directory to `frontend`
4. Framework: Vite (auto-detected)
5. Add environment variable: `VITE_API_URL` = your Render backend URL
6. Click Deploy

### After deploying both

Update `ALLOWED_ORIGINS` on Render to your Vercel URL:
```
ALLOWED_ORIGINS=https://your-app.vercel.app
```

---

## How It Works

### User Flow

1. User registers or logs in → JWT token stored in localStorage
2. A new Gemini chat session is created and stored in MongoDB
3. User sends a meal photo or text description
4. Frontend encodes image to base64 and sends to `/chat`
5. Backend decodes image, passes it to Gemini as `Part.from_bytes()`
6. Gemini returns calorie and macro estimates
7. Response is saved to MongoDB and returned to frontend
8. At end of day, user clicks "Send to Telegram"
9. Backend fetches all user messages, sends them to Gemini for summarization
10. Summary is POSTed to Telegram Bot API and delivered to user's phone

### Session Management

- Each login creates a new UUID session stored in MongoDB
- Gemini chat objects are kept in memory (`gemini_chats` dict) keyed by session ID
- If the server restarts, chat history is reloaded from MongoDB and a fresh Gemini chat is created

### Security

- Passwords are hashed with bcrypt before storing
- JWT tokens expire after 24 hours
- All chat and Telegram endpoints require a valid Bearer token
- CORS is restricted to the frontend origin via `ALLOWED_ORIGINS`

---

## Evolution of the Project

| Version | Stack |
|---------|-------|
| v1 | Streamlit + Twilio WhatsApp |
| v2 | Streamlit + Telegram |
| v3 | React + FastAPI + Telegram (current) |

Started as a Streamlit prototype for rapid development, then migrated to a full React + FastAPI architecture for better UI control, proper API separation, user authentication, and persistent storage.
