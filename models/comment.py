from corelib.db import PropsItem
from corelib.utils import cached_hybrid_property
from ext import db
from models.consts import K_COMMENT
from models.like import LikeMixin
from models.mixin import ActionMixin


class Comment(ActionMixin, LikeMixin, db.Model):
    __tablename__ = "comments"
    user_id = db.Column(db.Integer)
    target_id = db.Column(db.Integer)
    target_kind = db.Column(db.Integer)
    ref_id = db.Column(db.Integer, default=0)
    content = PropsItem("content", "")
    kind = K_COMMENT

    action_type = "comment"

    __table_args__ = (db.Index("idx_ti_tk_ui", target_id, target_kind, user_id),)

    @cached_hybrid_property
    def html_content(self):
        return self.content


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

    @property
    def n_comments(self):
        return self.get_n_comments()
