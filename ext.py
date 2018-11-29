import functools
import hashlib
from datetime import datetime

from dogpile.cache import make_region
from dogpile.cache.api import NO_VALUE
from flask_sqlalchemy import BaseQuery, DefaultMeta, Model, SQLAlchemy, _QueryProperty
from sqlalchemy import Column, DateTime, Integer, event, inspect
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base, declared_attr
from sqlalchemy.orm.attributes import get_history
from sqlalchemy.orm.interfaces import MapperOption

from config import REDIS_URL
from corelib.db import PropsMixin


def md5_key_mangler(key):
    if key.startswith("SELECT "):
        key = hashlib.md5(key.encode("ascii")).hexdigest()
    return key


def memoize(obj):
    cache = obj.cache = {}

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]

    return memoizer


regions = dict(
    default=make_region(key_mangler=md5_key_mangler).configure("dogpile.cache.redis"),
    arguments={"url": REDIS_URL},
)


def query_callable(regions, query_cls=CachingQuery):
    return functools.partial(query_cls, regions)


class Cache:
    def __init__(self, model, regions, label):
        self.model = model
        self.regions = regions
        self.label = label
        self.pk = getattr(model, "cache_pk", "id")

    def get(self, pk):
        return self.model.query.options(self.from_cache(pk=pk)).get(pk)

    def count(self, **kwargs):
        if kwargs:
            if len(kwargs) > 1:
                raise TypeError("filter accept only one attribute for filtering")
            key, value = list(kwargs.items())[0]
            if key not in self._attrs():
                raise TypeError(f"{self} does not have an attribute {key}")
        cache_key = self._count_cache_key(**kwargs)
        r = self.regions[self.label]
        count = r.get(cache_key)
        if count is NO_VALUE:
            count = self.model.query.filter_by(**kwargs).count()
            r.set(cache_key, count)
        return count

    def filter(self, order_by="asc", offset=None, limit=None, **kwargs):
        if kwargs:
            if len(kwargs) > 1:
                raise TypeError("filter accept only one attribute for filtering")
            key, value = list(kwargs.items())[0]
            if key not in self._attrs():
                raise TypeError(f"{self} does not have an attribute {key}")
        cache_key = self._cache_key(**kwargs)
        r = self.regions[self.label]
        pks = r.get(cache_key)
        if pks is NO_VALUE:
            pks = [
                o.id
                for o in self.model.query.filter_by(**kwargs).with_entities(
                    getattr(self.model, self.pk)
                )
            ]
            r.set(cache_key, pks)
        if order_by == "desc":
            pks.reverse()
        if offset is not None:
            pks = pks[offset:]
        if limit is not None:
            pks = pks[:limit]
        keys = [self._cache_key(id) for id in pks]
        return Query(self.get_entities(pks, r.get_multi(keys)))

    def get_entities(self, pks, objs):
        for pos, obj in enumerate(objs):
            if obj is NO_VALUE:
                yield self.get(pks[pos])
            else:
                yield obj[0]

    def flush(self, key):
        self.regions[self.label].delete(key)

    @memoize
    def _attrs(self):
        return [a.key for a in inspect(self.model).attrs if a.key != self.pk]

    @memoize
    def from_cache(self, cache_key=None, pk=None):
        if pk:
            cache_key = self._cache_key(pk)
        return FromCache(self.label, cache_key)

    @memoize
    def _count_cache_key(self, pk="all", **kwargs):
        return self._cache_key(pk, **kwargs) + "_count"

    @memoize
    def _cache_key(self, pk="all", **kwargs):
        q_filter = "".join(f"{k}={v}" for k, v in kwargs.items()) or self.pk
        return f"{self.model.__tablename__}.{q_filter}[{pk}]"

    def _flush_all(self, obj):
        for attr in self._attrs():
            added, unchanged, deleted = get_history(obj, attr)
            for value in list(deleted) + list(added):
                self.flush(self._cache_key(**{attr: value}))
        for key in (
            self._cache_key(),
            self._cache_key(getattr(obj, self.pk)),
            self._count_cache_key(),
            self._count_cache_key(getattr(obj, self.pk)),
        ):
            self.flush(key)


class BaseModel(PropsMixin, Model):
    cache_label = "default"
    cache_regions = regions
    query_class = query_callable(regions)

    __table_args__ = {"mysql_charset": "utf8mb4"}
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow())
    updated_at = Column(DateTime, default=None)

    def get_uuid(self):
        return f"/bran/{self.__class__.__name__}/{self.id}"

    def __repr__(self):
        return f"<{self.__class__.__name__} id:{self.id}>"

    @declared_attr
    def cache(cls):
        return Cache(cls, cls.cache_regions, cls.cache_label)

    @classmethod
    def get(cls, id):
        return cls.query.get(id)

    @classmethod
    def get_multi(cls, ids):
        return [cls.get(id) for id in ids]

    def url(self):
        return f"/{self.__class__.__name__.lower()}/{self.id}/"

    def to_dict(self):
        columns = self.__table__.columns.keys()
        return {key: getattr(self, key) for key in columns}

    @staticmethod
    def _flush_event(mapper, connection, target):
        target.cache._flush_all(target)
        target.__flush_event__(target)

    @staticmethod
    def _flush_del_event(mapper, connection, target):
        target.cache._flush_all(target)
        target.__flush_event__(target)

    @classmethod
    def _flush_event(cls, target):
        pass

    @classmethod
    def __declare_last__(cls):
        event.listen(cls, "before_delete", cls._flush_event)
        event.listen(cls, "after_update", cls._flush_event)
        event.listen(cls, "after_insert", cls._flush_del_event)
