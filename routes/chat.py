from fastapi import APIRouter
from models.schemas import ChatRequest, ChatResponse
from services.ai_service import run_agent

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    messages = [m.dict() for m in request.messages]
    reply = run_agent(messages)
    return ChatResponse(reply=reply)