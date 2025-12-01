import pdfplumber
import easyocr
from PIL import Image
import io
from utils.file_to_base64 import file_to_base64
from ai_agent import call_openrouter_vision
import json
import base64


try:
    reader = easyocr.Reader(['en'], gpu=False)
except:
    reader = None


def file_to_base64(file_obj):
    file_obj.seek(0)
    return base64.b64encode(file_obj.read()).decode()


def _clean_json(text):
    """Remove ```json fences and return raw JSON text."""
    if not text:
        return ""

    cleaned = (
        text.replace("```json", "")
            .replace("```", "")
            .strip()
    )
    return cleaned


def extract_pan_via_ai(file_obj):
    b64 = file_to_base64(file_obj)

    prompt = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": (
                    "Extract all important PAN card fields. "
                    "Respond ONLY JSON with keys: pan_number, name, father_name, dob."
                )
            },
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{b64}"}
        ]
    }

    raw = call_openrouter_vision([prompt])
    cleaned = _clean_json(raw)

    try:
        data = json.loads(cleaned)
    except Exception:
        data = {"raw_text": cleaned, "parse_error": True}

    data["raw_text"] = cleaned
    return data



def extract_aadhaar_via_ai(file_obj):
    b64 = file_to_base64(file_obj)

    prompt = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": (
                    "Extract Aadhaar card details. "
                    "Return ONLY JSON with keys: name, dob, gender, aadhaar_number, address, phone."
                )
            },
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{b64}"}
        ]
    }

    raw = call_openrouter_vision([prompt])
    cleaned = _clean_json(raw)

    try:
        data = json.loads(cleaned)
    except Exception:
        data = {"raw_text": cleaned, "parse_error": True}

    data["raw_text"] = cleaned
    return data

def _word_match(text, pattern):
    """
    Check both words appear somewhere in text.
    """
    if not text or not pattern:
        return False

    text = text.lower()
    words = [w.strip() for w in pattern.lower().split() if w]

    return all(w in text for w in words)  


def extract_text_from_pdf(file_obj):
    try:
        file_obj.seek(0)
        with pdfplumber.open(file_obj) as pdf:
            text = ""
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return text.strip()
    except Exception:
        return ""


def extract_text_from_image(file_obj):
    try:
        if reader is None:
            return ""

        file_obj.seek(0)
        img = Image.open(file_obj)
        buf = io.BytesIO()
        img.save(buf, format="PNG") 
        buf.seek(0)

        result = reader.readtext(buf.read(), detail=0)
        return " ".join(result)
    except Exception:
        return ""

def compare_with_resume(extracted, resume_data):
    """
    Compare PAN/Aadhaar extracted data with resume details.
    Returns dict with name_match, dob_match, phone_match.
    """

    text = extracted.get("raw_text", "").lower()
    out = {}

    if resume_data.get("name") and "name" in text:
        out["name_match"] = _word_match(text, resume_data["name"])
    else:
        out["name_match"] = None

    if resume_data.get("dob") and "dob" in text:
        dob = resume_data["dob"].replace("-", "/")
        out["dob_match"] = dob.lower() in text
    else:
        out["dob_match"] = None

    if resume_data.get("phone") and "phone" in text:
        out["phone_match"] = resume_data["phone"] in text
    else:
        out["phone_match"] = None

    return out

def smart_ocr(file_obj):
    """Decide best OCR method automatically."""
    filename = file_obj.filename.lower()

    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file_obj)

    if any(filename.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
        return extract_text_from_image(file_obj)

    return ""


def calculate_confidence(match_dict):
    """
    match_dict is expected to contain keys:
      - name_match: True/False/None
      - dob_match:  True/False/None
      - phone_match: True/False/None

    Only consider checks that are applicable (not None).
    Weights:
      name = 50, dob = 30, phone = 20
    Return: integer confidence 0..100
    """

    weights = {
        "name_match": 50,
        "dob_match": 30,
        "phone_match": 20
    }

    total_possible = 0
    score = 0

    for key, wt in weights.items():
        val = match_dict.get(key, None)
        if val is None:
            continue
        total_possible += wt
        if val is True:
            score += wt

    if total_possible == 0:
        return 0

    confidence = (score / total_possible) * 100
    return int(round(confidence))


def calculate_fraud_score(confidence):
    """
    Fraud = reverse confidence
    """
    return 100 - confidence


def risk_color(confidence):
    """
    UI color mapping
    """
    if confidence >= 90:
        return "green"
    if confidence >= 60:
        return "yellow"
    return "red"