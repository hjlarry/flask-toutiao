from flask.blueprints import Blueprint
from flask import render_template
from flask_security import current_user

from models.core import Post

bp = Blueprint("index", __name__)


@bp.route("/")
def index():
    return render_template("index.html", user=current_user)


@bp.route("/post/<int:id>")
def post(id):
    post = Post.get(id)
    return render_template("post.html", post=post)

