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

con = sqlite3.connect('/var/lib/pakon.db')
c = con.cursor()
try:
    c.execute('ATTACH DATABASE "/srv/pakon/pakon-archive.db" AS archive')
except:
    print("can't attach archive")


if (len(sys.argv)<5):
    print("usage: {} mac time_from time_to sort_key".format(sys.argv[0]))
    print(" time_from, time_to are relative to current time, eg. 86400 means one day ago")
    print(" sort_key can be: duration, bytes_both, bytes_send, bytes_received")
    print(" known MAC addresses are:")
    for row in c.execute("select src_mac,COUNT(*) from traffic where flow_id IS NULL AND src_mac NOT LIKE '' GROUP BY src_mac"):
        print("  "+row[0]+" - "+str(row[1])+" flows total")
    sys.exit(1)
else:
    now = time.time() - 2*3600
    domains = []
    time_from = now - int(sys.argv[2])
    time_to = now - int(sys.argv[3])
    last = [0,0,'',0,0]
    last2 = [0,0]
    for row in c.execute("""select start,duration,app_hostname,bytes_send,bytes_received from traffic where flow_id IS NULL AND src_mac LIKE ? AND (start BETWEEN ? AND ? OR (start+duration) BETWEEN ? AND ?)
    UNION ALL
    select start,duration,app_hostname,bytes_send,bytes_received from archive.traffic where src_mac LIKE ? AND (start BETWEEN ? AND ? OR (start+duration) BETWEEN ? AND ?)
    ORDER BY app_hostname,start""", (sys.argv[1],time_from,time_to,time_from,time_to,sys.argv[1],time_from,time_to,time_from,time_to)):
        row=[i for i in row]
	if not row[2]:
	    row[2]=u''
        if row[0]<time_from:
	    not_contained=time_from-row[0]
	    part=1.0*(row[1]-not_contained)/row[1]
	    row[1]-=int(not_contained)
	    row[3]=int(part*row[3])
	    row[4]=int(part*row[4])
        if row[0]+row[1]>time_to:
	    not_contained=row[0]+row[1]-time_to
	    part=1.0*(row[1]-not_contained)/row[1]
	    row[1]-=int(not_contained)
	    row[3]=int(part*row[3])
	    row[4]=int(part*row[4])
        if last[2]==row[2]:
	    if row[0] > last2[1]:
	        last[1]+=int(last2[1]-last2[0])
                last2=[row[0],row[0]+row[1]]
	    else:
		last2[1]=max(last2[1],row[0]+row[1])
            last[3]+=int(row[3])
	    last[4]+=int(row[4])
	else:
	    domains.append(last[1:])
	    last=[i for i in row]
            last2 = [0,0]
    domains.append(last[1:])
    if sys.argv[4] == "duration":
        domains = sorted(domains, key=lambda x: x[0])
    elif sys.argv[4] == "bytes_both":
        domains = sorted(domains, key=lambda x: x[2]+x[3])
    elif sys.argv[4] == "bytes_send":
        domains = sorted(domains, key=lambda x: x[2])
    elif sys.argv[4] == "bytes_received":
        domains = sorted(domains, key=lambda x: x[3])
    else:
        print("unknown sorting key: "+sys.argv[4])
	sys.exit(1)
    for d in domains:
        print(d)
