import re
from typing import Dict, Any
from .llm import chat

def extract_resume_identity_and_summary(text: str) -> Dict[str, Any]:
    prompt = f"""
You will receive a resume text. Extract:
1) person_name (best guess from header; if unclear, use "Unknown Candidate")
2) summary: 2-3 sentences
3) top_skills: 6-10 skills (strings)
4) roles: 0-6 role titles (strings)
5) seniority: one of [intern, junior, mid, senior, lead, manager, unknown]
6) email (if present)
7) phone (if present)

Return STRICT JSON only with keys:
person_name, summary, top_skills, roles, seniority, email, phone.

RESUME TEXT:
{text[:12000]}
"""
    out = chat([{"role": "user", "content": prompt}], temperature=0.1).strip()

    import json
    try:
        data = json.loads(out)
    except Exception:
        data = {
            "person_name": "Unknown Candidate",
            "summary": "Resume uploaded. Ask questions to explore.",
            "top_skills": [],
            "roles": [],
            "seniority": "unknown",
            "email": "",
            "phone": "",
        }

    data["person_name"] = (data.get("person_name") or "Unknown Candidate").strip()
    data["summary"] = (data.get("summary") or "").strip()
    data["top_skills"] = list(data.get("top_skills") or [])[:12]
    data["roles"] = list(data.get("roles") or [])[:10]
    data["seniority"] = (data.get("seniority") or "unknown").strip().lower()
    data["email"] = (data.get("email") or "").strip()
    data["phone"] = (data.get("phone") or "").strip()
    return data


def chunk_metadata(chunk_text: str) -> Dict[str, Any]:
    words = re.findall(r"[A-Za-z][A-Za-z\+\#\.]{2,}", chunk_text)
    words = [w.lower() for w in words]

    stop = set([
        "the","and","with","for","to","from","that","this","have","has","are","was","were","will",
        "page","location","boston","university","email","phone","resume","linkedin","github",
        "student","graduate","degree","gpa","course","courses","education","experience"
    ])

    kws = []
    for w in words:
        if w in stop:
            continue
        if w not in kws:
            kws.append(w)
        if len(kws) >= 12:
            break

    return {"skills_kw": kws[:12]}