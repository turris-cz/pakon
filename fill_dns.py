#!/usr/bin/env python3

import os
import sys
import time
import datetime
import time
import sqlite3
import signal
import errno
from multiprocessing import Process, Queue

interval = 3600

dns_threads = 8
dns_timeout = 5

def timeout_handler():
    raise Exception("Timeout!")

def reverse_lookup(q_in, q_out):
    signal.signal(signal.SIGALRM, timeout_handler)
    ip = ""
    while ip is not None:
        name = None
        ip = q_in.get()
        if ip is None:
            break
        signal.alarm(dns_timeout)
        try:
            name = socket.gethostbyaddr(ip)[0]
            q_out.put((ip, name))
        except:
            pass
        signal.alarm(0)

con = sqlite3.connect('/var/lib/pakon.db')
c = con.cursor()

def get_name_from_cache(time, client, ip):
    global con
    t = con.cursor()
    t.execute('SELECT name FROM dns WHERE time <= ? AND data = ? AND client = ? ORDER BY time DESC LIMIT 1', (time, ip, client))
    dns_entry = t.fetchone()
    name = None
    while dns_entry:
        name = dns_entry[0]
        print(ip+" -> "+name)
        t.execute('SELECT name FROM dns WHERE time <= ? AND data = ? AND client = ? AND type = "CNAME" ORDER BY time DESC LIMIT 1', (time, name, client))
        dns_entry = t.fetchone()
    return name

now = int(time.mktime(datetime.datetime.utcnow().timetuple()))
start = now-interval*2
print("Solving DNS")
print("Using DNS cache...")
cache = 0
reverse = 0
for row in c.execute('SELECT rowid, start, src_ip, dest_ip FROM traffic WHERE start >= ? AND app_hostname IS NULL', (start,)):
    name = get_name_from_cache(row[1], row[2], row[3])
    if name:
        t = con.cursor()
        t.execute('UPDATE traffic SET app_hostname = ? WHERE rowid = ?', (name, row[0]))
        cache = cache + 1
print(str(cache)+" records filled from DNS cache")
print("Trying reverse lookups...")
con.commit()
q_in = Queue()
q_out = Queue()
for row in c.execute('SELECT DISTINCT(dest_ip) FROM traffic WHERE start > ? AND app_hostname IS NULL', (start, )):
    q_in.put(row[0])
p = []
for i in range(0, dns_threads):
    q_in.put(None)
    tp = Process(target=reverse_lookup, args=(q_in,q_out))
    p.append(tp)
    tp.start()
for tp in p:
    tp.join()
while not q_out.empty():
    res = q_out.get()
    t.execute('UPDATE traffic SET app_hostname = ? WHERE start > ? AND dest_ip = ? AND app_hostname IS NULL', (res[1], start, res[0]))
    reverse = reverse + 1
print(str(reverse)+" records filled from reverse lookups")
con.commit()
c.execute('DELETE FROM dns WHERE time < ?', (start-3600, ))
con.commit()
