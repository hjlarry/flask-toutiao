import math
import redis
from datetime import datetime

from ext import db
from config import PER_PAGE
from corelib.mc import cache, rdb
from .consts import K_POST

# action_type, target_id, target_kind
MC_KEY_STATS_N = "action_n:{}:{}:{}"
# action_type, target_id, target_kind, page
MC_KEY_ACTION_ITEMS = "action_items:{}:{}:{}:{}"
# action_type, user_id, target_id, target_kind
MC_KEY_ACTION_ITEM_BY_USER = "action_item_by_user:{}:{}:{}:{}"
# action_type, user_id, target_kind, page
MC_KEY_ACTION_ITEMS_BY_USER = "action_items_by_user:{}:{}:{}:{}"


class BaseMixin:
    @classmethod
    def get_db_props(cls, kwargs):
        props = {}
        for col, default in cls._db_columns:
            props[col] = kwargs.pop(col, default)
        return props

    @classmethod
    def create_or_update(cls, **kwargs):
        session = db.session
        props = cls.get_db_props(kwargs)
        id = kwargs.pop("id", None)
        if id is not None:
            obj = cls.query.get(id)
            if obj:
                if "updated_at" not in kwargs:
                    kwargs["updated_at"] = datetime.now()
                for k, v in kwargs.items():
                    setattr(obj, k, v)
                session.commit()
                cls.update_db_props(obj, props)
                return False, obj
        obj = cls(**kwargs)
        obj.save()
        cls.update_db_props(obj, props)
        return True, obj

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.save()

    @classmethod
    def create(cls, **kwargs):
        props = cls.get_db_props(kwargs)
        if not kwargs:
            return False, None
        filter = cls.query.filter_by(**kwargs)
        obj = filter.first()
        if obj:
            return False, obj
        obj = cls(**kwargs)
        obj.save()
        cls.update_db_props(obj, props)
        return True, obj

    @classmethod
    def update_db_props(cls, obj, db_props):
        for prop, value in db_props.items():
            obj.set_props_item(prop, value)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class ActionMixin(BaseMixin):
    action_type = None

    @classmethod
    @cache(MC_KEY_STATS_N.format("{cls.action_type}", "{target_id}", "{target_kind}"))
    def get_count_by_target(cls, target_id, target_kind):
        return cls.query.filter_by(target_id=target_id, target_kind=target_kind).count()

    @classmethod
    @cache(
        MC_KEY_ACTION_ITEM_BY_USER.format(
            "{cls.action_type}", "{user_id}", "{target_id}", "{target_kind}"
        )
    )
    def get_by_target(cls, user_id, target_id, target_kind):
        return cls.query.filter_by(
            user_id=user_id, target_id=target_id, target_kind=target_kind
        ).first()

    @classmethod
    @cache(
        MC_KEY_ACTION_ITEMS_BY_USER.format(
            "{cls.action_type}", "{user_id}", "{target_kind}", "{page}"
        )
    )
    def get_target_ids_by_user(cls, user_id, target_kind=K_POST, page=1):
        query = cls.query.with_entities(cls.target_id).filter_by(
            user_id=user_id, target_kind=target_kind
        )
        posts = query.paginate(page, PER_PAGE)
        posts.items = [id for id, in posts.items]
        del posts.query
        return posts

    @classmethod
    @cache(
        MC_KEY_ACTION_ITEMS.format(
            "{cls.action_type}", "{target_id}", "{target_kind}", "{page}"
        )
    )
    def get_items_by_target(cls, target_id, target_kind, page=1):
        query = cls.query.filter_by(
            target_id=target_id, target_kind=target_kind
        ).order_by(cls.id.desc())
        if page is None:
            items = query.all()
        else:
            items = query.limit(PER_PAGE).offset(page * PER_PAGE * (page - 1))
        return items

    @classmethod
    def is_action_by(cls, user_id, target_id, target_kind):
        return bool(cls.get_by_target(user_id, target_id, target_kind))

    @classmethod
    def __flush_insert_event__(cls, target):
        super().__flush_insert_event__(target)
        target.clear_mc(target, 1)

    @classmethod
    def __flush_before_update_event__(cls, target):
        super().__flush_before_update_event__(target)
        target.clear_mc(target, -1)

    @classmethod
    def __flush_after_update_event__(cls, target):
        super().__flush_after_update_event__(target)
        target.clear_mc(target, 1)

    @classmethod
    def __flush_delete_event__(cls, target):
        super().__flush_delete_event__(target)
        target.clear_mc(target, -1)

    @classmethod
    def clear_mc(cls, target, amount):
        action_type = cls.action_type
        target_id = target.target_id
        target_kind = target.target_kind
        user_id = target.user_id
        stat_key = MC_KEY_STATS_N.format(action_type, target_id, target_kind)

        try:
            total = rdb.incr(stat_key, amount)
        except redis.exceptions.ResponseError:
            rdb.delete(stat_key)
            total = rdb.incr(stat_key, amount)
        rdb.delete(
            MC_KEY_ACTION_ITEM_BY_USER.format(
                action_type, user_id, target_id, target_kind
            )
        )

        pages = math.ceil((max(total, 0) or 1) / PER_PAGE)
        for p in list(range(1, pages + 1)) + [None]:
            rdb.delete(
                MC_KEY_ACTION_ITEMS.format(action_type, target_id, target_kind, p)
            )
            rdb.delete(
                MC_KEY_ACTION_ITEMS_BY_USER.format(action_type, user_id, target_kind, p)
            )
