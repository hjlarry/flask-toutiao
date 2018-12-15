from flask_migrate import Migrate
from flask.cli import click, with_appcontext
from social_flask_sqlalchemy import models as models_

from app import app
from ext import db
from corelib.db import rdb

migrate = Migrate(app, db)

import models.collect
import models.comment
import models.contact
import models.core
import models.like
import models.user


@app.cli.command()
def initdb():
    engine = db.get_engine()
    models_.PSABase.metadata.drop_all(engine)
    db.session.commit()
    db.drop_all()
    rdb.flushall()
    db.create_all()
    # models_.PSABase.metadata.create_all(engine)
    click.echo("Init finished!")


@app.cli.command()
def initcache():
    rdb.flushall()
    click.echo("Init cache finished!")


@app.cli.command()
@with_appcontext
def create_social_db():
    engine = db.get_engine()
    models_.PSABase.metadata.drop_all(engine)
    models_.PSABase.metadata.create_all(engine)
    click.echo("create social db finished!")
