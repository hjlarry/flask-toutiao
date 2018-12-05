from flask import Flask

import config
import views.index as index
from corelib.exmail import send_mail
from ext import db, security, mail
from forms import ExtendedRegisterForm
from models.user import user_datastore


def create_app():

    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    mail.init_app(app)

    _state = security.init_app(
        app, user_datastore, confirm_register_form=ExtendedRegisterForm
    )
    security._state = _state
    app.security = security
    security.send_mail_task(send_mail)

    app.register_blueprint(index.bp, url_prefix="/")

    return app


app = create_app()
