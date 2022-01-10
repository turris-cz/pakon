import json
import time
import datetime

from pakon import Config
from subprocess import Popen, PIPE

_PATTERNS = ["%d-%m-%YT%H:%M:%S", "%d-%m-%Y"]


def _datetime_parse(string, fmt):
    """Parse to pattern in specific manner"""
    try:
        dt = datetime.datetime.strptime(string, fmt)
        return True, int(time.mktime(dt.timetuple()))
    except ValueError:
        return False, None


def _try_parse(timestr):
    """Iteratively figure out what pattern suits the situation"""
    for pat in _PATTERNS:
        success, retval = _datetime_parse(timestr, pat)
        if success:
            return retval
    return None


def json_query(query):
    """Helper function to conform time format and also provide json in string format with newline"""
    for key in ("start", "end"):
        if key in query:
            query[key] = _try_parse(query[key])
    js = json.dumps(query) + "\n"
    query = js.encode()
    return query


def load_schema():
    """Helper function to load query schema"""
    rv = {}
    with open(str(Config.PROJECT_ROOT / "pakon" / "schema" / "pakon_query.json"), "r") as f:
        rv = json.load(f)
    return rv
