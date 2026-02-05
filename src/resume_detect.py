import re
from typing import Tuple, Dict, Any

def looks_like_resume(text: str) -> Tuple[bool, Dict[str, Any]]:
    t = text.lower()

    # strong resume signals
    signals = [
        "experience", "education", "skills", "projects",
        "linkedin", "github", "resume", "work history",
        "university", "bachelor", "master",
    ]
    score = sum(1 for s in signals if s in t)

    # heuristic contact extraction
    email = None
    phone = None
    m = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I)
    if m: email = m.group(0)
    p = re.search(r"(\+?\d[\d\s\-\(\)]{8,}\d)", text)
    if p: phone = p.group(0)

    meta = {"email": email or "", "phone": phone or ""}
    return (score >= 3), meta