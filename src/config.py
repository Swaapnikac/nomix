from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    APP_NAME: str = "nomix-recruiter"

    # Models (easy to swap)
    CHAT_MODEL: str = os.getenv("NOMIX_CHAT_MODEL", "gpt-4.1-mini")  #  [oai_citation:2‡OpenAI Platform](https://platform.openai.com/docs/models/gpt-4.1-mini?utm_source=chatgpt.com)
    REWRITE_MODEL: str = os.getenv("NOMIX_REWRITE_MODEL", "gpt-4o-mini")  #  [oai_citation:3‡OpenAI Platform](https://platform.openai.com/docs/models/gpt-4o-mini?utm_source=chatgpt.com)
    EMBED_MODEL: str = os.getenv("NOMIX_EMBED_MODEL", "text-embedding-3-large")  #  [oai_citation:4‡OpenAI Platform](https://platform.openai.com/docs/models/text-embedding-3-large?utm_source=chatgpt.com)

    # Chroma persistence
    CHROMA_DIR: str = os.getenv("NOMIX_CHROMA_DIR", "data/chroma")
    COLLECTION: str = os.getenv("NOMIX_COLLECTION", "nomix_docs")

    # Chunking
    CHUNK_TOKENS: int = int(os.getenv("NOMIX_CHUNK_TOKENS", "650"))
    CHUNK_OVERLAP: int = int(os.getenv("NOMIX_CHUNK_OVERLAP", "120"))

    # Retrieval
    TOP_K: int = int(os.getenv("NOMIX_TOP_K", "6"))

    # Safety
    MAX_FILES_PER_BATCH: int = int(os.getenv("NOMIX_MAX_FILES", "25"))

SETTINGS = Settings()