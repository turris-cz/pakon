#  Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#  This is free software, licensed under the GNU General Public License v3.
#  See /LICENSE for more information.

import glob
import re
import subprocess

from pakon_light import settings

UCI_DELIMITER = '__uci__delimiter__'


# TODO: replace with uci bindings - once available
def uci_get(opt):
    child = subprocess.Popen(
        ['/sbin/uci', '-d', UCI_DELIMITER, '-q', 'get', opt],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )

    out, err = child.communicate()
    out = out.strip().decode('ascii', 'ignore')
    if out.find(UCI_DELIMITER) != -1:
        return out.split(UCI_DELIMITER)
    else:
        return out


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
                    match = re.match(r'"([^"]+)"\s*:\s*"([^"]+)"', line)
                    if not match:
                        print("invalid line: " + line)
                        continue
                    adict[match.group(1)] = match.group(2)
    except IOError as e:
        settings.logger.exception("Can't load domains_services file.")
    return adict
