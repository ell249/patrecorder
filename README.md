# PAT Recorder

A web application for recording, managing, and exporting Portable Appliance Testing (PAT) results in compliance with **AS/NZS 3760**, **AS/NZS 5761**, and **AS/NZS 5762**. Manage an appliance register, log test and repair records, generate PDF certificates, and track what's due for testing — all from a browser.

## Features

- **Appliance register** — add, edit, and soft-delete appliances; track asset number, description, make/model, location, owner, class type (Class I, Class II, Battery/ELV, or Fixed RCD), supply type, serial number, and purchase details; attach multiple documents (invoices, calibration certificates, PDFs, images) to each appliance record
- **Test records** — full visual inspection checklist, electrical measurements (earth continuity, insulation resistance, leakage current, polarity), PASS/FAIL logic, auto-calculated next test due date; covers AS/NZS 3760, 5761, and 5762; AS/NZS 5762 tests link directly to one or more existing repair records and record up to five structured functional tests each with method description and PASS/FAIL result; Battery/ELV appliances use a simplified visual and functional inspection form with no electrical tests and no retest interval
- **RCD testing** — selecting the "Lead + RCD" test type adds an RCD Test section (RCD Type, Waveform, Rating) alongside the standard visual/electrical checks, with either a push-button PASS/FAIL result or a trip-time test recording results at 0° and 180°, auto-evaluated against the AS/NZS 3760 limits (≤ 40 ms for Type I/10 mA, ≤ 300 ms for Type II/30 mA)
- **Switchboards & Fixed RCDs** — a dedicated "Fixed RCD" appliance class for RCDs mounted at a switchboard, which skips the visual inspection and electrical test sections entirely and only records the RCD test; Switchboards are a first-class register (add, edit, list, detail) that Fixed RCD appliances link to, with a per-switchboard RCD compliance report (PDF) listing every RCD's latest result and test date; the dashboard highlights switchboards with RCDs that are overdue, never tested, or due within 30 days, per the AS/NZS 3760:2022 intervals (6-monthly push-button test; 12-monthly trip-time test in hostile/industrial environments, 24-monthly in non-hostile environments)
- **Repair records** — log ad-hoc repairs against any appliance with date, technician, description, parts cost, labour time, and photos; automatically locked once a subsequent test is recorded, preserving a tamper-evident history; Battery/ELV appliances do not require a post-repair electrical safety test
- **PDF certificate export** — professional A4 certificates per test standard, including appliance details, measurements, technician info, timestamp, and embedded QR code; separate repair history PDF per appliance and RCD compliance report PDF per switchboard
- **New to Service pathway** — flag appliances as new to service per AS/NZS 3760 cl. 1.2.1.1; set entry-to-service date and retest interval on the appliance record; print a compliant cord-wrap NTS label including entry date, next test due date, and the required "not tested" statement (cl. 2.5.2.1(c)); dashboard separates NTS-not-yet-due appliances from those requiring immediate testing
- **Dashboard** — counts of active appliances, tests due in the next 30 days, tests required (overdue, never tested, or repaired since last test), and switchboards needing RCD testing; due-for-testing table with reason badges and quick-action buttons
- **Global search** — searches appliance details, test comments, and repair descriptions; results grouped by type with matched-field snippets
- **First-run setup wizard** — browser-based database configuration; automatically creates the database, runs all migrations, and seeds default retest rules; activates automatically when the database is not configured or unreachable
- **Migration status page** — shows current schema revision and pending migrations; apply them with one click without CLI access
- **Safe Work Method Statements** — printable SWMS for PAT testing, appliance repair, and switchboard/fixed RCD testing; linked from the top of each respective form

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
5. **Record a test** — open the appliance, click *Add Test*, select the standard, complete the checklist and measurements, and save; choose "Lead + RCD" as the test type to also record an RCD push-button or trip-time result
6. **Add a switchboard and its fixed RCDs** — go to *Switchboards*, add a switchboard, then click *Add RCD* from the switchboard detail page to register a Fixed RCD appliance against it; testing a Fixed RCD only asks for the RCD result (no visual/electrical checklist)
7. **Record a repair** — click *Add Repair* on any appliance; the repair is automatically locked once a subsequent test is saved
8. **Export PDF** — from any test or repair record, click *Export PDF* to download a formatted certificate; from a switchboard, click *Download RCD Report* for a consolidated compliance PDF of every RCD on that board
9. **Check the dashboard** — the dashboard surfaces everything overdue or due within 30 days, flags appliances repaired since their last test, lists NTS appliances not yet due for their first test, and highlights switchboards with RCDs needing testing

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
│   ├── swms.html                    # SWMS — PAT testing
│   ├── swms_repair.html             # SWMS — appliance repair
│   ├── swms_switchboard_rcd.html    # SWMS — switchboard / fixed RCD testing
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
    ├── switchboard_list.html
    ├── switchboard_form.html
    ├── switchboard_detail.html
    ├── search_results.html
    ├── setup.html
    ├── setup_status.html
    └── pdf/
        ├── test_3760.html
        ├── test_5761.html
        ├── test_5762.html
        ├── test_fixed_rcd.html
        ├── repair_history.html
        └── switchboard_rcd_report.html
```

## Licence

MIT — see [LICENCE](LICENCE).

## Use of AI

Please note that AI (Claude) was used in the creation of this code.
