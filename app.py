
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# local imports
from database import Base, engine, SessionLocal
from models import Candidate, DocumentRequestLog
from utils.file_helpers import save_upload
from resume_parser import parse_resume
from ai_agent import extract_details_from_text, generate_document_request
from email_sender import send_email
from utils.validator import (
    extract_pan_via_ai,
    extract_aadhaar_via_ai,
    compare_with_resume,
    calculate_confidence,
    calculate_fraud_score,
    risk_color
)
from datetime import datetime
from utils.BGV import court_case_dummy, social_scan_dummy, employment_consistency, extract_employment_history
from ai_agent import generate_ai_summary
import json
from auth import bp as auth_bp, token_required, role_required
load_dotenv()

app = Flask(__name__)
CORS(app)

app.register_blueprint(auth_bp)
Base.metadata.create_all(bind=engine)




@app.route("/candidates/upload", methods=["POST"])
def upload_resume():
    db = SessionLocal()

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file received"}), 400

    saved_path = save_upload(file, "uploads/resumes")

    from datetime import datetime
    uploaded_at = datetime.utcnow()

    resume_text = parse_resume(saved_path)

    extracted = extract_details_from_text(resume_text) or {}
    email = extracted.get("email")
    if email:
        existing = db.query(Candidate).filter(Candidate.email == email).first()
    else:
        existing = None

    if existing:
        existing.name = extracted.get("name")
        existing.phone = extracted.get("phone")
        existing.dob = extracted.get("dob")
        existing.company = extracted.get("company")
        existing.designation = extracted.get("designation")
        existing.skills = str(extracted.get("skills"))
        existing.resume_file = saved_path
        existing.extraction_status = "updated"
        existing.upload_time = uploaded_at
        existing.parse_time = datetime.utcnow()
        existing.append_ai_log("resume re-uploaded and parsed")
        db.commit()
        return jsonify({"id": existing.id, "status": "updated_existing"})
    else:
        new_item = Candidate(
            name=extracted.get("name"),
            email=extracted.get("email"),
            phone=extracted.get("phone"),
            dob = extracted.get("dob"),
            company=extracted.get("company"),
            designation=extracted.get("designation"),
            skills=str(extracted.get("skills")),
            resume_file=saved_path,
            extraction_status="completed",
            upload_time=uploaded_at,
            parse_time=datetime.utcnow()
        )
        new_item.append_ai_log("initial parse")
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return jsonify({"id": new_item.id, "status": "uploaded"})






@app.route("/candidates", methods=["GET"])
def list_candidates():
    """Return a list of all candidate rows."""
    db = SessionLocal()
    items = db.query(Candidate).all()

    out = []
    for row in items:
        out.append({
            "id": row.id,
            "name": row.name,
            "email": row.email,
            "company": row.company,
            "extraction_status": row.extraction_status,
        })

    return jsonify(out)


@app.route("/candidates/<int:cand_id>", methods=["GET"])
def candidate_detail(cand_id):
    db = SessionLocal()
    row = db.query(Candidate).filter(Candidate.id == cand_id).first()

    if not row:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "id": row.id,
        "name": row.name,
        "email": row.email,
        "phone": row.phone,
        "company": row.company,
        "designation": row.designation,
        "skills": row.skills,
        "dob": row.dob,
        "resume_file": row.resume_file,
        "pan_file": row.pan_file,
        "aadhaar_file": row.aadhaar_file,
        "pan_validation": row.pan_validation,
        "aadhaar_validation": row.aadhaar_validation,
        "court_check": row.court_check,
        "social_scan": row.social_scan,
        "employment_check": row.employment_check,

        "upload_time": row.upload_time,
        "parse_time": row.parse_time,
        "document_request_time": row.document_request_time,
        "pan_upload_time": row.pan_upload_time,
        "aadhaar_upload_time": row.aadhaar_upload_time,

        "consent_given": row.consent_given,
        "consent_time": row.consent_time
    })





########  New functionality  ###################


@app.route("/candidates/<int:candidate_id>/request-documents", methods=["POST"])
def request_documents(candidate_id):
    db = SessionLocal()
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        return jsonify({"error": "Candidate not found"}), 404

    message = generate_document_request(candidate.name)
    email_sent = send_email(
        to_email=candidate.email,
        subject="Request for PAN & Aadhaar Verification",
        message=message
    )


    candidate.document_request_time = datetime.utcnow()
    candidate.append_ai_log(f"document_request: {message}")
    db.commit()

    log = DocumentRequestLog(candidate_id=candidate_id, message=message)
    db.add(log)
    db.commit()

    return jsonify({
        "candidate_id": candidate_id,
        "message": message,
        "email_sent": email_sent
    })






@app.route("/candidates/<int:candidate_id>/submit-documents", methods=["POST"])
def submit_documents(candidate_id):


    db = SessionLocal()
    c = db.query(Candidate).filter(Candidate.id == candidate_id).first()

    if not c:
        return jsonify({"error": "Candidate not found"}), 404

    pan_file = request.files.get("pan")
    aadhaar_file = request.files.get("aadhaar")


    if pan_file:
        c.pan_file = save_upload(pan_file, "uploads/documents")
        c.pan_upload_time = datetime.utcnow()

    if aadhaar_file:
        c.aadhaar_file = save_upload(aadhaar_file, "uploads/documents")
        c.aadhaar_upload_time = datetime.utcnow()
    
    try:
        resume_text = parse_resume(c.resume_file)
    except:
        resume_text = ""
    resume_data = {
        "name": c.name,
        "dob": c.dob,
        "phone": c.phone,
        "company": c.company,
    }

    
    # pan ai Extraction
    pan_info = None
    pan_match = None
    pan_conf = 0
    pan_fraud = 0
    pan_color = "red"
    if pan_file:
        pan_info = extract_pan_via_ai(pan_file)
        pan_match = compare_with_resume(pan_info, resume_data)
        pan_conf = calculate_confidence(pan_match)
        pan_fraud = calculate_fraud_score(pan_conf)
        pan_color = risk_color(pan_conf)
        c.pan_validation = json.dumps({
            "extracted": pan_info,
            "match": pan_match,
            "confidence": pan_conf,
            "fraud_score": pan_fraud,
            "color": pan_color
        })

    # aadhar ai Extraction
    aadhaar_info = None
    aadhaar_match = None
    aadhaar_conf = 0
    aadhaar_fraud = 0
    aadhaar_color = "red"
    if aadhaar_file:
        aadhaar_info = extract_aadhaar_via_ai(aadhaar_file)
        aadhaar_match = compare_with_resume(aadhaar_info, resume_data)
        aadhaar_conf = calculate_confidence(aadhaar_match)
        aadhaar_fraud = calculate_fraud_score(aadhaar_conf)
        aadhaar_color = risk_color(aadhaar_conf)


        c.aadhaar_validation = json.dumps({
            "extracted": aadhaar_info,
            "match": aadhaar_match,
            "confidence": aadhaar_conf,
            "fraud_score": aadhaar_fraud,
            "color": aadhaar_color
        })

    # court case
    court_result = court_case_dummy(c.name)
    c.court_check = json.dumps(court_result)

    # social scan
    social_result = social_scan_dummy(c.name, c.phone)
    c.social_scan = json.dumps(social_result)
    
    job_history = extract_employment_history(resume_text)
    emp_result = employment_consistency(job_history)

    c.employment_check = json.dumps(emp_result)
    db.commit()

    return jsonify({
        "status": "documents_uploaded",
        "pan": c.pan_validation,
        "aadhaar": c.aadhaar_validation,
        "court": c.court_check,
        "social": c.social_scan,
        "employment": c.employment_check
    })





######  New functionality


@app.route("/candidates/<int:candidate_id>/ai-summary", methods=["POST"])
def candidate_ai_summary(candidate_id):
    db = SessionLocal()
    c = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not c:
        return jsonify({"error": "Candidate not found"}), 404

    res_text = ""
    try:
        if c.resume_file and os.path.exists(c.resume_file):
            from resume_parser import parse_resume
            res_text = parse_resume(c.resume_file)
        else:
            res_text = c.skills or ""
    except Exception:
        res_text = c.skills or ""

    out = generate_ai_summary(res_text)
    c.ai_summary = out.get("summary") if isinstance(out, dict) else out
    c.top_skills = str(out.get("top_skills", [])) if isinstance(out, dict) else "[]"
    c.confidence = float(out.get("confidence", 50)) if isinstance(out, dict) else 50.0
    c.append_ai_log(f"ai_summary_generated:{json.dumps(out) if isinstance(out, dict) else str(out)[:200]}")
    db.commit()

    return jsonify({"summary": c.ai_summary, "top_skills": c.top_skills, "confidence": c.confidence})



#########   new functionality

@app.route("/candidates/<int:candidate_id>/consent", methods=["POST"])
def candidate_consent(candidate_id):
    db = SessionLocal()
    c = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not c:
        return jsonify({"error": "Candidate not found"}), 404

    payload = request.json or {}
    consent = payload.get("consent") is True
    note = payload.get("note", "")
    from datetime import datetime
    c.consent_given = consent
    c.consent_time = datetime.utcnow() if consent else None
    c.append_ai_log(f"consent:{consent};note:{note}")
    db.commit()
    return jsonify({"consent": c.consent_given, "consent_time": c.consent_time.isoformat() if c.consent_time else None})






##### new functionality


@app.route("/candidates/<int:candidate_id>/audit", methods=["GET"])
def candidate_audit(candidate_id):
    db = SessionLocal()
    c = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not c:
        return jsonify({"error": "Candidate not found"}), 404

    return jsonify({
        "upload_time": c.upload_time.isoformat() if c.upload_time else None,
        "parse_time": c.parse_time.isoformat() if c.parse_time else None,
        "document_request_time": c.document_request_time.isoformat() if c.document_request_time else None,
        "pan_upload_time": c.pan_upload_time.isoformat() if c.pan_upload_time else None,
        "aadhaar_upload_time": c.aadhaar_upload_time.isoformat() if c.aadhaar_upload_time else None,
        "ai_logs": c.ai_logs
    })


@app.route("/")
def index():
    return {"message": "Backend is running"}


if __name__ == "__main__":
    app.run(debug=True)
