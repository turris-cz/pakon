#   Copyright (C) 2017 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

import logging
import os
from pathlib import Path

logger = logging.getLogger('pakon-light')

DEV = os.environ.get('ENV') == 'dev'

ROOT_PATH = Path('./tmp') if DEV else Path('/')
DB_DIR = ROOT_PATH / 'var/lib/'
DB_PATH = DB_DIR / 'pakon.db'
ARCHIVE_DB_DIR = ROOT_PATH / 'srv/pakon'
ARCHIVE_DB_PATH = ARCHIVE_DB_DIR / 'pakon-archive.db'

LOGGING_PATH = '/tmp/pakon-light.log'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'short': {
            'format': '%(levelname)s [%(filename)s:%(lineno)s] %(message)s',
            'datefmt': '%d/%b/%Y %H:%M:%S',
        },
        'long': {
            'format': '[%(asctime)s] %(levelname)s [%(pathname)s:%(lineno)s] %(message)s',
            'datefmt': '%d/%b/%Y %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'short',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'long',
            'filename': LOGGING_PATH,
        }
    },
    'loggers': {
        'pakon-light': {
            'level': 'DEBUG',
            'handlers': ['file'],
            'propagate': False,
        },
        '': {
            'level': 'WARNING',
            'handlers': ['file'],
            'propagate': False,
        },
    },
}
