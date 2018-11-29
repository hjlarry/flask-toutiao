from flask import Flask

import config
from ext import security, db
import views.index as index


def create_app():
    from models.user import user_datastore

    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)

    _state = security.init_app(app, user_datastore)
    security._state = _state

    app.register_blueprint(index.bp, url_prefix="/")

    return app


app = create_app()

if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.run(port=8080, debug=True, use_reloader=True, threaded=True)
