import logging
from flask import Flask, jsonify, request

from pakon_api.backend import fetch_data, process_query  # noqa: E501, E402
# from pakon_api.auth import save_password


def create_app():
    app = Flask(__name__)
    logger = logging.Logger(__name__)

    @app.route('/pakon/api/get/')
    def get_data():
        _filters = process_query(request.args)
        return jsonify(fetch_data(_filters))

    @app.route('/pakon/register', methods=['POST'])
    def register():
        return request.json
        # save_password()

    @app.route('/pakon/login', methods=['POST'])
    def login():
        pass
