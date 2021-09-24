import jsonschema
from jsonschema.exceptions import ValidationError
from pakon_api.driver import pakon_socket

from pakon_api.utils import load_schema
from flask import jsonify

import json

def process_query(query):
    try:
        schema = load_schema()
        jsonschema.validate(query, schema)
    except ValidationError as e:
        return {"error": "{}".format(e)}, 500
    
    with pakon_socket as s:
       response =  s.sendall(json.dumps(query).encode())
     
    return {"success": response}, 200