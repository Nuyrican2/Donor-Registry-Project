"""Quarterly impact emails.

Eligibility rules (enforced in send_quarterly_emails):
  1. Donor has an email address on file.
  2. Donor has not opted out.
  3. Donation is within the termination window (1 year by default).
  4. Donor has not already received this quarter's email (EmailLog).

Each email contains the donor's product count, their donor ID (needed to
create an account), a link to the site, and a signed opt-out link.
"""
from datetime import date

from flask import current_app, render_template, url_for
from flask_mail import Message
from itsdangerous import BadSignature, URLSafeSerializer

from ..extensions import db, mail
from ..models import Donor, EmailLog

OPTOUT_SALT = "email-opt-out"


def current_quarter(today: date | None = None) -> str:
    today = today or date.today()
    return f"{today.year}-Q{(today.month - 1) // 3 + 1}"


def optout_token(donor: Donor) -> str:
    s = URLSafeSerializer(current_app.config["SECRET_KEY"], salt=OPTOUT_SALT)
    return s.dumps(donor.donor_id)


def verify_optout_token(token: str) -> Donor | None:
    s = URLSafeSerializer(current_app.config["SECRET_KEY"], salt=OPTOUT_SALT)
    try:
        donor_id = s.loads(token)
    except BadSignature:
        return None
    return Donor.query.filter_by(donor_id=donor_id).first()


def build_message(donor: Donor) -> Message:
    # A request context lets url_for work from the CLI script too, not just
    # from the admin page's request.
    with current_app.test_request_context():
        return _build_message(donor)


def _build_message(donor: Donor) -> Message:
    site_url = current_app.config["SITE_URL"].rstrip("/")
    context = {
        "donor": donor,
        "product_count": donor.product_count(),
        "state_count": len(donor.state_counts()),
        "register_url": f"{site_url}{url_for('auth.register')}",
        "login_url": f"{site_url}{url_for('auth.login')}",
        "optout_url": f"{site_url}{url_for('emails.opt_out', token=optout_token(donor))}",
    }
    msg = Message(
        subject="Your donation's impact this quarter",
        recipients=[donor.email],
        html=render_template("emails/quarterly.html", **context),
        body=render_template("emails/quarterly.txt", **context),
    )
    return msg


def send_quarterly_emails(dry_run: bool = False) -> dict:
    """Send this quarter's email to every eligible donor. Returns a summary."""
    quarter = current_quarter()
    termination_days = current_app.config["EMAIL_TERMINATION_DAYS"]

    sent, skipped = [], []
    for donor in Donor.query.all():
        if not donor.email_eligible(termination_days):
            skipped.append((donor.donor_id, "ineligible"))
            continue
        already = EmailLog.query.filter_by(donor_pk=donor.id, quarter=quarter).first()
        if already:
            skipped.append((donor.donor_id, "already sent this quarter"))
            continue

        if not dry_run:
            mail.send(build_message(donor))
            db.session.add(EmailLog(donor_pk=donor.id, quarter=quarter))
            db.session.commit()
        sent.append(donor.donor_id)

    return {"quarter": quarter, "sent": sent, "skipped": skipped, "dry_run": dry_run}
