from flask import jsonify, render_template, request, session

from app.auth_util import session_required_json
from app.extensions import db
from app.models import ResearchPaper, User
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


def _paper_feed_query(topic: str | None):
    q = ResearchPaper.query
    if topic:
        q = q.filter(ResearchPaper.topic == topic)
    return q.order_by(
        ResearchPaper.published_at.desc(),
        ResearchPaper.id.desc(),
    )


def _distinct_topics():
    rows = (
        ResearchPaper.query.with_entities(ResearchPaper.topic)
        .distinct()
        .order_by(ResearchPaper.topic.asc())
        .all()
    )
    return [r[0] for r in rows]


@bp.get("/")
def index():
    topic = (request.args.get("topic") or "").strip() or None
    papers = _paper_feed_query(topic).all()
    topics = _distinct_topics()
    return render_template(
        "index.html",
        papers=papers,
        topics=topics,
        active_topic=topic,
        page="home",
    )


@bp.get("/saved")
def saved():
    topics = _distinct_topics()
    return render_template(
        "index.html",
        papers=[],
        topics=topics,
        active_topic=None,
        page="saved",
        placeholder_title="Saved",
        placeholder_message="Sign-in based saving is not part of this build yet.",
    )


@bp.get("/profile")
def profile():
    topics = _distinct_topics()
    return render_template(
        "index.html",
        papers=[],
        topics=topics,
        active_topic=None,
        page="profile",
        placeholder_title="Profile",
        placeholder_message="Account settings will appear here in a future iteration.",
    )


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
    db.session.commit()
    return jsonify({"user": me_schema.dump(user)})


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@bp.get("/me")
@session_required_json
def me():
    user = User.query.get_or_404(session["user_id"])
    return jsonify({"user": me_schema.dump(user)})
