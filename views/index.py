from flask.blueprints import Blueprint
from flask import render_template

from models.core import Post

bp = Blueprint("index", __name__)


@bp.route("/")
def index():
    return "index"


@bp.route("/post/<int:id>")
def post(id):
    post = Post.get(id)
    return render_template("post.html", post=post)

