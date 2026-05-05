# Installation Guide — PAT Recorder

## Requirements

- Docker (recommended), **or** Python 3.11+ with pip
- MySQL 5.7+ or MariaDB 10.4+ server (can be a remote host)

---

## Option A — Docker (recommended)

### 1. Clone the repository

```bash
git clone <repo-url> patrecorder
cd patrecorder
```

### 2. Build the image

Copy the example Dockerfile and build:

```bash
cp Dockerfile.example Dockerfile
docker build -t patrecorder .
```

The image installs all WeasyPrint system dependencies automatically. Incremental rebuilds are fast because the dependency layer is cached.

### 3. Create the MySQL database

Log into MySQL and create the database and user:

```sql
CREATE DATABASE test_and_tag CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'pat_user'@'%' IDENTIFIED BY 'yourpassword';
GRANT ALL PRIVILEGES ON test_and_tag.* TO 'pat_user'@'%';
FLUSH PRIVILEGES;
```

### 4. Prepare host-side files

Create the upload directories before starting the container (Docker would otherwise create them as root-owned, causing permission errors):

```bash
mkdir -p static/uploads/tests static/uploads/repairs
```

Copy the example config so the container has a placeholder on first start:

```bash
cp config.example.py config.py
```

### 5. Start the container

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

Two bind mounts keep data on the host:

| Mount | Purpose |
|---|---|
| `config.py` | Database credentials. Mounted writable so the setup wizard can persist them after first run. |
| `static/uploads/` | User-uploaded photos. Survives container restarts and image upgrades. |

### 6. Complete setup in the browser

Open `http://<host-ip>:5090` — on first run all requests redirect to the setup wizard at `/setup`. Enter your MySQL credentials and click **Set Up Database**. The wizard will:

1. Test the connection
2. Create the database if it does not exist
3. Create all tables and run all migrations
4. Seed default retest interval rules
5. Write the credentials into `config.py` (via the volume mount)
6. Redirect you to the dashboard

### 7. Verify

Visit `http://<host-ip>:5090/setup/status`. All schema migrations should show as applied. You're ready to add your first appliance.

---

## Option B — Direct Python (no Docker)

### 1. Clone and create a virtual environment

```bash
git clone <repo-url> patrecorder
cd patrecorder
python3 -m venv env
source env/bin/activate
```

### 2. Install system dependencies (WeasyPrint)

**Ubuntu / Debian:**
```bash
sudo apt update
sudo apt install -y \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    libffi-dev gobject-introspection libgirepository1.0-dev
```

**macOS (Homebrew):**
```bash
brew install cairo pango gobject-introspection
```

**Windows:** Use WSL2 with Ubuntu — `wsl --install` — then follow the Ubuntu steps above.

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the MySQL database

Same as Option A step 3.

### 5. Configure the application

```bash
cp config.example.py config.py
```

You can leave `config.py` as-is — the first-run setup wizard will write the correct database URI into it automatically. If you prefer to configure it manually, edit `config.py`:

```python
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://USERNAME:PASSWORD@localhost/test_and_tag"
```

### 6. Create upload directories

```bash
mkdir -p static/uploads/tests static/uploads/repairs
```

### 7. Run the application

**Development:**
```bash
export FLASK_APP=app.py
flask run
```

**Production (Gunicorn):**
```bash
gunicorn -b 0.0.0.0:5090 --workers 2 --timeout 60 app:app
```

### 8. Complete setup in the browser

Open `http://127.0.0.1:5000` (Flask) or `http://127.0.0.1:5090` (Gunicorn). The app redirects to `/setup` automatically on first run. After saving credentials, visit `/setup/status` to confirm the schema is applied.

---

## Upgrading

After pulling a newer version:

```bash
# Docker — rebuild and restart
docker build -t patrecorder .
docker stop patrecorder && docker rm patrecorder
./start.sh

# Direct — reinstall dependencies
pip install -r requirements.txt
```

Then visit `/setup/status` and click **Apply Pending Migrations** if any are listed as pending.

You can also apply migrations from the command line:

```bash
# Docker
docker exec patrecorder flask db upgrade

# Direct (with venv active)
export FLASK_APP=app.py
flask db upgrade
```

---

## Safe Work Method Statements (SWMS)

Two SWMS documents are included as printable static HTML pages:

| File | Covers |
|---|---|
| `static/swms.html` | PAT testing — AS/NZS 3760, 5761, 5762 |
| `static/swms_repair.html` | Appliance repair — WHS Act 2011, AS/NZS 5762 |

Links to these documents appear at the top of the Test and Repair forms. They can be printed from a browser (**File → Print → Save as PDF**) to satisfy on-site WHS documentation requirements.

> **Important — review and customise before use:**
>
> These documents are provided as a starting-point template only. WHS laws vary between states and territories and are updated periodically. Before use you must verify all legislative references, update header fields (SWMS Reference, Revision, Prepared By, Approved By, Date), review hazard controls against your specific site, and have the finalised SWMS signed off by a competent person. All workers must read, understand, and sign the acknowledgement table before commencing work.
>
> The authors of PAT Recorder accept no liability for the suitability of these documents for any specific workplace. Compliance with WHS legislation is the responsibility of the PCBU.

---

## Configuration Reference

Settings can be configured through the first-run setup wizard at `/setup` or by editing `config.py` directly.

| Setting | Description |
|---|---|
| `SQLALCHEMY_DATABASE_URI` | Full SQLAlchemy MySQL URL, e.g. `mysql+pymysql://user:pass@host/test_and_tag` |
| `SECRET_KEY` | Flask session secret — set to a random value in production |
| `UPLOAD_FOLDER` | Absolute path for test photo storage |
| `MAX_CONTENT_LENGTH` | Maximum upload size in bytes (default: 200 MB) |

The `DATABASE_URL` and `SECRET_KEY` environment variables override the values in `config.py` if set.

---

## Troubleshooting

**App redirects to Setup on every visit**
- The database URL is not configured or the server is unreachable. Fill in the Setup form and save; the redirect clears once the connection succeeds.

**Settings saved via the wizard are lost after a Docker restart**
- `config.py` must exist as a file on the host before the container starts. If it doesn't exist, Docker creates it as a directory and writes fail silently. Run `cp config.example.py config.py` before starting the container.

**Database unreachable**
- Check that the host, port, username, and password are correct.
- Ensure the MySQL user has privileges on the `test_and_tag` database.
- If running in Docker, use the host machine's IP address rather than `localhost`.

**PDF generation fails (WeasyPrint)**
- Install the missing system libraries:

  ```bash
  # Ubuntu
  sudo apt install libcairo2 libpango-1.0-0 libpangocairo-1.0-0

  # macOS
  brew install cairo pango
  ```

- When running in Docker, the image installs these automatically — a PDF failure in Docker usually indicates a template error rather than a missing library.

**Permission denied on uploads folder**
```bash
chmod -R 755 static/uploads
```

**Migration error — `"can't locate revision"`**
```bash
rm -rf migrations/
export FLASK_APP=app.py
flask db init
flask db migrate -m "initial schema"
flask db upgrade
```

**Migration detects false drift (collation / FK name noise)**
- Normal when Alembic compares SQLAlchemy models against a MySQL schema. Review the generated migration and remove any operations that only rename constraints or change collation without changing column types or sizes.
