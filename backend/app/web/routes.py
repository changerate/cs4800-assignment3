from urllib.parse import urlparse

from flask import current_app, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import or_

from app.auth_util import session_required_json
from app.extensions import db
from app.models import ResearchPaper, User
from app.schemas import UserMeSchema
from app.services.ingestion import ingest_openalex_works
from app.services.openalex import (
    OpenAlexError,
    discover_params_from_request_args,
    discovery_has_criteria,
    fetch_openalex_works,
)
from app.web import bp

me_schema = UserMeSchema()

# Subfield query value for papers with no OpenAlex subfield (filter within a field).
SUBFIELD_NONE_PARAM = "_none"


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


def _paper_feed_query(
    topic: str | None = None,
    field: str | None = None,
    subfield: str | None = None,
    subfield_unclassified: bool = False,
):
    q = ResearchPaper.query
    if topic:
        q = q.filter(ResearchPaper.topic == topic)
    elif subfield_unclassified and field:
        q = q.filter(
            ResearchPaper.topic_field == field,
            or_(
                ResearchPaper.topic_subfield.is_(None),
                ResearchPaper.topic_subfield == "",
            ),
        )
    elif subfield and field:
        q = q.filter(
            ResearchPaper.topic_field == field,
            ResearchPaper.topic_subfield == subfield,
        )
    elif field:
        q = q.filter(ResearchPaper.topic_field == field)
    return q.order_by(
        ResearchPaper.published_at.desc(),
        ResearchPaper.id.desc(),
    )


def _topic_area_tree() -> list[tuple[str, list[tuple[str, list[str]]]]]:
    """Field → (subfield key, topic names) for sidebar filters; sub key _none = broad/unspecified."""
    from collections import defaultdict

    rows = (
        ResearchPaper.query.with_entities(
            ResearchPaper.topic_field,
            ResearchPaper.topic_subfield,
            ResearchPaper.topic,
        )
        .filter(ResearchPaper.topic_field.isnot(None))
        .all()
    )
    by_sub: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    other: dict[str, set[str]] = defaultdict(set)
    for f, sf, t in rows:
        if not t:
            continue
        if sf:
            by_sub[f][sf].add(t)
        else:
            other[f].add(t)
    out: list[tuple[str, list[tuple[str, list[str]]]]] = []
    all_fields = set(by_sub.keys()) | set(other.keys())
    for f in sorted(all_fields):
        subs: list[tuple[str, list[str]]] = []
        for sf in sorted(by_sub.get(f, {}).keys()):
            subs.append((sf, sorted(by_sub[f][sf])))
        if other.get(f):
            subs.append((SUBFIELD_NONE_PARAM, sorted(other[f])))
        out.append((f, subs))
    return out


def _sidebar_topics_context(
    *,
    sidebar_open_field: str | None = None,
    sidebar_open_subfield: str | None = None,
    active_topic: str | None = None,
) -> dict:
    return {
        "topic_areas": _topic_area_tree(),
        "sidebar_open_field": sidebar_open_field,
        "sidebar_open_subfield": sidebar_open_subfield,
        "active_topic": active_topic,
    }


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


@bp.get("/discover")
def discover():
    user = _get_authenticated_user()
    saved_ids = _saved_paper_ids(user)
    error = None
    meta = None
    papers: list[ResearchPaper] = []
    next_url: str | None = None
    params = discover_params_from_request_args(request.args)
    if discovery_has_criteria(params):
        try:
            payload = fetch_openalex_works(
                params,
                mailto=current_app.config.get("OPENALEX_MAILTO"),
            )
            papers = ingest_openalex_works(payload.get("results") or [])
            db.session.commit()
            meta = payload.get("meta")
            nc = meta.get("next_cursor") if isinstance(meta, dict) else None
            if nc:
                next_args = request.args.to_dict(flat=True)
                next_args["cursor"] = nc
                next_url = url_for("web.discover", **next_args)
        except OpenAlexError as exc:
            db.session.rollback()
            error = str(exc)
    return render_template(
        "discover.html",
        papers=papers,
        **_sidebar_topics_context(),
        page="discover",
        is_authenticated=user is not None,
        saved_ids=saved_ids,
        error=error,
        meta=meta,
        next_url=next_url,
    )


@bp.get("/")
def index():
    topic = (request.args.get("topic") or "").strip() or None
    field = (request.args.get("field") or "").strip() or None
    raw_sub = (request.args.get("subfield") or "").strip()
    subfield_unclassified = raw_sub == SUBFIELD_NONE_PARAM
    subfield = None if subfield_unclassified or not raw_sub else raw_sub

    sidebar_open_field = field
    sidebar_open_subfield = (
        SUBFIELD_NONE_PARAM if subfield_unclassified else subfield
    )
    if topic and not field and not raw_sub:
        hint = (
            ResearchPaper.query.with_entities(
                ResearchPaper.topic_field,
                ResearchPaper.topic_subfield,
            )
            .filter(ResearchPaper.topic == topic)
            .first()
        )
        if hint:
            hf, hs = hint
            sidebar_open_field = hf
            if hf and not hs:
                sidebar_open_subfield = SUBFIELD_NONE_PARAM
            else:
                sidebar_open_subfield = hs

    papers = _paper_feed_query(
        topic=topic,
        field=None if topic else field,
        subfield=None if topic else subfield,
        subfield_unclassified=False if topic else subfield_unclassified,
    ).all()
    user = _get_authenticated_user()
    saved_ids = _saved_paper_ids(user)
    return render_template(
        "index.html",
        papers=papers,
        **_sidebar_topics_context(
            sidebar_open_field=sidebar_open_field,
            sidebar_open_subfield=sidebar_open_subfield,
            active_topic=topic,
        ),
        filter_field=field,
        filter_subfield=subfield,
        filter_subfield_other=subfield_unclassified,
        page="home",
        is_authenticated=user is not None,
        saved_ids=saved_ids,
        related_source=None,
    )


@bp.get("/saved")
def saved():
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
        **_sidebar_topics_context(),
        filter_field=None,
        filter_subfield=None,
        filter_subfield_other=False,
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
    user = _get_authenticated_user()
    papers = _related_papers(seed)
    saved_ids = _saved_paper_ids(user)
    return render_template(
        "index.html",
        papers=papers,
        **_sidebar_topics_context(),
        filter_field=None,
        filter_subfield=None,
        filter_subfield_other=False,
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
    return render_template(
        "profile.html",
        **_sidebar_topics_context(),
        page="profile",
        user=user,
        is_authenticated=True,
    )


@bp.get("/auth")
def auth_page():
    user = _get_authenticated_user()
    if user is not None:
        return redirect(url_for("web.profile"))
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
        **_sidebar_topics_context(),
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
        return (
            render_template(
                "auth.html",
                **_sidebar_topics_context(),
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
        return (
            render_template(
                "auth.html",
                **_sidebar_topics_context(),
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
        return (
            render_template(
                "auth.html",
                **_sidebar_topics_context(),
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
        return (
            render_template(
                "auth.html",
                **_sidebar_topics_context(),
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
