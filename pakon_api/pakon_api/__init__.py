#
# pakon-api
# Copyright (C) 2021 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
#

__version__ = '0.0.1'

import os
from flask import Flask, jsonify, request
from pakon_api.pakon_api.auth import authorized

from pakon_api.pakon_api.backend import (
    fetch_data,
    process_query,
    register_user,
    login,
    logout
)


def create_app(test_config=None):
    app = Flask(__name__)

    app.config.from_mapping(
        DATABASE=os.path.join('auth.json')
    )

    app.secret_key = 'xdfrgesdfsdcx'

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    @app.route('/pakon/api/get/')
    @authorized
    def get_data():
        _filters = process_query(request.args)
        return jsonify(fetch_data(_filters))

    @app.route('/pakon/register', methods=['POST'])
    def register():
        res = register_user(request.json["password"])
        return jsonify(res)

    @app.route('/pakon/login', methods=['POST'])
    def login_route():
        res = login(request.json["password"])
        return jsonify(res)

    @app.route('/pakon/logout')
    def logout_route():
        return logout()

    return app
