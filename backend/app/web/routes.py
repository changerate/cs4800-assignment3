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


def _saved_paper_ids(user: User | None) -> set[int]:
    if user is None:
        return set()
    return {paper.id for paper in user.saved_papers}


def _tokenize(text: str) -> set[str]:
    tokens = []
    for raw in (text or "").lower().split():
        cleaned = "".join(ch for ch in raw if ch.isalnum())
        if len(cleaned) >= 3:
            tokens.append(cleaned)
    return set(tokens)


def _related_papers(seed: ResearchPaper, limit: int = 8) -> list[ResearchPaper]:
    seed_tokens = _tokenize(f"{seed.title} {seed.abstract} {seed.topic} {seed.venue or ''}")
    all_papers = ResearchPaper.query.filter(ResearchPaper.id != seed.id).all()
    scored = []
    for paper in all_papers:
        tokens = _tokenize(f"{paper.title} {paper.abstract} {paper.topic} {paper.venue or ''}")
        overlap = len(seed_tokens & tokens)
        topic_bonus = 8 if paper.topic == seed.topic else 0
        venue_bonus = 3 if seed.venue and paper.venue == seed.venue else 0
        score = overlap + topic_bonus + venue_bonus
        if score > 0:
            scored.append((score, paper))
    scored.sort(
        key=lambda entry: (
            entry[0],
            entry[1].published_at.isoformat() if entry[1].published_at else "",
            entry[1].id,
        ),
        reverse=True,
    )
    return [paper for _, paper in scored[:limit]]


@bp.get("/")
def index():
    topic = (request.args.get("topic") or "").strip() or None
    papers = _paper_feed_query(topic).all()
    topics = _distinct_topics()
    user = _get_authenticated_user()
    saved_ids = _saved_paper_ids(user)
    return render_template(
        "index.html",
        papers=papers,
        topics=topics,
        active_topic=topic,
        page="home",
        is_authenticated=user is not None,
        saved_ids=saved_ids,
        related_source=None,
    )


@bp.get("/saved")
def saved():
    topics = _distinct_topics()
    user = _get_authenticated_user()
    if user is None:
        return redirect(url_for("web.auth_page", next=request.path))
    papers = sorted(
        user.saved_papers,
        key=lambda p: (p.published_at or p.created_at.date(), p.id),
        reverse=True,
    )
    saved_ids = _saved_paper_ids(user)
    return render_template(
        "index.html",
        papers=papers,
        topics=topics,
        active_topic=None,
        page="saved",
        is_authenticated=True,
        saved_ids=saved_ids,
        related_source=None,
        feed_title="Saved papers",
        feed_lede="Your bookmarked papers are listed here. Remove any item with Unsave.",
    )


@bp.post("/papers/<int:paper_id>/save")
def save_paper(paper_id: int):
    user = _get_authenticated_user()
    if user is None:
        return redirect(url_for("web.auth_page", next=request.referrer or url_for("web.index")))
    paper = ResearchPaper.query.get_or_404(paper_id)
    if paper not in user.saved_papers:
        user.saved_papers.append(paper)
        db.session.commit()
    return redirect(request.referrer or url_for("web.index"))


@bp.post("/papers/<int:paper_id>/unsave")
def unsave_paper(paper_id: int):
    user = _get_authenticated_user()
    if user is None:
        return redirect(url_for("web.auth_page", next=request.referrer or url_for("web.index")))
    paper = ResearchPaper.query.get_or_404(paper_id)
    if paper in user.saved_papers:
        user.saved_papers.remove(paper)
        db.session.commit()
    return redirect(request.referrer or url_for("web.index"))


@bp.get("/papers/<int:paper_id>/related")
def show_related(paper_id: int):
    seed = ResearchPaper.query.get_or_404(paper_id)
    topics = _distinct_topics()
    user = _get_authenticated_user()
    papers = _related_papers(seed)
    saved_ids = _saved_paper_ids(user)
    return render_template(
        "index.html",
        papers=papers,
        topics=topics,
        active_topic=None,
        page="home",
        is_authenticated=user is not None,
        saved_ids=saved_ids,
        related_source=seed,
        feed_title=f"Related to: {seed.title}",
        feed_lede=(
            "Showing faux-vectorized recommendations using topic match, venue match, "
            "and keyword overlap."
        ),
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
