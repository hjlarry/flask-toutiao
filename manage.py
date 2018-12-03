from flask_migrate import Migrate
from flask.cli import click

from app import app
from ext import db

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
    db.create_all()
    click.echo("Init finished!")

