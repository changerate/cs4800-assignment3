from __future__ import annotations

import re
from datetime import datetime

from app.extensions import db


class ResearchPaper(db.Model):
    __tablename__ = "research_papers"
    __table_args__ = (
        db.UniqueConstraint(
            "source_provider",
            "source_record_id",
            name="uq_research_papers_provenance",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    abstract = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(120), nullable=False, index=True)
    topic_field = db.Column(db.String(120), nullable=True, index=True)
    topic_subfield = db.Column(db.String(120), nullable=True)
    venue = db.Column(db.String(200), nullable=True)
    published_at = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    feed_summary = db.Column(db.Text, nullable=True)
    doi = db.Column(db.String(255), nullable=True, unique=True, index=True)
    authors_json = db.Column(db.Text, nullable=True)
    publisher = db.Column(db.String(500), nullable=True)
    is_open_access = db.Column(db.Boolean, nullable=True)
    oa_status = db.Column(db.String(32), nullable=True)
    oa_url = db.Column(db.String(1000), nullable=True)
    landing_url = db.Column(db.String(1000), nullable=True)
    pdf_url = db.Column(db.String(1000), nullable=True)
    topic_tags_json = db.Column(db.Text, nullable=True)
    cited_by_count = db.Column(db.Integer, nullable=True)
    source_provider = db.Column(db.String(32), nullable=True)
    source_record_id = db.Column(db.String(64), nullable=True)

    saved_by_users = db.relationship(
        "User",
        secondary="user_saved_papers",
        back_populates="saved_papers",
        lazy="selectin",
    )

    def summary(self, max_len: int = 220) -> str:
        """Short teaser for feeds: prefer stored feed_summary, else abstract."""
        raw = (self.feed_summary or self.abstract or "").strip()
        text = re.sub(r"\s+", " ", raw)
        if len(text) <= max_len:
            return text
        chunk = text[: max_len + 1]
        if " " in chunk:
            chunk = chunk.rsplit(" ", 1)[0]
        return chunk.rstrip(",;:") + "…"
