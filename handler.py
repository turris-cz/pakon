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
import subprocess
import socketserver

#TODO: replace with uci bindings - once available
def uci_get(opt):
    delimiter = '__uci__delimiter__'
    chld = subprocess.Popen(['/sbin/uci', '-d', delimiter, '-q', 'get', opt],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = chld.communicate()
    out = out.strip().decode('ascii','ignore')
    if out.find(delimiter) != -1:
        return out.split(delimiter)
    else:
        return out

def build_filter(query):
    now = time.time()
    if "start" in query:
        time_from = int(query["start"])
    else:
        time_from = 0
    if "end" in query:
        time_to = int(query["end"])
    else:
        time_to=now
    where_clause="(start BETWEEN ? AND ? OR (start+duration) BETWEEN ? AND ?)"
    where_parameters=[time_from, time_to, time_from, time_to]
    if "mac" in query:
        fill=['?' for m in query["mac"]]
        where_clause+=" AND src_mac IN ("+",".join(fill)+")"
        where_parameters+=query["mac"]
    if "hostname" in query:
        fill=['?' for m in query["hostname"]]
        where_clause+=" AND app_hostname IN ("+",".join(fill)+")"
        where_parameters+=query["hostname"]
    return (time_from, time_to, where_clause, where_parameters)


def load_ignores():
    ignored={}
    try:
        for fn in glob.glob("/usr/share/pakon-light/domains_ignore/*.txt"):
            with open(fn) as f:
                for line in f:
                    if not line or line[0]=='#':
                        continue
                    ignored[line.strip()]=1
    except IOError:
        print("can't load domains_ignore file")
    return ignored

ignored=load_ignores()

def is_ignored(hostname):
    if not hostname:
        return False
    if hostname in ignored:
        return True
    parts=hostname.split('.')
    while parts:
        if ".".join(parts) in ignored:
            return True
        parts=parts[1:]
    return False

def query(query):
    archive_path = uci_get('pakon.common.archive_path') or '/srv/pakon/pakon-archive.db'
    con = sqlite3.connect('/var/lib/pakon.db')
    c = con.cursor()
    c.execute('ATTACH DATABASE ? AS archive', (archive_path,))
    try:
        query = json.loads(query)
    except ValueError:
        con.close()
        return '[]'
    (time_from, time_to, where_clause, where_parameters) = build_filter(query)
    aggregate = query["aggregate"] if "aggregate" in query else False
    filter = query["filter"] if "filter" in query else True
    domains = []
    if aggregate:
        last2 = [0,0]
        result=c.execute("""select start,duration,src_mac,coalesce(app_hostname,dest_ip) as app_hostname,(dest_port || '/' || lower(proto)) as dest_port,app_proto,bytes_send,bytes_received from traffic where flow_id IS NULL AND """+where_clause+"""
        UNION ALL
        select start,duration,src_mac,coalesce(app_hostname,dest_ip) as app_hostname,(dest_port || '/' || lower(proto)) as dest_port,app_proto,bytes_send,bytes_received from archive.traffic where """+where_clause+"""
        ORDER BY src_mac,app_hostname,dest_port,start""", where_parameters + where_parameters)
        last=c.fetchone()
        if last:
            last = [i for i in last]
        for row in result:
            row=[i for i in row]
            if filter and is_ignored(row[3]):
                continue
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
            if last[2]==row[2] and last[3]==row[3] and last[4]==row[4]:
                if row[0] > last2[1]:
                    last[1]+=int(last2[1]-last2[0])
                    last2=[row[0],row[0]+row[1]]
                else:
                    last2[1]=max(last2[1],row[0]+row[1])
                last[5]=(row[5] if row[5]==last[5] or last[5]=='?' else "?")
                last[6]+=int(row[6])
                last[7]+=int(row[7])
            else:
                if last[6]+last[7]>0:
                    domains.append(last)
                last=row
                last2 = [0,0]
        if last and last[6]+last[7]>0:
            domains.append(last)
        domains = sorted(domains, key=lambda x: x[6]+x[7])
    else:
        result = c.execute("""select start,duration,src_mac,coalesce(app_hostname,dest_ip) as app_hostname,(dest_port || '/' || lower(proto)) as dest_port,app_proto,bytes_send,bytes_received from traffic where flow_id IS NULL AND """+where_clause+"""
        UNION ALL
        select start,duration,src_mac,coalesce(app_hostname,dest_ip) as app_hostname,(dest_port || '/' || lower(proto)) as dest_port,app_proto,bytes_send,bytes_received from archive.traffic where """+where_clause+"""
        ORDER BY app_hostname,app_proto,start""", where_parameters + where_parameters)
        last=c.fetchone()
        if last:
            last = [i for i in last]
        for row in result:
            if not row[3]:
                continue
            if filter and is_ignored(row[3]):
                continue
            row=[i for i in row]
            if not row[3]:
                row[3]=''
            if last[3]==row[3] and last[4]==row[4]:
                if row[0] > last[0]+last[1]+1:
                    domains.append(last)
                else:
                    last[1]=max(last[1],int(row[0]-last[0]+row[1]))
                    last[5]=(row[5] if row[5]==last[5] or last[5]=='?' else "?")
                    last[6]+=row[6]
                    last[7]+=row[7]
                    continue
            else:
                domains.append(last)
            last=[i for i in row]
        if last:
            domains.append(last)
        domains = sorted(domains, key=lambda x: x[0])
    proto_ports = {'22/tcp': 'ssh', '80/tcp': 'http', '443/tcp': 'https', '53/tcp': 'dns', '53/udp': 'dns', '143/tcp': 'imap', '993/tcp': 'imaps', '587/tcp': 'smtp', '995/tcp': 'pop3s', '25/tcp': 'smtp', '465/tcp': 'smtps', '110/tcp': 'pop3'}
    #This is ugly hack for missing velues (due to aggregation). This should disappear in the future.
    proto_ports['/tcp']=''
    proto_ports['/udp']=''
    for d in domains:
        d[0]=datetime.datetime.fromtimestamp(d[0]).strftime('%Y-%m-%d %H:%M:%S')
        if d[4] in proto_ports:
            d[4]=proto_ports[d[4]]
    con.close()
    return json.dumps(domains)


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        with self.request.makefile() as f:
            data = f.readline().strip()
        self.request.sendall((query(data)+"\n").encode())

def main():
    try:
        os.unlink("/var/run/pakon-query.sock")
    except OSError:
        pass
    server = socketserver.UnixStreamServer("/var/run/pakon-query.sock", ThreadedTCPRequestHandler)
    server.serve_forever()
    server.shutdown()
    server.server_close()

if __name__ == "__main__":
    main()
