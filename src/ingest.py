from pypdf import PdfReader
from docx import Document
import io


def read_pdf_bytes(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    parts = []
    for i, page in enumerate(reader.pages):
        txt = page.extract_text() or ""
        txt = txt.strip()
        if txt:
            parts.append(f"[PAGE {i+1}]\n{txt}")
    return "\n\n".join(parts).strip()


def read_docx_bytes(data: bytes) -> str:
    f = io.BytesIO(data)
    doc = Document(f)
    lines = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(lines).strip()


def read_txt_bytes(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore").strip()


def read_file_to_text(filename: str, data: bytes) -> str:
    fn = filename.lower()
    if fn.endswith(".pdf"):
        return read_pdf_bytes(data)
    if fn.endswith(".docx"):
        return read_docx_bytes(data)
    if fn.endswith(".txt") or fn.endswith(".md"):
        return read_txt_bytes(data)
    return ""