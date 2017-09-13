#!/usr/bin/env python

import os
import sys
import time
import datetime
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
            print(ip+" -> "+name)
            q_out.put((ip, name))
        except:
            print("Can't resolve "+ip)
        signal.alarm(0)

con = sqlite3.connect('/var/lib/suricata-monitor.db')
c = con.cursor()

print("Solving DNS")
print("Using DNS cache...")
cache = 0
reverse = 0
for row in c.execute('SELECT rowid, end, duration, src_ip, dest_ip FROM traffic WHERE app_hostname_type = 0 AND end > duration + ?',(int(time.time())+interval*2, )):
	t = con.cursor()
	start = row[1] - row[2]
	t.execute('SELECT name FROM dns WHERE time <= ? AND data = ? AND client = ? ORDER BY time DESC LIMIT 1', (start, row[4], row[3]))
	dns_entry = t.fetchone()
	name = None
	last_name = ""
	while dns_entry is not None and last_name != name:
		last_name = name
		name = dns_entry[0]
		t.execute('SELECT name FROM dns WHERE time < ? AND data = ? AND client = ? AND type = "CNAME" ORDER BY time DESC LIMIT 1', (start, name, row[3]))
		dns_entry = t.fetchone()
	if name is not None:
		t.execute('UPDATE traffic SET app_hostname = ?, app_hostname_type = 2 WHERE rowid = ?', (name, row[0]))
		cache = cache + 1
print(str(cache)+" records filled from DNS cache")
print("Trying reverse lookups...")
con.commit()
q_in = Queue()
q_out = Queue()
for row in c.execute('SELECT distinct(dest_ip) FROM traffic WHERE app_hostname_type = 0'):
	print(row[0])
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
	t.execute('UPDATE traffic SET app_hostname = ?, app_hostname_type = 3 WHERE dest_ip = ? AND app_hostname = ""', (res[1], res[0]))
	reverse = reverse + 1
print(str(reverse)+" records filled from reverse lookups")
con.commit()
c.execute('DELETE FROM dns WHERE time < ?', (int(time.time())-12*3600, ))
con.commit()
