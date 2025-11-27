# import os
# import requests
# from dotenv import load_dotenv

# load_dotenv()
# # import pdb;pdb.set_trace()
# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# MODEL = "google/gemini-2.0-flash-001"

# def call_openrouter(prompt):
#     url = "https://openrouter.ai/api/v1/chat/completions"

#     headers = {
#         "Authorization": f"Bearer {OPENROUTER_API_KEY}",
#         "Referer": "http://localhost",
#         "X-Title": "Resume AI Agent",
#         "Content-Type": "application/json"
#     }

#     payload = {
#         "model": MODEL,
#         "messages": [
#             {"role": "user", "content": prompt}
#         ]
#     }

#     res = requests.post(url, json=payload, headers=headers)

#     try:
#         data = res.json()
#     except:
#         return "ERROR: Could not decode OpenRouter response"

#     print("🔍 OpenRouter Response:", data)

#     if "error" in data:
#         return f"ERROR: {data['error']}"

#     if "choices" not in data:
#         return "ERROR: No choices returned"

#     return data["choices"][0]["message"]["content"]


# def extract_details_from_text(text):
#     prompt = f"""
#     Extract candidate details from this resume text. 
#     Return ONLY JSON with keys:
#     name, email, phone, company, designation, skills

#     Resume:
#     {text}
#     """

#     output = call_openrouter(prompt)
#     import json
#     clean = output.strip().strip("```").replace("json", "").strip()
#     try:
#         return json.loads(clean)
#     except:
#         return {}
    
# def generate_document_request(name):
#     prompt = f"""
#     Write a polite, simple message asking {name} to share soft copies 
#     of their PAN card and Aadhaar for verification.

#     Keep message short, human, 3-4 lines.
#     """

#     return call_openrouter(prompt)
















































import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# this model works fine for our use-case (fast + cheap)
MODEL = "google/gemini-2.0-flash-001"


def _call_model(prompt_text):
    """Helper for calling the model API."""
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "resume-agent",
        # "Referer": "http://localhost"
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
        # fallback text; avoids crashing
        return ""

    # mainly for debugging while building
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
        return {}   # if model gives partial junk, just skip it


def generate_document_request(name):
    """Create a short/safe PAN + Aadhaar request using the model."""
    prompt = (
        f"Write a short, normal message asking {name} to share PAN and Aadhaar "
        f"documents for verification. Keep it simple (3–4 lines)."
    )
    return _call_model(prompt)
