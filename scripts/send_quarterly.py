"""Send (or preview) this quarter's impact emails from the command line.

Usage:
    python scripts/send_quarterly.py --dry-run   # preview who would get one
    python scripts/send_quarterly.py             # actually send

The same logic runs behind the admin page's "Send quarterly emails" button.
Schedule this script (Task Scheduler / cron) to fully automate the quarterly
send, or keep it manual via the admin page.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.emails.service import send_quarterly_emails


def main():
    dry_run = "--dry-run" in sys.argv
    app = create_app()
    with app.app_context():
        summary = send_quarterly_emails(dry_run=dry_run)

    verb = "Would send" if dry_run else "Sent"
    print(f"{summary['quarter']}: {verb} {len(summary['sent'])} email(s)")
    for donor_id in summary["sent"]:
        print(f"  sent     {donor_id}")
    for donor_id, reason in summary["skipped"]:
        print(f"  skipped  {donor_id} ({reason})")


if __name__ == "__main__":
    main()
