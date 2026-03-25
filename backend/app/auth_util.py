from functools import wraps
from typing import Any, Callable, TypeVar

from flask import jsonify, session

F = TypeVar("F", bound=Callable[..., Any])


def session_required_json(f: F) -> F:
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any):
        if session.get("user_id") is None:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
