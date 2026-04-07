"""
app.py
------
Main Flask application – ties together all blueprints,
configures authentication, and starts the development server.

Run:
    python app.py
"""

import os
import secrets

from flask import Flask
from flask_login import LoginManager

from models import db, User
from auth_routes import auth_bp
from dashboard_routes import dashboard_bp
from analysis_routes import analysis_bp

# ── Paths ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DB = os.path.join(BASE_DIR, "data", "database", "users.db")


def create_app() -> Flask:
    """Application factory – builds and configures the Flask app."""
    app = Flask(__name__)

    # ── Configuration ────────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{USER_DB}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ── Initialise extensions ────────────────────────────────────────
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Register blueprints ──────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(analysis_bp)

    # ── Create tables ────────────────────────────────────────────────
    with app.app_context():
        os.makedirs(os.path.dirname(USER_DB), exist_ok=True)
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
