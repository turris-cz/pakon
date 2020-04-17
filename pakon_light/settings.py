#   Copyright (C) 2017 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

import logging
import os

logger = logging.getLogger('pakon-light')

DEV = os.environ.get('ENV') == 'dev'

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
        # We want only our debug or info messages. Other libraries
        # do a lot of logging as well, for example module sh, but
        # it's a lot of data we don't care about.
        'pakon-light': {
            'level': 'DEBUG',
            'handlers': ['console' if DEV else 'file'],
            'propagate': False,
        },
        '': {
            'level': 'WARNING',
            'handlers': ['console' if DEV else 'file'],
            'propagate': False,
        },
    },
}
