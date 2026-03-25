from flask import jsonify, request, session

from app.activity_log import log_activity
from app.api.v1 import bp
from app.auth_util import session_required_json
from app.extensions import db
from app.models import Post, User
from app.schemas import PostSchema

post_schema = PostSchema()
posts_schema = PostSchema(many=True)


@bp.get("/posts")
def list_posts():
    limit = min(int(request.args.get("limit", 48)), 100)
    q = Post.query.order_by(Post.created_at.desc()).limit(limit)
    return jsonify({"posts": posts_schema.dump(q)})


@bp.get("/posts/<int:post_id>")
def get_post(post_id: int):
    post = Post.query.get_or_404(post_id)
    uid = session.get("user_id")
    if uid is not None:
        user = User.query.get(uid)
        name = user.username if user else "someone"
        log_activity("post.view", f"{name} opened “{post.title}”", user_id=uid)
        db.session.commit()
    return jsonify({"post": post_schema.dump(post)})


@bp.post("/posts")
@session_required_json
def create_post():
    uid = session["user_id"]
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    if not title or len(title) > 200:
        return jsonify({"error": "title is required (max 200 chars)"}), 400
    post = Post(user_id=uid, title=title, body=body or None)
    db.session.add(post)
    user = User.query.get(uid)
    uname = user.username if user else "user"
    log_activity("post.create", f"{uname} shared “{title}”", user_id=uid)
    db.session.commit()
    return jsonify({"post": post_schema.dump(post)}), 201
