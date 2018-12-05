from flask.blueprints import Blueprint
from flask import render_template, abort, request

from models.user import User

bp = Blueprint("account", __name__)


@bp.route("landing")
def landing():
    return render_template("security/landing.html")


