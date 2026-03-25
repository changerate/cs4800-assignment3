import json

from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from app.models import ResearchPaper


class ResearchPaperSchema(SQLAlchemyAutoSchema):
    summary = fields.Method("build_summary")
    authors = fields.Method("build_authors")
    topic_tags = fields.Method("build_topic_tags")

    class Meta:
        model = ResearchPaper
        load_instance = True

    def build_summary(self, obj: ResearchPaper) -> str:
        return obj.summary()

    def build_authors(self, obj: ResearchPaper) -> list:
        if not obj.authors_json:
            return []
        try:
            parsed = json.loads(obj.authors_json)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []

    def build_topic_tags(self, obj: ResearchPaper) -> list:
        if not obj.topic_tags_json:
            return []
        try:
            parsed = json.loads(obj.topic_tags_json)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
