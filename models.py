"""
models.py
---------
Database models and data-loading helpers.
"""

import os
import sqlite3

import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ── Paths ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RISK_DB = os.path.join(BASE_DIR, "data", "database", "risk_analysis.db")
MIX_CSV = os.path.join(BASE_DIR, "data", "processed", "investment_mix_results.csv")
RETURNS_CSV = os.path.join(BASE_DIR, "data", "processed", "returns_summary.csv")
ETA_CSV = os.path.join(BASE_DIR, "data", "processed", "eta_summary.csv")
PROCESSED_CSV = os.path.join(BASE_DIR, "data", "processed", "processed_prices.csv")
REPORT_TXT = os.path.join(BASE_DIR, "data", "reports", "final_report.txt")
REPORT_CSV_PATH = os.path.join(BASE_DIR, "data", "reports", "final_report.csv")
SPREADING_TXT = os.path.join(BASE_DIR, "data", "reports", "spreading_rules_report.txt")
FORECAST_CSV = os.path.join(BASE_DIR, "data", "processed", "price_forecast.csv")


# ── User model ───────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # Alert preferences
    alert_high_risk = db.Column(db.Boolean, default=True)
    alert_downward_trend = db.Column(db.Boolean, default=True)
    alert_daily_summary = db.Column(db.Boolean, default=False)

    investments = db.relationship('UserInvestment', backref='user', lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


# ── Investment Model ──────────────────────────────────────────────────
class UserInvestment(db.Model):
    __tablename__ = "user_investments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    crypto_data = db.Column(db.Text, nullable=False) # JSON string of allocation
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

# ── Data helpers ─────────────────────────────────────────────────────
def load_risk_results() -> pd.DataFrame:
    if not os.path.exists(RISK_DB):
        return pd.DataFrame()
    conn = sqlite3.connect(RISK_DB)
    df = pd.read_sql_query(
        """SELECT crypto_name, risk_level, trend, adjusted_eta, timestamp
           FROM risk_results
           WHERE timestamp = (SELECT MAX(timestamp) FROM risk_results)""",
        conn,
    )
    conn.close()
    return df


def load_investment_mixes() -> pd.DataFrame:
    if not os.path.exists(MIX_CSV):
        return pd.DataFrame()
    return pd.read_csv(MIX_CSV)


def load_returns_summary() -> pd.DataFrame:
    if not os.path.exists(RETURNS_CSV):
        return pd.DataFrame()
    return pd.read_csv(RETURNS_CSV)


def load_eta_summary() -> pd.DataFrame:
    if not os.path.exists(ETA_CSV):
        return pd.DataFrame()
    return pd.read_csv(ETA_CSV)


def load_processed_prices() -> pd.DataFrame:
    if not os.path.exists(PROCESSED_CSV):
        return pd.DataFrame()
    return pd.read_csv(PROCESSED_CSV)


def load_report_text() -> str:
    if not os.path.exists(REPORT_TXT):
        return "No report generated yet. Run the analysis pipeline first."
    with open(REPORT_TXT, "r") as f:
        return f.read()


def load_spreading_report() -> str:
    if not os.path.exists(SPREADING_TXT):
        return ""
    with open(SPREADING_TXT, "r") as f:
        return f.read()


def load_forecast() -> pd.DataFrame:
    if not os.path.exists(FORECAST_CSV):
        return pd.DataFrame()
    return pd.read_csv(FORECAST_CSV)
