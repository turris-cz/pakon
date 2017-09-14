#!/usr/bin/env python

import os
import sys
import time
import datetime
import sqlite3
import signal
import errno
from multiprocessing import Process, Queue

max_delay = 5
interval = 3600

con = sqlite3.connect('/var/lib/suricata-monitor.db')
c = con.cursor()

def squash(start):
    global con
    c = con.cursor()
    print("Squashing flows...")
    to_be_deleted = []
    for row in c.execute('SELECT (end-duration) AS start, end, duration, connections, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, app_hostname, app_hostname_type, rowid FROM traffic WHERE start > ? ORDER BY start', (start,)):
        if row[15] in to_be_deleted:
            continue
        print("trying:")
        print(row)
        current_start = int(row[0])
        current_end = int(row[1])
        current_connections = int(row[3])
        current_bytes_send = int(row[11])
        current_bytes_received = int(row[12])
        mac = row[4]
        src_port = row[6]
        dest_port = row[8]
        app_hostname_type = row[14]
        count = 0
        tmp = con.cursor()
        for entry in tmp.execute('SELECT (end-duration) AS start, end, duration, connections, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, app_hostname, app_hostname_type, rowid FROM traffic WHERE start >= ? AND src_mac = ? AND src_ip = ? AND dest_ip = ? AND app_proto = ? AND app_hostname = ? AND rowid != ? ORDER BY start', (current_start, mac, row[5], row[7], row[10], row[13], row[15])):
            if int(entry[0]) - max_delay > current_end:
                break
            print("joining with:")
            print(entry)
            current_end = max(current_end, int(entry[1]))
            current_connections += int(entry[3])
            current_bytes_send += int(entry[11])
            current_bytes_received += int(entry[12])
            if src_port!=entry[6]:
                src_port = ''
            if dest_port!=entry[8]:
                dest_port = ''
            if app_hostname_type!=entry[14]:
                app_hostname_type = ''
            count += 1
            to_be_deleted.append(entry[15])
        if count>0:
            tmp.execute('UPDATE traffic SET end = ?, duration = ?, connections = ?, src_port = ?, dest_port = ?, bytes_send = ?, bytes_received = ?, app_hostname_type = ? WHERE rowid = ?', (current_end, (current_end-current_start), current_connections, src_port, dest_port, current_bytes_send, current_bytes_received, app_hostname_type, row[15]))
            con.commit()
    for tbd in to_be_deleted:
        c.execute('DELETE FROM traffic WHERE rowid = ?', (tbd,))
    con.commit()
    return len(to_be_deleted)

now = int(time.mktime(datetime.datetime.utcnow().timetuple()))
start = now-interval*2
c = con.cursor()
c.execute('SELECT COUNT(*) FROM traffic WHERE (end-duration) > ?', (start, ))
count_entry = c.fetchone()
count=count_entry[0]
print("Squashing flows...")
deleted = squash(start)
print("Squashed {} entries (out of {} examined).".format(deleted, count))
c.execute('VACUUM FULL')
con.commit()
