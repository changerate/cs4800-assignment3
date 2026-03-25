from flask import jsonify, request

from app.api.v1 import bp
from app.models import Activity
from app.schemas import ActivitySchema

activities_schema = ActivitySchema(many=True)


@bp.get("/activity")
def list_activity():
    limit = min(int(request.args.get("limit", 30)), 100)
    q = Activity.query.order_by(Activity.created_at.desc()).limit(limit)
    return jsonify({"activity": activities_schema.dump(q)})
