"""
auth_routes.py
--------------
Blueprint handling user registration, login, and logout.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from models import db, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET", "POST"])
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Show login form and authenticate user."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Show registration form and create new user."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # Basic validation
        if not username or not email or not password:
            flash("All fields are required.", "warning")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "warning")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "warning")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return render_template("register.html")

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Log the current user out."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
