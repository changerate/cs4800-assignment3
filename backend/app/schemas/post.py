from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from app.models import Post


class PostSchema(SQLAlchemyAutoSchema):
    username = fields.String(attribute="author.username")

    class Meta:
        model = Post
        load_instance = True
        include_fk = True
