from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class Candidate:
    resume_id: str
    person_name: str
    summary: str
    email: str = ""
    phone: str = ""
    tags: List[str] = field(default_factory=list)

@dataclass
class AppState:
    candidates: Dict[str, Candidate] = field(default_factory=dict)
    active_resume_id: str | None = None
    shortlist: List[str] = field(default_factory=list)
    last_user_turns: List[str] = field(default_factory=list)