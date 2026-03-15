import os
from groq import Groq
from dotenv import load_dotenv
from services.cosmos_service import get_project, get_subprojects, update_project ,find_project

def extract_and_fetch(messages: list) -> str:
    full_text = " ".join(m["content"] for m in messages)

    # Extract anything that looks like a project_id (11 char alnum)
    import re
    id_match = re.search(r'\b[A-Z0-9]{11}\b', full_text)

    if id_match:
        result = find_project(id_match.group())
        if result:
            return f"Found by project_id:\n{result['data']}"

    # No ID found — try to match project name words
    words = full_text.split()
    for word in words:
        if len(word) > 4:   # skip short words like "the", "and"
            result = find_project(word)
            if result:
                return f"Found by project_name:\n{result['data']}"

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

def run_agent(messages: list) -> str:
    # Build conversation with system prompt
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Check last user message for project context
    last_user_msg = ""
    for m in messages:
        if m["role"] == "user":
            last_user_msg = m["content"]

    # Try to extract project data if names are mentioned
    project_context = extract_and_fetch(messages)
    if project_context:
        full_messages.append({
            "role": "system",
            "content": f"Here is the project data from the database:\n{project_context}"
        })

    full_messages += messages

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "llama-3.3-70b-versatile"),
        messages=full_messages,
        temperature=0.3,
    )
    return response.choices[0].message.content


#def extract_and_fetch(messages: list) -> str:
    """
    Simple extractor — looks for known super project names in conversation.
    In production, use function calling or an NER model.
    """
    super_projects = [
        "Digital Transformation", "Infrastructure Upgrade",
        "Customer Experience Platform", "Data Analytics Initiative",
        "Cloud Migration Program", "ERP Implementation",
        "Cybersecurity Overhaul", "Mobile First Strategy"
    ]

    full_text = " ".join(m["content"] for m in messages)

    found_super = None
    for sp in super_projects:
        if sp.lower() in full_text.lower():
            found_super = sp
            break

    if not found_super:
        return ""

    # Try to find a specific subproject
    projects = get_subprojects(found_super)
    for p in projects:
        if p["project_name"].lower() in full_text.lower():
            return str(p)   # return full record as context

    # Return list of available subprojects
    names = [p["project_name"] for p in projects]
    return f"Super project '{found_super}' has these subprojects: {names}"