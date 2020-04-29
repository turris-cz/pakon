#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

from pytest import fixture

from pakon_light.job import PakonJob
from pakon_light.settings import DB_PATH, DB_DIR, ARCHIVE_DB_PATH, ARCHIVE_DB_DIR, logger


@fixture()
def clear_db():
    if DB_PATH.is_file():
        DB_PATH.unlink()
    if DB_DIR.is_dir():
        DB_DIR.rmdir()

    if ARCHIVE_DB_PATH.is_file():
        ARCHIVE_DB_PATH.unlink()
    if ARCHIVE_DB_DIR.is_dir():
        ARCHIVE_DB_DIR.rmdir()


@fixture()
def TestPakonJob():
    class TestPakonJob(PakonJob):
        def main(self):
            ...

    return TestPakonJob
