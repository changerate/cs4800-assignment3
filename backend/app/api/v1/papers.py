from flask import current_app, jsonify, request
from sqlalchemy import func, or_

from app.api.v1 import bp
from app.extensions import db
from app.models import ResearchPaper
from app.schemas import ResearchPaperSchema
from app.services.ingestion import ingest_openalex_works
from app.services.openalex import (
    OpenAlexError,
    discover_params_from_request_args,
    discovery_has_criteria,
    fetch_openalex_works,
)

schemas = ResearchPaperSchema(many=True)


@bp.get("/papers")
def list_papers():
    topic = (request.args.get("topic") or "").strip()
    field = (request.args.get("field") or "").strip()
    raw_sub = (request.args.get("subfield") or "").strip()
    subfield_unclassified = raw_sub == "_none"
    subfield = None if subfield_unclassified or not raw_sub else raw_sub
    sort = (request.args.get("sort") or "recency").strip().lower()
    if sort not in {"recency", "citations"}:
        sort = "recency"
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
    if sort == "citations":
        q = q.order_by(
            func.coalesce(ResearchPaper.cited_by_count, -1).desc(),
            ResearchPaper.published_at.desc().nullslast(),
            ResearchPaper.id.desc(),
        )
    else:
        q = q.order_by(
            ResearchPaper.published_at.desc(),
            ResearchPaper.id.desc(),
        )
    q = q.limit(min(int(request.args.get("limit", 100)), 200))
    return jsonify({"papers": schemas.dump(q)})


@bp.get("/papers/discover")
def discover_papers():
    params = discover_params_from_request_args(request.args)
    if not discovery_has_criteria(params):
        return (
            jsonify(
                {
                    "error": (
                        "Provide at least one of q, title, author, concept, year, is_oa "
                        "(or pass cursor to continue paging)."
                    )
                }
            ),
            400,
        )
    try:
        payload = fetch_openalex_works(
            params,
            mailto=current_app.config.get("OPENALEX_MAILTO"),
        )
        ingested = ingest_openalex_works(payload.get("results") or [])
        db.session.commit()
    except OpenAlexError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 502

    return jsonify({"meta": payload.get("meta"), "papers": schemas.dump(ingested)})


@bp.get("/papers/topics")
def paper_topics():
    rows = (
        ResearchPaper.query.with_entities(ResearchPaper.topic)
        .distinct()
        .order_by(ResearchPaper.topic.asc())
        .all()
    )
    topics = [r[0] for r in rows]
    return jsonify({"topics": topics})
