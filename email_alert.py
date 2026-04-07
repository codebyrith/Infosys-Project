"""
Email Alert Module
Sends an email alert when any cryptocurrency has HIGH risk
or a DOWNWARD trend, based on data in the SQLite database.

How it works:
  1. Reads risk analysis results from the SQLite database.
  2. Filters rows that have HIGH risk or DOWNWARD trend.
  3. If any risky cryptos are found, builds an alert message
     and sends it via email using SMTP (Gmail by default).
"""

# ── Standard library imports ─────────────────────────────────────────
import os              # For file paths and reading environment variables
import sqlite3         # For connecting to the SQLite database
import smtplib         # For sending emails via an SMTP server
from email.mime.text import MIMEText              # Plain-text email body
from email.mime.multipart import MIMEMultipart    # Email with headers + body

# ── Third-party imports ──────────────────────────────────────────────
import pandas as pd                # Data manipulation (DataFrames)
from dotenv import load_dotenv     # Reads .env file into environment variables

# Load the .env file so that os.getenv() can read our secret credentials
# (email address, password, etc.) without hard-coding them in the source
load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────
# BASE_DIR = folder where this script lives (crypto_investment_manager/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Full path to the SQLite database that stores risk analysis results
DB_PATH = os.path.join(BASE_DIR, "data", "database", "risk_analysis.db")

# ── Email credentials from environment variables ─────────────────────
# These values come from the .env file.  The second argument is a default
# value used if the variable is not set.
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")      # Mail server address
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))                # Mail server port (587 = TLS)
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")                  # Sender's email address
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")              # Sender's app password
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")              # Recipient's email address


# ── Data loading ─────────────────────────────────────────────────────

def load_risk_results() -> pd.DataFrame:
    """
    Connect to the SQLite database, read the entire 'risk_results' table
    into a pandas DataFrame, then close the connection and return the data.
    """
    conn = sqlite3.connect(DB_PATH)                          # Open DB connection
    df = pd.read_sql("SELECT * FROM risk_results", conn)     # Run SQL query → DataFrame
    conn.close()                                             # Always close after reading
    return df


def filter_alerts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the DataFrame to keep only rows that need an alert.
    A row is flagged if:
      - risk_level is 'HIGH'   → the crypto is very volatile/risky
      - trend is 'DOWNWARD'    → the price is trending downward
    Either condition alone is enough to trigger an alert.
    """
    # The '|' operator means OR → keep the row if EITHER condition is True
    mask = (df["risk_level"] == "HIGH") | (df["trend"] == "DOWNWARD")
    return df[mask]


# ── Email builder ────────────────────────────────────────────────────

def build_email_body(alert_df: pd.DataFrame) -> str:
    """
    Build a human-readable plain-text email body that lists every
    cryptocurrency that triggered an alert, along with its risk level
    and trend direction.

    Returns the complete message as a single string.
    """
    lines = []

    # ---- Header section ----
    lines.append("CRYPTO INVESTMENT MANAGER – RISK ALERT")
    lines.append("=" * 50)
    lines.append("")

    # ---- Column headings (left-aligned with padding) ----
    # '<15' means left-align within 15 characters of width
    lines.append(f"{'Crypto':<15} {'Risk Level':<12} {'Trend':<10}")
    lines.append("-" * 50)

    # ---- One line per flagged cryptocurrency ----
    for _, row in alert_df.iterrows():
        lines.append(
            f"{row['crypto_name']:<15} {row['risk_level']:<12} {row['trend']:<10}"
        )

    # ---- Footer / call to action ----
    lines.append("")
    lines.append("Please review your portfolio and take action.")

    # Join all lines with newlines to form the full email body
    return "\n".join(lines)


def send_email(subject: str, body: str, recipient_email: str = None) -> None:
    """
    Send an email using Python's smtplib.

    Args:
        subject:         Email subject line.
        body:            Plain-text email body.
        recipient_email: Override recipient address (used by the web app
                         to send alerts to the logged-in user's email).
                         Falls back to EMAIL_RECEIVER from .env if not provided.

    Steps:
      1. Create a MIMEMultipart message (supports headers + body).
      2. Attach the plain-text body.
      3. Connect to the SMTP server (e.g. smtp.gmail.com on port 587).
      4. Upgrade the connection to TLS (encrypted).
      5. Log in with the sender's credentials.
      6. Send the email to the receiver.
    The 'with' block automatically closes the connection when done.
    """
    receiver = recipient_email or EMAIL_RECEIVER

    # Build the email message object
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER         # Who is sending
    msg["To"] = receiver               # Who receives
    msg["Subject"] = subject           # Email subject line
    msg.attach(MIMEText(body, "plain"))  # Attach the body as plain text

    # Connect, encrypt, authenticate, and send
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()                                        # Upgrade to TLS encryption
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)               # Authenticate
        server.sendmail(EMAIL_SENDER, receiver, msg.as_string())  # Send


def send_user_investment_alerts(risk_df):
    """
    Check all users and their investments. If any of their invested coins
    have a HIGH risk or DOWNWARD trend, send them a personalized email.
    """
    from app import create_app
    from models import db, User, UserInvestment
    import json

    app = create_app()
    with app.app_context():
        users = User.query.all()
        for user in users:
            investments = UserInvestment.query.filter_by(user_id=user.id).all()
            if not investments:
                continue
            
            # Collect all unique coins a user has invested in
            invested_coins = set()
            for inv in investments:
                data = json.loads(inv.crypto_data)
                # data keys are like "Rank", "Score", "Bitcoin", "Ethereum", "Binancecoin"
                # We want just the crypto names
                for k, v in data.items():
                    if isinstance(v, (int, float)) and v > 0 and k not in ("rank", "score", "weighted_return", "weighted_eta", "weighted_risk"):
                        invested_coins.add(k.lower())

            # Check if any invested coin is in trouble
            user_alerts = []
            for _, row in risk_df.iterrows():
                if row['crypto_name'].lower() in invested_coins:
                    if row["risk_level"] == "HIGH" or row["trend"] == "DOWNWARD":
                        user_alerts.append(row)

            if user_alerts:
                alert_df = pd.DataFrame(user_alerts)
                body = build_email_body(alert_df)
                body = f"Hello {user.username},\n\nSome of the coins you invested in are showing risky patterns. " + \
                       "We wanted to let you know so you can protect your investments:\n\n" + body
                
                subject = "Crypto Investment Alert – Action Required"
                # Send email to the user's specific email
                try:
                    if EMAIL_SENDER and EMAIL_PASSWORD:
                        send_email(subject, body, recipient_email=user.email)
                        print(f"Sent investment alert to {user.email}")
                except Exception as e:
                    print(f"Failed to send investment alert to {user.email}: {e}")

# ── Main ─────────────────────────────────────────────────────────────

def main():
    """
    Entry point for the Email Alert module.
    Loads risk data → filters for alerts → sends email if needed.
    """

    # Step 1: Load all risk results from the database
    print("Loading risk results from database...")
    risk_df = load_risk_results()

    # Step 2: Keep only the rows that need an alert (HIGH risk or DOWNWARD trend)
    print("Checking for alerts...")
    alert_df = filter_alerts(risk_df)

    # Step 3: If no risky cryptos found, print a safe message and stop
    if alert_df.empty:
        print("No alerts triggered. All cryptos are within safe levels.")
        return

    # Step 4: Build the email content from the flagged rows
    body = build_email_body(alert_df)
    subject = "Crypto Risk Alert – Action Required"

    # Show the alert in the console as well
    print(f"\nAlert triggered for {len(alert_df)} crypto(s):")
    print(body)

    # Step 5: Try to send the email (only if all credentials are set)
    if EMAIL_SENDER and EMAIL_PASSWORD and EMAIL_RECEIVER:
        try:
            send_email(subject, body)
            print("\nAlert email sent successfully.")
        except Exception as e:
            # If sending fails (wrong password, network issue, etc.) show the error
            print(f"\nFailed to send email: {e}")
    else:
        # Credentials missing → remind the user to set them in .env
        print(
            "\nEmail credentials not configured. "
            "Set EMAIL_SENDER, EMAIL_PASSWORD, and EMAIL_RECEIVER "
            "environment variables to enable email alerts."
        )

    # Step 6: Send personalized alerts to users who have invested in falling coins
    print("\nChecking user investments for personalized alerts...")
    send_user_investment_alerts(risk_df)

# This block runs only when the script is executed directly (not imported)
if __name__ == "__main__":
    main()
