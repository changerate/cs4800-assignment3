from urllib.parse import urlparse

from flask import jsonify, redirect, render_template, request, session, url_for

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


def _get_authenticated_user() -> User | None:
    user_id = session.get("user_id")
    if user_id is None:
        return None
    user = db.session.get(User, user_id)
    if user is None:
        session.clear()
        return None
    return user


def _is_safe_next(next_url: str | None) -> bool:
    if not next_url:
        return False
    parsed = urlparse(next_url)
    return parsed.scheme == "" and parsed.netloc == "" and next_url.startswith("/")


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
    user = _get_authenticated_user()
    return render_template(
        "index.html",
        papers=papers,
        topics=topics,
        active_topic=topic,
        page="home",
        is_authenticated=user is not None,
    )


@bp.get("/saved")
def saved():
    topics = _distinct_topics()
    user = _get_authenticated_user()
    return render_template(
        "index.html",
        papers=[],
        topics=topics,
        active_topic=None,
        page="saved",
        placeholder_title="Saved",
        placeholder_message="Sign-in based saving is not part of this build yet.",
        is_authenticated=user is not None,
    )


@bp.get("/profile")
def profile():
    user = _get_authenticated_user()
    if user is None:
        return redirect(url_for("web.auth_page", next=request.path))
    topics = _distinct_topics()
    return render_template(
        "profile.html",
        topics=topics,
        active_topic=None,
        page="profile",
        user=user,
        is_authenticated=True,
    )


@bp.get("/auth")
def auth_page():
    user = _get_authenticated_user()
    if user is not None:
        return redirect(url_for("web.profile"))
    topics = _distinct_topics()
    mode = (request.args.get("mode") or "login").strip().lower()
    if mode not in {"login", "signup"}:
        mode = "login"
    next_path = (request.args.get("next") or "").strip()
    if not _is_safe_next(next_path):
        next_path = ""
    info = None
    if (request.args.get("created") or "").strip() == "1":
        info = "Account created. Please log in."
    elif (request.args.get("logged_out") or "").strip() == "1":
        info = "You have been signed out."
    return render_template(
        "auth.html",
        topics=topics,
        active_topic=None,
        page="auth",
        is_authenticated=False,
        mode=mode,
        next_path=next_path,
        error=None,
        info=info,
        signup_email="",
        signup_username="",
        login_username="",
    )


@bp.post("/auth/signup")
def signup():
    username, email, password = _parse_credentials()
    if not username or not email or len(password) < 6:
        topics = _distinct_topics()
        return (
            render_template(
                "auth.html",
                topics=topics,
                active_topic=None,
                page="auth",
                is_authenticated=False,
                mode="signup",
                next_path="",
                error="Username, email, and password (6+ chars) are required.",
                info=None,
                signup_email=email,
                signup_username=username,
                login_username="",
            ),
            400,
        )
    if User.query.filter(
        (User.username == username) | (User.email == email)
    ).first():
        topics = _distinct_topics()
        return (
            render_template(
                "auth.html",
                topics=topics,
                active_topic=None,
                page="auth",
                is_authenticated=False,
                mode="signup",
                next_path="",
                error="Username or email already taken.",
                info=None,
                signup_email=email,
                signup_username=username,
                login_username="",
            ),
            409,
        )
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return redirect(url_for("web.auth_page", mode="login", created=1))


@bp.post("/auth/login")
def login_page():
    username, _, password = _parse_credentials()
    next_path = (request.form.get("next") or "").strip()
    if not _is_safe_next(next_path):
        next_path = ""
    if not username or not password:
        topics = _distinct_topics()
        return (
            render_template(
                "auth.html",
                topics=topics,
                active_topic=None,
                page="auth",
                is_authenticated=False,
                mode="login",
                next_path=next_path,
                error="Username and password are required.",
                info=None,
                signup_email="",
                signup_username="",
                login_username=username,
            ),
            400,
        )
    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        topics = _distinct_topics()
        return (
            render_template(
                "auth.html",
                topics=topics,
                active_topic=None,
                page="auth",
                is_authenticated=False,
                mode="login",
                next_path=next_path,
                error="Invalid credentials.",
                info=None,
                signup_email="",
                signup_username="",
                login_username=username,
            ),
            401,
        )
    session["user_id"] = user.id
    db.session.commit()
    if next_path:
        return redirect(next_path)
    return redirect(url_for("web.index"))


@bp.post("/auth/logout")
def logout_page():
    session.clear()
    return redirect(url_for("web.auth_page", mode="login", logged_out=1))


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
