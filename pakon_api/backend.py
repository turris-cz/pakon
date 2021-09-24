import jsonschema
from jsonschema.exceptions import ValidationError
from pakon_api.driver import pakon_socket

from pakon_api.utils import load_schema, json_query


def process_query(query):
    try:
        schema = load_schema()
        jsonschema.validate(query, schema)
    except ValidationError as e:
        return {"error": "{}".format(e)}, 500

    query = json_query(query)
    data, error = pakon_socket(query)

    if data:
        return data, 200
    else:
        return {"eroror": f"no data, {error}"}, 500
