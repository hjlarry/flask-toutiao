import pathlib
import pickle
from datetime import datetime
from html.parser import HTMLParser

import feedparser

from app import app
from models.core import Post, Tag, PostTag, db
from models.search import Item
from models.user import User


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return "".join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def save_results(entry, user_id):
    try:
        content = entry.content and entry.content[0].value
    except AttributeError:
        content = entry.summary or entry.title

    try:
        created_at = datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        created_at = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")

    try:
        tags = entry.tags
    except AttributeError:
        tags = []

    try:
        ok, post = Post.create_or_update(
            author_id=user_id,
            title=entry.title,
            orig_url=entry.link,
            content=strip_tags(content),
            created_at=created_at,
            tags=[tag.term for tag in tags],
        )
    except Exception as e:
        raise e


def fetch(url):
    metafile = pathlib.Path("test.data")
    if not metafile.exists():
        d = feedparser.parse(url)
        with open(metafile, "wb") as f:
            pickle.dump(d, f)
    else:
        with open(metafile, "rb") as f:
            d = pickle.load(f)
    entries = d.entries
    _, user1 = User.create(
        name="hjlarry",
        email="hjlarry@163.com",
        password="123",
        active=True,
        confirmed_at=datetime.utcnow(),
    )
    _, user2 = User.create(
        name="hjlarry1",
        email="hjlarry1@163.com",
        password="123",
        active=True,
        confirmed_at=datetime.utcnow(),
    )
    _, user3 = User.create(
        name="hjlarry2",
        email="hjlarry2@163.com",
        password="123",
        active=True,
        confirmed_at=datetime.utcnow(),
    )

    for entry in entries[:20]:
        save_results(entry, user1.id)

    for entry in entries[20:90]:
        save_results(entry, user2.id)

    for entry in entries[90:]:
        save_results(entry, user3.id)
    # Item.bulk_update(posts, op_type="create")

    user1.follow(user2.id)
    user1.follow(user3.id)
    user2.follow(user3.id)


def main():
    with app.test_request_context():
        Item._index.delete(ignore=404)
        Item.init()
        for model in (Post, Tag, PostTag, User):
            model.query.delete()
        db.session.commit()
        fetch("http://www.dongwm.com/atom.xml")


if __name__ == "__main__":
    main()
