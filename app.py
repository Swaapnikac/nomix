import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv

# ---- Your project modules (must exist in your repo) ----
from src.ingest import read_file_to_text
from src.resume_detect import looks_like_resume
from src.chunking import chunk_by_tokens
from src.metadata_llm import extract_resume_identity_and_summary, chunk_metadata
from src.sections import detect_section
from src.name_parse import guess_name_from_text
from src.rewrite import rewrite_query
from src.intent import detect_sections
from src.retrieval import retrieve_for_candidate, retrieve_for_shortlist, rank_candidates_for_query
from src.llm_answer import answer_with_evidence
from src.storage import upsert_docs

load_dotenv()
st.set_page_config(page_title="NoMix Recruiter", page_icon="🛡️", layout="wide")


# ----------------------------
# Data models
# ----------------------------
@dataclass
class Candidate:
    resume_id: str
    person_name: str
    summary: str
    tags: List[str]


@dataclass
class NonResumeDoc:
    file_name: str
    size_kb: int


# ----------------------------
# Safety / env
# ----------------------------
def require_keys():
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Missing OPENAI_API_KEY in .env")
        st.stop()
    if not os.getenv("PINECONE_API_KEY"):
        st.error("Missing PINECONE_API_KEY in .env")
        st.stop()
    if not os.getenv("PINECONE_INDEX"):
        st.error("Missing PINECONE_INDEX in .env")
        st.stop()


def sha16(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def safe_label(s: str, n: int = 40) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def normalize_name(s: str) -> str:
    return "".join(ch.lower() for ch in (s or "") if ch.isalnum() or ch.isspace()).strip()


def looks_like_who_is(q: str) -> bool:
    ql = q.lower().strip()
    return ql.startswith("who is") or ql.startswith("tell me about") or ql.startswith("summarize")


def resolve_candidate_from_query(q: str, candidates: Dict[str, Candidate]) -> Optional[str]:
    """
    If user asks 'who is X / tell me about X / summarize X', resolve X to a candidate.
    Very safe: only used to SELECT which resume_id to retrieve from (NoMix still holds).
    """
    qn = normalize_name(q)
    if not qn:
        return None

    triggers = ["who is", "tell me about", "about", "summarize", "summary of"]
    if not any(t in qn for t in triggers):
        return None

    best = None
    best_hit = 0

    for rid, c in candidates.items():
        cn = normalize_name(c.person_name)
        if not cn:
            continue

        # token overlap (strong)
        for token in cn.split():
            if len(token) >= 4 and token in qn:
                if len(token) > best_hit:
                    best_hit = len(token)
                    best = rid

        # full substring match
        if cn and cn in qn and len(cn) > best_hit:
            best_hit = len(cn)
            best = rid

    return best


# ----------------------------
# Session init
# ----------------------------
if "candidates" not in st.session_state:
    st.session_state.candidates: Dict[str, Candidate] = {}
if "active_resume_id" not in st.session_state:
    st.session_state.active_resume_id: Optional[str] = None
if "shortlist" not in st.session_state:
    st.session_state.shortlist: List[str] = []
if "non_resumes" not in st.session_state:
    st.session_state.non_resumes: List[NonResumeDoc] = []

if "mode" not in st.session_state:
    st.session_state.mode = "scout"
if "rewrite" not in st.session_state:
    st.session_state.rewrite = True
if "strict" not in st.session_state:
    st.session_state.strict = True
if "cites" not in st.session_state:
    st.session_state.cites = True

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi — I’m **NoMix Recruiter** 🛡️\n\nUpload resumes and ask me anything."}
    ]

if "last_user_turns" not in st.session_state:
    st.session_state.last_user_turns = []


# ----------------------------
# CSS (SAFE: never hides containers)
# ----------------------------
st.markdown(
    """
<style>
:root{
  --bg:#ffffff;
  --soft:#f6f1ea;
  --card:#ffffff;
  --border:rgba(0,0,0,0.10);
  --text:#111827;
  --muted:#6b7280;
  --accent:#a16207;
  --shadow:0 10px 26px rgba(0,0,0,0.08);
}
header[data-testid="stHeader"]{background:transparent!important;}
.stApp{background:var(--bg)!important;color:var(--text)!important;}
.block-container{padding-top:1.2rem;max-width:1280px;}
section[data-testid="stSidebar"]{background:var(--soft)!important;border-right:1px solid var(--border)!important;}
section[data-testid="stSidebar"] *{color:var(--text)!important;}

.card{
  background:var(--card)!important;
  border:1px solid var(--border)!important;
  border-radius:18px!important;
  padding:16px!important;
  box-shadow:var(--shadow);
}
.mini{
  background:#fff!important;
  border:1px solid var(--border)!important;
  border-radius:14px!important;
  padding:12px!important;
}

.hero h1{font-size:2.6rem;font-weight:900;letter-spacing:-0.02em;margin:0;}
.hero p{margin:.2rem 0 0 0;color:var(--muted);font-weight:600;}

.typing{
  display:inline-flex;align-items:center;gap:8px;
  padding:10px 12px;border:1px solid var(--border)!important;background:#fff!important;
  border-radius:14px;box-shadow:0 8px 18px rgba(0,0,0,0.06);
}
.dot{width:8px;height:8px;background:var(--accent)!important;border-radius:999px;animation:blink 1.1s infinite;opacity:.35;}
.dot:nth-child(2){animation-delay:.18s;}
.dot:nth-child(3){animation-delay:.36s;}
@keyframes blink{0%,80%,100%{transform:translateY(0);opacity:.35;}40%{transform:translateY(-3px);opacity:.95;}}

[data-testid="stChatMessage"]{
  background:#fff!important;border-radius:16px!important;border:1px solid var(--border)!important;padding:10px!important;
}
label[data-testid="stWidgetLabel"]{margin-bottom:0.3rem!important;}
</style>
""",
    unsafe_allow_html=True,
)


# ----------------------------
# Sidebar
# ----------------------------
with st.sidebar:
    st.markdown("### Controls")
    st.session_state.mode = st.selectbox("Mode", ["single", "scout"], index=1 if st.session_state.mode == "scout" else 0)
    st.session_state.rewrite = st.toggle("Rewrite queries", value=st.session_state.rewrite)
    st.session_state.strict = st.toggle("Strict mode (don’t guess)", value=st.session_state.strict)
    st.session_state.cites = st.toggle("Show citations", value=st.session_state.cites)

    st.markdown("---")
    st.markdown(
        """
**Mode guide**
- **Single**: answers only for the **Active Candidate** (best for “he/she” follow-ups).
- **Scout**: compares/searches across a **Shortlist**.
""".strip()
    )

    if st.session_state.non_resumes:
        st.markdown("---")
        st.markdown("### Other uploads")
        for d in st.session_state.non_resumes[-8:]:
            st.caption(f"📄 {d.file_name} ({d.size_kb} KB)")


# ----------------------------
# Header
# ----------------------------
st.markdown(
    """
<div class="hero">
  <h1>NoMix Recruiter</h1>
  <p>Evidence-grounded answers • zero cross-candidate mixing</p>
</div>
""",
    unsafe_allow_html=True,
)


# ----------------------------
# Top row: Upload + Candidate control
# ----------------------------
topL, topR = st.columns([1.2, 1.0], gap="large")

with topL:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Upload files")

    uploads = st.file_uploader("PDF / DOCX / TXT", accept_multiple_files=True, key="uploader")
    st.caption("Accepted: PDF, DOCX, TXT")

    upload_clicked = st.button("Upload files", type="primary", use_container_width=True, disabled=not uploads)
    st.markdown("</div>", unsafe_allow_html=True)

with topR:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Candidate Control")

    ids = list(st.session_state.candidates.keys())

    if not ids:
        st.caption("Upload resumes to create candidates.")
    else:
        # ensure active exists
        if st.session_state.active_resume_id not in ids:
            st.session_state.active_resume_id = ids[0]

        # Active candidate select
        st.session_state.active_resume_id = st.selectbox(
            "Active Candidate",
            options=ids,
            index=ids.index(st.session_state.active_resume_id),
            format_func=lambda rid: safe_label(st.session_state.candidates[rid].person_name),
            key="active_candidate_select",
        )

        # Shortlist only matters in scout
        if st.session_state.mode == "scout":
            st.session_state.shortlist = st.multiselect(
                "Scout Shortlist",
                options=ids,
                default=[x for x in st.session_state.shortlist if x in ids],
                format_func=lambda rid: safe_label(st.session_state.candidates[rid].person_name),
                key="shortlist_select",
            )
        else:
            st.session_state.shortlist = []

    st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------
# Upload handling
# ----------------------------
if upload_clicked:
    require_keys()
    os.makedirs("data", exist_ok=True)

    prog = st.progress(0)
    status = st.empty()

    total = len(uploads)
    resume_count = 0
    nonresume_count = 0

    for idx, uf in enumerate(uploads, start=1):
        status.markdown(f"**Reading {idx}/{total}: {uf.name}**")
        prog.progress(int((idx - 1) / max(1, total) * 100))

        data = uf.read()
        size_kb = max(1, int(len(data) / 1024))

        # Extract text (light)
        text = read_file_to_text(uf.name, data)
        if not text or len(text.strip()) < 80:
            st.session_state.non_resumes.append(NonResumeDoc(file_name=uf.name, size_kb=size_kb))
            st.toast(f"📄 {uf.name}: couldn’t read well (uploaded only)")
            nonresume_count += 1
            continue

        is_resume, _reason = looks_like_resume(text)
        if not is_resume:
            # ✅ store only, no processing
            st.session_state.non_resumes.append(NonResumeDoc(file_name=uf.name, size_kb=size_kb))
            st.toast(f"📄 {uf.name}: not a resume (uploaded only)")
            nonresume_count += 1
            continue

        resume_id = sha16(text)
        if resume_id in st.session_state.candidates:
            st.toast(f"✅ {uf.name}: already uploaded (skipped)")
            continue

        # identity + summary
        status.markdown(f"**Understanding resume {idx}/{total}: {uf.name}**")
        info = extract_resume_identity_and_summary(text)

        person = (info.get("person_name") or "").strip()
        if not person or person.lower() in ["unknown", "unknown candidate", "n/a", "na"]:
            person = guess_name_from_text(text) or uf.name.rsplit(".", 1)[0]

        tags = list(info.get("top_skills") or [])[:8]
        summary = (info.get("summary") or "").strip()

        st.session_state.candidates[resume_id] = Candidate(
            resume_id=resume_id,
            person_name=person,
            summary=summary,
            tags=tags,
        )

        if not st.session_state.active_resume_id:
            st.session_state.active_resume_id = resume_id

        # Chunk + upload (faster, fewer vectors)
        status.markdown(f"**Uploading resume {idx}/{total}: {uf.name}**")
        chunks = chunk_by_tokens(text, chunk_tokens=900, overlap_tokens=90)

        ids_, docs_, metas_ = [], [], []
        for i, c in enumerate(chunks):
            cid = f"{resume_id}:{i}"
            md = {
                "doc_type": "resume",
                "resume_id": resume_id,
                "person_name": person,
                "source_file": uf.name,
                "section": detect_section(c.text),
                "top_skills": info.get("top_skills", []),  # your storage.py should sanitize lists
                **chunk_metadata(c.text),
            }
            ids_.append(cid)
            docs_.append(c.text)
            metas_.append(md)

        upsert_docs(ids_, docs_, metas_)
        resume_count += 1
        st.toast(f"✅ Resume uploaded: {person}")

    prog.progress(100)
    status.markdown("**Done ✅**")
    st.success(f"Resumes indexed: {resume_count} • Other files uploaded only: {nonresume_count}")
    st.rerun()


# ----------------------------
# Main: Chat + Insights
# ----------------------------
left, right = st.columns([1.55, 1.0], gap="large")

with left:
    st.markdown("### Chat")
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    user_q = st.chat_input("Ask a question…")

    if user_q:
        require_keys()

        # show user message immediately
        st.session_state.messages.append({"role": "user", "content": user_q})
        with st.chat_message("user"):
            st.markdown(user_q)

        # context for rewrite
        st.session_state.last_user_turns.append(user_q)
        st.session_state.last_user_turns = st.session_state.last_user_turns[-5:]

        rewritten = rewrite_query(user_q, st.session_state.last_user_turns) if st.session_state.rewrite else user_q
        sections = detect_sections(user_q)

        # strict threshold tuning
        min_score = 0.32 if st.session_state.strict else 0.20
        if looks_like_who_is(user_q):
            min_score = 0.22 if st.session_state.strict else 0.18

        with st.chat_message("assistant"):
            typing = st.empty()
            typing.markdown(
                '<div class="typing"><span class="dot"></span><span class="dot"></span><span class="dot"></span>'
                '<span style="margin-left:6px;opacity:.9;">NoMix Recruiter is thinking…</span></div>',
                unsafe_allow_html=True,
            )
            time.sleep(0.10)

            all_ids = list(st.session_state.candidates.keys())
            if not all_ids:
                typing.empty()
                msg = "Upload resumes first so I can answer questions."
                st.markdown(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
                st.stop()

            # ✅ KEY FIX: resolve "who is X" to a specific candidate and answer from that resume only
            resolved_id = resolve_candidate_from_query(user_q, st.session_state.candidates)

            if resolved_id:
                chunks = retrieve_for_candidate(rewritten, resolved_id, k=14, sections=sections)
                target = st.session_state.candidates[resolved_id].person_name

                answer = answer_with_evidence(
                    user_query=user_q,
                    rewritten_query=rewritten,
                    active_candidate_name=target,
                    evidence_chunks=chunks[:12],
                    mode="single",
                    min_score=min_score,
                )

                typing.empty()
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                # normal behavior by mode
                if st.session_state.mode == "single":
                    rid = st.session_state.active_resume_id or all_ids[0]
                    chunks = retrieve_for_candidate(rewritten, rid, k=14, sections=sections)
                    target = st.session_state.candidates[rid].person_name

                    answer = answer_with_evidence(
                        user_query=user_q,
                        rewritten_query=rewritten,
                        active_candidate_name=target,
                        evidence_chunks=chunks[:12],
                        mode="single",
                        min_score=min_score,
                    )

                    typing.empty()
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})

                else:
                    shortlist = st.session_state.shortlist
                    if not shortlist:
                        typing.empty()
                        msg = "Scout mode needs a Shortlist. Select candidates in Candidate Control (or switch to Single)."
                        st.markdown(msg)
                        st.session_state.messages.append({"role": "assistant", "content": msg})
                    else:
                        chunks = retrieve_for_shortlist(rewritten, shortlist, k=20, sections=sections)
                        rankings = rank_candidates_for_query(rewritten, shortlist)

                        radar = ["**Talent Radar (Top matches in shortlist)**"]
                        for rid, score in rankings[:5]:
                            c = st.session_state.candidates.get(rid)
                            if c:
                                radar.append(f"- **{c.person_name}** — match score: `{score:.3f}`")

                        answer = answer_with_evidence(
                            user_query=user_q,
                            rewritten_query=rewritten,
                            active_candidate_name="Shortlist",
                            evidence_chunks=chunks[:12],
                            mode="scout",
                            min_score=min_score,
                        )

                        final = "\n".join(radar) + "\n\n---\n\n" + answer

                        if st.session_state.cites and chunks:
                            final += "\n\n---\n**Evidence citations:**\n"
                            for i, ch in enumerate(chunks[:5], start=1):
                                md = ch.get("meta") or {}
                                final += (
                                    f"- [{i}] {md.get('person_name','')} • {md.get('source_file','')} "
                                    f"• section={md.get('section','')} • score={ch.get('score',0):.3f}\n"
                                )

                        typing.empty()
                        st.markdown(final)
                        st.session_state.messages.append({"role": "assistant", "content": final})


with right:
    st.markdown("### Insights")
    if st.session_state.active_resume_id and st.session_state.active_resume_id in st.session_state.candidates:
        c = st.session_state.candidates[st.session_state.active_resume_id]
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"**Active:** {c.person_name}")
        if c.summary:
            st.caption(c.summary)
        if c.tags:
            st.caption("Skills seen: " + ", ".join(c.tags[:10]))
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="mini">Upload resumes to enable insights.</div>', unsafe_allow_html=True)


# ----------------------------
# Candidates (list only)
# ----------------------------
st.markdown("### Candidates")
ids = list(st.session_state.candidates.keys())

if not ids:
    st.markdown('<div class="mini">No candidates yet. Upload resumes above.</div>', unsafe_allow_html=True)
else:
    ids = sorted(ids, key=lambda rid: (st.session_state.candidates[rid].person_name or "").lower())

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.caption("Uploaded resumes")
    for rid in ids:
        c = st.session_state.candidates[rid]
        name = c.person_name or "Unknown Candidate"
        st.markdown(f"**• {name}**")
        if c.summary:
            st.caption(c.summary[:160] + ("…" if len(c.summary) > 160 else ""))
        st.divider()
    st.markdown("</div>", unsafe_allow_html=True)