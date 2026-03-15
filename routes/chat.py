from fastapi import APIRouter
from models.schemas import ChatRequest, ChatResponse
from services.ai_service import run_agent
from services.cosmos_service import find_project, update_project
import re

router = APIRouter()

def extract_update_intent(text: str):
    """Extract project name and new details from update message."""
    match = re.search(
        r'update\s+(.+?)\s+(?:with|to|:)\s+(.+)',
        text, re.IGNORECASE
    )
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    messages = [m.dict() for m in request.messages]
    last_msg = messages[-1]["content"].strip() if messages else ""

    # ── User said yes — look back in history for update intent ──
    if last_msg.lower() in ["yes", "yes.", "confirm", "ok", "sure", "yeah"]:

        # Scan previous messages for last update request
        for msg in reversed(messages[:-1]):
            if msg["role"] == "user":
                project_hint, new_details = extract_update_intent(msg["content"])
                if project_hint and new_details:
                    # Found the update request — now write to DB
                    result = find_project(project_hint)

                    if result and result.get("data"):
                        data = result["data"]

                        if isinstance(data, list):
                            data = data[0]  # take first match

                        updated = update_project(
                            super_project_name=data["super_project_name"],
                            project_name=data["project_name"],
                            new_details=new_details
                        )

                        if updated:
                            return ChatResponse(
                                reply=(
                                    f"✅ Successfully updated in Cosmos DB!\n\n"
                                    f"Project Name  : {data['project_name']}\n"
                                    f"Super Project : {data['super_project_name']}\n"
                                    f"New Details   : {new_details}"
                                )
                            )
                        else:
                            return ChatResponse(
                                reply="❌ Update failed — project not found in database."
                            )
                    else:
                        return ChatResponse(
                            reply=f"❌ Could not find project '{project_hint}' in the database."
                        )

        # No update found in history
        return ChatResponse(
            reply="I'm not sure what to confirm. Please type your update request again like:\nupdate <project name> with <new details>"
        )

    # ── User said no / cancel ────────────────────────────────
    if last_msg.lower() in ["no", "no.", "cancel", "stop"]:
        return ChatResponse(
            reply="Okay, update cancelled. Let me know if you need anything else."
        )

    # ── Detect update intent — ask for confirmation ──────────
    project_hint, new_details = extract_update_intent(last_msg)

    if project_hint and new_details:
        result = find_project(project_hint)

        if result and result.get("data"):
            data = result["data"]

            if isinstance(data, list):
                data = data[0]

            return ChatResponse(
                reply=(
                    f"Please confirm this update:\n\n"
                    f"Project  : {data['project_name']}\n"
                    f"Super    : {data['super_project_name']}\n"
                    f"New text : {new_details}\n\n"
                    f"Type yes to confirm or no to cancel."
                )
            )
        else:
            return ChatResponse(
                reply=f"Could not find project '{project_hint}'. Please check the name and try again."
            )

    # ── Normal agent conversation ────────────────────────────
    reply = run_agent(messages)
    return ChatResponse(reply=reply)
