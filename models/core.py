import pathlib
import math
import redis
from urllib.parse import urlparse

from ext import db
from corelib.db import PropsItem
from corelib.mc import rdb, cache
from corelib.utils import cached_hybrid_property, is_numeric, trunc_utf8
from config import PER_PAGE
from .mixin import BaseMixin
from .consts import K_POST
from .comment import CommentMixin
from .like import LikeMixin
from .collect import CollectMixin
from .user import User

MC_KEY_ALL_TAGS = "core:all_tags"
MC_KEY_POSTS_BY_TAG = "core:posts_by_tags:{}:{}"
MC_KEY_POST_COUNT_BY_TAG = "core:count_by_tags:{}"
MC_KEY_POST_TAGS = "core:post:{}:tags"
HERE = pathlib.Path(__file__).resolve()


class Post(BaseMixin, CommentMixin, LikeMixin, CollectMixin, db.Model):
    __tablename__ = "posts"
    author_id = db.Column(db.Integer)
    title = db.Column(db.String(128), default="")
    orig_url = db.Column(db.String(255), default="")
    can_comment = db.Column(db.Boolean, default=True)
    content = PropsItem("content", "")
    kind = K_POST

    __table_args__ = (db.Index("idx_title", title), db.Index("idx_authorId", author_id))

    @cached_hybrid_property
    def abstract_content(self):
        return trunc_utf8(self.content, 100)

    @cached_hybrid_property
    def author(self):
        return User.get(self.author_id)

    @cached_hybrid_property
    def orig_netloc(self):
        return urlparse(self.orig_url).netloc

    @classmethod
    def get(cls, identifier):
        if is_numeric(identifier):
            return cls.cache.get(identifier)
        return cls.cache.filter(title=identifier).first()

    @property
    @cache(MC_KEY_POST_TAGS.format("{self.id}"))
    def tags(self):
        at_ids = (
            PostTag.query.with_entities(PostTag.tag_id)
            .filter(PostTag.post_id == self.id)
            .all()
        )
        tags = Tag.query.filter(Tag.id.in_((id for id, in at_ids))).all()
        return tags

    @classmethod
    def create_or_update(cls, **kwargs):
        tags = kwargs.pop("tags", [])
        created, obj = super(Post, cls).create_or_update(**kwargs)
        if tags:
            PostTag.update_multi(obj.id, tags)
        return created, obj

    def delete(self):
        id = self.id
        super().delete()
        for pt in PostTag.query.filter_by(post_id=id):
            pt.delete()

    @classmethod
    def __flush_event__(cls, target):
        rdb.delete(MC_KEY_ALL_TAGS)

    @staticmethod
    def _flush_insert_event(mapper, connection, target):
        target._flush_event(mapper, connection, target)
        target.__flush_insert_event__(target)


class Tag(BaseMixin, db.Model):
    __tablename__ = "tags"
    name = db.Column(db.String(128), default="", unique=True)

    __table_args__ = (db.Index("idx_name", name),)

    @classmethod
    def get_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    def update(self, **kwargs):
        raise NotImplementedError("tag table can`t update ")

    def delete(self):
        raise NotImplementedError("tag table can`t delete ")

    @classmethod
    def create(cls, **kwargs):
        name = kwargs.pop("name")
        kwargs["name"] = name.lower()
        return super().create(**kwargs)

    @classmethod
    @cache(MC_KEY_ALL_TAGS)
    def all_tags(cls):
        return cls.query.all()

    @classmethod
    def __flush_event__(cls, target):
        rdb.delete(MC_KEY_ALL_TAGS)


class PostTag(BaseMixin, db.Model):
    __tablename__ = "post_tags"
    post_id = db.Column(db.Integer)
    tag_id = db.Column(db.Integer)

    __table_args__ = (
        db.Index("idx_post_id", post_id, "updated_at"),
        db.Index("idx_tag_id", tag_id, "updated_at"),
    )

    @classmethod
    def _get_post_by_tag(cls, identifier):
        if not identifier:
            return []
        if not is_numeric(identifier):
            tag = Tag.get_by_name(identifier)
            if not tag:
                return []
            identifier = tag.id
        at_ids = (
            cls.query.with_entities(cls.post_id).filter(cls.tag_id == identifier).all()
        )
        query = Post.query.filter(Post.id.in_(id for id, in at_ids)).order_by(
            Post.id.desc()
        )
        return query

    @classmethod
    @cache(MC_KEY_POSTS_BY_TAG.format("{identifier}", "{page}"))
    def get_post_by_tag(cls, identifier, page=1):
        query = cls._get_post_by_tag(identifier)
        posts = query.paginate(page, PER_PAGE)
        del posts.query  # Fix `TypeError: can't pickle _thread.lock objects`
        return posts

    @classmethod
    @cache(MC_KEY_POST_COUNT_BY_TAG.format("{identifier}"))
    def get_count_by_tag(cls, identifier):
        query = cls._get_post_by_tag(identifier)
        return query.count()

    @classmethod
    def update_multi(cls, post_id, tags):
        origin_tags = Post.get(post_id).tags
        need_add = set()
        need_del = set()
        for tag in tags:
            if tag not in origin_tags:
                need_add.add(tag)
        for tag in origin_tags:
            if tag not in tags:
                need_del.add(tag)
        need_add_tag_ids = set()
        need_del_tag_ids = set()
        for tag_name in need_add:
            _, tag = Tag.create(name=tag_name)
            need_add_tag_ids.add(tag.id)
        for tag_name in need_del:
            _, tag = Tag.create(name=tag_name)
            need_del_tag_ids.add(tag.id)

        if need_del_tag_ids:
            obj = cls.query.filter(
                cls.post_id == post_id, cls.tag_id.in_(need_del_tag_ids)
            )
            # 更新之前进行查询，获取最新的更新对象
            obj.delete(synchronize_session="fetch")
        for tag_id in need_add_tag_ids:
            cls.create(post_id=post_id, tag_id=tag_id)
        db.session.commit()

    @staticmethod
    def clear_mc(target, amount):
        post_id = target.post_id
        tag_name = Tag.get(target.tag_id).name
        for ident in (post_id, tag_name):
            total = int(PostTag.get_count_by_tag(ident))
            try:
                rdb.incr(MC_KEY_POST_COUNT_BY_TAG.format(ident), amount)
            except redis.exceptions.ResponseError:
                rdb.delete(MC_KEY_POST_COUNT_BY_TAG.format(ident))
                rdb.incr(MC_KEY_POST_COUNT_BY_TAG.format(ident), amount)
            pages = math.ceil((max(total, 0) or 1) / PER_PAGE)
            for p in range(1, pages + 1):
                rdb.delete(MC_KEY_POSTS_BY_TAG.format(ident, p))

    @staticmethod
    def _flush_insert_event(mapper, connection, target):
        super(PostTag, target)._flush_insert_event(mapper, connection, target)
        target.clear_mc(target, 1)

    @staticmethod
    def _flush_before_update_event(mapper, connection, target):
        super(PostTag, target)._flush_before_update_event(mapper, connection, target)
        target.clear_mc(target, -1)

    @staticmethod
    def _flush_after_update_event(mapper, connection, target):
        super(PostTag, target)._flush_after_update_event(mapper, connection, target)
        target.clear_mc(target, 1)

    @staticmethod
    def _flush_delete_event(mapper, connection, target):
        super(PostTag, target)._flush_delete_event(mapper, connection, target)
        target.clear_mc(target, -1)
