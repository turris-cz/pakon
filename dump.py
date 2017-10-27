#!/usr/bin/env python3

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
import glob

con = sqlite3.connect('/var/lib/pakon.db')
c = con.cursor()
c.execute('ATTACH DATABASE "/srv/pakon/pakon-archive.db" AS archive')


if (len(sys.argv)<2):
    print("usage: {} query".format(sys.argv[0]))
    sys.exit(1)

def timezone_offset():
    is_dst = time.daylight and time.localtime().tm_isdst > 0
    utc_offset = - (time.altzone if is_dst else time.timezone)
    return utc_offset

def build_filter(query):
    now = time.time() - timezone_offset()
    if "start" in query:
        time_from = now - int(query["start"])
    else:
        time_from = 0
    if "end" in query:
        time_to = now - int(query["end"])
    else:
        time_to=now
    where_clause="(start BETWEEN ? AND ? OR (start+duration) BETWEEN ? AND ?)"
    where_parameters=[time_from, time_to, time_from, time_to]
    if "mac" in query:
        where_clause+=" AND src_mac LIKE ?"
        where_parameters.append(query["mac"])
    if "hostname" in query:
        where_clause+=" AND app_hostname LIKE ?"
        where_parameters.append(query["hostname"])
    return (time_from, time_to, where_clause, where_parameters)


def load_ignores():
    ignored={}
    try:
        for fn in glob.glob("/usr/share/pakon-light/domains_ignore/*.txt"):
            with open(fn) as f:
                for line in f:
                    ignored[line.strip()]=1
    except IOError:
        print("can't load domains_ignore file")
    return ignored

ignored=load_ignores()

def query(query):
    query = json.loads(query)
    (time_from, time_to, where_clause, where_parameters) = build_filter(query)
    aggregate = query["aggregate"] if "aggregate" in query else False
    filter = query["filter"] if "filter" in query else True
    domains = []
    if aggregate:
        last2 = [0,0]
        result=c.execute("""select start,duration,src_mac,coalesce(app_hostname,dest_ip) as app_hostname,dest_port,app_proto,bytes_send,bytes_received from traffic where flow_id IS NULL AND """+where_clause+"""
        UNION ALL
        select start,duration,src_mac,app_hostname,dest_port,app_proto,bytes_send,bytes_received from archive.traffic where """+where_clause+"""
        ORDER BY app_hostname,start""", where_parameters + where_parameters)
        last = [i for i in c.fetchone()]
        for row in result:
            if filter and row[3] in ignored:
                continue
            row=[i for i in row]
            row[0]+=timezone_offset()
            if not row[3]:
                row[3]=''
            if row[0]<time_from:
                not_contained=time_from-row[0]
                part=1.0*(row[1]-not_contained)/row[1]
                row[1]-=int(not_contained)
                row[6]=int(part*row[6])
                row[7]=int(part*row[7])
            if row[0]+row[1]>time_to:
                not_contained=row[0]+row[1]-time_to
                part=1.0*(row[1]-not_contained)/row[1]
                row[1]-=int(not_contained)
                row[6]=int(part*row[6])
                row[7]=int(part*row[7])
            if last[3]==row[3]:
                if row[0] > last2[1]:
                    last[1]+=int(last2[1]-last2[0])
                    last2=[row[0],row[0]+row[1]]
                else:
                    last2[1]=max(last2[1],row[0]+row[1])
                last[4]=(last[4] if row[4]==last[4] else "")
                last[5]=(last[5] if row[5]==last[5] else "")
                last[6]+=int(row[6])
                last[7]+=int(row[7])
            else:
                domains.append(last)
                last=[i for i in row]
                last2 = [0,0]
        domains.append(last)
        domains = sorted(domains, key=lambda x: x[6]+x[7])
    else:
        result = c.execute("""select start,duration,src_mac,coalesce(app_hostname,dest_ip) as app_hostname,dest_port,app_proto,bytes_send,bytes_received from traffic where flow_id IS NULL AND """+where_clause+"""
        UNION ALL
        select start,duration,src_mac,app_hostname,dest_port,app_proto,bytes_send,bytes_received from archive.traffic where """+where_clause+"""
        ORDER BY app_hostname,start""", where_parameters + where_parameters)
        last = [i for i in c.fetchone()]
        for row in result:
            if filter and row[3] in ignored:
                continue
            row=[i for i in row]
            row[0]+=timezone_offset()
            if not row[3]:
                row[3]=''
            if last[3]==row[3]:
                if row[0] > last[0]+last[1]+3:
                    domains.append(last)
                else:
                    last[1]=max(last[1],int(row[0]-last[0]+row[1]))
                    last[4]=(last[4] if row[4]==last[4] else "")
                    last[5]=(last[5] if row[5]==last[5] else "")
                    last[6]+=row[6]
                    last[7]+=row[7]
                    continue
            else:
                domains.append(last)
            last=[i for i in row]
        domains.append(last)
        domains = sorted(domains, key=lambda x: x[0])
    return json.dumps(domains)

print(query(sys.argv[1]))
