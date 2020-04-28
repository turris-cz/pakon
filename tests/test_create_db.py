#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

from pakon_light.cli.create_db import create_db
from pakon_light.models.traffic import Traffic

DB_PATH = 'sqlite://'


def test_create_db():
    create_db(DB_PATH, Traffic)
