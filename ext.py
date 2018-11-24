import functools
import hashlib
from datetime import datetime

from dogpile.cache import make_region
from flask_sqlalchemy import BaseQuery, DefaultMeta, Model, SQLAlchemy, _QueryProperty
from sqlalchemy import Column, DateTime, Integer, event, inspect
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base, declared_attr
from sqlalchemy.orm.attributes import get_history
from sqlalchemy.orm.interfaces import MapperOption

from config import REDIS_URL


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
