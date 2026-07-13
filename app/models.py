"""Database models.

Two source tables (Donor, Product) mirror the company's two databases and are
joined on donor_id. Account holds the login the donor creates on the site.
"""
from datetime import date, datetime, timedelta

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


class Donor(db.Model):
    """One row per donation. Mirrors the donor CSV / database."""

    __tablename__ = "donors"

    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255))
    donation_date = db.Column(db.Date)
    opted_out = db.Column(db.Boolean, default=False, nullable=False)

    products = db.relationship("Product", back_populates="donor", lazy="dynamic")
    account = db.relationship("Account", back_populates="donor", uselist=False)

    def product_count(self) -> int:
        return self.products.count()

    def state_counts(self) -> dict:
        """Map of destination state -> number of products sent there."""
        rows = (
            db.session.query(Product.destination_state, db.func.count(Product.id))
            .filter(Product.donor_pk == self.id, Product.destination_state.isnot(None))
            .group_by(Product.destination_state)
            .all()
        )
        return {state: count for state, count in rows}

    def email_eligible(self, termination_days: int = 365) -> bool:
        """Quarterly emails require an address, no opt-out, and a donation
        within the termination window (1 year by default)."""
        if not self.email or self.opted_out:
            return False
        if self.donation_date is None:
            return False
        return date.today() <= self.donation_date + timedelta(days=termination_days)

    def __repr__(self):
        return f"<Donor {self.donor_id}>"


class Product(db.Model):
    """One row per product created from a donation. Mirrors the product CSV."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(64), unique=True, nullable=False, index=True)
    donor_pk = db.Column(db.Integer, db.ForeignKey("donors.id"), nullable=False)
    product_type = db.Column(db.String(120))
    destination_state = db.Column(db.String(2), index=True)  # e.g. "TX"
    shipped_date = db.Column(db.Date)

    donor = db.relationship("Donor", back_populates="products")

    def __repr__(self):
        return f"<Product {self.serial_number}>"


class Account(UserMixin, db.Model):
    """A login the donor creates on the website using their donor ID."""

    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)
    donor_pk = db.Column(
        db.Integer, db.ForeignKey("donors.id"), unique=True, nullable=False
    )
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    donor = db.relationship("Donor", back_populates="account")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Account {self.email}>"


class EmailLog(db.Model):
    """Record of every quarterly email sent, so a donor is emailed at most
    once per quarter."""

    __tablename__ = "email_log"

    id = db.Column(db.Integer, primary_key=True)
    donor_pk = db.Column(db.Integer, db.ForeignKey("donors.id"), nullable=False)
    quarter = db.Column(db.String(7), nullable=False)  # e.g. "2026-Q3"
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint("donor_pk", "quarter"),)


@login_manager.user_loader
def load_user(account_id: str):
    return db.session.get(Account, int(account_id))
