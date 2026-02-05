from typing import Any, Dict, List, Optional, Tuple
from .storage import query_docs


def retrieve_for_candidate(query: str, resume_id: str, k: int = 10, sections: Optional[List[str]] = None):
    filt: Dict[str, Any] = {
        "doc_type": {"$eq": "resume"},
        "resume_id": {"$eq": resume_id},
    }
    if sections:
        filt["section"] = {"$in": sections}
    return query_docs(query_text=query, filter=filt, top_k=k)


def retrieve_for_shortlist(query: str, resume_ids: List[str], k: int = 14, sections: Optional[List[str]] = None):
    filt: Dict[str, Any] = {
        "doc_type": {"$eq": "resume"},
        "resume_id": {"$in": resume_ids},
    }
    if sections:
        filt["section"] = {"$in": sections}
    return query_docs(query_text=query, filter=filt, top_k=k)


def rank_candidates_for_query(query: str, resume_ids: List[str], per_candidate_k: int = 4) -> List[Tuple[str, float]]:
    rankings = []
    for rid in resume_ids:
        chunks = retrieve_for_candidate(query, rid, k=per_candidate_k)
        best = max([c.get("score", 0.0) for c in chunks], default=0.0)
        rankings.append((rid, best))
    rankings.sort(key=lambda x: x[1], reverse=True)
    return rankings