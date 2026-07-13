"""CSV import: loads the two company exports into the database.

Expected files (see data/sample_*.csv for the format):

donors.csv   -> donor_id, email, donation_date (YYYY-MM-DD)
products.csv -> serial_number, donor_id, product_type, destination_state, shipped_date

Import is an upsert keyed on donor_id / serial_number, so re-running it with
a fresh export simply updates everything. Because dashboards query the
database live, every donor's dashboard reflects the new data immediately —
this is what the admin "Refresh data" button runs.
"""
import csv
import io
from datetime import datetime

from ..extensions import db
from ..models import Donor, Product


def _parse_date(value: str):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date: {value!r}")


def import_donors(file_or_path) -> dict:
    """Upsert donors from a CSV file object or path. Returns counts."""
    created = updated = 0
    for row in _read_rows(file_or_path):
        donor_id = row["donor_id"].strip()
        if not donor_id:
            continue
        donor = Donor.query.filter_by(donor_id=donor_id).first()
        if donor is None:
            donor = Donor(donor_id=donor_id)
            db.session.add(donor)
            created += 1
        else:
            updated += 1
        donor.email = row.get("email", "").strip() or donor.email
        donor.donation_date = _parse_date(row.get("donation_date", "")) or donor.donation_date
    db.session.commit()
    return {"created": created, "updated": updated}


def import_products(file_or_path) -> dict:
    """Upsert products from a CSV file object or path. Returns counts.

    Rows whose donor_id has no matching donor are skipped and reported so
    bad joins are visible instead of silent.
    """
    created = updated = 0
    skipped = []
    for row in _read_rows(file_or_path):
        serial = row["serial_number"].strip()
        donor_id = row["donor_id"].strip()
        if not serial:
            continue
        donor = Donor.query.filter_by(donor_id=donor_id).first()
        if donor is None:
            skipped.append(serial)
            continue
        product = Product.query.filter_by(serial_number=serial).first()
        if product is None:
            product = Product(serial_number=serial, donor=donor)
            db.session.add(product)
            created += 1
        else:
            product.donor = donor
            updated += 1
        product.product_type = row.get("product_type", "").strip() or product.product_type
        state = row.get("destination_state", "").strip().upper()
        product.destination_state = state[:2] if state else product.destination_state
        product.shipped_date = _parse_date(row.get("shipped_date", "")) or product.shipped_date
    db.session.commit()
    return {"created": created, "updated": updated, "skipped": skipped}


def _read_rows(file_or_path):
    """Yield dict rows from a path, bytes stream, or text stream."""
    if hasattr(file_or_path, "read"):
        raw = file_or_path.read()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8-sig")
        stream = io.StringIO(raw)
    else:
        stream = open(file_or_path, newline="", encoding="utf-8-sig")
    with stream:
        for row in csv.DictReader(stream):
            yield {(k or "").strip().lower(): (v or "") for k, v in row.items()}
