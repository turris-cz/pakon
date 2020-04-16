#!/usr/bin/env python3

import os
import sys
import sqlite3
import re
import glob

#TODO: remove duplicate code (shared with monitor.py). Maybe create a package?
class MultiReplace:
    "perform replacements specified by regex and adict all at once"
    " The regex is constructed such that it matches the whole string (.* in the beginnin and end),"
    " the actual key from adict is the first group of match (ignoring possible prefix and suffix)."
    " The whole string is then replaced (the replacement is specified by adict)"
    def __init__(self, adict):
        self.setup(adict)

    def setup(self, adict):
        self.adict = adict
        self.rx = re.compile("^.*("+'|'.join(map(re.escape, adict))+").*$")

    def replace(self, text):
        def one_xlat(match):
            return self.adict[match.group(1)]
        return self.rx.sub(one_xlat, text)

def load_replaces():
    adict={}
    try:
        for fn in glob.glob("/usr/share/pakon-light/domains_replace/*.conf"):
            with open(fn) as f:
                for line in f:
                    line=line.strip()
                    if not line:
                        continue
                    match = re.match('"([^"]+)"\s*:\s*"([^"]+)"', line)
                    if not match:
                        print("invalid line: "+line)
                        continue
                    adict[match.group(1)]=match.group(2)
    except IOError:
        print("can't load domains_services file")
    return adict

def replace(db, multiple_replace):
    con = sqlite3.connect(db)
    c = con.cursor()
    replaced = 0
    for row in c.execute('SELECT DISTINCT(app_hostname) FROM traffic WHERE app_hostname IS NOT NULL'):
        name = multiple_replace.replace(row[0])
        if name!=row[0]:
            t = con.cursor()
            t.execute("UPDATE traffic SET app_hostname = ? WHERE app_hostname = ?", (name, row[0]))
            replaced += t.rowcount
    con.commit()
    con.close()
    print("Replaced "+str(replaced)+" hostnames in "+db)

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
