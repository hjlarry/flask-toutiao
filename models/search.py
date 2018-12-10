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
                items.extends(items_)

        return Pagination(query, page, per_page, rs.hits.total, items)

