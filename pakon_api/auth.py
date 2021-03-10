from flask import session
from pakon_api.db import get_db
from tinydb import Query

import pbkdf2


def _encode_pbkdef2(password):
    return pbkdf2.crypt(password, iterations=1000)


def _check_encrypted(password):
    _hash = get_hash()
    return _hash == pbkdf2.crypt(password, salt=_hash)


def update_password(password):
    pwd_en = _encode_pbkdef2(password)
    return save_password(pwd_en)


def login_to_pakon(password):
    """ Mark session as `logged` if password is correct. """
    if _check_encrypted(password):
        # session['logged'] = True
        return True
    return False


def logout_from_pakon():
    session['logged'] = False
    return True


def save_password(password):
    # check if password exists
    db = get_db()
    db.truncate()
    res = db.insert({
        "role": "master",
        "hash": password
    })
    return res == 1


def get_hash(role="master"):
    db = get_db()
    query = Query()
    try:
        entry = db.search(
            query.role == role
        )[0]["hash"]
    except (IndexError, KeyError):
        return False
    return entry
