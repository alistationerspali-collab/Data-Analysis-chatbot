"""FastAPI entry point."""
from fastapi import FastAPI
from pydantic import BaseModel
from app.chat.chat_handler import handle

app = FastAPI(title="Data Analysis Chatbot (Busy + Groq)")


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@app.post("/chat")
async def chat(request: ChatRequest):
    return handle(request.message, request.session_id)


@app.get("/health")
async def health():
    return {"status": "ok"}