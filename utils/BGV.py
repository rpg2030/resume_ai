import json
from difflib import SequenceMatcher
from ai_agent import _call_model
from datetime import datetime

def court_case_dummy(full_name):
    """Always return clean record (dummy engine)."""
    return {
        "status": "no_records_found",
        "matches": 0,
        "confidence": 95,
        "checked_name": full_name
    }


def social_scan_dummy(full_name, phone=None):
    """Always return social clean status."""
    return {
        "status": "clean",
        "risk_score": 0,
        "comment": "No negative digital footprint found",
        "checked_profile": full_name
    }

def extract_employment_history(resume_text):
    """
    Returns:
    [
        {"company": "ABC Pvt Ltd", "from": "2020", "to": "2022"},
        {"company": "XYZ Ltd", "from": "2018", "to": "2020"},
        ...
    ]
    """
    prompt = f"""
    Extract employment history from this resume.

    Return ONLY JSON list, each item having:
    - company
    - from (year or YYYY-MM)
    - to (year or YYYY-MM or 'present')

    Resume:
    {resume_text}
    """

    out = _call_model(prompt)
    cleaned = out.strip().strip("```").replace("json","").strip()
    try:
        return json.loads(cleaned)
    except:
        return []
    
def employment_consistency(employment_list):
    """
    employment_list = [
        {"company": "...", "from": "2020", "to": "2022"},
        ...
    ]
    """
    if not employment_list:
        return {
            "consistency_score": 0,
            "reasons": ["No employment history found"],
            "color": "red"
        }

    durations = []
    reasons = []

    for job in employment_list:
        try:
            start = job["from"]
            end = job["to"]

            # Standardize formats
            if len(start) == 4:
                start = f"{start}-01"

            if end.lower() == "present":
                end = f"{datetime.utcnow().year}-12"
            elif len(end) == 4:
                end = f"{end}-12"

            year_start = int(start.split("-")[0])
            year_end = int(end.split("-")[0])

            duration_years = max(0, year_end - year_start)
            durations.append(duration_years)

        except:
            continue

    if not durations:
        return {
            "consistency_score": 0,
            "reasons": ["Unable to compute job durations"],
            "color": "red"
        }

    avg_years = sum(durations) / len(durations)

    if avg_years >= 2:
        score = 90
        color = "green"
        reasons.append(f"Average tenure {avg_years:.1f} years — Very stable")
    elif avg_years >= 1:
        score = 70
        color = "yellow"
        reasons.append(f"Average tenure {avg_years:.1f} years — Moderate stability")
    else:
        score = 40
        color = "red"
        reasons.append(f"Average tenure only {avg_years:.1f} years — Frequent job changes")

    return {
        "consistency_score": score,
        "reasons": reasons,
        "color": color
    }