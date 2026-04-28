import os
import re
import pymysql
from urllib.parse import urlparse

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_migrate import upgrade

from app import db

bp = Blueprint("setup", __name__)


# ---------------------------------------------------------
# Startup DB health check (called from app.py create_app)
# ---------------------------------------------------------

def _check_db(app):
    """
    Returns True if the DB is reachable and the appliance table exists.
    Called at startup to decide whether the setup wizard is needed.
    """
    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if 'user:pass@' in uri or 'USERNAME:PASSWORD' in uri:
        return False
    try:
        p = urlparse(uri.replace('mysql+pymysql://', 'mysql://'))
        conn = pymysql.connect(
            host=p.hostname,
            port=p.port or 3306,
            user=p.username,
            password=p.password or '',
            database=p.path.lstrip('/'),
            connect_timeout=3,
        )
        with conn.cursor() as c:
            c.execute("SELECT 1 FROM appliance LIMIT 1")
        conn.close()
        return True
    except Exception:
        return False


# ---------------------------------------------------------
# Intercept all requests when setup is required
# ---------------------------------------------------------

@bp.before_app_request
def require_setup():
    # Lazy evaluation: determine on the first request whether setup is needed.
    # This avoids a startup-time DB check in create_app(), which would bake the
    # result into the process at launch and require a restart after setup completes.
    if current_app.config.get('SETUP_REQUIRED') is None:
        current_app.config['SETUP_REQUIRED'] = not _check_db(
            current_app._get_current_object()
        )

    if not current_app.config.get('SETUP_REQUIRED'):
        return

    # Only the initial setup form and static files are allowed
    # through when the DB is not yet configured.
    ALLOWED = {'setup.index', 'setup.run_setup', 'static'}
    if request.endpoint in ALLOWED:
        return
    return redirect(url_for('setup.index'))


# ---------------------------------------------------------
# GET /setup  — initial configuration form
# ---------------------------------------------------------

@bp.route('/setup', methods=['GET'])
def index():
    if not current_app.config.get('SETUP_REQUIRED'):
        return redirect(url_for('setup.status'))

    uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    prefill = _parse_uri(uri)
    return render_template('setup.html', prefill=prefill, error=None)


# ---------------------------------------------------------
# POST /setup  — process credentials, create DB, migrate
# ---------------------------------------------------------

@bp.route('/setup', methods=['POST'])
def run_setup():
    db_host = request.form.get('db_host', 'localhost').strip()
    db_port = int(request.form.get('db_port', '3306').strip() or 3306)
    db_user = request.form.get('db_user', '').strip()
    db_password = request.form.get('db_password', '')
    db_name = request.form.get('db_name', 'test_and_tag').strip()

    prefill = {'host': db_host, 'port': db_port, 'user': db_user, 'name': db_name}

    # Step 1 — Test raw connection (no database selected yet)
    try:
        conn = pymysql.connect(
            host=db_host, port=db_port,
            user=db_user, password=db_password,
            connect_timeout=5,
        )
    except Exception as e:
        return render_template('setup.html', prefill=prefill,
                               error=f"Could not connect to MySQL: {e}")

    # Step 2 — Create database
    try:
        with conn.cursor() as c:
            c.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
        conn.close()
    except Exception as e:
        conn.close()
        return render_template('setup.html', prefill=prefill,
                               error=f"Could not create database '{db_name}': {e}")

    new_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    # Step 3 — Reconfigure SQLAlchemy engine in-process with the new URI
    current_app.config['SQLALCHEMY_DATABASE_URI'] = new_uri
    db.engine.dispose()

    # Step 4 — Run all Alembic migrations (creates all tables)
    try:
        upgrade()
    except Exception as e:
        return render_template('setup.html', prefill=prefill,
                               error=f"Migration failed: {e}")

    # Step 5 — Seed default retest rules if table is empty
    try:
        _seed_retest_rules()
    except Exception as e:
        current_app.logger.warning(f"Could not seed retest rules: {e}")

    # Step 6 — Write config.py last so the dev reloader (if active) only fires
    # after the database is fully set up. On restart, _check_db will pass and
    # SETUP_REQUIRED will be set to False without needing manual intervention.
    try:
        _write_config(new_uri)
    except Exception as e:
        # Non-fatal for the current session — credentials are already in memory.
        current_app.logger.warning(f"Could not write config.py: {e}")

    # Step 7 — Clear the setup flag for the current running process
    current_app.config['SETUP_REQUIRED'] = False

    flash('Database initialised successfully. Welcome to PAT Recorder!', 'success')
    return redirect(url_for('main.dashboard'))


# ---------------------------------------------------------
# GET /setup/status  — migration status and upgrade page
# ---------------------------------------------------------

@bp.route('/setup/status', methods=['GET'])
def status():
    uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    conn_info = _parse_uri(uri)
    migration_status = _get_migration_status()
    return render_template('setup_status.html',
                           conn_info=conn_info,
                           migration=migration_status)


# ---------------------------------------------------------
# POST /setup/upgrade  — apply pending migrations
# ---------------------------------------------------------

@bp.route('/setup/upgrade', methods=['POST'])
def run_upgrade():
    try:
        upgrade()
        flash('Database upgraded successfully.', 'success')
    except Exception as e:
        flash(f'Upgrade failed: {e}', 'danger')
    return redirect(url_for('setup.status'))


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _parse_uri(uri):
    """Extract host/port/user/db_name from a SQLAlchemy URI for form pre-fill."""
    defaults = {'host': 'localhost', 'port': 3306, 'user': '', 'name': 'test_and_tag'}
    if not uri or 'user:pass@' in uri or 'USERNAME:PASSWORD' in uri:
        return defaults
    try:
        p = urlparse(uri.replace('mysql+pymysql://', 'mysql://'))
        return {
            'host': p.hostname or 'localhost',
            'port': p.port or 3306,
            'user': p.username or '',
            'name': p.path.lstrip('/') or 'test_and_tag',
        }
    except Exception:
        return defaults


def _write_config(new_uri):
    """Overwrite config.py with the new database URI, preserving other settings."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.py')
    with open(config_path, 'r') as f:
        content = f.read()

    content = re.sub(
        r'(os\.environ\.get\s*\(\s*["\']DATABASE_URL["\']\s*,\s*")[^"\']*(["\'])',
        rf'\g<1>{new_uri}\2',
        content,
    )

    if new_uri not in content:
        content = re.sub(
            r'(SQLALCHEMY_DATABASE_URI\s*=\s*)[^\n]+',
            rf'\1"{new_uri}"',
            content,
        )

    with open(config_path, 'w') as f:
        f.write(content)


def _seed_retest_rules():
    from models import RetestRule
    if RetestRule.query.count() == 0:
        rules = [
            RetestRule(class_type='ANY',      supply_type='ANY',          interval_days=365),
            RetestRule(class_type='CLASS I',  supply_type='ANY',          interval_days=365),
            RetestRule(class_type='CLASS I',  supply_type='PORTABLE',     interval_days=180),
            RetestRule(class_type='CLASS II', supply_type='ANY',          interval_days=730),
            RetestRule(class_type='CLASS II', supply_type='PORTABLE',     interval_days=365),
            RetestRule(class_type='ANY',      supply_type='CONSTRUCTION', interval_days=90),
        ]
        db.session.add_all(rules)
        db.session.commit()


def _get_migration_status():
    """
    Returns a dict describing the current migration state:
      current_rev   — short revision ID applied to the DB (or None)
      head_rev      — short revision ID of the latest migration script
      pending       — list of {revision, doc} dicts not yet applied, oldest first
      is_up_to_date — True when current == head
      never_migrated — True when no alembic_version row exists
      error         — error string if status could not be determined
    """
    from sqlalchemy import text
    from alembic.script import ScriptDirectory
    from alembic.config import Config as AlembicConfig

    result = {
        'current_rev': None,
        'head_rev': None,
        'pending': [],
        'is_up_to_date': False,
        'never_migrated': False,
        'error': None,
    }

    # Query current revision from the alembic_version table
    try:
        with db.engine.connect() as conn:
            row = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            result['current_rev'] = row[:8] if row else None
            result['never_migrated'] = row is None
    except Exception as e:
        result['error'] = f"Could not read migration state: {e}"
        return result

    # Load head revision from migration scripts on disk
    try:
        migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations')
        cfg = AlembicConfig()
        cfg.set_main_option('script_location', migrations_dir)
        script = ScriptDirectory.from_config(cfg)
        head = script.get_current_head()
        result['head_rev'] = head[:8] if head else None
    except Exception as e:
        result['error'] = f"Could not read migration scripts: {e}"
        return result

    # Full revision IDs for comparison
    try:
        with db.engine.connect() as conn:
            full_current = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    except Exception:
        full_current = None

    result['is_up_to_date'] = (full_current == head)

    # Enumerate pending revisions (oldest first) if not up to date
    if not result['is_up_to_date']:
        try:
            all_revs = list(script.walk_revisions())  # head → base order
            pending = []
            for rev in all_revs:
                if rev.revision == full_current:
                    break
                pending.append({
                    'revision': rev.revision[:8],
                    'doc': rev.doc or '(no description)',
                })
            result['pending'] = list(reversed(pending))  # oldest first
        except Exception as e:
            result['error'] = f"Could not enumerate pending migrations: {e}"

    return result
