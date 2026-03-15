from fastapi import APIRouter
from models.schemas import ChatRequest, ChatResponse
from services.ai_service import run_agent
from services.cosmos_service import find_project, update_project_by_id
import re

router = APIRouter()


def extract_update_intent(text: str):
    """
    Detects patterns like:
    update id 5 with new text here
    update 5 with new text here
    update id 23 to new text here
    update project 5: new text here
    """
    match = re.search(
        r'update\s+(?:id\s+|project\s+)?(\d{1,3})\s+(?:with|to|:)\s+(.+)',
        text, re.IGNORECASE
    )
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    messages = [m.dict() for m in request.messages]
    last_msg = messages[-1]["content"].strip() if messages else ""

    # ── User confirmed with yes ──────────────────────────────
    if last_msg.lower() in ["yes", "yes.", "confirm", "ok", "sure", "yeah"]:

        # Scan history for the last update request
        for msg in reversed(messages[:-1]):
            if msg["role"] == "user":
                item_id, new_details = extract_update_intent(msg["content"])
                if item_id and new_details:

                    # Write to Cosmos DB using id
                    updated = update_project_by_id(item_id, new_details)

                    if updated:
                        return ChatResponse(
                            reply=(
                                f"✅ Successfully updated in Cosmos DB!\n\n"
                                f"ID           : {updated.get('id')}\n"
                                f"Project Name : {updated.get('project_name')}\n"
                                f"Super Project: {updated.get('super_project_name')}\n"
                                f"New Details  : {new_details}"
                            )
                        )
                    else:
                        return ChatResponse(
                            reply=f"❌ No project found with ID {item_id}."
                        )

        return ChatResponse(
            reply="I could not find a pending update. Please try again:\nupdate id 5 with your new details here"
        )

    # ── User cancelled ───────────────────────────────────────
    if last_msg.lower() in ["no", "no.", "cancel", "stop"]:
        return ChatResponse(
            reply="Update cancelled. Let me know if you need anything else."
        )

    # ── Detect update intent ─────────────────────────────────
    item_id, new_details = extract_update_intent(last_msg)

    if item_id and new_details:
        # First check if the project exists
        result = find_project(item_id)

        if result and result.get("data"):
            data = result["data"]
            if isinstance(data, list):
                data = data[0]

            # Ask for confirmation before writing
            return ChatResponse(
                reply=(
                    f"Please confirm this update:\n\n"
                    f"ID           : {data.get('id')}\n"
                    f"Project Name : {data.get('project_name')}\n"
                    f"Super Project: {data.get('super_project_name')}\n"
                    f"New Details  : {new_details}\n\n"
                    f"Type yes to confirm or no to cancel."
                )
            )
        else:
            return ChatResponse(
                reply=f"❌ No project found with ID {item_id}. Please check the ID and try again."
            )

    # ── Normal conversation ──────────────────────────────────
    reply = run_agent(messages)
    return ChatResponse(reply=reply)
