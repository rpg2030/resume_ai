# Resume Agent System — Client Documentation

## Purpose
A full‑stack platform for HR teams to parse resumes, extract candidate information, request and validate KYC documents (PAN/Aadhaar) using AI‑based extraction, and run mock background verification with full auditability and consent tracking.

Login functionality exists in code but is currently disabled and intentionally excluded from this document.

---

## High-Level Flow
- Resume upload
- Resume parsing and candidate data extraction
- Candidate record creation/update
- AI-generated document request (email) and logging
- Candidate PAN/Aadhaar uploads
- AI extraction of document details and comparison with resume
- Confidence and fraud scoring + risk color mapping
- Mock BGV checks (court, social, employment consistency)
- AI candidate summary (optional)
- Consent management and audit trail

---

## Data Model (Key Entities)

### Candidate
- id: int
- name: string
- email: string
- phone: string
- company: string
- designation: string
- skills: text
- dob: string
- resume_file: string
- extraction_status: string
- pan_file: string
- aadhaar_file: string
- upload_time: datetime
- parse_time: datetime
- document_request_time: datetime
- pan_upload_time: datetime
- aadhaar_upload_time: datetime
- ai_logs: text (JSON array of {ts, msg})
- ai_summary: text
- top_skills: text
- pan_validation: text (JSON)
- aadhaar_validation: text (JSON)
- document_fraud: text (JSON; reserved)
- court_check: text (JSON)
- social_scan: text (JSON)
- employment_check: text (JSON)
- consent_given: bool
- consent_time: datetime

### DocumentRequestLog
- id: int
- candidate_id: int
- message: text

---

## Backend API
Base: Backend Flask app
Auth: Not required for the endpoints listed below in current build.

### POST /candidates/upload
- **Purpose**: Upload a resume (PDF/DOCX), parse it, and create/update a candidate.
- **Request**: multipart/form-data
  - file: resume file
- **Responses**:
  - 200 OK: {"id": int, "status": "uploaded" | "updated_existing"}
  - 400 Bad Request: {"error": "No file received"}
- **Side effects**:
  - Saves resume in uploads/resumes
  - Parses text and extracts fields via AI
  - Upserts `Candidate`
  - Sets `upload_time` and `parse_time`
  - Appends `ai_logs` (e.g., "initial parse" or "resume re-uploaded and parsed")

### GET /candidates
- **Purpose**: List candidates for dashboard.
- **Response**: Array of
  - {"id", "name", "email", "company", "extraction_status"}

### GET /candidates/<id>
- **Purpose**: Candidate profile view.
- **Response**:
  - {"id","name","email","phone","company","designation","skills","dob","resume_file","pan_file","aadhaar_file","pan_validation","aadhaar_validation","court_check","social_scan","employment_check","upload_time","parse_time","document_request_time","pan_upload_time","aadhaar_upload_time","consent_given","consent_time"}

### POST /candidates/<id>/request-documents
- **Purpose**: Generate an AI-personalized request message and email the candidate for PAN/Aadhaar.
- **Response**:
  - {"candidate_id": int, "message": string, "email_sent": bool}
- **Side effects**:
  - Updates `document_request_time`
  - Appends message to `ai_logs`
  - Inserts `DocumentRequestLog`

### POST /candidates/<id>/submit-documents
- **Purpose**: Accept PAN/Aadhaar images; run AI extraction and validation; run mock BGV.
- **Request**: multipart/form-data
  - pan: image file (optional)
  - aadhaar: image file (optional)
- **Response**:
  - {"status":"documents_uploaded","pan": <json|null>,"aadhaar": <json|null>,"court": <json>,"social": <json>,"employment": <json>}
- **Validation JSON shape** (for `pan` and `aadhaar`):
  - {"extracted": {...}, "match": {...}, "confidence": 0-100, "fraud_score": 0-100, "color": "green|yellow|red"}
- **Side effects**:
  - Saves documents in uploads/documents; sets `pan_upload_time`/`aadhaar_upload_time`
  - Extracts PAN/Aadhaar details via AI
  - Compares with resume data (name, dob, phone, company)
  - Computes confidence, fraud score, and risk color
  - Runs mock court/social/employment checks
  - Persists all results to `Candidate`

### POST /candidates/<id>/ai-summary
- **Purpose**: Generate AI summary and top skills from resume text.
- **Response**: {"summary": string, "top_skills": stringified list, "confidence": float}
- **Side effects**:
  - Saves `ai_summary`, `top_skills`, `confidence`
  - Appends `ai_logs`

### POST /candidates/<id>/consent
- **Purpose**: Capture candidate consent for KYC.
- **Request JSON**: {"consent": true|false, "note": "optional"}
- **Response**: {"consent": bool, "consent_time": iso8601|null}
- **Side effects**:
  - Sets `consent_given` and `consent_time`
  - Appends `ai_logs` with consent note

### GET /candidates/<id>/audit
- **Purpose**: Retrieve audit trail for a candidate.
- **Response**: {"upload_time","parse_time","document_request_time","pan_upload_time","aadhaar_upload_time","ai_logs"}

### GET /
- **Purpose**: Health check.
- **Response**: {"message":"Backend is running"}

---

## AI vs OCR for PAN/Aadhaar Extraction

- **Why AI-first**
  - More robust on varied layouts, low-quality scans, and noisy backgrounds.
  - Direct structured extraction (name, number, DOB) vs. OCR+regex fragility.

- **Current approach**
  - `extract_pan_via_ai(file)` and `extract_aadhaar_via_ai(file)` extract structured data with an LLM.
  - `compare_with_resume(extracted, resume_data)` checks name/DOB/phone/company.
  - `calculate_confidence(match)` returns a 0–100 score.
  - `calculate_fraud_score(confidence)` inversely maps confidence to risk.
  - `risk_color(confidence)` maps to UI bands:
    - 90–100 → green
    - 60–89 → yellow
    - <60 → red (needs review)

- **Future-ready hybrid (optional)**
  - OCR as primary, AI as fallback on low confidence.
  - Not enabled in current implementation; AI-first is documented here.

---

## Background Verification (Mock Engine)

- **Court Case Search (dummy)**: Simulated lookup using candidate name.
- **Social Footprint Scan (dummy)**: Simulated signals using name/phone.
- **Employment Consistency Check**:
  - Extracts job history from resume text.
  - Flags gaps, overlaps, or anomalies.

Results are stored in `court_check`, `social_scan`, and `employment_check` JSON fields.

---

## Document Fraud Detection (Simple)

- Uses AI-extracted document fields and compares to resume data.
- Key checks: name and DOB consistency; optional phone/company correlation.
- Produces `confidence`, `fraud_score`, and `color` for quick triage.
- Stored in `pan_validation` and `aadhaar_validation`.

---

## Consent & Compliance

- Consent is required before KYC upload (enforced in UI and persisted via `/consent`).
- `consent_given` and `consent_time` are saved per candidate.
- Audit trail supports compliance reviews.

---

## Audit Trail

- Timestamps: `upload_time`, `parse_time`, `document_request_time`, `pan_upload_time`, `aadhaar_upload_time`.
- `ai_logs` includes document requests, AI summary events, and consent notes.
- Available via `GET /candidates/<id>/audit`.

---

## Frontend UX Summary

- **Resume Upload**: Drag-and-drop with progress; on success, navigate to profile/dashboard.
- **Dashboard**: Table shows name, email, company, extraction status.
- **Profile View**:
  - Displays extracted data and validation sections with confidence colors.
  - Actions: Request documents, Upload PAN/Aadhaar, Generate AI Summary.
  - Consent screen before KYC upload (disclaimer + checkbox).
  - BGV section with mock results (court, social, employment consistency).
- **Confidence-based Highlighting**:
  - ≥90: green
  - 60–89: yellow
  - <60: red with “needs review”.

---

## Storage & Configuration

- **Files**
  - Resumes: `backend/uploads/resumes`
  - Documents: `backend/uploads/documents`
- **Database**
  - SQLAlchemy models: `candidates`, `doc_requests`
  - Backed by configured SQLAlchemy engine (e.g., SQLite)
- **Environment**
  - Uses `.env` for provider keys and settings where applicable (AI, email, etc.).

---

## Example Payloads

- **Consent** (POST /candidates/<id>/consent)
```json
{"consent": true, "note": "Agree to KYC verification"}
```

- **AI Summary** (Response)
```json
{"summary": "Senior ML Engineer...", "top_skills": "['Python','NLP','LLMs']", "confidence": 88.0}
```

---

## Operational Notes

- AI extraction methods are defined in `backend/utils/validator.py` and invoked by `/submit-documents`.
- Resume parsing (`parse_resume`) and AI detail extraction (`extract_details_from_text`) run during `/candidates/upload`.
- Email sending for document requests is handled by the email utility and logged via `DocumentRequestLog` and `ai_logs`.

---

## Limitations & Next Steps

- Mock BGV checks; no live government or social APIs are called.
- Consider adding OCR as a primary with AI fallback if required by client policy.
- Add rate limiting and auth when enabling production login/roles.
- Add Postman collection and detailed field-level confidence per attribute if needed by client.
