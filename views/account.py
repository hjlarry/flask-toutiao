from flask.blueprints import Blueprint
from flask import render_template, abort, request
from flask_security import login_required

from models.user import User
from models.core import Post
from models.collect import CollectItem
from models.like import LikeItem
from models.contact import Contact
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


@bp.route("user/<identifier>")
def user(identifier):
    return render_user_page(identifier, "user.html", User, endpoint="account.user")


@bp.route("settings", methods=["GET", "POST"])
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


@bp.route("user/<identifier>/like")
def user_likes(identifier):
    return render_user_page(
        identifier, "user_card.html", Post, "like", "account.user_likes"
    )


@bp.route("user/<identifier>/collect")
def user_collects(identifier):
    return render_user_page(
        identifier, "user_card.html", Post, "collect", "account.user_collects"
    )


@bp.route("user_following/<identifier>/")
def user_following(identifier):
    user = User.cache.get(identifier)
    return render_template("user.html", user=user)


@bp.route("user_followers/<identifier>/")
def user_followers(identifier):
    user = User.cache.get(identifier)
    return render_template("user.html", user=user)


def render_user_page(
    identifier, template_file, target_cls, type="following", endpoint=None
):
    user = User.cache.get(identifier)
    if not user:
        user = User.cache.filter(name=identifier).first()
    if not user:
        abort(404)
    page = request.args.get("page", default=1, type=int)
    if type == "collect":
        p = CollectItem.get_target_ids_by_user(user.id, page=page)
    elif type == "like":
        p = LikeItem.get_target_ids_by_user(user.id, page=page)
    elif type == "following":
        p = Contact.get_following_ids(user.id, page=page)

    p.items = target_cls.get_multi(p.items)
    return render_template(template_file, **locals())
