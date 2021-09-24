import pakon_api
import jsonschema
from jsonschema.exceptions import ValidationError
from pakon_api.driver import pakon_socket

from pakon_api.utils import load_schema, json_query
from flask import jsonify

import json
import socket

import sys

# def process_query(query):
#     response = []
#     try:
#         schema = load_schema()
#         jsonschema.validate(query, schema)
#     except ValidationError as e:
#         return {"error": "{}".format(e)}, 500
    
#     with pakon_socket() as s:
#         query = json.dumps(query)
#         s.sendall(json.dumps(query+"\n").encode())
#         with s.makefile() as f:
#             response = f.readline().strip()
    
#     try:
#         data=json.loads(response)
#     except Exception as e:
#         return {"error": "{}".format(e)}, 500
     
#     return data, 200



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
        return {"eroror": error}, 500
