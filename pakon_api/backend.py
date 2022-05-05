import jsonschema
from jsonschema.exceptions import ValidationError

from pakon_api.utils import load_schema, json_query
from pakon.query_socket.__main__ import query as native_query


def process_query(query):
    try:
        schema = load_schema()
        jsonschema.validate(query, schema)
    except ValidationError as e:
        return {"error": "{}".format(e)}, 500

    query = json_query(query)
    try:
        data = native_query(query)
    except Exception as e:
        err = e
        data = []


    if data:
        return data, 200
    else:
        return {"eroror": f"no data, {err}"}, 500
