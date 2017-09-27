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

def multiple_replace(text):
    def one_xlat(match):
        return multiple_replace.adict[match.group(1)]
    return multiple_replace.rx.sub(one_xlat, text)


con = sqlite3.connect('/var/lib/pakon.db')
c = con.cursor()


adict={}
try:
    data_file = open('/usr/share/pakon-light/domains_replace.json')
    adict = json.load(data_file)
except IOError:
    print("can't load domains_services file")
    sys.exit(1)

multiple_replace.adict = adict
multiple_replace.rx = re.compile("^.*("+'|'.join(map(re.escape, adict))+").*$")

now = int(time.mktime(datetime.datetime.utcnow().timetuple()))
start = now-interval*2
replaced = 0
for row in c.execute('SELECT DISTINCT(app_hostname) FROM traffic WHERE start >= ? AND app_hostname IS NOT NULL AND flow_id IS NULL', (start,)):
    name = multiple_replace(row[0])
    if name!=row[0]:
        t = con.cursor()
        t.execute("UPDATE traffic SET app_hostname = ? WHERE app_hostname = ? AND flow_id IS NULL", (name, row[0]))
        replaced += t.rowcount
con.commit()
print("Replaced "+str(replaced)+" hostnames")
