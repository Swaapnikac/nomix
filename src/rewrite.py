from .llm import chat

def rewrite_query(user_query: str, last_turns: list[str]) -> str:
    context = "\n".join([f"- {t}" for t in last_turns[-5:]])
    prompt = f"""
Rewrite the user query to be recruiter-search friendly and explicit.
- Preserve intent.
- Expand vague terms into concrete skills.
- Use prior context when helpful.
Return ONLY the rewritten query.

Prior conversation (most recent last):
{context}

User query:
{user_query}
"""
    return chat([{"role":"user","content":prompt}], temperature=0.2).strip()