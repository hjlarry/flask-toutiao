from flask import g, render_template
from flask_security import current_user
from werkzeug.wsgi import DispatcherMiddleware

import config
from corelib.exmail import send_mail
from corelib.flask_ import Flask
from corelib.utils import update_url_query
from ext import db, debug_bar, mail, security
from forms import ExtendedLoginForm, ExtendedRegisterForm
from models.user import user_datastore, OAuth, User
from views.account import bp as account_bp, github_bp
from views.api.api_app import json_api
from views.index import bp as index_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    init_app(app)
    register_bp(app)
    app.context_processor(inject_template_global)
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/api": json_api})

    return app


def init_app(app):
    db.init_app(app)
    mail.init_app(app)
    debug_bar.init_app(app)
    _state = security.init_app(
        app,
        user_datastore,
        confirm_register_form=ExtendedRegisterForm,
        login_form=ExtendedLoginForm,
    )
    security._state = _state
    app.security = security
    security.send_mail_task(send_mail)


def register_bp(app):
    app.register_blueprint(index_bp, url_prefix="/")
    app.register_blueprint(account_bp, url_prefix="/")
    app.register_blueprint(github_bp, url_prefix="/login_oauth")


def inject_template_global():
    return {
        "isinstance": isinstance,
        "current_user": current_user,
        "getattr": getattr,
        "hasattr": hasattr,
        "dir": dir,
        "len": len,
        "update_url_query": update_url_query,
    }


app = create_app()


@app.teardown_request
def teardown_request(exception):
    if exception:
        db.session.rollback()
    db.session.remove()


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404
