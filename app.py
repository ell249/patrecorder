from datetime import datetime, timezone
from flask import Flask, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.exc import OperationalError, ProgrammingError
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config
from utils import format_standard

db = SQLAlchemy()


class _IngressFix:
    """Copy HA's X-Ingress-Path header into WSGI SCRIPT_NAME so url_for() generates correct prefixed URLs."""
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        ingress = environ.get('HTTP_X_INGRESS_PATH', '')
        if ingress:
            environ['SCRIPT_NAME'] = ingress
        return self.app(environ, start_response)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.wsgi_app = _IngressFix(app.wsgi_app)

    # ---------------------------------------------------------
    # Database init
    # ---------------------------------------------------------
    db.init_app(app)
    migrate = Migrate(app, db)

    # ---------------------------------------------------------
    # SETUP_REQUIRED is determined lazily on the first request
    # by the require_setup before_app_request hook in setup.py.
    # Setting None here signals "not yet evaluated".
    # ---------------------------------------------------------
    app.config['SETUP_REQUIRED'] = None

    # ---------------------------------------------------------
    # Template context
    # ---------------------------------------------------------
    @app.context_processor
    def inject_now():
        return {"now": datetime.now(timezone.utc)}

    # ---------------------------------------------------------
    # Register Jinja Filters
    # ---------------------------------------------------------
    app.jinja_env.filters["std"] = format_standard

    # ---------------------------------------------------------
    # Register Blueprints (setup first so its before_app_request fires)
    # ---------------------------------------------------------
    from setup import bp as setup_bp
    app.register_blueprint(setup_bp)

    from views import bp as main_bp
    app.register_blueprint(main_bp)

    from printer import bp as printer_bp
    app.register_blueprint(printer_bp)

    # ---------------------------------------------------------
    # Database schema error handler
    # Catches missing columns / tables and sends the user to
    # the status page where they can apply pending migrations.
    # ---------------------------------------------------------
    @app.errorhandler(OperationalError)
    @app.errorhandler(ProgrammingError)
    def handle_db_schema_error(e):
        app.logger.error("Database schema error: %s", e)
        flash(
            "A database error occurred — a migration may be required. "
            f"Detail: {e.orig}",
            "danger",
        )
        return redirect(url_for("setup.status"))

    return app


# ---------------------------------------------------------
# App instance for WSGI servers
# ---------------------------------------------------------
app = create_app()
