import math

from ext import db
from models.mixin import BaseMixin
from corelib.mc import cache, rdb
from config import PER_PAGE

MC_KEY_FOLLOWING = "following:{}:{}"
MC_KEY_FOLLOWERS = "followers:{}:{}"
MC_KEY_FOLLOW_ITEM = "is_followed:{}:{}"


class Contact(BaseMixin, db.Model):
    __tablename__ = "contacts"
    to_id = db.Column(db.Integer)
    from_id = db.Column(db.Integer)

    __table_args__ = (
        db.UniqueConstraint("from_id", "to_id", name="uk_from_to"),
        db.Index("idx_to_time_from", to_id, "created_at", from_id),
        db.Index("idx_time_to_from", "created_at", to_id, from_id),
    )

    def update(self, **kwargs):
        # Contact表不应该被更新
        raise NotImplementedError("contact table can`t update ")

    @classmethod
    def create(cls, **kwargs):
        ok, obj = super().create(**kwargs)
        cls.clear_mc(obj, 1)
        return ok, obj

    def delete(self):
        super().delete()
        self.clear_mc(self, -1)

    @classmethod
    @cache(MC_KEY_FOLLOW_ITEM.format("{from_id}", "{to_id}"))
    def get_follow_item(cls, from_id, to_id):
        return cls.query.filter_by(from_id=from_id, to_id=to_id).first()

    @classmethod
    @cache(MC_KEY_FOLLOWING.format("{user_id}", "{page}"))
    def get_following_ids(cls, user_id, page=1):
        query = cls.query.with_entities(cls.to_id).filter_by(from_id=user_id)
        following = query.paginate(page, PER_PAGE)
        following.items = [id for id, in following.items]
        del following.query
        return following

    @classmethod
    @cache(MC_KEY_FOLLOWERS.format("{user_id}", "{page}"))
    def get_follower_ids(cls, user_id, page=1):
        query = cls.query.with_entities(cls.from_id).filter_by(to_id=user_id)
        follower = query.paginate(page, PER_PAGE)
        follower.items = [id for id, in follower.items]
        del follower.query
        return follower

    @classmethod
    def clear_mc(cls, target, amount):
        to_id = target.to_id
        from_id = target.from_id

        st = userFollowStats.get_or_create(to_id)
        follower_count = st.follower_count or 0
        st.follower_count = follower_count + amount
        st.save()
        st = userFollowStats.get_or_create(from_id)
        following_count = st.following_count or 0
        st.following_count = following_count + amount
        st.save()

        rdb.delete(MC_KEY_FOLLOW_ITEM.format(from_id, to_id))

        for user_id, total, mc_key in (
            (to_id, follower_count, MC_KEY_FOLLOWERS),
            (from_id, following_count, MC_KEY_FOLLOWING),
        ):
            pages = math.ceil((max(total, 0) or 1) / PER_PAGE)
            for p in range(1, pages + 1):
                rdb.delete(mc_key.format(user_id, p))


class userFollowStats(BaseMixin, db.Model):
    # 表的id存储的contact的to_id，也就是user的id
    follower_count = db.Column(db.Integer, default=0)
    following_count = db.Column(db.Integer, default=0)

    __table_args__ = {"mysql_charset": "utf8"}

    @classmethod
    def get(cls, id):
        return cls.cache.get(id)

    @classmethod
    def get_or_create(cls, id, **kw):
        st = cls.get(id)
        if not st:
            session = db.create_scoped_session()
            st = cls(id=id)
            session.add(st)
            session.commit()
        # 如果直接把这个scoped_session()的st返回了，会造成sqlalchemy.exc.InvalidRequestError:
        #  Object '<userFollowStats at 0x1058976d8>' is already attached to session '5' (this is '4')
        st = cls.get(id)
        return st
