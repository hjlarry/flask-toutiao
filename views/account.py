from datetime import datetime
from flask.blueprints import Blueprint
from flask import render_template, abort, request
from flask_security import login_required, current_user, login_user
from flask_dance.contrib.github import make_github_blueprint
from flask_dance.consumer.backend.sqla import SQLAlchemyBackend
from flask_dance.consumer import oauth_authorized

from ext import db
from models.user import User, OAuth
from models.core import Post
from models.collect import CollectItem
from models.like import LikeItem
from models.contact import Contact
from corelib.utils import AttrDict


bp = Blueprint("account", __name__)
github_bp = make_github_blueprint(
    backend=SQLAlchemyBackend(OAuth, db.session, user=current_user)
)


@oauth_authorized.connect_via(github_bp)
def github_logged_in(blueprint, token):
    if not token:
        return False
    resp = blueprint.session.get("/user")
    if not resp.ok:
        return False

    github_info = resp.json()
    github_user_id = str(github_info["id"])
    oauth = OAuth.query.filter_by(
        provider=blueprint.name, provider_user_id=github_user_id
    ).first()
    if oauth:
        user = User.get(oauth.user_id)
    else:
        oauth = OAuth(
            provider=blueprint.name, provider_user_id=github_user_id, token=token
        )
        ok, user = User.create(
            email=github_info["email"],
            name=github_info["name"],
            github_id=github_info["login"],
            active=True,
            confirmed_at=datetime.utcnow(),
        )
        if ok:
            from handler.tasks import add_user_avatar

            add_user_avatar.delay(user, github_info["avatar_url"])
            oauth.user_id = user.id
            oauth.save()

    login_user(user)
    return False


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


@bp.route("user/<identifier>/likes")
def user_likes(identifier):
    return render_user_page(
        identifier, "user_card.html", Post, "like", "account.user_likes"
    )


@bp.route("user/<identifier>/collects")
def user_collects(identifier):
    return render_user_page(
        identifier, "user_card.html", Post, "collect", "account.user_collects"
    )


@bp.route("user/<identifier>/following")
def user_following(identifier):
    return render_user_page(
        identifier, "user.html", User, "following", "account.user_following"
    )


@bp.route("user/<identifier>/followers")
def user_followers(identifier):
    return render_user_page(
        identifier, "user.html", User, "follower", "account.user_followers"
    )


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
    elif type == "follower":
        p = Contact.get_follower_ids(user.id, page=page)

    p.items = target_cls.get_multi(p.items)
    return render_template(template_file, **locals())
