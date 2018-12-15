from flask import g, render_template, flash
from flask_security import current_user, login_user
from werkzeug.wsgi import DispatcherMiddleware
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.consumer.backend.sqla import SQLAlchemyBackend
from flask_dance.consumer import oauth_authorized
from sqlalchemy.orm.exc import NoResultFound

import config
from corelib.exmail import send_mail
from corelib.flask_ import Flask
from corelib.utils import update_url_query
from ext import db, debug_bar, mail, security
from forms import ExtendedLoginForm, ExtendedRegisterForm
from models.user import user_datastore, OAuth, User
from views.account import bp as account_bp
from views.api.api_app import json_api
from views.index import bp as index_bp

github_bp = make_github_blueprint(
    backend=SQLAlchemyBackend(OAuth, db.session, user=current_user)
)


@oauth_authorized.connect_via(github_bp)
def github_logged_in(blueprint, token):
    if not token:
        flash("Failed to log in with GitHub.", category="error")
        return False

    resp = blueprint.session.get("/user")
    if not resp.ok:
        msg = "Failed to fetch user info from GitHub."
        flash(msg, category="error")
        return False

    github_info = resp.json()
    github_user_id = str(github_info["id"])

    # Find this OAuth token in the database, or create it
    query = OAuth.query.filter_by(
        provider=blueprint.name, provider_user_id=github_user_id
    )
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = OAuth(
            provider=blueprint.name, provider_user_id=github_user_id, token=token
        )

    if oauth.user:
        login_user(oauth.user)
        flash("Successfully signed in with GitHub.")

    else:
        user = User(
            # Remember that `email` can be None, if the user declines
            # to publish their email address on GitHub!
            email=github_info["email"],
            name=github_info["name"],
        )
        oauth.user = user
        db.session.add_all([user, oauth])
        db.session.commit()
        login_user(user)
        flash("Successfully signed in with GitHub.")

    return False


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
    app.register_blueprint(github_bp, url_prefix="/git")


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


@app.before_request
def global_user():
    g.user = current_user


@app.teardown_request
def teardown_request(exception):
    if exception:
        db.session.rollback()
    db.session.remove()


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404
