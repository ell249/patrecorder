# PAT Recorder

A web application for recording, managing, and exporting Portable Appliance Testing (PAT) results in compliance with **AS/NZS 3760**, **AS/NZS 5761**, and **AS/NZS 5762**. Manage an appliance register, log test and repair records, generate PDF certificates, and track what's due for testing — all from a browser.

## Features

- **Appliance register** — add, edit, and soft-delete appliances; track asset number, description, make/model, location, owner, class type, supply type, serial number, and purchase details
- **Test records** — full visual inspection checklist, electrical measurements (earth continuity, insulation resistance, leakage current, polarity, RCD trip time), PASS/FAIL logic, auto-calculated next test due date; covers AS/NZS 3760, 5761, and 5762
- **Repair records** — log ad-hoc repairs against any appliance with date, technician, description, parts cost, labour time, and photos; automatically locked once a subsequent test is recorded, preserving a tamper-evident history
- **PDF certificate export** — professional A4 certificates per test standard, including appliance details, measurements, technician info, timestamp, and embedded QR code; separate repair history PDF per appliance
- **New to Service pathway** — flag appliances as new to service per AS/NZS 3760 cl. 1.2.1.1; set entry-to-service date and retest interval on the appliance record; print a compliant cord-wrap NTS label including entry date, next test due date, and the required "not tested" statement (cl. 2.5.2.1(c)); dashboard separates NTS-not-yet-due appliances from those requiring immediate testing
- **Dashboard** — counts of active appliances, tests due in the next 30 days, and tests required (overdue, never tested, or repaired since last test); due-for-testing table with reason badges and quick-action buttons
- **Global search** — searches appliance details, test comments, and repair descriptions; results grouped by type with matched-field snippets
- **First-run setup wizard** — browser-based database configuration; automatically creates the database, runs all migrations, and seeds default retest rules; activates automatically when the database is not configured or unreachable
- **Migration status page** — shows current schema revision and pending migrations; apply them with one click without CLI access
- **Safe Work Method Statements** — printable SWMS for PAT testing and appliance repair; linked from the top of each respective form

## Support

<a href="https://www.buymeacoffee.com/ell249" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

If you find PAT Recorder useful, consider [buying me a coffee](https://buymeacoffee.com/ell249) — it's always appreciated!

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Framework | Flask |
| ORM | SQLAlchemy + Flask-Migrate (Alembic) |
| Database | MySQL 5.7+ / MariaDB 10.4+ |
| Templates | Jinja2 + Bootstrap 5 |
| PDF generation | WeasyPrint |
| QR codes | qrcode[pil] |
| Deployment | Docker / Gunicorn |

## Quick Start

See [INSTALL.md](INSTALL.md) for full installation instructions.

```bash
cp Dockerfile.example Dockerfile
cp config.example.py config.py
docker build -t patrecorder .
./start.sh
```

Open `http://<host-ip>:5090` — the app will redirect you to the **Setup** page on first run. Enter your MySQL credentials and click **Set Up Database**.

## Usage

1. **Setup** — on first run the app redirects to `/setup`; enter MySQL credentials and click *Set Up Database* to create the schema and seed defaults
2. **Add a tester** — go to *Testers* and register each certified technician before recording tests
3. **Add an appliance** — click *Add Appliance*, fill in the asset details, and save
4. **New to service** — if the appliance is new from the supplier, tick *New to Service* when adding it, set the entry date and retest interval, and print an NTS label from the appliance detail page; the dashboard will exclude it from the overdue list until the interval elapses
5. **Record a test** — open the appliance, click *Add Test*, select the standard, complete the checklist and measurements, and save
6. **Record a repair** — click *Add Repair* on any appliance; the repair is automatically locked once a subsequent test is saved
7. **Export PDF** — from any test or repair record, click *Export PDF* to download a formatted certificate
8. **Check the dashboard** — the dashboard surfaces everything overdue or due within 30 days, flags appliances repaired since their last test, and lists NTS appliances not yet due for their first test

## Project Structure

```
patrecorder/
├── app.py               # Flask app factory + first-run redirect
├── label.py             # Brother QL label image generation (test labels + NTS labels)
├── config.py            # Database URI and app config
├── models.py            # ORM models (Appliance, Tester, TestRecord, RepairRecord, …)
├── views.py             # Route handlers
├── utils.py             # PDF generation, QR codes, helper functions
├── setup.py             # First-run setup wizard routes
├── requirements.txt
│
├── sql/
│   ├── create_database.sql
│   ├── create_tables.sql
│   └── insert_default_retest_rules.sql
│
├── static/
│   ├── css/
│   ├── swms.html            # SWMS — PAT testing
│   ├── swms_repair.html     # SWMS — appliance repair
│   └── uploads/
│       ├── tests/
│       └── repairs/
│
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── appliance_list.html
    ├── appliance_detail.html
    ├── appliance_form.html
    ├── test_form.html
    ├── test_detail.html
    ├── repair_form.html
    ├── repair_detail.html
    ├── search_results.html
    ├── setup.html
    ├── setup_status.html
    └── pdf/
        ├── test_3760.html
        ├── test_5761.html
        ├── test_5762.html
        └── repair_history.html
```

## Licence

MIT — see [LICENCE](LICENCE).

## Use of AI

Please note that AI (Claude) was used in the creation of this code.
