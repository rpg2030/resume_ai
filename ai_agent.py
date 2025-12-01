
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("AI_MODEL", "google/gemini-2.0-flash-001")

def _call_model(prompt_text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "resume-agent"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt_text}]
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        data = r.json()
    except Exception:
        return ""
    print("Model raw:", data if isinstance(data, dict) else str(data)[:200])
    if not isinstance(data, dict) or "choices" not in data:
        return ""
    return data["choices"][0]["message"]["content"]


def call_openrouter_vision(messages):
    """Call Gemini vision model for image-based extraction."""
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "resume-agent",
        "Referer": "http://localhost"
    }

    payload = {
        "model": "google/gemini-2.0-flash-001",  
        "messages": messages
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=40)
        data = resp.json()
    except Exception:
        return ""

    print("Vision raw:", data)

    if not isinstance(data, dict) or "choices" not in data:
        return ""

    return data["choices"][0]["message"]["content"]


def extract_details_from_text(text):
    prompt = f"""
    Read the resume text below and extract ONLY the fields you can confidently identify.

    Return a JSON object containing ANY of these keys *only if found*:
    - name
    - email
    - phone
    - company
    - designation
    - skills
    - dob

    Do NOT include a key if the information is missing or uncertain.
    Do NOT add comments or explanations.

    Resume Text:
    {text}
"""

    output = _call_model(prompt)
    cleaned = output.strip().strip("```").replace("json", "").strip()
    try:
        return json.loads(cleaned)
    except Exception:
        return {}

def generate_document_request(name):
    prompt = (
        f"Write a short, polite message asking {name} to share scanned "
        "copies of their PAN card and Aadhaar for verification. Keep it 2-4 lines."
    )
    return _call_model(prompt)

def generate_ai_summary(resume_text):
    """
    Ask model to create a short candidate summary and top 5 skills.
    Returns dict: {summary: str, top_skills: [..]}
    """
    prompt = (
        "Read the following resume text and return a JSON object with keys:\n"
        "summary (short paragraph), top_skills (list of top 5 skills), confidence (0-100)\n\n"
        f"{resume_text}"
    )
    raw = _call_model(prompt)
    cleaned = raw.strip().strip("```").replace("json", "").strip()
    try:
        out = json.loads(cleaned)
        return out
    except Exception:
        return {"summary": resume_text[:400], "top_skills": [], "confidence": 50}