import requests
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore
from sqlalchemy import func as alchemyFn

from ext import db
from config import UPLOAD_FOLDER
from models.mixin import BaseMixin
from models.contact import Contact, userFollowStats
from corelib.utils import generate_id

roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer(), db.ForeignKey("users.id")),
    db.Column("role_id", db.Integer(), db.ForeignKey("role.id")),
)


class User(db.Model, UserMixin, BaseMixin):
    __tablename__ = "users"
    bio = db.Column(db.String(128), default="")
    name = db.Column(db.String(128), default="")
    nickname = db.Column(db.String(128), default="")
    email = db.Column(db.String(191), default="")
    password = db.Column(db.String(191))
    website = db.Column(db.String(191), default="")
    github_id = db.Column(db.String(191), default="")
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
    roles = db.relationship(
        "Role", secondary=roles_users, backref=db.backref("users", lazy="dynamic")
    )

    _stats = None

    __table_args__ = (db.Index("idx_name", name), db.Index("idx_email", email))

    def url(self):
        return f"/user/{self.id}"

    @property
    def avatar_path(self):
        avatar_id = self.avatar_id
        return "" if not avatar_id else f"/static/avatars/{avatar_id}.png"

    def update_avatar(self, avatar_id):
        self.avatar_id = avatar_id
        self.save()

    def upload_avatar(self, img):
        avatar_id = generate_id()
        filename = UPLOAD_FOLDER / "avatars" / f"{avatar_id}.png"
        with open(filename, "wb") as f:
            img.save(f)
        self.update_avatar(avatar_id)

    def follow(self, from_id):
        ok, _ = Contact.create(to_id=self.id, from_id=from_id)
        if ok:
            self._stats = None
        return ok

    def unfollow(self, from_id):
        contact = Contact.get_follow_item(from_id, self.id)
        if contact:
            contact.delete()
            self._stats = None
            return True
        return False

    def is_followed_by(self, user_id):
        contact = Contact.get_follow_item(user_id, self.id)
        return bool(contact)

    @property
    def n_followers(self):
        return self._follow_stats[0]

    @property
    def n_following(self):
        return self._follow_stats[1]

    @property
    def _follow_stats(self):
        if self._stats is None:
            stats = userFollowStats.get(self.id)
            if not stats:
                self._stats = 0, 0
            else:
                self._stats = stats.follower_count, stats.following_count
        return self._stats


class Role(db.Model, RoleMixin):
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(191))


class BranSQLAlchemyUserDatastore(SQLAlchemyUserDatastore):
    def get_user_name(self, identifier):
        return self._get_user(identifier, "name")

    def get_user_email(self, identifier):
        return self._get_user(identifier, "email")

    def _get_user(self, identifier, attr):
        user_model_query = self.user_model.query
        if hasattr(self.user_model, "roles"):
            from sqlalchemy.orm import joinedload

            user_model_query = user_model_query.options(joinedload("roles"))

        query = alchemyFn.lower(getattr(self.user_model, attr)) == alchemyFn.lower(
            identifier
        )
        rv = user_model_query.filter(query).first()
        if rv is not None:
            return rv


user_datastore = BranSQLAlchemyUserDatastore(db, User, Role)

