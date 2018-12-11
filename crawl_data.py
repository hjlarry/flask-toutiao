import pathlib
import pickle
from datetime import datetime
from html.parser import HTMLParser

import feedparser

from app import app
from models.core import Post, Tag, PostTag, db
from models.search import Item


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
    posts = []

    for entry in entries:
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
                author_id=2,
                title=entry.title,
                orig_url=entry.link,
                content=strip_tags(content),
                created_at=created_at,
                tags=[tag.term for tag in tags],
            )
            if ok:
                posts.append(post)
        except Exception as e:
            raise e
    Item.bulk_update(posts, op_type="create")


def main():
    with app.test_request_context():
        Item._index.delete(ignore=404)
        Item.init()
        for model in (Post, Tag, PostTag):
            model.query.delete()
        db.session.commit()
        fetch("http://www.dongwm.com/atom.xml")


if __name__ == "__main__":
    main()
