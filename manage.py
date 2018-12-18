from flask.cli import click
from flask_migrate import Migrate

import models.collect
import models.comment
import models.contact
import models.core
import models.like
import models.user  # noqa
from app import app
from corelib.db import rdb
from ext import db

migrate = Migrate(app, db)


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
