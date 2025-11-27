
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

load_dotenv()

app = Flask(__name__)
CORS(app)

Base.metadata.create_all(bind=engine)

@app.route("/candidates/upload", methods=["POST"])
def upload_resume():
    db = SessionLocal()

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file received"}), 400
    # import pdb;pdb.set_trace()
    saved_path = save_upload(file, "uploads/resumes")
    resume_text = parse_resume(saved_path)

    extracted = extract_details_from_text(resume_text) or {}
    email = extracted.get("email")

    if not email:
        new_item = Candidate(
            name=extracted.get("name"),
            email=None,
            phone=extracted.get("phone"),
            company=extracted.get("company"),
            designation=extracted.get("designation"),
            skills=str(extracted.get("skills")),
            resume_file=saved_path,
            extraction_status="completed"
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return jsonify({"id": new_item.id, "status": "uploaded"})

    existing = db.query(Candidate).filter(Candidate.email == email).first()

    if existing:
        existing.name = extracted.get("name")
        existing.phone = extracted.get("phone")
        existing.company = extracted.get("company")
        existing.designation = extracted.get("designation")
        existing.skills = str(extracted.get("skills"))
        existing.resume_file = saved_path
        existing.extraction_status = "updated"

        db.commit()
        return jsonify({"id": existing.id, "status": "updated_existing"})

    new_item = Candidate(
        name=extracted.get("name"),
        email=email,
        phone=extracted.get("phone"),
        company=extracted.get("company"),
        designation=extracted.get("designation"),
        skills=str(extracted.get("skills")),
        resume_file=saved_path,
        extraction_status="completed"
    )

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
        "resume_file": row.resume_file,
        "pan_file": row.pan_file,
        "aadhaar_file": row.aadhaar_file
    })


@app.route("/candidates/<int:cand_id>/request-documents", methods=["POST"])
def request_docs(cand_id):
    """Generate PAN/Aadhaar request and email it."""
    db = SessionLocal()
    row = db.query(Candidate).filter(Candidate.id == cand_id).first()

    if not row:
        return jsonify({"error": "Candidate not found"}), 404

    email_msg = generate_document_request(row.name)
    mail_status = send_email(
        to_email=row.email,
        subject="Request for PAN & Aadhaar Verification",
        message=email_msg
    )

    entry = DocumentRequestLog(candidate_id=cand_id, message=email_msg)
    db.add(entry)
    db.commit()

    return jsonify({
        "candidate_id": cand_id,
        "message": email_msg,
        "email_sent": mail_status
    })


@app.route("/candidates/<int:cand_id>/submit-documents", methods=["POST"])
def submit_docs(cand_id):
    """Attach uploaded proof files for a candidate."""
    db = SessionLocal()
    row = db.query(Candidate).filter(Candidate.id == cand_id).first()

    if not row:
        return jsonify({"error": "Candidate not found"}), 404

    pan_f = request.files.get("pan")
    ad_f = request.files.get("aadhaar")

    if pan_f:
        row.pan_file = save_upload(pan_f, "uploads/documents")

    if ad_f:
        row.aadhaar_file = save_upload(ad_f, "uploads/documents")

    db.commit()
    return jsonify({"status": "documents_uploaded"})


@app.route("/")
def index():
    return {"message": "Backend is running"}


if __name__ == "__main__":
    app.run(debug=True)
