from celery.utils.log import get_task_logger

from app import app as flask_app
from handler.celery import app
from models.search import Item, TARGET_MAPPER
from models.consts import K_POST
from models.core import Post
from models.feed import (
    feed_to_followers as feed_to_followers_,
    feed_post as feed_post_,
    remove_post_from_feed as remove_post_from_feed_,
    remove_user_posts_from_feed as remove_user_posts_from_feed_,
    ActivityFeed,
)


logger = get_task_logger(__name__)


class RequestContextTask(app.Task):
    abstract = True

    def __call__(self, *args, **kwargs):
        with flask_app.test_request_context():
            return super().__call__(*args, **kwargs)


@app.task(base=RequestContextTask)
def reindex(id, kind, op_type):
    target_cls = TARGET_MAPPER.get(kind)
    if not target_cls:
        logger.info(f"Reindex error : unexpected kind {kind}")
        return

    target = target_cls.get(id)
    if not target:
        logger.info(f"Reindex error: unexpected {target.__class__.__name__}<id={id}>")
        return
    logger.info(f"Reindex {target.__class__.__name__}<id={id}>")
    if kind != K_POST:
        return

    item = None

    if op_type == "create":
        item = Item.add(target)
    elif op_type == "update":
        item = Item.update_item(target)
    elif op_type == "delete":
        item = Item.get(target.id, target.kind)

    if item:
        logger.info(f"Reindex finish {target.__class__.__name__}<id={id}>")
    else:
        logger.info(f"Reindex failed {target.__class__.__name__}<id={id}>")


@app.task(base=RequestContextTask)
def feed_to_followers(visit_id, uid):
    feed_to_followers_(visit_id, uid)
    logger.info(f"Feed to followers {visit_id}, {uid}")


@app.task(base=RequestContextTask)
def feed_post(post_id):
    post = Post.get(post_id)
    feed_post_(post)
    logger.info(f"feed post post_id={post_id}")


@app.task(base=RequestContextTask)
def remove_post_from_feed(post_id, author_id):
    post = Post.get(post_id)
    remove_post_from_feed_(post, author_id)
    logger.info(f"remove_post_from_feed post_id={post_id}, author_id={author_id}")


@app.task(base=RequestContextTask)
def remove_user_posts_from_feed(visit_id, uid):
    remove_user_posts_from_feed_(visit_id, uid)
    logger.info(f"remove_user_posts_from_feed_ visit_id={visit_id}, uid={uid}")


@app.task(base=RequestContextTask)
def add_to_activity_feed(post_id):
    post = Post.get(post_id)
    ActivityFeed.add(int(post.created_at.strftime("%s")), post_id)
    logger.info(f"add_to_activity_feed post_id={post_id}")
