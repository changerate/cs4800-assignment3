from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from app.models import User


class UserMeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        exclude = ("password_hash",)
