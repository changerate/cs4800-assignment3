from flask import jsonify

from app.api.v1 import bp
from app.models import Vehicle
from app.schemas import VehicleSchema

vehicles_schema = VehicleSchema(many=True)


@bp.get("/vehicles")
def list_vehicles():
    q = Vehicle.query.order_by(Vehicle.name.asc())
    return jsonify({"vehicles": vehicles_schema.dump(q)})
