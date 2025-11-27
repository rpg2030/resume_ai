
import pdfplumber
import docx
from utils.text_cleaner import clean_text


def _read_pdf(path):
    """Extract text from a PDF file (best effort)."""
    txt = []

    try:
        with pdfplumber.open(path) as pdf:
            for pg in pdf.pages:
                t = pg.extract_text()
                if t:
                    txt.append(t)
    except Exception:
        return ""

    return clean_text("\n".join(txt))


def _read_docx(path):
    """Extract text from a .docx resume."""
    try:
        doc = docx.Document(path)
        parts = [p.text for p in doc.paragraphs]
        return clean_text("\n".join(parts))
    except Exception:
        return ""


def parse_resume(path):
    """
    Returns plain text from a resume (pdf/docx).
    Fallback: empty string.
    """
    low = path.lower()

    if low.endswith(".pdf"):
        return _read_pdf(path)

    if low.endswith(".docx"):
        return _read_docx(path)

    return ""
