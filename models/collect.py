from ext import db
from models.mixin import ActionMixin


class CollectItem(ActionMixin, db.Model):
    __tablename__ = "collect_items"
    user_id = db.Column(db.Integer)
    target_id = db.Column(db.Integer)
    target_kind = db.Column(db.Integer)

    action_type = "collect"

    __table_args__ = (db.Index("idx_ti_tk_ui", target_id, target_kind, user_id),)


class CollectMixin:
    def collect(self, user_id):
        item = CollectItem.get_by_target(user_id, self.id, self.kind)
        if item:
            return False

        ok, _ = CollectItem.create(
            user_id=user_id, target_id=self.id, target_kind=self.kind
        )
        return ok

    def uncollect(self, user_id):
        item = CollectItem.get_by_target(user_id, self.id, self.kind)
        if item:
            item.delete()
            return True
        return False

    @property
    def n_collects(self):
        return CollectItem.get_count_by_target(self.id, self.kind)

    def is_collected_by(self, user_id):
        return CollectItem.is_action_by(user_id, self.id, self.kind)
