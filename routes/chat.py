from fastapi import APIRouter
from models.schemas import ChatRequest, ChatResponse
from services.ai_service import run_agent
from services.cosmos_service import find_project, update_project
import re

router = APIRouter()

# In-memory store for pending updates
# key = session (we use last user msg hash), value = {project, new_details}
pending_updates = {}

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    messages = [m.dict() for m in request.messages]
    last_msg = messages[-1]["content"].strip() if messages else ""

    # ── Step 1: User confirms a pending update ───────────────
    if last_msg.lower() in ["yes", "yes.", "confirm", "ok", "sure", "yeah"]:
        if pending_updates:
            # Get the most recent pending update
            key = list(pending_updates.keys())[-1]
            pending = pending_updates.pop(key)

            updated = update_project(
                super_project_name=pending["super_project_name"],
                project_name=pending["project_name"],
                new_details=pending["new_details"]
            )

            if updated:
                return ChatResponse(
                    reply=(
                        f"✅ Done! Project updated successfully in the database.\n\n"
                        f"Project Name  : {pending['project_name']}\n"
                        f"Super Project : {pending['super_project_name']}\n"
                        f"New Details   : {pending['new_details']}"
                    )
                )
            else:
                return ChatResponse(reply="❌ Update failed. Project not found in database.")

    # ── Step 2: User cancels ─────────────────────────────────
    if last_msg.lower() in ["no", "no.", "cancel", "stop"]:
        pending_updates.clear()
        return ChatResponse(reply="Okay, update cancelled. Let me know if you need anything else.")

    # ── Step 3: Detect update intent ────────────────────────
    # Matches: "update DT-DevOps Pipeline with new text here"
    update_match = re.search(
        r'update\s+(.+?)\s+(?:with|to|:)\s+(.+)',
        last_msg, re.IGNORECASE
    )

    if update_match:
        project_hint = update_match.group(1).strip()
        new_details  = update_match.group(2).strip()

        result = find_project(project_hint)

        if result and result.get("data"):
            data = result["data"]

            if isinstance(data, list):
                names = [p["project_name"] for p in data]
                return ChatResponse(
                    reply=f"Multiple projects found: {', '.join(names)}.\nPlease be more specific about which one to update."
                )

            # Store pending update — wait for confirmation
            pending_updates["latest"] = {
                "project_name":      data["project_name"],
                "super_project_name": data["super_project_name"],
                "new_details":       new_details
            }

            return ChatResponse(
                reply=(
                    f"Please confirm — are you sure you want to update this project?\n\n"
                    f"Project  : {data['project_name']}\n"
                    f"Super    : {data['super_project_name']}\n"
                    f"New text : {new_details}\n\n"
                    f"Type **yes** to confirm or **no** to cancel."
                )
            )
        else:
            return ChatResponse(
                reply=f"Could not find a project matching '{project_hint}'. Please check the name and try again."
            )

    # ── Step 4: Normal agent conversation ───────────────────
    reply = run_agent(messages)
    return ChatResponse(reply=reply)
