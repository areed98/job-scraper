from flask import Flask
from config import Config
from .extensions import db, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    config_class.init_dirs()

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Blueprints
    from .routes.jobs import jobs_bp
    from .routes.resume import resume_bp
    from .routes.settings import settings_bp

    app.register_blueprint(jobs_bp)
    app.register_blueprint(resume_bp, url_prefix="/resume")
    app.register_blueprint(settings_bp, url_prefix="/settings")

    # Import models so Flask-Migrate can detect them
    from . import models  # noqa: F401

    return app
