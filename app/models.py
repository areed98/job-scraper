from datetime import datetime
from .extensions import db


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))
    url = db.Column(db.String(2048), unique=True, nullable=False)
    description = db.Column(db.Text)
    source = db.Column(db.String(64))          # linkedin / indeed
    match_score = db.Column(db.Integer)        # 0-100
    match_analysis = db.Column(db.Text)        # Claude's reasoning
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)

    decision = db.relationship("Decision", uselist=False, back_populates="job", cascade="all, delete-orphan")
    tailored_resume = db.relationship("TailoredResume", uselist=False, back_populates="job", cascade="all, delete-orphan")

    @property
    def status(self):
        if self.decision:
            return self.decision.choice
        return "undecided"


class Decision(db.Model):
    __tablename__ = "decisions"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False, unique=True)
    choice = db.Column(db.String(16), nullable=False)   # yes / no / maybe
    reason = db.Column(db.Text)
    decided_at = db.Column(db.DateTime, default=datetime.utcnow)

    job = db.relationship("Job", back_populates="decision")


class TailoredResume(db.Model):
    __tablename__ = "tailored_resumes"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False, unique=True)
    original_text = db.Column(db.Text)
    tailored_text = db.Column(db.Text)
    diff_html = db.Column(db.Text)
    approved = db.Column(db.Boolean, default=False)
    approved_at = db.Column(db.DateTime)
    pdf_path = db.Column(db.String(512))       # relative path under static/

    job = db.relationship("Job", back_populates="tailored_resume")


class ResumeProfile(db.Model):
    """Stores the active master resume text extracted from the uploaded PDF."""
    __tablename__ = "resume_profiles"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    extracted_text = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
