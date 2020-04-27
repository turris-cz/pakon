#  Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#  This is free software, licensed under the GNU General Public License v3.
#  See /LICENSE for more information.

import ctypes
from ctypes.util import find_library

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


