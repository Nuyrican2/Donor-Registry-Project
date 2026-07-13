"""Account creation and login.

Registration is gated by donor ID: an account can only be created for a
donor_id that already exists in the imported data, and each donor gets at
most one account. The dashboard data exists whether or not an account has
been created yet — registering just "activates" access to it.
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..models import Account, Donor

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.impact"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        donor_id = request.form.get("donor_id", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        donor = Donor.query.filter_by(donor_id=donor_id).first()
        if donor is None:
            flash("We couldn't find that donor ID. Please check the ID from your email.", "error")
        elif donor.account is not None:
            flash("An account already exists for this donor ID. Try logging in.", "error")
        elif Account.query.filter_by(email=email).first() is not None:
            flash("An account with this email already exists.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        else:
            account = Account(donor=donor, email=email)
            account.set_password(password)
            db.session.add(account)
            db.session.commit()
            login_user(account)
            flash("Welcome! Your account is active.", "success")
            return redirect(url_for("dashboard.impact"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        account = Account.query.filter_by(email=email).first()
        if account and account.check_password(password):
            login_user(account)
            return redirect(url_for("dashboard.impact"))
        flash("Invalid email or password.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
