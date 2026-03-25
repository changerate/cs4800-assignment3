from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from app.models import Activity


class ActivitySchema(SQLAlchemyAutoSchema):
    username = fields.Method("get_username", allow_none=True)

    class Meta:
        model = Activity
        load_instance = True
        include_fk = True

    def get_username(self, obj: Activity) -> str | None:
        return obj.user.username if obj.user else None
