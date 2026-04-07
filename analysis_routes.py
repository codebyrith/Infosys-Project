"""
analysis_routes.py
------------------
Blueprint for risk analysis, reports, and running the full pipeline.
"""

import os
import io
import sys
import subprocess

from flask import (
    Blueprint, render_template, flash, redirect,
    url_for, send_file, request, Response,
)
from flask_login import login_required, current_user

from models import (
    load_risk_results,
    load_report_text,
    load_spreading_report,
    load_forecast,
    load_processed_prices,
    REPORT_CSV_PATH,
    FORECAST_CSV,
)

analysis_bp = Blueprint("analysis", __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_TXT = os.path.join(BASE_DIR, "data", "reports", "final_report.txt")


@analysis_bp.route("/forecast")
@login_required
def forecast():
    forecast_df = load_forecast()
    forecast_records = forecast_df.to_dict("records") if not forecast_df.empty else []
    return render_template("forecast.html", forecast_data=forecast_records)


@analysis_bp.route("/run-forecast", methods=["POST"])
@login_required
def run_forecast():
    days = request.form.get("days", "30")
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(BASE_DIR, "price_forecast.py"), days],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
            timeout=120,
        )
        if result.returncode == 0:
            flash("Forecast generated successfully!", "success")
        else:
            flash("Forecast failed: " + result.stderr[:200], "danger")
    except subprocess.TimeoutExpired:
        flash("Forecast timed out.", "danger")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    return redirect(url_for("analysis.forecast"))


@analysis_bp.route("/download-forecast")
@login_required
def download_forecast():
    if os.path.exists(FORECAST_CSV):
        return send_file(FORECAST_CSV, as_attachment=True, download_name="price_forecast.csv")
    flash("No forecast file available.", "warning")
    return redirect(url_for("analysis.forecast"))


@analysis_bp.route("/risk-analysis")
@login_required
def risk_analysis():
    risk_df = load_risk_results()
    risk_records = risk_df.to_dict("records") if not risk_df.empty else []
    return render_template("risk_analysis.html", risk_data=risk_records)


@analysis_bp.route("/reports")
@login_required
def reports():
    report_text = load_report_text()
    spreading_text = load_spreading_report()
    return render_template(
        "reports.html",
        report_text=report_text,
        spreading_text=spreading_text,
    )


@analysis_bp.route("/download-report")
@login_required
def download_report():
    if os.path.exists(REPORT_TXT):
        return send_file(REPORT_TXT, as_attachment=True, download_name="final_report.txt")
    flash("No report available to download.", "warning")
    return redirect(url_for("analysis.reports"))


@analysis_bp.route("/download-csv")
@login_required
def download_csv():
    if os.path.exists(REPORT_CSV_PATH):
        return send_file(REPORT_CSV_PATH, as_attachment=True, download_name="final_report.csv")
    flash("No CSV report available.", "warning")
    return redirect(url_for("analysis.reports"))


@analysis_bp.route("/download-pdf")
@login_required
def download_pdf():
    report_text = load_report_text()
    if report_text.startswith("No report"):
        flash("No report available to download.", "warning")
        return redirect(url_for("analysis.reports"))

    # Generate a simple text-based PDF
    try:
        pdf_bytes = _generate_text_pdf(report_text)
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment; filename=final_report.pdf"},
        )
    except Exception:
        # Fallback: download as .txt if PDF generation fails
        return send_file(REPORT_TXT, as_attachment=True, download_name="final_report.txt")


def _generate_text_pdf(text: str) -> bytes:
    """Generate a minimal PDF from plain text using fpdf2 if available, else raw PDF."""
    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", size=9)
        for line in text.split("\n"):
            pdf.cell(0, 5, line, ln=True)
        return pdf.output()
    except ImportError:
        # Minimal raw PDF as fallback
        buf = io.BytesIO()
        lines = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").split("\n")
        y = 750
        stream_lines = []
        for line in lines:
            if y < 50:
                break
            stream_lines.append(f"BT /F1 9 Tf 50 {y} Td ({line}) Tj ET")
            y -= 12
        stream = "\n".join(stream_lines)
        content = (
            "%PDF-1.4\n"
            "1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            "2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
            "/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
            f"4 0 obj<</Length {len(stream)}>>stream\n{stream}\nendstream\nendobj\n"
            "5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Courier>>endobj\n"
            "xref\n0 6\n"
            "trailer<</Size 6/Root 1 0 R>>\nstartxref\n0\n%%EOF"
        )
        buf.write(content.encode("latin-1"))
        return buf.getvalue()


@analysis_bp.route("/run-analysis", methods=["GET", "POST"])
@login_required
def run_analysis():
    output = None
    success = None

    if request.method == "POST":
        main_script = os.path.join(BASE_DIR, "main.py")
        try:
            result = subprocess.run(
                [sys.executable, main_script],
                capture_output=True,
                text=True,
                cwd=BASE_DIR,
                timeout=300,
            )
            output = result.stdout + result.stderr
            success = result.returncode == 0

            if success:
                _send_user_alert(current_user.email)
                flash("Analysis pipeline completed successfully!", "success")
            else:
                flash("Analysis pipeline failed. Check the output below.", "danger")

        except subprocess.TimeoutExpired:
            output = "Pipeline timed out after 5 minutes."
            success = False
            flash("Analysis pipeline timed out.", "danger")
        except Exception as e:
            output = str(e)
            success = False
            flash(f"Error running pipeline: {e}", "danger")

    return render_template("run_analysis.html", output=output, success=success)


def _send_user_alert(recipient_email: str) -> None:
    try:
        from email_alert import load_risk_results as load_alerts
        from email_alert import filter_alerts, build_email_body, send_email

        risk_df = load_alerts()
        alert_df = filter_alerts(risk_df)
        if alert_df.empty:
            return

        body = build_email_body(alert_df)
        subject = "Crypto Risk Alert – Action Required"
        send_email(subject, body, recipient_email=recipient_email)
    except Exception:
        pass
