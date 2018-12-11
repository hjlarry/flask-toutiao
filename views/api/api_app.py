from flask import Flask, get_template_attribute
from flask.views import MethodView

from ext import db, security
from models.core import Post
from models.user import user_datastore

from .utils import ApiFlask, ApiResult


def create_app():
    app = ApiFlask(__name__, template_folder="../../templates")
    app.config.from_object("config")
    db.init_app(app)
    security.init_app(app, user_datastore)
    return app


json_api = create_app()


@json_api.errorhandler(404)
def error_handler(error):
    return ApiResult({"r": 1})

