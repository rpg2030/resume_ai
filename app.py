# import os
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from dotenv import load_dotenv

# from database import Base, engine, SessionLocal
# from models import Candidate, DocumentRequestLog
# from utils.file_helpers import save_upload
# from resume_parser import parse_resume
# from ai_agent import extract_details_from_text, generate_document_request
# from email_sender import send_email


# load_dotenv()

# app = Flask(__name__)
# CORS(app)

# # create DB tables if not exist
# Base.metadata.create_all(bind=engine)


# @app.route("/candidates/upload", methods=["POST"])
# def upload_resume():
#     db = SessionLocal()

#     if "file" not in request.files:
#         return jsonify({"error": "No resume file provided"}), 400

#     file = request.files["file"]
#     file_path = save_upload(file, "uploads/resumes")
#     # import pdb;pdb.set_trace()
#     extracted_text = parse_resume(file_path)

#     ai_data = extract_details_from_text(extracted_text)

#     candidate = Candidate(
#         name=ai_data.get("name"),
#         email=ai_data.get("email"),
#         phone=ai_data.get("phone"),
#         company=ai_data.get("company"),
#         designation=ai_data.get("designation"),
#         skills=str(ai_data.get("skills")),
#         resume_file=file_path,
#         extraction_status="completed"
#     )

#     db.add(candidate)
#     db.commit()
#     db.refresh(candidate)

#     return jsonify({"id": candidate.id, "status": "uploaded"})


# @app.route("/candidates", methods=["GET"])
# def get_candidates():
#     db = SessionLocal()
#     records = db.query(Candidate).all()

#     data = []
#     for c in records:
#         data.append({
#             "id": c.id,
#             "name": c.name,
#             "email": c.email,
#             "company": c.company,
#             "extraction_status": c.extraction_status
#         })

#     return jsonify(data)


# @app.route("/candidates/<int:candidate_id>", methods=["GET"])
# def get_candidate_detail(candidate_id):
#     db = SessionLocal()
#     c = db.query(Candidate).filter(Candidate.id == candidate_id).first()

#     if not c:
#         return jsonify({"error": "Candidate not found"}), 404

#     return jsonify({
#         "id": c.id,
#         "name": c.name,
#         "email": c.email,
#         "phone": c.phone,
#         "company": c.company,
#         "designation": c.designation,
#         "skills": c.skills,
#         "resume_file": c.resume_file,
#         "pan_file": c.pan_file,
#         "aadhaar_file": c.aadhaar_file
#     })


# @app.route("/candidates/<int:candidate_id>/request-documents", methods=["POST"])
# def request_documents(candidate_id):
#     db = SessionLocal()
#     candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()

#     if not candidate:
#         return jsonify({"error": "Candidate not found"}), 404

#     message = generate_document_request(candidate.name)
#     email_sent = send_email(
#         to_email=candidate.email,
#         subject="Request for PAN & Aadhaar Verification",
#         message=message
#     )

#     # store the generated message in DB
#     log = DocumentRequestLog(
#         candidate_id=candidate_id,
#         message=message
#     )
#     db.add(log)
#     db.commit()

#     return jsonify({
#         "candidate_id": candidate_id,
#         "message": message,
#         "email_sent": email_sent
#     })

# @app.route("/candidates/<int:candidate_id>/submit-documents", methods=["POST"])
# def submit_documents(candidate_id):
#     db = SessionLocal()
#     c = db.query(Candidate).filter(Candidate.id == candidate_id).first()

#     if not c:
#         return jsonify({"error": "Candidate not found"}), 404

#     pan_file = request.files.get("pan")
#     aadhaar_file = request.files.get("aadhaar")

#     if pan_file:
#         c.pan_file = save_upload(pan_file, "uploads/documents")

#     if aadhaar_file:
#         c.aadhaar_file = save_upload(aadhaar_file, "uploads/documents")

#     db.commit()

#     return jsonify({"status": "documents_uploaded"})


# @app.route("/", methods=["GET"])
# def home():
#     return {"message": "Resume AI Agent Backend Running"}


# if __name__ == "__main__":
#     app.run(debug=True)




































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

# env variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# create tables (only if they don't exist)
Base.metadata.create_all(bind=engine)


# @app.route("/candidates/upload", methods=["POST"])
# def upload_resume():
#     """Handles resume upload and triggers AI extraction."""

#     db = SessionLocal()

#     file = request.files.get("file")
#     if not file:
#         return jsonify({"error": "No file received"}), 400

#     # store file locally
#     saved_path = save_upload(file, "uploads/resumes")

#     # read + clean text from resume
#     resume_text = parse_resume(saved_path)

#     # extract fields from AI agent
#     extracted = extract_details_from_text(resume_text) or {}

#     new_item = Candidate(
#         name=extracted.get("name"),
#         email=extracted.get("email"),
#         phone=extracted.get("phone"),
#         company=extracted.get("company"),
#         designation=extracted.get("designation"),
#         skills=str(extracted.get("skills")),
#         resume_file=saved_path,
#         extraction_status="completed"
#     )

#     db.add(new_item)
#     db.commit()
#     db.refresh(new_item)

#     return jsonify({"id": new_item.id, "status": "uploaded"})









@app.route("/candidates/upload", methods=["POST"])
def upload_resume():
    db = SessionLocal()

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file received"}), 400

    saved_path = save_upload(file, "uploads/resumes")
    resume_text = parse_resume(saved_path)

    extracted = extract_details_from_text(resume_text) or {}
    email = extracted.get("email")

    # if we couldn't detect an email, just make a new entry
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

    # check if candidate already exists
    existing = db.query(Candidate).filter(Candidate.email == email).first()

    if existing:
        # update fields
        existing.name = extracted.get("name")
        existing.phone = extracted.get("phone")
        existing.company = extracted.get("company")
        existing.designation = extracted.get("designation")
        existing.skills = str(extracted.get("skills"))
        existing.resume_file = saved_path
        existing.extraction_status = "updated"

        db.commit()
        return jsonify({"id": existing.id, "status": "updated_existing"})

    # otherwise create new one
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

    # store message for logs
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
