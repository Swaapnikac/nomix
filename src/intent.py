import re
from typing import List

def detect_sections(question: str) -> List[str]:
    q = question.lower().strip()

    # If user clearly asks about a category, prioritize that section
    if re.search(r"\b(education|degree|university|college|gpa|course|major|minor)\b", q):
        return ["education"]
    if re.search(r"\b(experience|work|employment|intern|company|role|responsibilit|timeline)\b", q):
        return ["experience"]
    if re.search(r"\b(project|projects|built|developed|implemented|github|portfolio|demo)\b", q):
        return ["projects"]
    if re.search(r"\b(skill|skills|tools|tech stack|technologies|framework|language)\b", q):
        return ["skills"]
    if re.search(r"\b(email|phone|contact|linkedin|website)\b", q):
        return ["contact"]

    # For general questions, allow a wider net (but still focused)
    return ["experience", "projects", "skills", "education", "general"]