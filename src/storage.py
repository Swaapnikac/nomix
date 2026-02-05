import os
from typing import Any, Dict, List, Optional

from openai import OpenAI
from pinecone import Pinecone

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

_client: Optional[OpenAI] = None
_pc: Optional[Pinecone] = None
_index = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def _get_index():
    global _pc, _index
    if _index is None:
        _pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        _index = _pc.Index(os.environ["PINECONE_INDEX"])
    return _index


def _sanitize_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pinecone metadata supports: str, int, float, bool, list[str]
    Convert anything else to str safely.
    """
    out: Dict[str, Any] = {}
    for k, v in (meta or {}).items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            out[k] = v
        elif isinstance(v, list):
            out[k] = [str(x) for x in v[:50]]
        else:
            out[k] = str(v)
    return out


def _batch(items, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def upsert_docs(ids: List[str], docs: List[str], metas: List[Dict[str, Any]]):
    """
    FAST path:
    - batch embeddings (96 chunks per OpenAI call by default)
    - batch upsert (250 vectors per Pinecone call by default)
    """
    if not ids or not docs:
        return

    client = _get_client()
    index = _get_index()

    embed_batch = int(os.getenv("EMBED_BATCH", "96"))     # 64–128 ideal
    upsert_batch = int(os.getenv("UPSERT_BATCH", "250"))  # 200–500 ideal

    zipped = list(zip(ids, docs, metas))
    vectors = []

    for batch in _batch(zipped, embed_batch):
        b_ids = [x[0] for x in batch]
        b_docs = [x[1] for x in batch]
        b_metas = [_sanitize_meta(x[2]) for x in batch]

        # Store chunk text so query can return it without separate storage
        for i, txt in enumerate(b_docs):
            b_metas[i]["text"] = txt

        emb = client.embeddings.create(model=EMBED_MODEL, input=b_docs)
        embs = [e.embedding for e in emb.data]

        for _id, vec, md in zip(b_ids, embs, b_metas):
            vectors.append({"id": _id, "values": vec, "metadata": md})

    for chunk in _batch(vectors, upsert_batch):
        index.upsert(vectors=chunk)


def query_docs(query_text: str, filter: Optional[Dict[str, Any]] = None, top_k: int = 10) -> List[Dict[str, Any]]:
    client = _get_client()
    index = _get_index()

    q = client.embeddings.create(model=EMBED_MODEL, input=[query_text]).data[0].embedding

    res = index.query(
        vector=q,
        top_k=top_k,
        include_metadata=True,
        filter=filter or None,
    )

    out: List[Dict[str, Any]] = []
    for m in (res.get("matches") or []):
        md = m.get("metadata") or {}
        out.append(
            {
                "id": m.get("id", ""),
                "score": float(m.get("score", 0.0)),
                "text": md.get("text", ""),
                "meta": md,
            }
        )
    return out