from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models import ResearchPaper

_CANONICAL_FIELDS = frozenset(
    {
        "title",
        "abstract",
        "feed_summary",
        "topic",
        "topic_field",
        "topic_subfield",
        "venue",
        "published_at",
        "doi",
        "authors_json",
        "publisher",
        "is_open_access",
        "oa_status",
        "oa_url",
        "landing_url",
        "pdf_url",
        "topic_tags_json",
        "cited_by_count",
        "source_provider",
        "source_record_id",
    }
)


def upsert_research_paper(fields: dict[str, Any]) -> ResearchPaper:
    """Insert or update a row keyed by (source_provider, source_record_id), else DOI."""
    payload = {k: v for k, v in fields.items() if k in _CANONICAL_FIELDS}
    src = payload.get("source_provider")
    rid = payload.get("source_record_id")
    paper: ResearchPaper | None = None
    if src and rid:
        paper = ResearchPaper.query.filter_by(
            source_provider=src,
            source_record_id=rid,
        ).first()
    if paper is None and payload.get("doi"):
        paper = ResearchPaper.query.filter_by(doi=payload["doi"]).first()
    if paper is None:
        paper = ResearchPaper()
        db.session.add(paper)
    for key, value in payload.items():
        setattr(paper, key, value)
    return paper


def ingest_openalex_works(works: list[Any]) -> list[ResearchPaper]:
    """Normalize and upsert OpenAlex work dicts (does not commit)."""
    out: list[ResearchPaper] = []
    from app.services.openalex import normalize_openalex_work

    for work in works:
        if not isinstance(work, dict):
            continue
        row = normalize_openalex_work(work)
        if not row.get("source_record_id"):
            continue
        out.append(upsert_research_paper(row))
    return out
