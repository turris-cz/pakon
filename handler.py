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
from euci import EUci, UciExceptionNotFound


proto_ports = {'22/tcp': 'ssh', '80/tcp': 'http', '443/tcp': 'https', '53/tcp': 'dns', '53/udp': 'dns', '143/tcp': 'imap', '993/tcp': 'imaps', '587/tcp': 'smtp', '995/tcp': 'pop3s', '25/tcp': 'smtp', '465/tcp': 'smtps', '110/tcp': 'pop3'}

def load_names():
    mac2name = {}
    i = 0
    try:
        with EUci() as uci:
            while True:
                name = uci.get("dhcp.@host[{}].name".format(i))
                mac = uci.get("dhcp.@host[{}].mac".format(i)).lower()
                mac2name[mac] = name
                i += 1
    except UciExceptionNotFound:
        pass

    return mac2name


def build_filter(query, name2mac):
    now = time.time()
    if "start" in query:
        time_from = int(query["start"])
    else:
        time_from = 0
    if "end" in query:
        time_to = int(query["end"])
    else:
        time_to = int(now)
    where_clause="start BETWEEN ? AND ?"
    where_parameters=[time_from, time_to]
    if "mac" in query:
        for i in range(len(query["mac"])):
            if query["mac"][i] in name2mac:
                query["mac"][i]=name2mac[query["mac"][i]]
            query["mac"][i]=query["mac"][i].lower()
        fill=['?' for m in query["mac"]]
        where_clause+=" AND src_mac IN ("+",".join(fill)+")"
        where_parameters+=query["mac"]
    if "hostname" in query:
        fill=['?' for m in query["hostname"]]
        where_clause+=" AND hostname IN ("+",".join(fill)+")"
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


def get_data_from_live(con, where_clause, where_parameters, filter):
    # get data from live database
    # Basically, perform archivation of live flows - convert to non-overlapping
    # intervals. Just return it, don't write anything to permanent storage.
    c = con.cursor()
    flows = []
    for row_mac in c.execute("SELECT DISTINCT src_mac FROM traffic WHERE flow_id IS NULL AND " + where_clause, where_parameters):
        src_mac = row_mac['src_mac']
        c2 = con.cursor()
        for row_hostname in c2.execute("SELECT DISTINCT COALESCE(app_hostname,dest_ip) AS hostname FROM traffic WHERE src_mac = ? AND flow_id IS NULL AND " + where_clause, [src_mac,] + where_parameters):
            hostname = row_hostname['hostname']
            if filter and is_ignored(hostname):
                continue
            flows += squash_live_for_mac_and_hostname(con, src_mac, hostname, where_clause, where_parameters)
    return flows


def squash_live_for_mac_and_hostname(con, src_mac, hostname, where_clause, where_parameters):
    def add_flow(flow):
        flows.append([flow['start'], int(flow['duration']), flow['src_mac'], flow['hostname'], flow['dest_port'], flow['app_proto'], flow['bytes_send'], flow['bytes_received']])
    def merge_flows(flow1, flow2):
        if flow2['end'] > flow1['end']:
            flow1['end'] = flow2['end']
            flow1['duration'] = int(flow1['end'] - flow1['start'])
        flow1['bytes_send'] += flow2['bytes_send']
        flow1['bytes_received'] += flow2['bytes_received']
        if flow1['app_proto'] != flow2['app_proto']:
            flow1['app_proto'] = ''
    c = con.cursor()
    flows = []
    current_flow = None
    for row in c.execute("SELECT start, duration, (start+duration) AS end, src_mac, COALESCE(app_hostname,dest_ip) AS hostname, (dest_port || '/' || lower(proto)) AS dest_port, app_proto, bytes_send, bytes_received FROM traffic WHERE src_mac = ? AND COALESCE(app_hostname,dest_ip) = ? AND flow_id IS NULL AND " + where_clause + " ORDER BY start", [src_mac, hostname] + where_parameters):
        row = dict(row)
        row['start'] = float(row['start'])
        row['end'] = float(row['end'])
        row['duration'] = int(row['duration'])
        row['bytes_send'] = int(row['bytes_send'])
        row['bytes_received'] = int(row['bytes_received'])
        if not current_flow:
            current_flow = row
        elif current_flow['end'] + 1 > row['start']:
            merge_flows(current_flow, row)
        else:
            add_flow(current_flow)
            current_flow = row
    if current_flow:
        add_flow(current_flow)
    return flows


def get_data_from_archive(con, where_clause, where_parameters, filter):
    # get data from archive database - just sorted by time, nothing more special
    def add_flow(flow):
        flows.append([flow['start'], int(flow['duration']), flow['src_mac'], flow['hostname'], flow['dest_port'], flow['app_proto'], flow['bytes_send'], flow['bytes_received']])
    flows = []
    c = con.cursor()
    for row in c.execute("SELECT start, duration, src_mac, COALESCE(app_hostname, dest_ip) AS hostname, (dest_port || '/' || lower(proto)) AS dest_port, app_proto, bytes_send, bytes_received FROM archive.traffic WHERE " + where_clause, where_parameters):
        if filter and is_ignored(row['hostname']):
            continue
        row = dict(row)
        row['start'] = float(row['start'])
        row['duration'] = int(row['duration'])
        row['bytes_send'] = int(row['bytes_send'])
        row['bytes_received'] = int(row['bytes_received'])
        add_flow(row)
    return flows


def get_aggregate_data_from_archive(con, where_clause, where_parameters, filter):
    # get data from archive database
    # The trick here: flows for any specific triple (src_mac, hostname, dest_port)
    # are non-overlapping. This means we can just sum durations, without taking any
    # special care for overlaps. Thus we can do the agregation with one SQL query.
    def add_flow(flow):
        flows.append([flow['start'], int(flow['duration']), flow['src_mac'], flow['hostname'], flow['dest_port'], flow['app_proto'], flow['bytes_send'], flow['bytes_received']])
    flows = []
    c = con.cursor()
    for row in c.execute("SELECT start, SUM(duration) AS duration, src_mac, COALESCE(app_hostname, dest_ip) AS hostname, (dest_port || '/' || lower(proto)) AS dest_port, app_proto, SUM(bytes_send) AS bytes_send, SUM(bytes_received) AS bytes_received FROM archive.traffic WHERE " + where_clause + " GROUP BY src_mac, hostname, dest_port", where_parameters):
        if filter and is_ignored(row['hostname']):
            continue
        row = dict(row)
        row['start'] = float(row['start'])
        row['duration'] = int(row['duration'])
        row['bytes_send'] = int(row['bytes_send'])
        row['bytes_received'] = int(row['bytes_received'])
        add_flow(row)
    return flows


def aggregate_flows(flows):
    # take all flows and aggregate them
    # return flows where each tuple (src_mac, hostname, dest_port) appears only once
    # solution is based on the fact that flows don't overlap, so we can sum all values
    flows.sort(key=lambda x: (x[3], x[4], x[5]))
    flows_agg = []
    current_flow = flows[0]
    for i in range(1, len(flows)):
        if current_flow[3] == flows[i][3] and current_flow[4] == flows[i][4] and current_flow[5] == flows[i][5]:
            current_flow[1] += flows[i][1]
            current_flow[6] += flows[i][6]
            current_flow[7] += flows[i][7]
        else:
            flows_agg.append(current_flow)
            current_flow = flows[i]
    flows_agg.append(current_flow)
    return flows_agg


def query(query):
    mac2name = load_names()

    with EUci() as uci:
        archive_path = uci.get(
            'pakon', 'archive', 'path',
            dtype='str',
            default='/srv/pakon/pakon-archive.db'
        )

    con = sqlite3.connect('/var/lib/pakon.db')
    con.row_factory = sqlite3.Row
    con.execute('ATTACH DATABASE ? AS archive', (archive_path,))
    try:
        query = json.loads(query)
    except ValueError:
        con.close()
        return '[]'
    (time_from, time_to, where_clause, where_parameters) = build_filter(query, {v:k for k,v in mac2name.items()})
    aggregate = query["aggregate"] if "aggregate" in query else False
    filter = query["filter"] if "filter" in query else True
    if aggregate:
        flows = get_aggregate_data_from_archive(con, where_clause, where_parameters, filter)
        flows += get_data_from_archive(con, where_clause, where_parameters, filter)
        if flows:
            flows = aggregate_flows(flows)
            flows.sort(key=lambda x: x[6] + x[7])
    else:
        # sorted by time - archive data is always older than data from live database
        flows = get_data_from_archive(con, where_clause, where_parameters, filter)
        # just need to sort live data
        flows += sorted(get_data_from_live(con, where_clause, where_parameters, filter), key=lambda x: x[0])
    for flow in flows:
        flow[0]=datetime.datetime.fromtimestamp(flow[0]).strftime('%Y-%m-%d %H:%M:%S')
        if flow[2] in mac2name:
            flow[2]=mac2name[flow[2]]
        if flow[4] in proto_ports:
            flow[4]=proto_ports[flow[4]]
    con.close()
    if aggregate:
        return json.dumps(flows[1:])
    else:
        return json.dumps(flows)


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
