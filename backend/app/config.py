import os
from pathlib import Path

from dotenv import load_dotenv

_backend_root = Path(__file__).resolve().parent.parent
load_dotenv(_backend_root / ".env")


def _default_database_url() -> str:
    configured = os.environ.get("DATABASE_URL")
    if configured:
        return configured
    # Vercel's filesystem is read-only except /tmp.
    if os.environ.get("VERCEL"):
        return "sqlite:////tmp/app.db"
    # Local default: run commands from backend/
    return "sqlite:///./app.db"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-change-me"
    SQLALCHEMY_DATABASE_URI = _default_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Optional: use the polite pool for OpenAlex (https://docs.openalex.org/)
    OPENALEX_MAILTO = os.environ.get("OPENALEX_MAILTO") or None


class DevelopmentConfig(Config):
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"


class ProductionConfig(Config):
    DEBUG = False


def get_config(name: str | None) -> type[Config]:
    if name == "production":
        return ProductionConfig
    return DevelopmentConfig
