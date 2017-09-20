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

interval = 3600

def multiple_replace(text):
    def one_xlat(match):
        return multiple_replace.adict[match.group(1)]
    return multiple_replace.rx.sub(one_xlat, text)


con = sqlite3.connect('/var/lib/pakon.db')
c = con.cursor()


# list from ndpi - https://github.com/ntop/nDPI/blob/dev/src/lib/ndpi_content_match.c.inc#L8025
# TODO: move this to separate config-like file
adict = {
"facebook.com": "facebook.com",
"fbstatic-a.akamaihd.net": "facebook.com",
".fbcdn.net": "facebook.com",
"fbcdn-": "facebook.com",
".facebook.net": "facebook.com",

"youtube.": "youtube.com",
"youtu.be.": "youtube.com",
"yt3.ggpht.com": "youtube.com",
".googlevideo.com": "youtube.com",
".ytimg.com": "youtube.com",
"youtube-nocookie.": "youtube.com",
"ggpht.com": "youtube.com",
"googleusercontent.com": "youtube.com"
}

multiple_replace.adict = adict
multiple_replace.rx = re.compile("^.*("+'|'.join(map(re.escape, adict))+").*$")

now = int(time.mktime(datetime.datetime.utcnow().timetuple()))
start = now-interval*2
replaced = 0
for row in c.execute('SELECT DISTINCT(app_hostname) FROM traffic WHERE start >= ? AND app_hostname IS NOT NULL', (start,)):
    name = multiple_replace(row[0])
    if name!=row[0]:
        t = con.cursor()
        t.execute("UPDATE traffic SET app_hostname = ? WHERE app_hostname = ?", (name, row[0]))
        replaced += t.rowcount
con.commit()
print("Replaced "+str(replaced)+" hostnames")
