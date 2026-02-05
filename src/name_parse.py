import re

def guess_name_from_text(text: str) -> str:
    # Take top lines; resumes usually start with a name
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    top = lines[:8]

    # remove obvious non-name lines
    bad = ["resume", "curriculum vitae", "cv", "linkedin", "github", "portfolio", "email", "phone"]
    top = [ln for ln in top if not any(b in ln.lower() for b in bad)]

    # candidate: first line with mostly letters and 2-4 words
    for ln in top:
        ln2 = re.sub(r"[^A-Za-z\s\-]", "", ln).strip()
        words = [w for w in ln2.split() if w]
        if 1 < len(words) <= 4 and len(ln2) >= 4:
            # avoid ALL CAPS headings like "EDUCATION"
            if ln2.isupper() and len(words) == 1:
                continue
            return " ".join(words)[:60]

    return "Candidate"