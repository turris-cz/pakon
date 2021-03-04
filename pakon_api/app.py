import logging

from flask import Flask, jsonify, request

app = Flask(__name__)
logger = logging.Logger(__name__)

from pakon_api.backend import fetch_data, process_query, get_filtred  # noqa: E501, E402


@app.route('/pakon/api/get/')
def get_data():
    _filters = process_query(request.args)
    return jsonify(fetch_data(_filters))


@app.route('/pakon/api/get/filter_on_api/')
def filter_on_api():
    return jsonify(get_filtred(request.args))
