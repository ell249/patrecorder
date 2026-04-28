from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from utils import format_standard

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ---------------------------------------------------------
    # Database init
    # ---------------------------------------------------------
    db.init_app(app)
    migrate = Migrate(app, db)

    # ---------------------------------------------------------
    # Check whether DB is reachable; flag setup wizard if not
    # ---------------------------------------------------------
    from setup import _check_db
    app.config['SETUP_REQUIRED'] = not _check_db(app)

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

    return app


# ---------------------------------------------------------
# App instance for WSGI servers
# ---------------------------------------------------------
app = create_app()
