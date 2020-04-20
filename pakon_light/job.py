#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

import argparse
import logging.config
from abc import ABC, abstractmethod

from pakon_light import settings


class Job(ABC):
    def run(self):
        """
        Method to be called to start the job.
        """
        self.config_logging()
        args = self.parse_args()
        try:
            settings.logger.info('%s is starting', self.job_name)
            self.main(args)
            settings.logger.info('%s finished', self.job_name)
        except KeyboardInterrupt:
            settings.logger.info('%s was aborted', self.job_name)
            exit(2)
        except Exception:  # pylint: disable=broad-except
            settings.logger.exception('%s was ended with an exception', self.job_name)
            exit(3)

    def config_logging(self):
        if not settings.DEV:
            settings.LOGGING['handlers']['file']['filename'] = f'{settings.LOGGING_PATH}{self.job_name}.log'
        logging.config.dictConfig(settings.LOGGING)

    def parse_args(self):
        return self.get_parser().parse_args()

    def get_parser(self):
        """
        Constructs parsers for command line arguments. In case you want to add
        more arguments to your job, override `parse_args_arguments` instead.
        """
        parser = argparse.ArgumentParser()
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
