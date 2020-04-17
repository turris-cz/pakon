#  Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#  This is free software, licensed under the GNU General Public License v3.
#  See /LICENSE for more information.

import argparse
import os

from pakon_light import settings
from pakon_light.model import Base
from pakon_light.utils import uci_get
from sqlalchemy import create_engine

DB_DIR = '.'
# DB_DIR = '/var/lib/'
DB_PATH = f'{DB_DIR}/pakon.db'

ARCHIVE_DB_DIR = '.'
# ARCHIVE_DB_DIR = '/srv/pakon'
ARCHIVE_DB_PATH = f'{ARCHIVE_DB_DIR}/pakon-archive.db'


def main():
    args = parse_args()
    create_db(DB_PATH)
    create_db(uci_get('pakon.archive.path') or ARCHIVE_DB_PATH)


def create_db(path):
    settings.logger.info('create_db is starting...')

    db_directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(db_directory, exist_ok=True)

    db_engine = create_engine(f'sqlite:///{path}', echo=True)
    connection = db_engine.connect()

    Base.metadata.create_all(db_engine)

    connection.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description='Create pakon and pakon-archive SQLite databases.'
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='run in verbose mode',
    )
    return parser.parse_args()


if __name__ == '__main__':
    main()
