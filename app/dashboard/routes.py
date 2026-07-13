"""Donor-facing dashboard: impact tab (count + US map) and mission tab."""
from flask import Blueprint, jsonify, render_template
from flask_login import current_user, login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def impact():
    """Tab 1: number of products created + map of destination states."""
    donor = current_user.donor
    return render_template(
        "dashboard/impact.html",
        donor=donor,
        product_count=donor.product_count(),
    )


@dashboard_bp.route("/mission")
def mission():
    """Tab 2: company mission, photos, and team. Public page."""
    return render_template("dashboard/mission.html")


@dashboard_bp.route("/api/impact")
@login_required
def impact_data():
    """JSON consumed by the map script: product totals per destination state.

    The data is queried live, so any admin CSV import is reflected on the
    next page load — no per-account rebuild needed.
    """
    donor = current_user.donor
    return jsonify(
        {
            "donor_id": donor.donor_id,
            "product_count": donor.product_count(),
            "states": donor.state_counts(),  # e.g. {"TX": 3, "CA": 1}
        }
    )
