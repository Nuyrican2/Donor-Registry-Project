"""Public opt-out endpoint hit from the unsubscribe link in emails."""
from flask import Blueprint, render_template

from ..extensions import db
from .service import verify_optout_token

emails_bp = Blueprint("emails", __name__)


@emails_bp.route("/opt-out/<token>")
def opt_out(token: str):
    donor = verify_optout_token(token)
    if donor is None:
        return render_template("emails/optout.html", success=False), 404

    donor.opted_out = True
    db.session.commit()
    return render_template("emails/optout.html", success=True)
