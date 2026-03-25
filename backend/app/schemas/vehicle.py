from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from app.models import Vehicle


class VehicleSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Vehicle
        load_instance = True
