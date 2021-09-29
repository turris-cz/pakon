import json
import time
import datetime


def json_query(query):
    """Helper function to conform time format and also provide json in string format with newline"""
    for key in ("start", "end"):
        if key in query:
            query[key] = datetime_parse(query[key], "%d-%m-%YT%H:%M:%S")
    js = json.dumps(query) + "\n"
    query = js.encode()
    return query


def load_schema():
    """Helper function to load query schema"""
    rv = {}
    with open("schema/pakon_query.json", "r") as f:
        rv = json.load(f)
    return rv


def datetime_parse(string, fmt):
    try:
        dt = datetime.datetime.strptime(string, fmt)
        return int(time.mktime(dt.timetuple()))
    except ValueError:
        return None()
