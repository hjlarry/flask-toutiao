from flask.blueprints import Blueprint
from flask import render_template, abort, request
from flask_security import login_required

from models.user import User
from corelib.utils import AttrDict


bp = Blueprint("account", __name__)


@bp.route("register_landing")
def register_landing():
    """注册后跳转页面"""
    return render_template("security/register_landing.html")


@bp.route("reset_landing")
def reset_landing():
    """重置密码后跳转页面"""
    return render_template("security/reset_landing.html")


@bp.route("confirm_landing")
def confirm_landing():
    """在邮件中点击确认链接后跳转页面"""
    return render_template("security/confirm_landing.html")


@bp.route("user/<identifier>/")
def user(identifier):
    user = User.cache.get(identifier)
    if not user:
        user = User.cache.filter(name=identifier).first()
    if not user:
        abort(404)
    return render_template("user.html", user=user)


@bp.route("settings/", methods=["GET", "POST"])
@login_required
def settings():
    notice = False
    if request.method == "POST":
        user = request.user
        image = request.files.get("user_image")
        d = request.form.to_dict()
        d.pop("submit", None)
        form = AttrDict(d)
        user.update(**form)
        if image:
            user.upload_avatar(image)
        notice = True
    return render_template("settings.html", notice=notice)
