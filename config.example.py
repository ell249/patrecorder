import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://user:pass@localhost/test_and_tag"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads", "tests")
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024

    # Label printer (Brother QL)
    BASE_URL        = os.environ.get("BASE_URL", "")
    BROTHER_PRINTER = os.environ.get("BROTHER_PRINTER", "")
    BROTHER_MODEL   = os.environ.get("BROTHER_MODEL", "QL-810W")
    BROTHER_LABEL   = os.environ.get("BROTHER_LABEL", "62")
    BROTHER_RED     = os.environ.get("BROTHER_RED", "false")
