from pydantic import BaseModel
from typing import Optional, List

class Message(BaseModel):
    role: str        # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ChatResponse(BaseModel):
    reply: str

class ProjectUpdate(BaseModel):
    project_details: str
    project_name:    Optional[str] = None