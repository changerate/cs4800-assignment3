from app.extensions import db
from app.models import Activity


def log_activity(kind: str, message: str, user_id: int | None = None) -> Activity:
    row = Activity(kind=kind, message=message, user_id=user_id)
    db.session.add(row)
    return row
