import re

SECTION_HEADERS = [
    ("education", ["education", "academics", "academic background"]),
    ("experience", ["experience", "work experience", "employment", "professional experience"]),
    ("projects", ["projects", "project experience", "selected projects"]),
    ("skills", ["skills", "technical skills", "core skills", "tools"]),
    ("contact", ["contact", "contacts"]),
]

def detect_section(chunk: str) -> str:
    t = chunk.lower()

    for section, keys in SECTION_HEADERS:
        for k in keys:
            # header-like match
            if re.search(rf"(^|\n)\s*{re.escape(k)}\s*[:\-]?\s*($|\n)", t):
                return section

    # heuristic signals
    if "university" in t or "bachelor" in t or "master" in t or "gpa" in t:
        return "education"
    if "intern" in t or "company" in t or "worked" in t or "responsibilities" in t:
        return "experience"
    if "github" in t or "built" in t or "implemented" in t:
        return "projects"
    if "python" in t or "java" in t or "react" in t or "sql" in t:
        return "skills"

    return "general"