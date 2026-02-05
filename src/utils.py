import hashlib

def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()

def clamp_text(s: str, n: int = 8000) -> str:
    s = s or ""
    return s[:n]