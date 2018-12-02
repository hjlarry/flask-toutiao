from ext import db
from models.mixin import BaseMixin
from models.like import LikeMixin
from models.consts import K_COMMENT
from corelib.db import PropsItem
from corelib.mc import pcache, rdb, cache
from corelib.utils import cached_hybrid_property


MC_KEY_COMMENT_LIST = "comment_list:{}:{}"
MC_KEY_COMMENT_N = "comment_list_n:{}:{}"


class Comment(BaseMixin, LikeMixin, db.Model):
    __tablename__ = "comments"
    user_id = db.Column(db.Integer)
    target_id = db.Column(db.Integer)
    target_kind = db.Column(db.Integer)
    ref_id = db.Column(db.Integer, default=0)
    content = PropsItem("content", "")
    kind = K_COMMENT

    __table_args__ = (db.Index("idx_ti_tk_ui", target_id, target_kind, user_id),)

    @cached_hybrid_property
    def html_content(self):
        return self.content

    @classmethod
    def __flush_event__(cls, target):
        for key in (MC_KEY_COMMENT_LIST, MC_KEY_COMMENT_N):
            rdb.delete(key.format(target.id, target.kind))


class CommentMixin:
    def add_comment(self, user_id, content, ref_id=None):
        _, obj = Comment.create(
            user_id=user_id, target_id=self.id, target_kind=self.kind, ref_id=ref_id
        )
        obj.content = content
        return True

    def del_comment(self, user_id, comment_id):
        comment = Comment.get(comment_id)
        if (
            comment
            and comment.user_id == user_id
            and comment.target_id == self.id
            and comment.target_kind == self.kind
        ):
            comment.delete()
            return True
        return False

    def get_comments(self, page, per_page):
        return self._get_comments(start=per_page * (page - 1), limit=per_page)

    @pcache(MC_KEY_COMMENT_LIST.format("{self.id}", "{self.kind}"))
    def _get_comments(self, start=0, limit=20):
        return (
            Comment.query.filter_by(target_id=self.id, target_kind=self.kind)
            .order_by(Comment.id.desc())
            .all()
        )

    @property
    def n_comments(self):
        return self.get_n_comments()

    @cache(MC_KEY_COMMENT_N.format("{self.id}", "{self.kind}"))
    def get_n_comments(self):
        return Comment.get_count_by_target(self.id, self.kind)
