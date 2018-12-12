from flask import Flask, get_template_attribute, request
from flask.views import MethodView

from ext import db, security
from models.core import Post
from models.user import user_datastore

from .utils import ApiFlask, ApiResult, marshal_with
from .exceptions import ApiException, httperrors
from .schemas import PostSchema


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
        ok = getattr(post, self.do_action)(request.user_id)
        if not ok:
            raise ApiException(httperrors.illegal_state.value)
        return self._merge(post)


class LikeApi(ActionApi):
    do_action = "like"
    undo_action = "unlike"

view = LikeApi.as_view("like")
json_api.add_url_rule(f"/post/<int:post_id>/like", view_func=view, methods=["POST"])

