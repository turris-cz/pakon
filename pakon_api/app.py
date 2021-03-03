import logging

from flask import Flask, jsonify, request

app = Flask(__name__)
logger = logging.Logger(__name__)

from pakon_api.backend import fetch_data, process_query  # noqa: E402


@app.route('/get/')
def get_data():
    _filters = process_query(request.args)
    return jsonify(fetch_data(_filters))
