import os
from pathlib import Path
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, current_app, send_from_directory
)
from werkzeug.utils import secure_filename
from ..extensions import db
from ..models import Job, TailoredResume, ResumeProfile
from ..services.pdf_service import extract_text_from_pdf, generate_pdf
from ..services.claude_client import tailor_resume

resume_bp = Blueprint("resume", __name__)

ALLOWED_EXTENSIONS = {"pdf"}


def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@resume_bp.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("resume")
        if not file or not _allowed(file.filename):
            return render_template("resume/upload.html", error="Please upload a PDF file.")

        filename = secure_filename(file.filename)
        resume_dir = current_app.config["RESUME_DIR"]
        save_path = resume_dir / filename
        file.save(str(save_path))

        extracted = extract_text_from_pdf(str(save_path))

        # Deactivate previous profiles
        ResumeProfile.query.update({"is_active": False})
        profile = ResumeProfile(filename=filename, extracted_text=extracted, is_active=True)
        db.session.add(profile)
        db.session.commit()

        return redirect(url_for("settings.index"))

    return render_template("resume/upload.html")


@resume_bp.route("/tailor/<int:job_id>")
def tailor(job_id):
    """Generate tailored resume for a job (or return cached). Returns modal partial."""
    job = Job.query.get_or_404(job_id)

    profile = ResumeProfile.query.filter_by(is_active=True).order_by(ResumeProfile.id.desc()).first()
    if not profile:
        return "<p class='text-red-500'>No resume uploaded yet.</p>", 400

    tr = job.tailored_resume
    if not tr:
        tailored_text, diff_html = tailor_resume(profile.extracted_text, job.title, job.description)
        tr = TailoredResume(
            job_id=job_id,
            original_text=profile.extracted_text,
            tailored_text=tailored_text,
            diff_html=diff_html,
        )
        db.session.add(tr)
        db.session.commit()

    return render_template("resume/diff_modal.html", job=job, tr=tr)


@resume_bp.route("/approve/<int:job_id>", methods=["POST"])
def approve(job_id):
    """Generate PDF from approved tailored resume."""
    job = Job.query.get_or_404(job_id)
    tr = TailoredResume.query.filter_by(job_id=job_id).first_or_404()

    resume_dir = current_app.config["RESUME_DIR"]
    pdf_filename = f"tailored_{job_id}_{secure_filename(job.company)}_{secure_filename(job.title)}.pdf"
    pdf_path = resume_dir / pdf_filename

    generate_pdf(tr.tailored_text, str(pdf_path))

    tr.approved = True
    tr.approved_at = datetime.utcnow()
    tr.pdf_path = f"resume/{pdf_filename}"
    db.session.commit()

    return render_template("resume/approved.html", job=job, tr=tr)


@resume_bp.route("/download/<int:job_id>")
def download(job_id):
    tr = TailoredResume.query.filter_by(job_id=job_id).first_or_404()
    if not tr.pdf_path:
        return "No PDF generated yet.", 404
    resume_dir = current_app.config["RESUME_DIR"]
    filename = Path(tr.pdf_path).name
    return send_from_directory(str(resume_dir), filename, as_attachment=True)
