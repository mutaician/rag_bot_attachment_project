"""
System prompts for the knowledge-base agent.
"""

from app import db
from app.schemas import DocumentStatus

SYSTEM_PROMPT = """You are an internal knowledge base assistant for company documents.

Available indexed documents:
{inventory}

Rules:
- Answer ONLY using information from search_documents results. Do not invent facts.
- Call search_documents when you need facts from the knowledge base. You may search multiple times with different queries.
- If search returns nothing relevant, say you could not find that in the uploaded documents.
- Cite source filenames when stating facts from documents.
- Be concise and helpful. Use markdown when it improves clarity.
"""


def build_system_message() -> dict[str, str]:
    """System message with live document inventory (ready docs only)."""
    docs = db.list_documents()
    ready = [d for d in docs if d.status == DocumentStatus.READY]
    if ready:
        lines = [f"- {d.filename} (v{d.version})" for d in ready]
        inventory = "\n".join(lines)
    else:
        inventory = "(no documents indexed yet — tell the user to upload files on the Dashboard)"

    return {"role": "system", "content": SYSTEM_PROMPT.format(inventory=inventory)}
