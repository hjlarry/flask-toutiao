from flask import Flask, get_template_attribute
from flask.views import MethodView

from ext import db, security
from models.core import Post
from models.user import user_datastore

from .utils import ApiFlask, ApiResult
from .exceptions import ApiException, httperrors


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

