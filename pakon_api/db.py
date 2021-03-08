from tinydb import TinyDB, Query
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = TinyDB(current_app.config["DATABASE"])


def clear_db(db):
    g.db.truncate()


def save_password(password):
    # check if password exists
    g.db.truncate()
    res = g.db.insert({
        "role": "master",
        "hash": password
    })
    return res == 1


def get_hash(role="master"):
    query = Query()
    try:
        entry = g.db.search(
            query.role == role
        )[0]["hash"]
    except (IndexError, KeyError):
        return False
    return entry
