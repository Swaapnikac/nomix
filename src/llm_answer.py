from typing import Dict, Any, List, Optional
from .answer_guard import answer_with_citations, verify_and_trim

def answer_with_evidence(
    user_query: str,
    rewritten_query: str,
    active_candidate_name: str,
    evidence_chunks: List[Dict[str, Any]],
    mode: str,
    min_score: float = 0.30,
) -> str:
    if not evidence_chunks:
        return "I don’t have that information in the provided resume evidence."

    best = max([c.get("score", 0.0) for c in evidence_chunks], default=0.0)
    if best < min_score:
        return "I don’t have that information in the provided resume evidence."

    # Pass 1: forced-citation answer
    drafted = answer_with_citations(
        question=user_query,
        rewritten=rewritten_query,
        candidate_label=active_candidate_name if mode == "single" else "Shortlist",
        chunks=evidence_chunks,
    )

    if drafted.strip() == "I don’t have that information in the provided resume evidence.":
        return drafted

    # Pass 2: verification trim
    verified = verify_and_trim(drafted, evidence_chunks)

    return verified