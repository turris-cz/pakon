from tinydb import TinyDB
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = TinyDB(current_app.config["DATABASE"])
    return g.db


def clear_db(db):
    db.truncate()
