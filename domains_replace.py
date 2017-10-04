#!/usr/bin/env python

import os
import sys
import time
import datetime
import time
import sqlite3
import signal
import errno
import re
import json

interval = 3600

class MultiReplace:
    "perform replacements specified by regex and adict all at once"
    " The regex is constructed such that it matches the whole string (.* in the beginnin and end),"
    " the actual key from adict is the first group of match (ignoring possible prefix and suffix)."
    " The whole string is then replaced (the replacement is specified by adict)"
    def __init__(self, adict):
        self.adict = adict
        self.rx = re.compile("^.*("+'|'.join(map(re.escape, adict))+").*$")

    def replace(self, text):
        def one_xlat(match):
            return self.adict[match.group(1)]
        return self.rx.sub(one_xlat, text)




adict={}
try:
    with open('/usr/share/pakon-light/domains_replace.conf') as f:
        for line in f:
	    match = re.match('\s*"([^"]+)"\s*:\s*"([^"]+)"\s*', line)
	    if not match:
	        if re.match('\s*', line): #ignore empty lines
		    continue
	        print("invalid line: "+line)
		continue
	    adict[match.group(1)]=match.group(2)
except IOError:
    print("can't load domains_services file")
    sys.exit(1)

if not adict:
    print("empty dictionary of replacements, nothing to do")
    sys.exit(1)

con = sqlite3.connect('/var/lib/pakon.db')
c = con.cursor()

multiple_replace = MultiReplace(adict)

now = int(time.mktime(datetime.datetime.utcnow().timetuple()))
start = now-interval*2
replaced = 0
for row in c.execute('SELECT DISTINCT(app_hostname) FROM traffic WHERE start >= ? AND app_hostname IS NOT NULL AND flow_id IS NULL', (start,)):
    name = multiple_replace.replace(row[0])
    if name!=row[0]:
        t = con.cursor()
        t.execute("UPDATE traffic SET app_hostname = ? WHERE app_hostname = ? AND flow_id IS NULL", (name, row[0]))
        replaced += t.rowcount
con.commit()
print("Replaced "+str(replaced)+" hostnames")
