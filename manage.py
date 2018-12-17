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
    db.session.commit()
    db.drop_all()
    rdb.flushall()
    db.create_all()
    click.echo("Init finished!")


@app.cli.command()
def initcache():
    rdb.flushall()
    click.echo("Init cache finished!")

