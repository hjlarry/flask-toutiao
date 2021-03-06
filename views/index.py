from flask.blueprints import Blueprint
from flask import render_template, send_from_directory, request
from flask_security import login_required

from models.core import Post, Tag, PostTag
from models.search import Item
from models.feed import get_user_feed
from config import UPLOAD_FOLDER

bp = Blueprint("index", __name__)


@bp.route("/")
@login_required
def index():
    page = request.args.get("page", type=int, default=1)
    posts = get_user_feed(request.user_id, page)
    return render_template("index.html", posts=posts, page=page)


@bp.route("/static/avatars/<path>")
def avatars(path):
    return send_from_directory(UPLOAD_FOLDER / "avatars", path)


@bp.route("/post/<identifier>")
def post(identifier):
    post = Post.get(identifier)
    return render_template("post.html", post=post)


@bp.route("/tag/<identifier>")
def tag(identifier):
    identifier = identifier.lower()
    tag = Tag.get_by_name(identifier)
    if not tag:
        tag = Tag.get_or_404(identifier)
    page = request.args.get("page", type=int, default=1)
    type = request.args.get("type", default="latest")
    if type == "latest":
        posts = PostTag.get_post_by_tag(identifier, page)
    elif type == "hot":
        posts = Item.get_post_ids_by_tag(tag, page, order_by="hot")
        posts.items = Post.get_multi(posts.items)
    else:
        posts = []
    return render_template(
        "tag.html", tag=tag, identifier=identifier, posts=posts, type=type
    )


@bp.route("/search")
def search():
    query = request.args.get("q", "")
    page = request.args.get("page", default=1, type=int)
    posts = Item.new_search(query, page)
    tags = Tag.all_tags()
    return render_template("search.html", query=query, posts=posts, tags=tags)
