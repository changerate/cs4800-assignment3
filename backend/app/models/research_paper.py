from __future__ import annotations

import re
from datetime import datetime

from app.extensions import db


class ResearchPaper(db.Model):
    __tablename__ = "research_papers"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    abstract = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(120), nullable=False, index=True)
    venue = db.Column(db.String(200), nullable=True)
    published_at = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def summary(self, max_len: int = 220) -> str:
        """Short teaser from the abstract (word-safe truncation)."""
        text = re.sub(r"\s+", " ", (self.abstract or "").strip())
        if len(text) <= max_len:
            return text
        chunk = text[: max_len + 1]
        if " " in chunk:
            chunk = chunk.rsplit(" ", 1)[0]
        return chunk.rstrip(",;:") + "…"
