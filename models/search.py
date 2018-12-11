from collections import defaultdict

from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import Document, Integer, Text, Boolean, Q, Keyword
from elasticsearch.helpers import parallel_bulk
from elasticsearch.exceptions import ConflictError
from flask_sqlalchemy import Pagination

from corelib.mc import cache, rdb
from models.consts import K_POST
from models.core import Post
from config import ES_HOSTS, PER_PAGE


connections.create_connection(hosts=ES_HOSTS)

ITEM_MC_KEY = "core:search:{}:{}"
SERACH_FIELDS = ["title^10", "tags^5", "content^2"]
TARGET_MAPPER = {K_POST: Post}


def get_item_data(item):
    try:
        content = item.content
    except AttributeError:
        content = ""
    try:
        tags = [tag.name for tag in item.tags]
    except AttributeError:
        tags = []
    return {
        "id": item.id,
        "tags": tags,
        "content": content,
        "title": item.title,
        "kind": item.kind,
        # "n_likes": item.n_likes,
        # "n_comments": item.n_comments,
        # "n_collects": item.n_collects,
    }


class Item(Document):
    title = Text()
    kind = Integer()
    content = Text()
    n_likes = Integer()
    n_collects = Integer()
    n_comments = Integer()
    can_show = Boolean()
    tags = Text(fields={"row": Keyword()})

    class Index:
        name = "test"

    @classmethod
    @cache(ITEM_MC_KEY.format("{id}", "{kind}"))
    def get(cls, id, kind):
        return super().get(f"{id}_{kind}")

    @classmethod
    def add(cls, item):
        obj = cls(**get_item_data(item))
        obj.save()
        obj.clear_mc(item.id, item.kind)
        return obj

    @classmethod
    def update_item(cls, item):
        obj = cls.get(item.id, item.kind)
        if obj is None:
            return cls.add(obj)
        if not obj:
            return

        kw = get_item_data(item)
        try:
            obj.update(**kw)
        except ConflictError:
            obj.clear_mc(item.id, item.kind)
            obj = cls.get(item.id, item.kind)
            obj.update(**kw)
        obj.clear_mc(item.id, item.kind)
        return True

    @classmethod
    def clear_mc(cls, id, kind):
        rdb.delete(ITEM_MC_KEY.format(id, kind))

    @classmethod
    def delete(cls, item):
        rs = cls.get(item.id, item.kind)
        if rs:
            super(cls, rs).delete()
            cls.clear_mc(item.id, item.kind)
            return True
        return False

    @classmethod
    def get_es(cls):
        search = cls.search()
        return connections.get_connection(search._using)

    @classmethod
    def bulk_update(cls, items, chunk_size=5000, op_type="update", **kwargs):
        index = cls._index._name
        _type = cls._doc_type.name
        obj = [
            {
                "_op_type": op_type,
                "_id": f"{doc.id}_{doc.kind}",
                "_index": index,
                "_type": _type,
                "_source": doc.to_dict(),
            }
            for doc in items
        ]
        client = cls.get_es()
        rs = list(parallel_bulk(client, obj, chunk_size=chunk_size, **kwargs))
        for item in items:
            cls.clear_mc(item.id, item.kind)
        return rs

    @classmethod
    def new_search(cls, query, page, order_by=None, per_page=PER_PAGE):
        s = cls.search()
        s = s.query("multi_match", query=query, fields=SERACH_FIELDS)
        start = (page - 1) * PER_PAGE
        s = s.extra(**{"from": start, "size": per_page})
        s = s if order_by is None else s.sort(order_by)
        rs = s.execute()
        dct = defaultdict(list)
        for i in rs:
            dct[i.kind].append(i.id)

        items = []
        for kind, ids in dct.items():
            target_cls = TARGET_MAPPER.get(kind)
            if target_cls:
                items_ = target_cls.get_multi(ids)
                items.extend(items_)

        return Pagination(query, page, per_page, rs.hits.total, items)

