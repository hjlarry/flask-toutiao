from collections import defaultdict

from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import Document, Integer, Text, Boolean, Q, Keyword
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
    def clear_mc(cls, id, kind):
        rdb.delete(ITEM_MC_KEY.format(id, kind))

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

