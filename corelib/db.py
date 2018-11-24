import copy
import json
from datetime import datetime

from walrus import Database

from config import REDIS_URL
from corelib.local_cache import lc

rdb = Database.from_url(REDIS_URL)


class PropsMixin:
    @property
    def _props_name(self):
        return f"__{self.get_uuid()}/props_cached"

    @property
    def _props_db_key(self):
        return f"{self.get_uuid()}/props"

    def _get_props(self):
        props = lc.get(self._props_name)
        if props is None:
            props = rdb.get(self._props_db_key) or ""
            props = json.loads(props) if props else {}
            lc.set(self._props_name, props)
        return props

    def _set_props(self, props):
        rdb.set(self._props_db_key, json.dumps(props))
        lc.delete(self._props_name)

    def _destroy_props(self):
        rdb.delete(self._props_db_key)
        lc.delete(self._props_name)

    get_props = _get_props
    set_props = _set_props

    props = property(_get_props, _set_props)

    def get_props_item(self, key, default=None):
        return self.props.get(key, default)

    def set_props_item(self, key, value):
        props = self.props
        props[key] = value
        self.props = props

    def delete_props_item(self, key):
        props = self.props
        props.pop(key, None)
        self.props = props

    def update_props(self, data):
        props = self.props
        props.update(data)
        self.props = props

    def incr_props_item(self, key):
        n = self.get_props_item(key, 0)
        n += 1
        self.set_props_item(key, n)
        return n

    def decr_props_item(self, key, min_val=0):
        n = self.get_props_item(key, 0)
        n -= 1
        n = n if n > min_val else min_val
        self.set_props_item(key, n)
        return n

