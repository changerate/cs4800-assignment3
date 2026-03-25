from flask import jsonify, request

from app.api.v1 import bp
from app.models import ResearchPaper
from app.schemas import ResearchPaperSchema

schema = ResearchPaperSchema()
schemas = ResearchPaperSchema(many=True)


@bp.get("/papers")
def list_papers():
    topic = (request.args.get("topic") or "").strip()
    q = ResearchPaper.query
    if topic:
        q = q.filter(ResearchPaper.topic == topic)
    q = q.order_by(
        ResearchPaper.published_at.desc(),
        ResearchPaper.id.desc(),
    ).limit(min(int(request.args.get("limit", 100)), 200))
    return jsonify({"papers": schemas.dump(q)})


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
