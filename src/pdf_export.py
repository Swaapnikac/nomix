from dataclasses import dataclass
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

@dataclass
class CandidateBrief:
    name: str
    summary: str
    tags: List[str]
    email: str = ""
    phone: str = ""

def export_candidate_brief_pdf(path: str, title: str, candidates: List[CandidateBrief]):
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    y = height - 60

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, title)
    y -= 30

    for cand in candidates:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, cand.name)
        y -= 16

        c.setFont("Helvetica", 10)
        contact = " • ".join([x for x in [cand.email, cand.phone] if x])
        if contact:
            c.drawString(50, y, contact)
            y -= 14

        if cand.summary:
            for line in wrap(cand.summary, 95):
                c.drawString(50, y, line)
                y -= 12

        if cand.tags:
            c.setFont("Helvetica-Oblique", 10)
            c.drawString(50, y, "Top skills: " + ", ".join(cand.tags[:10]))
            y -= 14

        y -= 10
        if y < 120:
            c.showPage()
            y = height - 60

    c.save()

def wrap(text: str, width: int):
    words = text.split()
    line = []
    out = []
    for w in words:
        if len(" ".join(line + [w])) <= width:
            line.append(w)
        else:
            out.append(" ".join(line))
            line = [w]
    if line:
        out.append(" ".join(line))
    return out