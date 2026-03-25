import os
from pathlib import Path

from dotenv import load_dotenv

_backend_root = Path(__file__).resolve().parent.parent
load_dotenv(_backend_root / ".env")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-change-me"
    # Default: ./app.db relative to the process working directory (run Flask from `backend/`)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///./app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


class DevelopmentConfig(Config):
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"


class ProductionConfig(Config):
    DEBUG = False


def get_config(name: str | None) -> type[Config]:
    if name == "production":
        return ProductionConfig
    return DevelopmentConfig
