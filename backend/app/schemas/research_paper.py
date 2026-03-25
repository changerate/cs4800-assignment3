from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from app.models import ResearchPaper


class ResearchPaperSchema(SQLAlchemyAutoSchema):
    summary = fields.Method("build_summary")

    class Meta:
        model = ResearchPaper
        load_instance = True

    def build_summary(self, obj: ResearchPaper) -> str:
        return obj.summary()
