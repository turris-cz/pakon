#  Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#  This is free software, licensed under the GNU General Public License v3.
#  See /LICENSE for more information.

import os
import sys
import sqlite3

from pakon_light.utils import load_replaces, MultiReplace


def replace(db, multiple_replace):
    con = sqlite3.connect(db)
    c = con.cursor()
    replaced = 0
    for row in c.execute('SELECT DISTINCT(app_hostname) FROM traffic WHERE app_hostname IS NOT NULL'):
        name = multiple_replace.replace(row[0])
        if name != row[0]:
            t = con.cursor()
            t.execute("UPDATE traffic SET app_hostname = ? WHERE app_hostname = ?", (name, row[0]))
            replaced += t.rowcount
    con.commit()
    con.close()
    print("Replaced " + str(replaced) + " hostnames in " + db)


def main():
    adict = load_replaces()
    if not adict:
        print("empty dictionary of replacements, nothing to do")
        sys.exit(1)
    multiple_replace = MultiReplace(adict)
    if os.path.exists('/var/lib/pakon.db'):
        replace('/var/lib/pakon.db', multiple_replace)
    if os.path.exists('/srv/pakon/pakon-archive.db'):
        replace('/srv/pakon/pakon-archive.db', multiple_replace)


if __name__ == "__main__":
    main()
