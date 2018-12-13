from ext import db

from models.mixin import BaseMixin
from corelib.mc import cache, rdb
from config import PER_PAGE

MC_KEY_CONTACT_N = "contact_n:{}:{}"


class Contact(BaseMixin, db.Model):
    __tablename__ = "contacts"
    to_id = db.Column(db.Integer)
    from_id = db.Column(db.Integer)

    __table_args__ = (
        db.UniqueConstraint("from_id", "to_id", name="uk_from_to"),
        db.Index("idx_to_time_from", to_id, "created_at", from_id),
        db.Index("idx_time_to_from", "created_at", to_id, from_id),
    )

    @classmethod
    def get_follow_item(cls, from_id, to_id):
        return cls.query.filter_by(from_id=from_id, to_id=to_id).first()

    @classmethod
    def get_following_ids(cls, user_id, page=1):
        query = cls.query.with_entities(cls.to_id).filter_by(from_id=user_id)
        following = query.paginate(page, PER_PAGE)
        following.items = [id for id, in following.items]
        del following.query
        return following


class userFollowStats(BaseMixin, db.Model):
    follower_count = db.Column(db.Integer, default=0)
    following_count = db.Column(db.Integer, default=0)

    __table_args__ = {"mysql_charset": "utf8"}

