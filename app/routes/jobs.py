from flask import Blueprint, render_template, request, jsonify, current_app
import math
from ..extensions import db
from ..models import Job, Decision
from ..services.scraper import run_scrape
from ..services.claude_client import score_job

jobs_bp = Blueprint("jobs", __name__)


def _str(val, default=""):
    """Convert a value to str, treating NaN/None as the default."""
    if val is None:
        return default
    try:
        if math.isnan(float(val)):
            return default
    except (TypeError, ValueError):
        pass
    return str(val).strip() or default


@jobs_bp.route("/")
def index():
    from ..models import ResumeProfile
    profile = ResumeProfile.query.filter_by(is_active=True).order_by(ResumeProfile.id.desc()).first()
    undecided = (
        Job.query
        .outerjoin(Decision)
        .filter(Decision.id == None)  # noqa: E711
        .order_by(Job.match_score.desc())
        .all()
    )
    decided = (
        Job.query
        .join(Decision)
        .order_by(Decision.decided_at.desc())
        .all()
    )
    return render_template("jobs/index.html", undecided=undecided, decided=decided, profile=profile)


@jobs_bp.route("/jobs/refresh", methods=["POST"])
def refresh():
    """Scrape new jobs and score them. Returns updated job list partial."""
    limit = current_app.config["MAX_JOBS_PER_REFRESH"]
    threshold = current_app.config["MATCH_SCORE_THRESHOLD"]
    search_term = request.form.get("search-term", "software engineer").strip() or "software engineer"

    from ..models import ResumeProfile
    profile = ResumeProfile.query.filter_by(is_active=True).order_by(ResumeProfile.id.desc()).first()
    if not profile:
        return render_template("jobs/_no_resume.html"), 400

    resume_text = profile.extracted_text
    raw_jobs = run_scrape(limit, search_term=search_term)
    added = 0

    for raw in raw_jobs:
        url = _str(raw.get("job_url") or raw.get("url", ""))
        if not url:
            continue
        if Job.query.filter_by(url=url).first():
            continue

        description = _str(raw.get("description"))
        score, analysis = score_job(resume_text, _str(raw.get("title")), description)

        if score < threshold:
            # Still save it so we don't re-fetch, but mark low score
            pass

        job = Job(
            title=_str(raw.get("title"), "Untitled"),
            company=_str(raw.get("company"), "Unknown"),
            location=_str(raw.get("location")),
            url=url,
            description=description,
            source=_str(raw.get("site")),
            match_score=score,
            match_analysis=analysis,
        )
        db.session.add(job)
        added += 1

    db.session.commit()

    undecided = (
        Job.query
        .outerjoin(Decision)
        .filter(Decision.id == None)  # noqa: E711
        .order_by(Job.match_score.desc())
        .all()
    )
    return render_template("jobs/_job_list.html", undecided=undecided, added=added)


@jobs_bp.route("/jobs/<int:job_id>/decision", methods=["POST"])
def decide(job_id):
    """Record yes/no/maybe decision. Returns updated card partial."""
    job = Job.query.get_or_404(job_id)
    choice = request.form.get("choice", "").lower()
    reason = request.form.get("reason", "")

    if choice not in ("yes", "no", "maybe"):
        return "Invalid choice", 400

    if job.decision:
        job.decision.choice = choice
        job.decision.reason = reason
        from datetime import datetime
        job.decision.decided_at = datetime.utcnow()
    else:
        dec = Decision(job_id=job_id, choice=choice, reason=reason)
        db.session.add(dec)

    db.session.commit()
    return render_template("jobs/_job_card.html", job=job)
