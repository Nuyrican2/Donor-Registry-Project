# Donor Impact Portal

A small Flask application that connects the company's two data sources
(donors and products, joined on **donor ID**) and turns them into:

1. **Quarterly impact emails** — each eligible donor gets an email with the
   number of products their donation created, their donor ID, a link to this
   site, and an unsubscribe link.
2. **A donor website** — donors create an account with the donor ID from
   their email, then see a two-tab dashboard:
   - **My Impact** — how many products their donation created, plus a US map
     with a dot on each state that received a product.
   - **Our Mission** — the company's mission, team photos, and a link back to
     the company site.
3. **An admin page** — one button to refresh all dashboards from fresh CSV
   exports, one button to send the quarterly email batch (with dry-run).

## How the pieces fit

```
donors.csv ─┐                            ┌─ quarterly email (count + donor ID + links)
            ├─ importer ──► database ────┤
products.csv┘   (admin      (SQLite,     └─ dashboard (live queries, so an import
                 button)     joined on       instantly updates every donor's view)
                             donor_id)
```

Business rules built in:

- Registration only works with a donor ID that exists in the imported data;
  one account per donor. The dashboard data exists before the account does —
  registering just activates access.
- Quarterly emails go only to donors who: have an email on file, have not
  opted out, donated **within the last year** (the termination period,
  configurable via `EMAIL_TERMINATION_DAYS` in [config.py](config.py)), and
  have not already received this quarter's email.
- Every email carries a signed one-click unsubscribe link.

## Project layout

```
run.py                     Dev entry point
config.py                  All configuration (reads .env)
app/
  models.py                Donor, Product, Account, EmailLog
  auth/routes.py           Register (donor-ID gated), login, logout
  dashboard/routes.py      Impact tab, mission tab, /api/impact JSON
  admin/routes.py          CSV import + send-emails buttons (password gated)
  emails/service.py        Quarterly email builder, eligibility, opt-out tokens
  emails/routes.py         /opt-out/<token> endpoint
  services/importer.py     CSV upsert logic for both files
  templates/               Jinja pages + the email (HTML and plain-text)
  static/                  Styles, US map script, placeholder images
scripts/
  import_csv.py            CLI alternative to the admin import button
  send_quarterly.py        CLI alternative to the send button (schedulable)
data/
  sample_donors.csv        Fake data showing the expected CSV columns
  sample_products.csv
```

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env     # then edit .env: SECRET_KEY, ADMIN_PASSWORD, SMTP
python run.py              # http://localhost:5000
```

Load the sample data to try it out:

```powershell
python scripts/import_csv.py data/sample_donors.csv data/sample_products.csv
```

Then visit `http://localhost:5000/register` and sign up with donor ID
`D-000001`, or go to `http://localhost:5000/admin` for the admin page.

## Expected CSV formats

**donors.csv** — one row per donation:

| column | example | notes |
|---|---|---|
| `donor_id` | `D-000001` | unique key joining the two files |
| `email` | `person@example.com` | may be blank (no emails sent) |
| `donation_date` | `2026-03-14` | `YYYY-MM-DD` or `MM/DD/YYYY` |

**products.csv** — one row per product made from a donation:

| column | example | notes |
|---|---|---|
| `serial_number` | `SN-10001` | unique per product |
| `donor_id` | `D-000001` | must match a donor row |
| `product_type` | `Amniotic membrane graft` | free text |
| `destination_state` | `TX` | two-letter US state code |
| `shipped_date` | `2026-04-01` | optional |

Imports are upserts: re-importing a fresh export updates existing rows and
adds new ones, and every dashboard reflects it immediately.

## The quarterly send

Manual: log into `/admin`, keep **Dry run** checked to preview the recipient
list, then uncheck it and click send. Or from the command line:

```powershell
python scripts/send_quarterly.py --dry-run
python scripts/send_quarterly.py
```

To automate it, schedule `scripts/send_quarterly.py` with Windows Task
Scheduler or cron for the first day of each quarter — the once-per-quarter
guard (`EmailLog`) makes repeat runs harmless.

## Important notes for production

- **Privacy:** donor emails + donation dates are sensitive (health-adjacent)
  data. Keep real CSVs out of git (`.gitignore` already excludes
  `data/*.csv`), use HTTPS in production, and check with the company whether
  HIPAA or state privacy rules apply to this data before launch.
- **Database:** SQLite is fine to start; set `DATABASE_URL` in `.env` to move
  to Postgres without code changes.
- **Email deliverability:** use a real transactional email service (SendGrid,
  Postmark, SES) as the SMTP server in `.env` so quarterly emails don't land
  in spam.
- **Secrets:** `SECRET_KEY` signs both sessions and unsubscribe links —
  rotate it and the unsubscribe links in old emails stop working.
