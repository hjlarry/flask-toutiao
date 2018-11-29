from flask_security import UserMixin

from ext import db
from models.mixin import BaseMixin


class User(db.Model, UserMixin, BaseMixin):
    __tablename__ = "users"
    intro = db.Column(db.String(128), default="")
    name = db.Column(db.String(128), default="")
    nickname = db.Column(db.String(128), default="")
    email = db.Column(db.String(191), default="")
    password = db.Column(db.String(191))
    website = db.Column(db.String(191), default="")
    github_url = db.Column(db.String(191), default="")
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    active = db.Column(db.Boolean())
    icon_color = db.Column(db.String(7))
    confirmed_at = db.Column(db.DateTime())
    company = db.Column(db.String(191), default="")
    avatar_id = db.Column(db.String(20), default="")


user_datastore = None

