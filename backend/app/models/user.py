from __future__ import annotations

from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

user_saved_papers = db.Table(
    "user_saved_papers",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column(
        "paper_id",
        db.Integer,
        db.ForeignKey("research_papers.id"),
        primary_key=True,
    ),
    db.Column("created_at", db.DateTime, default=datetime.utcnow, nullable=False),
)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    saved_papers = db.relationship(
        "ResearchPaper",
        secondary=user_saved_papers,
        back_populates="saved_by_users",
        lazy="selectin",
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
