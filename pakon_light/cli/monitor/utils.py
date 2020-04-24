#  Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#  This is free software, licensed under the GNU General Public License v3.
#  See /LICENSE for more information.

import ctypes
import glob
import re
import sys
from ctypes.util import find_library

from pakon_light import settings

libc = ctypes.CDLL(find_library('c'))

PR_SET_PDEATHSIG = 1
SIGKILL = 9


def set_death_signal():
    libc.prctl(PR_SET_PDEATHSIG, SIGKILL)


class everyN:
    def __init__(self, cnt):
        self.cnt = cnt
        self.cur = 0

    def __bool__(self):
        self.cur += 1
        if self.cnt == self.cur:
            self.cur = 0
            return True
        return False


class MultiReplace:
    """
     Perform replacements specified by regex and adict all at once.
     The regex is constructed such that it matches the whole string (.* in the beginnin and end),
     the actual key from adict is the first group of match (ignoring possible prefix and suffix).
     The whole string is then replaced (the replacement is specified by adict).
    """

    def __init__(self, adict):
        if not adict:
            adict = {}

        self.adict = adict
        self.rx = re.compile("^.*(" + '|'.join(map(re.escape, adict)) + ").*$")

    def replace(self, text):
        def one_xlat(match):
            return self.adict[match.group(1)]

        return self.rx.sub(one_xlat, text)


def load_replaces():
    adict = {}
    try:
        for fn in glob.glob("/usr/share/pakon-light/domains_replace/*.conf"):
            with open(fn) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    match = re.match('"([^"]+)"\s*:\s*"([^"]+)"', line)
                    if not match:
                        print("invalid line: " + line)
                        continue
                    adict[match.group(1)] = match.group(2)
    except IOError as e:
        settings.logger.exception("Can't load domains_services file.")
    return adict

