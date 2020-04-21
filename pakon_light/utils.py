#  Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#  This is free software, licensed under the GNU General Public License v3.
#  See /LICENSE for more information.

import subprocess

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
