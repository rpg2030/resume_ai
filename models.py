from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float
from database import Base
import datetime
import json


def now_utc():
    return datetime.datetime.utcnow()

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True)
    phone = Column(String(200), nullable=True)
    company = Column(String(200), nullable=True)
    designation = Column(String(200), nullable=True)
    skills = Column(Text, nullable=True)
    dob = Column(String(200), nullable=True)

    resume_file = Column(String(300), nullable=True)
    extraction_status = Column(String(50), default="pending", nullable=True)

    pan_file = Column(String(300), nullable=True)
    aadhaar_file = Column(String(300), nullable=True)

    # New functionality
    upload_time = Column(DateTime, default=None, nullable=True)
    parse_time = Column(DateTime, default=None, nullable=True)
    document_request_time = Column(DateTime, default=None, nullable=True)
    pan_upload_time = Column(DateTime, default=None, nullable=True)
    aadhaar_upload_time = Column(DateTime, default=None, nullable=True)
    # ai logs
    ai_logs = Column(Text, default="[]")      
    ai_summary = Column(Text, nullable=True)
    top_skills = Column(Text, nullable=True)
    # validation    
    pan_validation = Column(Text, nullable=True)
    aadhaar_validation = Column(Text, nullable=True)
    document_fraud = Column(Text, nullable=True)

    court_check = Column(Text, nullable=True)
    social_scan = Column(Text, nullable=True)
    employment_check = Column(Text, nullable=True)

    consent_given = Column(Boolean, default=False)
    consent_time = Column(DateTime, default=None, nullable=True)

    def append_ai_log(self, message):
        try:
            logs = json.loads(self.ai_logs or "[]")
        except Exception:
            logs = []
        logs.append({"ts": now_utc().isoformat(), "msg": message})
        self.ai_logs = json.dumps(logs)

class DocumentRequestLog(Base):
    __tablename__ = "doc_requests"

    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer)
    message = Column(Text)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(120), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    password_hash = Column(String(300), nullable=False)
    role = Column(String(50), default="CANDIDATE")  # HR or CANDIDATE
