from flask.blueprints import Blueprint
from flask import render_template, send_from_directory
from flask_security import current_user

from models.core import Post
from config import UPLOAD_FOLDER

bp = Blueprint("index", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/static/avatars/<path>")
def avatars(path):
    return send_from_directory(UPLOAD_FOLDER / "avatars", path)


@bp.route("/post/<int:id>")
def post(id):
    post = Post.get(id)
    return render_template("post.html", post=post)

