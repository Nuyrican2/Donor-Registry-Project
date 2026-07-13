"""Password-gated admin page.

Two buttons live here:
  * Refresh data — upload the latest donors/products CSV exports; every
    donor dashboard reflects the new data immediately.
  * Send quarterly emails — runs the eligibility rules and sends this
    quarter's batch (with a dry-run option to preview who would get one).
"""
from functools import wraps

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..models import Account, Donor, Product
from ..services.importer import import_donors, import_products
from ..emails.service import send_quarterly_emails

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)

    return wrapped


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    from flask import current_app

    if request.method == "POST":
        if request.form.get("password") == current_app.config["ADMIN_PASSWORD"]:
            session["is_admin"] = True
            return redirect(url_for("admin.home"))
        flash("Wrong admin password.", "error")
    return render_template("admin/login.html")


@admin_bp.route("/logout")
def logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@admin_required
def home():
    stats = {
        "donors": Donor.query.count(),
        "products": Product.query.count(),
        "accounts": Account.query.count(),
        "opted_out": Donor.query.filter_by(opted_out=True).count(),
    }
    return render_template("admin/home.html", stats=stats)


@admin_bp.route("/import", methods=["POST"])
@admin_required
def import_csv():
    donors_file = request.files.get("donors_csv")
    products_file = request.files.get("products_csv")

    if donors_file and donors_file.filename:
        result = import_donors(donors_file)
        flash(f"Donors: {result['created']} created, {result['updated']} updated.", "success")
    if products_file and products_file.filename:
        result = import_products(products_file)
        msg = f"Products: {result['created']} created, {result['updated']} updated."
        if result["skipped"]:
            msg += f" Skipped (no matching donor): {', '.join(result['skipped'][:10])}"
        flash(msg, "success" if not result["skipped"] else "error")
    if not (donors_file and donors_file.filename) and not (
        products_file and products_file.filename
    ):
        flash("Choose at least one CSV file to import.", "error")

    return redirect(url_for("admin.home"))


@admin_bp.route("/send-emails", methods=["POST"])
@admin_required
def send_emails():
    dry_run = request.form.get("dry_run") == "on"
    summary = send_quarterly_emails(dry_run=dry_run)
    verb = "Would send" if dry_run else "Sent"
    flash(
        f"{verb} {len(summary['sent'])} email(s) for {summary['quarter']}; "
        f"{len(summary['skipped'])} skipped.",
        "success",
    )
    return redirect(url_for("admin.home"))
