#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

import os
import socket
import subprocess
import sys
from abc import ABC, abstractmethod

from pakon_light import settings

from .utils import set_death_signal


class Source(ABC):
    @abstractmethod
    def get_message(self):
        pass

    @abstractmethod
    def close(self):
        pass


class UnixSocketSource(Source):
    def __init__(self):
        try:
            os.unlink("/var/run/pakon.sock")
        except OSError:
            pass
        try:
            self.client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            self.client.bind("/var/run/pakon.sock")
        except OSError as e:
            settings.logger.error("Can't read socket")
            settings.logger.error(e)
            sys.exit(1)

    def get_message(self):
        return self.client.makefile().readline()

    def close(self):
        self.client.close()


class ConntrackScriptSource(Source):
    def __init__(self):
        try:
            self.devnull = open(os.devnull, 'w')
            self.conntrack = subprocess.Popen(
                ["/usr/bin/python3", "/usr/libexec/suricata_conntrack_flows.py", "/var/run/pakon.sock"], shell=False,
                stdout=subprocess.PIPE, stderr=self.devnull, preexec_fn=set_death_signal)
        except OSError as e:
            settings.logger.error("Can't run flows_conntrack.py")
            settings.logger.error(e)
            sys.exit(1)

    def get_message(self):
        return self.conntrack.stdout.readline().decode()

    def close(self):
        self.conntrack.terminate()
