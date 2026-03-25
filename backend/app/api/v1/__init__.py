from flask import Blueprint

bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")

from app.api.v1 import activity, posts, vehicles  # noqa: E402,F401
