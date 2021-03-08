from tinydb import TinyDB, Query

db = TinyDB('auth.js')


def save_password(password):
    # check if password exists
    db.truncate()
    res = db.insert({
        "role": "master",
        "hash": password
    })
    return res == 1


def get_hash(role="master"):
    query = Query()
    try:
        entry = db.search(
            query.role == role
        )[0]["hash"]
    except (IndexError, KeyError):
        return False
    return entry
