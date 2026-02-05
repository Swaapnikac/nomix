import os
from openai import OpenAI

EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

def client() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY missing")
    return OpenAI(api_key=key)

def embed_texts(texts: list[str]) -> list[list[float]]:
    c = client()
    resp = c.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]

def chat(messages, temperature: float = 0.2) -> str:
    c = client()
    out = c.chat.completions.create(
        model=CHAT_MODEL,
        temperature=temperature,
        messages=messages,
    )
    return out.choices[0].message.content