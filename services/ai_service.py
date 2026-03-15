import os
import re
from groq import Groq
from dotenv import load_dotenv
from services.cosmos_service import get_project, get_subprojects, update_project ,find_project

def extract_and_fetch(messages: list) -> str:
    last_user_msg = ""
    for m in messages:
        if m["role"] == "user":
            last_user_msg = m["content"]

    if not last_user_msg:
        return ""

    full_text = last_user_msg.strip()


    # Step 1 — check if user typed a number (simple id like 1, 2, 3...)
    id_match = re.search(r'\b(\d{1,3})\b', full_text)
    if id_match:
        result = find_project(id_match.group())
        if result and result.get("data"):
            project = result["data"]
            summary = summarise_project(project)
            return f"""
Name       : {project.get('project_name')}
Super      : {project.get('super_project_name')}
ID         : {project.get('id')}
Summary    : {summary}
"""

    # Step 2 — try whole message as project name
    result = find_project(full_text)
    if result and result.get("data"):
        data = result["data"]
        if isinstance(data, list):
            names = [p["project_name"] for p in data]
            return f"Multiple projects found: {', '.join(names)}. Please be more specific."
        summary = summarise_project(data)
        return f"""
Name       : {data.get('project_name')}
Super      : {data.get('super_project_name')}
ID         : {data.get('id')}
Summary    : {summary}
"""

    # Step 3 — try each word individually
    fillers = {'find','search','show','get','project','name','id','the','a','an',
               'me','please','tell','about','check','what','is','for','i','want'}

    words = [w for w in re.split(r'\s+', full_text)
             if w.lower() not in fillers and len(w) > 2]

    for word in words:
        clean = re.sub(r'[^a-zA-Z0-9\-]', '', word)
        if len(clean) > 3:
            result = find_project(clean)
            if result and result.get("data"):
                data = result["data"]
                if isinstance(data, list):
                    names = [p["project_name"] for p in data]
                    return f"Multiple projects found: {', '.join(names)}. Be more specific."
                summary = summarise_project(data)
                return f"""
Name       : {data.get('project_name')}
Super      : {data.get('super_project_name')}
ID         : {data.get('id')}
Summary    : {summary}
"""

    return ""
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are a smart project management assistant.

Your job step by step:
1. Greet the user and ask for a Project ID or Project Name
2. Once you receive it, search the database and show a clean summary
3. If user says "update", ask what they want to change, confirm, then update
4. If project is not found, say so politely and ask again

When showing a project summary, ALWAYS use this clean format:

📋 Project Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━
🔖 Project Name   : <name>
🆔 Project ID     : <project id>
📝 Details        : < line summary in simple English>
━━━━━━━━━━━━━━━━━━━━━━━━━━

Never dump raw JSON or technical data to the user.
Always be concise, professional, and friendly.

"""

def summarise_project(project: dict) -> str:
    prompt = f"""
Given this raw project data, write a clean 2-3 line summary
in simple English. Focus on what the project is about,
its goal, and key outcome. Do NOT include technical IDs or JSON.

Project Name    : {project.get('project_name')}
Super Project   : {project.get('super_project_name')}
Project Details : {project.get('project_details')}

Write only the summary paragraph, nothing else.
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=150
    )
    return response.choices[0].message.content.strip()


# ── DEFINED SECOND ────────────────────────────────────────────
def extract_and_fetch(messages: list) -> str:
    last_user_msg = ""
    for m in messages:
        if m["role"] == "user":
            last_user_msg = m["content"]

    if not last_user_msg:
        return ""

    full_text = last_user_msg.strip()

    # Step 1 — check if user typed a number id (1, 2, 3...)
    id_match = re.search(r'\b(\d{1,3})\b', full_text)
    if id_match:
        result = find_project(id_match.group())
        if result and result.get("data"):
            project = result["data"]
            summary = summarise_project(project)
            return f"""
Name       : {project.get('project_name')}
Super      : {project.get('super_project_name')}
ID         : {project.get('id')}
Summary    : {summary}
"""

    # Step 2 — try whole message as project name
    result = find_project(full_text)
    if result and result.get("data"):
        data = result["data"]
        if isinstance(data, list):
            names = [p["project_name"] for p in data]
            return f"Multiple projects found: {', '.join(names)}. Please be more specific."
        summary = summarise_project(data)
        return f"""
Name       : {data.get('project_name')}
Super      : {data.get('super_project_name')}
ID         : {data.get('id')}
Summary    : {summary}
"""

    # Step 3 — try each word individually
    fillers = {'find','search','show','get','project','name','id','the','a','an',
               'me','please','tell','about','check','what','is','for','i','want'}

    words = [w for w in re.split(r'\s+', full_text)
             if w.lower() not in fillers and len(w) > 2]

    for word in words:
        clean = re.sub(r'[^a-zA-Z0-9\-]', '', word)
        if len(clean) > 3:
            result = find_project(clean)
            if result and result.get("data"):
                data = result["data"]
                if isinstance(data, list):
                    names = [p["project_name"] for p in data]
                    return f"Multiple projects found: {', '.join(names)}. Be more specific."
                summary = summarise_project(data)
                return f"""
Name       : {data.get('project_name')}
Super      : {data.get('super_project_name')}
ID         : {data.get('id')}
Summary    : {summary}
"""

    return ""


# ── MAIN AGENT — called last ──────────────────────────────────
def run_agent(messages: list) -> str:
    project_context = extract_and_fetch(messages)

    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if project_context:
        full_messages.append({
            "role": "system",
            "content": f"Database result for the user's query:\n{project_context}"
        })

    full_messages += messages

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=full_messages,
        temperature=0.3,
        max_tokens=300
    )
    return response.choices[0].message.content.strip()