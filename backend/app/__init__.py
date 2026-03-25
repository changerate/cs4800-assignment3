import os

from flask import Flask

from app.config import get_config
from app.extensions import db, migrate


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static",
    )
    cfg = os.environ.get("FLASK_CONFIG") or config_name
    app.config.from_object(get_config(cfg))

    db.init_app(app)
    migrate.init_app(app, db)

    from app import models as _models  # noqa: F401

    from app.api.v1 import bp as api_v1_bp
    from app.web import bp as web_bp

    app.register_blueprint(api_v1_bp)
    app.register_blueprint(web_bp)

    from app import cli as cli_module

    cli_module.register_commands(app)

    return app
