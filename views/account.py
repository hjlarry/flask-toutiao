from flask.blueprints import Blueprint
from flask import render_template, abort, request

from models.user import User

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