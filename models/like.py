from ext import db
from models.mixin import ActionMixin


class LikeItem(ActionMixin, db.Model):
    __tablename__ = "like_items"
    user_id = db.Column(db.Integer)
    target_id = db.Column(db.Integer)
    target_kind = db.Column(db.Integer)

    action_type = "like"

    __table_args__ = (db.Index("idx_ti_tk_ui", target_id, target_kind, user_id),)


class LikeMixin:
    def like(self, user_id):
        item = LikeItem.get_by_target(user_id, self.id, self.kind)
        if item:
            return False

        LikeItem.create(user_id=user_id, target_id=self.id, target_kind=self.kind)
        return True

    def unlike(self, user_id):
        item = LikeItem.get_by_target(user_id, self.id, self.kind)
        if item:
            item.delete()
            return True
        return False

    @property
    def n_likes(self):
        return LikeItem.get_count_by_target(self.id, self.kind)

    def is_liked_by(self, user_id):
        return LikeItem.is_action_by(user_id, self.id, self.kind)
