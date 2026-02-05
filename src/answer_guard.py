import re
from typing import Dict, Any, List, Tuple
from .llm import chat

SYSTEM = """You are NoMix Recruiter.
You MUST be truthful and grounded.
You MUST follow the formatting rules exactly.
"""

def build_context(chunks: List[Dict[str, Any]], max_chunks: int = 8) -> str:
    parts = []
    for i, ch in enumerate(chunks[:max_chunks], start=1):
        md = ch.get("meta") or {}
        parts.append(
            f"[{i}] person={md.get('person_name','')} "
            f"file={md.get('source_file','')} section={md.get('section','')} score={ch.get('score',0):.3f}\n"
            f"{ch.get('text','')}"
        )
    return "\n\n".join(parts).strip()

def has_citation(s: str) -> bool:
    return bool(re.search(r"\[\d+\]", s))

def normalize_citations(answer: str, max_cite: int) -> Tuple[str, bool]:
    """
    Ensures citations are within [1..max_cite].
    Returns (answer, ok).
    """
    cites = re.findall(r"\[(\d+)\]", answer)
    for c in cites:
        n = int(c)
        if n < 1 or n > max_cite:
            return answer, False
    return answer, True

def answer_with_citations(question: str, rewritten: str, candidate_label: str, chunks: List[Dict[str, Any]]) -> str:
    context = build_context(chunks, max_chunks=8)

    prompt = f"""
Return an answer that is ONLY supported by evidence.

Rules:
- Every sentence MUST end with at least one citation like [1] or [2][3].
- Use ONLY the evidence below.
- If evidence does not contain the answer, respond exactly:
  I don’t have that information in the provided resume evidence.

Output format:
ANSWER:
<2–7 sentences with citations>

QUESTION:
{question}

REWRITTEN QUERY:
{rewritten}

CANDIDATE CONTEXT:
{candidate_label}

EVIDENCE:
{context}
""".strip()

    out = chat(
        [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        temperature=0.15,
    ).strip()

    # extract ANSWER block if present
    m = re.search(r"ANSWER:\s*(.*)", out, flags=re.S)
    ans = (m.group(1).strip() if m else out.strip())

    # enforce at least one citation per sentence (soft check)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", ans) if s.strip()]
    if not sentences:
        return "I don’t have that information in the provided resume evidence."

    if any(not has_citation(s) for s in sentences):
        # If model forgets citations, fail safe.
        return "I don’t have that information in the provided resume evidence."

    ans, ok = normalize_citations(ans, max_cite=min(len(chunks), 8))
    if not ok:
        return "I don’t have that information in the provided resume evidence."

    return ans

def verify_and_trim(answer: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Second pass: remove unsupported claims.
    The verifier returns either the same answer (citations preserved) or a safer shorter answer.
    """
    context = build_context(chunks, max_chunks=8)

    prompt = f"""
You are a verifier. You will receive an answer with citations [1], [2]...
Your job:
- Remove any sentence that is not directly supported by the cited evidence.
- Keep citations on remaining sentences.
- If nothing is supported, return exactly:
  I don’t have that information in the provided resume evidence.

Return ONLY the final cleaned answer (no headings).

ANSWER TO VERIFY:
{answer}

EVIDENCE:
{context}
""".strip()

    cleaned = chat(
        [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        temperature=0.0,
    ).strip()

    # final hard check: still requires citations per sentence unless it's the not-found line
    if cleaned.strip() == "I don’t have that information in the provided resume evidence.":
        return cleaned

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]
    if any(not has_citation(s) for s in sentences):
        return "I don’t have that information in the provided resume evidence."

    cleaned, ok = normalize_citations(cleaned, max_cite=min(len(chunks), 8))
    if not ok:
        return "I don’t have that information in the provided resume evidence."

    return cleaned