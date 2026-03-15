from fastapi import APIRouter
from models.schemas import ChatRequest, ChatResponse
from services.ai_service import run_agent
from services.cosmos_service import update_project, get_project
import re

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    messages = [m.dict() for m in request.messages]

    # Check if user wants to update a project
    last_msg = messages[-1]["content"].lower() if messages else ""

    # Detect update intent — "update project X with Y"
    update_match = re.search(
        r'update\s+(.+?)\s+(?:with|to|:)\s+(.+)',
        last_msg, re.IGNORECASE
    )

    if update_match:
        project_hint = update_match.group(1).strip()
        new_details  = update_match.group(2).strip()

        # Find the project first
        from services.cosmos_service import find_project
        result = find_project(project_hint)

        if result and result.get("data"):
            data = result["data"]
            if not isinstance(data, list):
                updated = update_project(
                    super_project_name=data["super_project_name"],
                    project_name=data["project_name"],
                    new_details=new_details
                )
                if updated:
                    return ChatResponse(
                        reply=f"✅ Updated successfully!\n\n"
                              f"Project Name  : {data['project_name']}\n"
                              f"Super Project : {data['super_project_name']}\n"
                              f"New Details   : {new_details}"
                    )

    # Normal agent flow
    reply = run_agent(messages)
    return ChatResponse(reply=reply)