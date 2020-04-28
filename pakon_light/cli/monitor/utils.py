#  Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#  This is free software, licensed under the GNU General Public License v3.
#  See /LICENSE for more information.

import ctypes
import re
import subprocess
from ctypes.util import find_library

from cachetools import cached, TTLCache

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


@cached(TTLCache(maxsize=256, ttl=3600))
def get_dev_mac(ip):
    pid = subprocess.Popen(["ip", "neigh", "show", ip], stdout=subprocess.PIPE)
    s = pid.communicate()[0].decode()
    if not s:
        settings.logging.debug("No entry in `ip neigh show` for {}".format(ip))
        return "", ""
    res = re.search(r"dev\s+([^\s]+)\s+.*lladdr\s+((?:[a-f\d]{1,2}\:){5}[a-f\d]{1,2})", s)
    if not res:
        settings.logging.warning("no match for dev&mac in output of `ip neigh show {}`: {}".format(ip, s))
        return "", ""
    dev = res.groups()[0]
    mac = res.groups()[1]
    return dev, mac


def is_flow_to_delete(data):
    app_proto_is_dns = data['app_proto'] == 'dns'
    no_bytes_toserver = int(data['flow']['bytes_toserver']) == 0
    no_bytes_toclient = int(data['flow']['bytes_toclient']) == 0
    return app_proto_is_dns or no_bytes_toserver or no_bytes_toclient