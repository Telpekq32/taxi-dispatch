import os
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent
load_dotenv(basedir / ".env")


def database_uri():
    uri = os.getenv("DATABASE_URL", f"sqlite:///{basedir / 'taxi_dispatch.db'}")
    # Render and some other hosts provide the legacy postgres:// scheme.
    if uri.startswith("postgres://"):
        return uri.replace("postgres://", "postgresql+psycopg://", 1)
    if uri.startswith("postgresql://"):
        return uri.replace("postgresql://", "postgresql+psycopg://", 1)
    return uri


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Flask-WTF's token check remains enabled; Netlify proxies mean the browser's
    # Referer host can differ from the upstream Render host.
    WTF_CSRF_SSL_STRICT = os.getenv("NETLIFY_PROXY", "0") != "1"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER", str(basedir / "app" / "static" / "uploads")
    )
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf"}
    ITEMS_PER_PAGE = 10
