#  Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#  This is free software, licensed under the GNU General Public License v3.
#  See /LICENSE for more information.

import os
from pathlib import Path

from pakon_light import settings
from pakon_light.job import Job

from pakon_light.models import Traffic, TrafficArchive
from pakon_light.settings import DEV
from pakon_light.utils import uci_get
from sqlalchemy import create_engine

ROOT_PATH = Path('./tmp') if DEV else Path('/')

DB_DIR = ROOT_PATH / 'var/lib/'
DB_PATH = DB_DIR / 'pakon.db'

ARCHIVE_DB_DIR = ROOT_PATH / 'srv/pakon'
ARCHIVE_DB_PATH = ARCHIVE_DB_DIR / 'pakon-archive.db'


def main():
    CreateDBJob().run()


class CreateDBJob(Job):
    def main(self, args):
        create_db(DB_PATH, Traffic)

        archive_db_path = ARCHIVE_DB_PATH
        if not DEV:
            archive_db_path = uci_get('pakon.archive.path') or ARCHIVE_DB_PATH

        create_db(archive_db_path, TrafficArchive)


def create_db(path, model):
    settings.logger.info('Start creating "%s"...', {path})
    db_directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(db_directory, exist_ok=True)

    db_engine = create_engine(f'sqlite:///{path}', echo=True)
    connection = db_engine.connect()

    model.metadata.create_all(db_engine)

    connection.close()
    settings.logger.info('"%s" is created.', path)


if __name__ == '__main__':
    main()
