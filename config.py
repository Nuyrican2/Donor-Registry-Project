"""Central configuration, loaded from environment variables (.env)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _default_sqlite_path() -> Path:
    """SQLite must not live in a OneDrive/Dropbox-synced folder — sync can
    corrupt the file while the app is writing to it. Default to LOCALAPPDATA."""
    root = Path(os.environ.get("LOCALAPPDATA", BASE_DIR)) / "DonorRegistry"
    root.mkdir(parents=True, exist_ok=True)
    return root / "donor_registry.db"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{_default_sqlite_path()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Public URL of the site, used to build links inside emails.
    SITE_URL = os.environ.get("SITE_URL", "http://localhost:5000")

    # Password that gates the /admin page.
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

    # Quarterly emails stop this many days after the donation date.
    EMAIL_TERMINATION_DAYS = 365

    # SMTP / Flask-Mail
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 25))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "false").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "Donor Program <no-reply@example.com>"
    )

    # When true, emails are printed to the console instead of sent (for dev).
    MAIL_SUPPRESS_SEND = os.environ.get("MAIL_SUPPRESS_SEND", "false").lower() == "true"
