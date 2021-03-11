from flask import session
from pakon_api.db import get_db
from tinydb import Query
from functools import wraps
from flask import jsonify

import pbkdf2


def _logged_in():
    return session.get('logged', False)


def authorized(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if _logged_in():
            func(*args, **kwargs)
        else:
            return jsonify({"error": "not authorized"})
    return wrapper


def _encode_pbkdef2(password):
    return pbkdf2.crypt(password, iterations=1000)


def _check_encrypted(password):
    _hash = get_hash()
    return _hash == pbkdf2.crypt(password, salt=_hash)


def update_password(password):
    if get_hash() is False:
        pwd_en = _encode_pbkdef2(password)
        return {"success": save_password(pwd_en)}
    else:
        return {"error": "admin already registered"}


def login_to_pakon(password):
    """ Mark session as `logged` if password is correct. """
    if _check_encrypted(password):
        session['logged'] = True
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
