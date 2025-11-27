

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "google/gemini-2.0-flash-001"


def _call_model(prompt_text):
    """Helper for calling the model API."""
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "resume-agent",
        "Referer": "http://localhost"
    }

    body = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt_text}
        ]
    }

    try:
        resp = requests.post(url, json=body, headers=headers)
        data = resp.json()
    except Exception:
        return ""

    print("Model raw:", data)

    out = data.get("choices", [])
    if not out:
        return ""

    return out[0]["message"]["content"]


def extract_details_from_text(text):
    """
    Ask the model to pull name/email/etc. from resume text.
    Doesn't enforce strict JSON structure.
    """

    prompt = (
        "Pull basic candidate fields out of this resume text. "
        "Give me a JSON dict with keys: name, email, phone, company, designation, skills.\n\n"
        f"Resume:\n{text}"
    )

    raw = _call_model(prompt)
    cleaned = raw.strip().replace("```", "").replace("json", "").strip()

    try:
        return json.loads(cleaned)
    except Exception:
        return {}  


def generate_document_request(name):
    """Create a short/safe PAN + Aadhaar request using the model."""
    prompt = (
        f"Write a short, normal message asking {name} to share PAN and Aadhaar "
        f"documents for verification. Keep it simple (3–4 lines)."
    )
    return _call_model(prompt)
