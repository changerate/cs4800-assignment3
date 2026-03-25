from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from app.models import User
from app.schemas.vehicle import VehicleSchema


class UserMeSchema(SQLAlchemyAutoSchema):
    vehicle = fields.Nested(VehicleSchema, allow_none=True)

    class Meta:
        model = User
        load_instance = True
        exclude = ("password_hash",)
