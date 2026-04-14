import os
from pathlib import Path

BASE_DIR = Path(__file__).parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

    # Database
    DATA_DIR = Path(os.environ.get("DATA_DIR", str(BASE_DIR / "data")))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{DATA_DIR / 'jobs.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Resume storage
    RESUME_DIR = Path(os.environ.get("RESUME_DIR", str(BASE_DIR / "static" / "resume")))

    # Scraping
    MAX_JOBS_PER_REFRESH = int(os.environ.get("MAX_JOBS_PER_REFRESH", 25))
    MATCH_SCORE_THRESHOLD = int(os.environ.get("MATCH_SCORE_THRESHOLD", 50))

    # Claude model
    CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-5")

    @classmethod
    def init_dirs(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.RESUME_DIR.mkdir(parents=True, exist_ok=True)
