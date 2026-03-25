from flask import Blueprint

bp = Blueprint("web", __name__)

from app.web import routes  # noqa: E402,F401
