from flask import Flask, get_template_attribute, request
from flask.views import MethodView

from ext import db, security
from models.core import Post
from models.user import user_datastore, User

from .utils import ApiFlask, ApiResult, marshal_with
from .exceptions import ApiException, httperrors
from .schemas import PostSchema, AuthorSchema


def create_app():
    app = ApiFlask(__name__, template_folder="../../templates")
    app.config.from_object("config")
    db.init_app(app)
    security.init_app(app, user_datastore)
    return app


json_api = create_app()


@json_api.errorhandler(ApiException)
def api_error_handler(error):
    return error.to_result()


@json_api.errorhandler(401)
@json_api.errorhandler(403)
@json_api.errorhandler(404)
@json_api.errorhandler(500)
def error_handler(error):
    if hasattr(error, "name"):
        status = error.code
        if status == 403:
            msg = "无权限"
        else:
            msg = error.name
    else:
        msg = error.msg
        status = 500
    return ApiResult({"errmsg": msg, "r": 1, "status": status})


class ActionApi(MethodView):
    do_action = None
    undo_action = None

    def _prepare(self, post_id):
        post = Post.get(post_id)
        if not post:
            raise ApiException(httperrors.post_not_found.value)
        return post

    def _merge(self, post):
        user_id = request.user_id
        post.is_liked = post.is_liked_by(user_id)
        post.is_collected = post.is_collected_by(user_id)
        return post

    @marshal_with(PostSchema)
    def post(self, post_id):
        post = self._prepare(post_id)
        if self.do_action == "add_comment":
            content = request.form.get("content")
            ok, comment = getattr(post, self.do_action)(request.user_id, content)
            if ok:
                macro = get_template_attribute("_macros.html", "render_comment")
                return {"html": str(macro(comment).replace("\n\r", ""))}
        else:
            ok = getattr(post, self.do_action)(request.user_id)
        if not ok:
            raise ApiException(httperrors.illegal_state.value)
        return self._merge(post)

    @marshal_with(PostSchema)
    def delete(self, post_id):
        post = self._prepare(post_id)
        if self.undo_action == "del_comment":
            comment_id = request.form.get("comment_id")
            ok = getattr(post, self.undo_action)(request.user_id, comment_id)
        else:
            ok = getattr(post, self.undo_action)(request.user_id)
        if not ok:
            raise ApiException(httperrors.illegal_state.value)
        return self._merge(post)


class LikeApi(ActionApi):
    do_action = "like"
    undo_action = "unlike"


class CollectApi(ActionApi):
    do_action = "collect"
    undo_action = "uncollect"


class CommentApi(ActionApi):
    do_action = "add_comment"
    undo_action = "del_comment"


class FollowApi(MethodView):
    def _prepare(self, user_id):
        user = User.get(user_id)
        if not user:
            raise ApiException(httperrors.not_found.value)
        return user

    def _merge(self, user):
        user.is_followed = user.is_followed_by(request.user_id)
        return user

    @marshal_with(AuthorSchema)
    def post(self, user_id):
        user = self._prepare(user_id)
        ok = user.follow(request.user_id)
        if not ok:
            raise ApiException(httperrors.illegal_state.value)
        return self._merge(user)

    @marshal_with(AuthorSchema)
    def delete(self, user_id):
        user = self._prepare(user_id)
        ok = user.unfollow(request.user_id)
        if not ok:
            raise ApiException(httperrors.illegal_state.value)
        return self._merge(user)


for name, view_cls in (
    ("like", LikeApi),
    ("collect", CollectApi),
    ("comment", CommentApi),
):
    view = view_cls.as_view(name)
    json_api.add_url_rule(
        f"/post/<int:post_id>/{name}", view_func=view, methods=["POST", "DELETE"]
    )

follow_view = FollowApi.as_view("follow")
json_api.add_url_rule(
    f"/user/<int:user_id>/follow", view_func=follow_view, methods=["POST", "DELETE"]
)
