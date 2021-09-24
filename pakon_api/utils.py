import json

def load_schema():
    rv = {}
    with open("schema/pakon_query.json", "r") as f:
        rv = json.load(f)
    return rv