from flask.blueprints import Blueprint
from flask import render_template, send_from_directory, abort, request, url_for
from flask_security import current_user

from models.core import Post, Tag, PostTag
from config import UPLOAD_FOLDER

bp = Blueprint("index", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/static/avatars/<path>")
def avatars(path):
    return send_from_directory(UPLOAD_FOLDER / "avatars", path)


@bp.route("/post/<identifier>")
def post(identifier):
    post = Post.get(identifier)
    return render_template("post.html", post=post)


@bp.route("/tags/<identifier>")
def tag(identifier):
    identifier = identifier.lower()
    tag = Tag.get_by_name(identifier)
    if not tag:
        tag = Tag.get_or_404(identifier)
    page = request.args.get("page", type=int, default=1)
    posts = PostTag.get_post_by_tag(identifier, page)
    return render_template("tag.html", tag=tag, identifier=identifier, posts=posts)

