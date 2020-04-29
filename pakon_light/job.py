#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

import argparse
import logging.config
import os
from abc import ABC, abstractmethod

from pakon_light.utils import uci_get
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models.traffic import Traffic
from .models.traffic_archive import TrafficArchive

from .settings import ARCHIVE_DB_PATH, DB_PATH, logger, LOGGING, DEV, LOGGING_PATH


class Job(ABC):
    def run(self):
        """
        Method to be called to start the job.
        """
        args = self.parse_args()
        self.config_logging(debug=args.debug)

        try:
            logger.info('%s is starting', self.job_name)
            self.main(args)
            logger.info('%s finished', self.job_name)
        except KeyboardInterrupt:
            logger.info('%s was aborted', self.job_name)
            exit(2)
        except Exception:  # pylint: disable=broad-except
            logger.exception('%s was ended with an exception', self.job_name)
            exit(3)

    def config_logging(self, debug):
        if not DEV and not debug:
            LOGGING['handlers']['file']['filename'] = f'{LOGGING_PATH}{self.job_name}.log'
        else:
            LOGGING['loggers']['']['handlers'] = ['console']
            LOGGING['loggers']['pakon-light']['handlers'] = ['console']

        logging.config.dictConfig(LOGGING)

    def parse_args(self):
        return self.get_parser().parse_args()

    def get_parser(self):
        """
        Constructs parsers for command line arguments. In case you want to add
        more arguments to your job, override `parse_args_arguments` instead.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('-d', '--debug', action='store_true')

        self.parse_args_arguments(parser)
        return parser

    @property
    def job_name(self):
        return self.__class__.__name__

    @abstractmethod
    def main(self, args):
        """
        Override to provide functionality of the job.
        """

    def parse_args_arguments(self, parser):
        """
        Override to add your arguments to the parser.
        """


class PakonJob(Job):
    def __init__(self, with_live_db=False, with_archive_db=False):
        if with_live_db:
            self.live_db_session = self.create_db_session(DB_PATH, Traffic)
        if with_archive_db:
            archive_db_path = uci_get('pakon.archive.path') or ARCHIVE_DB_PATH
            self.archive_db_session = self.create_db_session(archive_db_path, TrafficArchive)

    @staticmethod
    def create_db_session(path, model):
        logger.info('Start creating "%s"...', {path})
        db_directory = os.path.dirname(os.path.abspath(path))
        os.makedirs(db_directory, exist_ok=True)

        db_engine = create_engine(f'sqlite:///{path}', echo=True)
        Session = sessionmaker(bind=db_engine)
        model.metadata.create_all(db_engine)

        logger.info('"%s" is created.', path)
        return Session()

    def __del__(self):
        if hasattr(self, 'live_db_session'):
            logger.info('Close live DB session.')
            self.live_db_session.close()

        if hasattr(self, 'archive_db_session'):
            logger.info('Close archive DB session.')
            self.archive_db_session.close()
