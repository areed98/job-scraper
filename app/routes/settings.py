from flask import Blueprint, render_template
from ..models import ResumeProfile

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/")
def index():
    profile = ResumeProfile.query.filter_by(is_active=True).order_by(ResumeProfile.id.desc()).first()
    return render_template("settings/index.html", profile=profile)
