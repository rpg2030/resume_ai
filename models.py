from sqlalchemy import Column, Integer, String, Text
from database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    email = Column(String(200))
    phone = Column(String(50))
    company = Column(String(200))
    designation = Column(String(200))
    skills = Column(Text)

    resume_file = Column(String(300))
    extraction_status = Column(String(50), default="pending")

    pan_file = Column(String(300), nullable=True)
    aadhaar_file = Column(String(300), nullable=True)

class DocumentRequestLog(Base):
    __tablename__ = "doc_requests"

    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer)
    message = Column(Text)
