# PAT Recorder — Installation Instructions

This document covers system requirements, dependency installation, database setup, and application startup for running PAT Recorder on a local machine or server.

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Install System Dependencies](#2-install-system-dependencies)
3. [Prepare the Project](#3-prepare-the-project)
4. [Create Python Virtual Environment](#4-create-python-virtual-environment)
5. [Install and Configure MySQL](#5-install-and-configure-mysql)
6. [Configure Database Credentials](#6-configure-database-credentials)
7. [Database Migrations](#7-database-migrations)
8. [Create Uploads Directories](#8-create-uploads-directories)
9. [Run the Application](#9-run-the-application)
10. [Docker Deployment (Optional)](#10-docker-deployment-optional)
11. [Development Mode (Optional)](#11-development-mode-optional)
12. [Safe Work Method Statements (SWMS)](#12-safe-work-method-statements-swms)
13. [Troubleshooting](#13-troubleshooting)
14. [Feature Summary](#14-feature-summary)
15. [Support](#15-support)

---

## 1. System Requirements

**Operating System:**
- Ubuntu 22.04+ or Debian 12+ (recommended)
- macOS 13+
- Windows (via WSL2 — required for full WeasyPrint/PDF support)

**Required Software:**
- Python 3.9 or newer
- MySQL 5.7+ or MariaDB 10.4+
- WeasyPrint system dependencies (Cairo, Pango, GObject)

---

## 2. Install System Dependencies

**Ubuntu / Debian:**
```bash
sudo apt update
sudo apt install -y \
    python3 python3-venv python3-pip \
    libffi-dev libcairo2 libpango-1.0-0 \
    libpangocairo-1.0-0 gobject-introspection \
    libgirepository1.0-dev
```

**macOS (Homebrew):**
```bash
brew install python3 cairo pango gobject-introspection
```

**Windows:**

Use WSL2 with Ubuntu for full compatibility:
```bash
wsl --install
```

---

## 3. Prepare the Project

Place (or clone) the project folder anywhere on your system:

```
patrecorder/
```

---

## 4. Create Python Virtual Environment

```bash
cd patrecorder
python3 -m venv env
source env/bin/activate          # Windows WSL: same command
pip install -r requirements.txt
```

---

## 5. Install and Configure MySQL

**Ubuntu:**
```bash
sudo apt install mysql-server
sudo service mysql start
```

**macOS:**
```bash
brew install mysql
brew services start mysql
```

**Create a MySQL user for the application:**
```sql
mysql -u root -p
CREATE USER 'pat_user'@'localhost' IDENTIFIED BY 'yourpassword';
GRANT ALL PRIVILEGES ON test_and_tag.* TO 'pat_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

The database and all tables are created automatically by the first-run setup wizard the first time you start the application (see [Section 9](#9-run-the-application)).

The SQL files in `sql/` are provided as reference material only:

| File | Description |
|------|-------------|
| `sql/create_database.sql` | `CREATE DATABASE` statement |
| `sql/create_tables.sql` | All table definitions |
| `sql/insert_default_retest_rules.sql` | Default retest interval seed data |

**Tables created by the wizard:**

*Core tables:*
| Table | Description |
|-------|-------------|
| `tester` | Certified testers (name, certificate number, phone) |
| `appliance` | Appliance register (asset details, class, disposal info) |
| `retest_rule` | Recommended retest intervals by class/supply type |

*Test tables:*
| Table | Description |
|-------|-------------|
| `test_record` | Test results per AS/NZS 3760, 5761, and 5762 (visual inspection, electrical measurements, overall result) |
| `test_photo` | Photos attached to test records |

*Repair tables:*
| Table | Description |
|-------|-------------|
| `repair_record` | Ad-hoc repair events (description, cost, labour time, lock status, disposal flag) |
| `repair_photo` | Photos attached to repair records |

---

## 6. Configure Database Credentials

Copy the example config:
```bash
cp config.example.py config.py
```

You do not need to edit `config.py` manually. The first-run setup wizard will write the correct database URI into `config.py` automatically when you submit the setup form.

If you prefer to configure it manually, open `config.py` and update:
```python
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://USERNAME:PASSWORD@localhost/test_and_tag"
```

---

## 7. Database Migrations

Database migrations are run automatically by the first-run setup wizard. No migration commands are needed on a fresh install.

For subsequent application updates that include schema changes:
```bash
export FLASK_APP=app.py
flask db upgrade
```

If Flask-Migrate reports `"can't locate revision"`, re-initialise the migrations folder:
```bash
flask db init
flask db migrate -m "initial schema"
flask db upgrade
```

---

## 8. Create Uploads Directories

```bash
mkdir -p static/uploads/tests
mkdir -p static/uploads/repairs
```

---

## 9. Run the Application

```bash
export FLASK_APP=app.py
flask run
```

The application will be available at: **http://127.0.0.1:5000**

On a fresh install (or when the database is not reachable), all requests are automatically redirected to the setup wizard at: **http://127.0.0.1:5000/setup**

Enter your MySQL credentials and click **"Set Up Database"**. The wizard will:

1. Test the connection
2. Create the database if it does not exist
3. Create all tables and run all migrations
4. Seed default retest interval rules
5. Redirect you to the dashboard

No CLI commands are required beyond starting the application.

---

## 10. Docker Deployment (Optional)

Docker lets you run PAT Recorder without installing Python or any system dependencies directly on the host. MySQL must run separately (another container or an existing managed server) — PAT Recorder does not bundle a database.

**Prerequisites:**
- Docker Engine installed on the host
- An accessible MySQL 5.7+ or MariaDB 10.4+ server

### Build the Image

Copy the example Dockerfile and build the image:
```bash
cp Dockerfile.example Dockerfile
docker build -t patrecorder .
```

The image bakes in the application code but **not** the database credentials or uploaded photos — both are supplied at runtime via bind mounts. The Python dependency layer is cached, so incremental rebuilds are fast.

### Prepare Host-Side Files

Create the upload directories before starting the container (Docker would otherwise create them as root-owned, causing permission errors):
```bash
mkdir -p static/uploads/tests static/uploads/repairs
```

Copy the example config so the container has a placeholder on first start:
```bash
cp config.example.py config.py
```

### Start the Container

Copy the example start script and run it:
```bash
cp start.example.sh start.sh
chmod +x start.sh
./start.sh
```

The script runs:
```bash
docker run -d \
  -p 5090:5090 \
  --restart unless-stopped \
  --name patrecorder \
  -v "$PWD/config.py:/app/config.py" \
  -v "$PWD/static/uploads:/app/static/uploads" \
  patrecorder
```

**Bind mounts:**

| Mount | Purpose |
|-------|---------|
| `config.py` | Database credentials. Mounted writable so the in-browser setup wizard can persist credentials after first run. |
| `static/uploads/` | User-uploaded photos. Mounted writable so photos survive container restarts and image upgrades. |

The application will be available at: **http://\<host-ip\>:5090**

### First-Run Setup Inside Docker

On the first visit, all requests redirect to the setup wizard at **http://\<host-ip\>:5090/setup**. Enter the MySQL credentials for your external database server and click **"Set Up Database"**. The wizard will:

1. Test the connection
2. Create the database if it does not exist
3. Create all tables
4. Seed default retest interval rules
5. Write the credentials into `config.py` on the host (via the volume mount)
6. Redirect you to the dashboard

No CLI access to the container is required.

### Applying Future Migrations

After upgrading to a newer image version, navigate to **http://\<host-ip\>:5090/setup/status**. The page shows the current migration revision and any pending updates. Click **"Apply Pending Migrations"** to apply them.

### Container Management Commands

```bash
# View logs
docker logs patrecorder

# Restart after a code update (rebuild first)
docker build -t patrecorder .
docker stop patrecorder && docker rm patrecorder
./start.sh

# Stop the container
docker stop patrecorder
```

---

## 11. Development Mode (Optional)

```bash
export FLASK_ENV=development
flask run
```

Enables automatic reload on file changes and full debug output.

---

## 12. Safe Work Method Statements (SWMS)

Two SWMS documents are included as printable static HTML pages:

| File | Covers |
|------|--------|
| `static/swms.html` | PAT testing — AS/NZS 3760, 5761, 5762 |
| `static/swms_repair.html` | Appliance repair — WHS Act 2011, AS/NZS 5762 |

Links to these documents appear automatically at the top of the Test and Repair forms within the application. They can also be printed directly from a browser (**File → Print → Save as PDF**) to satisfy on-site WHS documentation requirements.

> **IMPORTANT — Review and customise before use:**
>
> The included SWMS documents are provided as a starting-point template only. They reference Commonwealth model WHS legislation and Australian Standards current at the time of writing, but WHS laws vary between states and territories and are updated periodically. Before allowing workers to rely on these documents you must:
>
> 1. Verify that all legislative references (Acts, Regulations, Standards) are correct and current for your jurisdiction and the date of use.
> 2. Update the document header fields — SWMS Reference, Revision, Prepared By, Approved By, and Date — to reflect your organisation's details.
> 3. Review the hazard register and control measures against the specific conditions, equipment, and work environment at your site. Add, remove, or modify entries as required.
> 4. Confirm that PPE specifications and test-pass criteria match your organisation's procedures and any applicable site rules.
> 5. Have the finalised SWMS reviewed and signed off by a competent person (e.g., WHS officer, site manager, or licensed electrician) before use.
> 6. Ensure all workers performing testing or repair work read, understand, and sign the SWMS acknowledgement table prior to commencing work.
> 7. Review the SWMS after any incident, near miss, or change to the work process, and at least annually.
>
> The authors of PAT Recorder accept no liability for the completeness or suitability of these documents for any specific workplace. Compliance with WHS legislation is the responsibility of the PCBU.

---

## 13. Troubleshooting

**PDF generation errors (WeasyPrint) — missing system libraries:**

```bash
# Ubuntu
sudo apt install libcairo2 libpango-1.0-0 libpangocairo-1.0-0

# macOS
brew install cairo pango
```

**MySQL connection refused:**
```bash
sudo service mysql status
sudo service mysql start
```

**Permission denied on uploads folder:**
```bash
chmod -R 755 static/uploads
```

**Migration error — `"can't locate revision"`:**
```bash
rm -rf migrations/
flask db init
flask db migrate -m "initial schema"
flask db upgrade
```

**Migration detects false drift (collation / FK name noise):**

This is normal when Alembic compares SQLAlchemy models against a MySQL schema. Review the generated migration and remove any operations that only rename constraints or change collation without changing column types or sizes.

---

## 14. Feature Summary

After installation the application supports:

**Appliance register**
- Add, edit, and dispose of appliances
- Track asset number, description, make/model, location, owner, class type (Class I / II), appliance type, serial number, purchase date/price, and receipt image
- Record and display creation timestamp

**Test records (AS/NZS 3760, 5761, 5762)**
- Full visual inspection checklist (PASS / FAIL / N/A per field)
- Electrical measurements: earth continuity, insulation resistance, leakage current, polarity test, RCD trip time
- Class-aware defaults (earth continuity N/A for Class I enforced server-side)
- AS/NZS 5761 fields: condition assessment, functional check, safe-for-resale
- AS/NZS 5762 fields: repair description, repaired by, parts replaced, post-repair functional test
- PDF certificate export (WeasyPrint) per standard

**Repair records**
- Log ad-hoc repairs against any appliance
- Fields: repair date, repaired by, description, comments, parts cost ($), labour time (HH:MM), photos
- Repairs automatically locked (read-only) when a subsequent test post-dating the repair is recorded
- Backdate support: repairs created/edited with a date prior to an existing test are locked immediately
- PDF repair history export per appliance

**Dashboard**
- Counts: Active Appliances, Upcoming Tests (next 30 days), Tests Required (overdue + never tested + repaired since last test)
- "Tests Required" tooltip explains all three categories
- Due-for-testing table with reason badges and quick-action buttons

**Global search**
- Searches appliances, test comments/tags, and repair comments/descriptions
- Results grouped by type with matched-field snippets

**First-run setup wizard**
- Browser-based database configuration (no CLI required)
- Automatically creates database, runs all migrations, and seeds default data
- Activated automatically when the database is not configured or unreachable

**Safe Work Method Statements**
- Printable SWMS for PAT testing and for appliance repair
- Linked from the top of each respective form

---

## 15. Support

For help extending or deploying the system, raise an issue or contact the project maintainer.
