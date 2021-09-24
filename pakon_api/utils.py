import json

def json_query(query):
    js = json.dumps(query) + "\n"
    query = js.encode()
    return query

def load_schema():
    rv = {}
    with open("schema/pakon_query.json", "r") as f:
        rv = json.load(f)
    return rv