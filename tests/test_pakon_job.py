#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

from pakon_light.models.traffic import Traffic
from pakon_light.settings import ARCHIVE_DB_PATH, DB_PATH
from sqlalchemy import MetaData, create_engine


def test_create_dbs_if_not_exist(clear_db, TestPakonJob):
    assert not DB_PATH.exists()
    assert not ARCHIVE_DB_PATH.exists()

    TestPakonJob(with_live_db=True, with_archive_db=True)

    assert DB_PATH.exists()
    assert ARCHIVE_DB_PATH.exists()


DB_COLUMNS = [
    'rowid',
    'start',
    'duration',
    'src_mac',
    'src_ip',
    'src_port',
    'dest_ip',
    'proto',
    'app_proto',
    'bytes_send',
    'bytes_received',
    'app_hostname',
    'flow_id',
    'dest_port',
]


def test_create_db_scheme_if_not_exists(clear_db, TestPakonJob):
    TestPakonJob(with_live_db=True)
    _check_db_columns(DB_PATH, DB_COLUMNS)


ARCHIVE_DB_COLUMNS = [
    'rowid',
    'start',
    'duration',
    'src_mac',
    'src_ip',
    'src_port',
    'dest_ip',
    'proto',
    'app_proto',
    'bytes_send',
    'bytes_received',
    'app_hostname',
    'details',
    'dest_port',
]


def test_create_archive_db_scheme_if_not_exists(clear_db, TestPakonJob):
    TestPakonJob(with_archive_db=True)
    _check_db_columns(ARCHIVE_DB_PATH, ARCHIVE_DB_COLUMNS)


def _check_db_columns(db_path, columns):
    breakpoint()
    db_engine = create_engine(f'sqlite:///{db_path}', echo=True)
    meta = MetaData()
    meta.reflect(bind=db_engine)

    assert list(meta.tables) == ['traffic']

    traffic = meta.tables['traffic']
    traffic_columns = [str(column) for column in traffic.columns]
    expected_traffic_columns = [f'traffic.{column}' for column in columns]
    traffic_columns.sort()
    expected_traffic_columns.sort()
    assert traffic_columns == expected_traffic_columns


def test_dont_recreate_db_if_already_exists(clear_db, TestPakonJob):
    pakon_job = TestPakonJob(with_live_db=True)
    assert _get_traffic_count(pakon_job) == 0
    pakon_job.live_db_session.add(Traffic())
    pakon_job.live_db_session.commit()
    assert _get_traffic_count(pakon_job) == 1
    del pakon_job  # delete job and close db session

    pakon_job = TestPakonJob(with_live_db=True)

    assert _get_traffic_count(pakon_job) == 1


def _get_traffic_count(job):
    traffic_count = job.live_db_session.query(Traffic).count()
    job.live_db_session.commit()
    return traffic_count
