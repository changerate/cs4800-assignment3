from flask import jsonify, render_template, request, session

from app.activity_log import log_activity
from app.auth_util import session_required_json
from app.extensions import db
from app.models import User, Vehicle
from app.schemas import UserMeSchema
from app.web import bp

me_schema = UserMeSchema()


def _parse_credentials():
    if request.is_json:
        data = request.get_json(silent=True) or {}
        return (
            (data.get("username") or "").strip(),
            (data.get("email") or "").strip(),
            (data.get("password") or ""),
        )
    return (
        (request.form.get("username") or "").strip(),
        (request.form.get("email") or "").strip(),
        (request.form.get("password") or ""),
    )


@bp.get("/")
def index():
    return render_template("index.html")


@bp.post("/register")
def register():
    username, email, password = _parse_credentials()
    if not username or not email or len(password) < 6:
        return (
            jsonify({"error": "username, email, and password (6+ chars) required"}),
            400,
        )
    if User.query.filter(
        (User.username == username) | (User.email == email)
    ).first():
        return jsonify({"error": "username or email already taken"}), 409
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    session["user_id"] = user.id
    log_activity("auth.register", f"{user.username} joined", user_id=user.id)
    db.session.commit()
    return jsonify({"user": me_schema.dump(user)}), 201


@bp.post("/login")
def login():
    username, _, password = _parse_credentials()
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401
    session["user_id"] = user.id
    log_activity("auth.login", f"{user.username} signed in", user_id=user.id)
    db.session.commit()
    return jsonify({"user": me_schema.dump(user)})


@bp.post("/logout")
def logout():
    uid = session.get("user_id")
    label = None
    if uid:
        user = db.session.get(User, uid)
        label = user.username if user else None
    session.clear()
    if label:
        log_activity("auth.logout", f"{label} signed out", user_id=None)
        db.session.commit()
    return jsonify({"ok": True})


@bp.get("/me")
@session_required_json
def me():
    user = User.query.get_or_404(session["user_id"])
    return jsonify({"user": me_schema.dump(user)})


@bp.put("/me/vehicle")
@session_required_json
def me_vehicle():
    user = User.query.get_or_404(session["user_id"])
    data = request.get_json(silent=True) or {}
    raw = data.get("vehicle_id")
    if raw is None:
        user.vehicle_id = None
        log_activity(
            "vehicle.clear",
            f"{user.username} cleared their vehicle",
            user_id=user.id,
        )
    else:
        try:
            vid = int(raw)
        except (TypeError, ValueError):
            return jsonify({"error": "vehicle_id must be an integer or null"}), 400
        if Vehicle.query.get(vid) is None:
            return jsonify({"error": "unknown vehicle"}), 404
        user.vehicle_id = vid
        v = Vehicle.query.get(vid)
        label = v.name if v else "a vehicle"
        log_activity(
            "vehicle.set",
            f"{user.username} chose {label}",
            user_id=user.id,
        )
    db.session.commit()
    return jsonify({"user": me_schema.dump(user)})
