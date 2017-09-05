#!/usr/bin/env python

import fileinput
import os, os.path
import string
import socket
import sys
import subprocess
import re
import time
import datetime
import sqlite3
import signal
import errno
from multiprocessing import Process, Queue

dns_timeout = 5
dns_threads = 15
roll = {}
window = {}
top = {}
roll[99] = int(time.time())
roll[99] = roll[99] - 3600
roll[80] = roll[99] - 48 * 3600
window[80] = 600
top[80] = 500
roll[50] = roll[99] - 7 * 24 * 3600
window[50] = 3600
top[50] = 100

delimiter = '__uci__delimiter__'
debug = False
p = []

def timeout_handler():
    raise Exception("Timeout!")

signal.signal(signal.SIGALRM, timeout_handler)

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
            signal.alarm(0)
            q_out.put((ip, name))
        except:
            print("Can't resolve {}".format(ip))
        signal.alarm(0)

# uci get wrapper
def uci_get(opt):
    chld = subprocess.Popen(['/sbin/uci', '-d', delimiter, '-q', 'get', opt],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = chld.communicate()
    out = string.strip(out).encode('ascii','ignore')
    if out.find(delimiter) != -1:
        return out.split(delimiter)
    else:
        return out

con = False

con = sqlite3.connect('/var/lib/suricata-archive.db')

def get_row_data(entry):
    current_entry = []
    for i in range(0,11):
        if i in (2,3,4,5,6,7,8):
            current_entry.append(str(entry[i]))
        else:
            current_entry.append(int(entry[i]))
    return current_entry

def merge_row(current_entry, entry):
    if current_entry[1] < current_entry[0] - (int(entry[0]) - int(entry[1])):
        current_entry[1] = current_entry[0] - (int(entry[0]) - int(entry[1]))
        for i in (3,4,5,6,7,8):
            if(entry[i] != current_entry[i]):
                current_entry[i] = ''
        current_entry[9] = current_entry[9] + entry[9]
        current_entry[10] = current_entry[10] + entry[10]
    return current_entry

def squash(fr, to, window, end, top):
    global con
    mac_cur = con.cursor()
    squashed = 0
    over_the_top = 0
    squashed_checked = 0
    print("Squashing from {} to {} ending {}".format(fr, to, end))
    for mac_row in mac_cur.execute('SELECT distinct(src_mac) FROM traffic WHERE details = ? AND end < ?', (fr, end)):
        print("Squashing entries with mac {}".format(mac_row[0]))
        host_cur = con.cursor()
        for host_row in host_cur.execute('SELECT distinct(app_level_hostname) FROM traffic WHERE details = ? AND end < ? AND src_mac = ?', (fr, end, mac_row[0])):
            tmp = con.cursor()
            current_entry = None
            for entry in tmp.execute('SELECT end, duration, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received '
                                     'FROM traffic WHERE details = ? AND end < ? AND src_mac = ? AND app_level_hostname = ? ORDER BY end DESC', (fr, end, mac_row[0], host_row[0])):
                squashed_checked = squashed_checked + 1
                if current_entry is None:
                    current_entry = get_row_data(entry)
                else:
                    if (current_entry[0] - current_entry[1]) - entry[0] < window:
                        squashed = squashed + 1
                        current_entry = merge_row(current_entry, entry)
                    else:
                        con.cursor().execute('INSERT INTO traffic VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(
                                              current_entry[0], current_entry[1], to, current_entry[2], current_entry[3], current_entry[4], current_entry[5],
                                              current_entry[6], current_entry[7], current_entry[8], current_entry[9], current_entry[10], host_row[0]))
                        current_entry = get_row_data(entry)
            if current_entry is not None:
                tmp.execute('SELECT end, duration, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, rowid '
                            'FROM traffic WHERE details = ? AND end < ? AND src_mac = ? AND app_level_hostname = ? ORDER BY end DESC LIMIT 1', (to, current_entry[0], mac_row[0], host_row[0]))
                entry = tmp.fetchone()
                if entry is not None and (current_entry[0] - current_entry[1]) - entry[0] < window:
                    squashed = squashed + 1
                    current_entry = merge_row(current_entry, entry)
                    tmp.execute('DELETE FROM traffic WHERE rowid = ?', (entry[11]))
                con.cursor().execute('INSERT INTO traffic VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(
                                      current_entry[0], current_entry[1], to, current_entry[2], current_entry[3], current_entry[4], current_entry[5],
                                      current_entry[6], current_entry[7], current_entry[8], current_entry[9], current_entry[10], host_row[0]))
        if(top is not None and top > 0):
            print("Limiting entries for mac {} to top {}".format(mac_row[0], top))
            host_cur.execute('SELECT end, duration, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, rowid FROM traffic '
                             'WHERE details = ? AND src_mac = ? AND app_level_hostname = ""', (to, mac_row[0]))
            row = host_cur.fetchone()
            to_delete = []
            if row is not None:
                current_entry = get_row_data(row)
                to_delete.append((row[11],))
            else:
                current_entry = None
            for row in host_cur.execute('SELECT end, duration, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, rowid FROM traffic '
                                    'WHERE src_mac = ? AND '
                                    'rowid NOT IN (select rowid from traffic order by duration desc limit -1 offset ?) AND '
                                    'rowid NOT IN (select rowid from traffic order by bytes_send desc limit -1 offset ?) AND '
                                    'rowid NOT IN (select rowid from traffic order by bytes_received desc limit -1 offset ?)', (
                                     mac_row[0],top,top,top)):
                to_delete.append((row[11],))
                over_the_top = over_the_top + 1
                if current_entry is not None:
                    current_entry = merge_row(current_entry, row)
                else:
                    current_entry = get_row_data(row)
            if current_entry is not None:
                host_cur.execute('INSERT INTO traffic VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(
                                      current_entry[0], current_entry[1], to, current_entry[2], current_entry[3], current_entry[4], current_entry[5],
                                      current_entry[6], current_entry[7], current_entry[8], current_entry[9], current_entry[10], ""))
                host_cur.executemany('DELETE FROM traffic WHERE rowid = ?', to_delete)
    print("Squashed {} entries (checked {})".format(squashed, squashed_checked))
    print("{} entries over the top".format(over_the_top))
    mac_cur.execute('DELETE FROM traffic WHERE details = ? AND end < ?', (fr, end))
    print("Deleted {} entries".format(mac_cur.rowcount))

# Create database if it was empty
c = con.cursor()
try:
     c.execute('CREATE TABLE traffic '
               '(end integer, duration integer, details integer, '
               'src_mac text, src_ip text, src_port integer, dest_ip text, dest_port integer, '
               'proto text, app_proto text, bytes_send integer, '
               'bytes_received integer, app_level_hostname text)')
except:
     print('Table "traffic" already exists')
try:
    c.execute('CREATE TABLE dns '
              '(time integer, client text, name text, type text, data text)')
except:
     print('Table "dns" already exists')
try:
    c.execute('CREATE INDEX dns_lookup ON dns(client,data,time)')
except:
    print('Index "dns_lookup" already exists')
try:
    c.execute('CREATE INDEX traffic_lookup ON traffic(details, end, src_mac, app_level_hostname)')
except:
    print('Index "traffic_lookup" already exists')

# Main loop

def exit_gracefully(signum, frame):
    global c, con, p
    if not con:
        return
    con.commit()
    if con:
         con.close()
    for tp in p:
        tp.terminate()
        tp.join()
    sys.exit(0)

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)

try:
    c.execute('ATTACH DATABASE "/var/lib/suricata-monitor.db" AS live')
    c.execute('INSERT INTO traffic SELECT end, duration, 99, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, app_level_hostname FROM live.traffic WHERE end < ?', (roll[99],))
    c.execute('INSERT INTO dns SELECT * FROM live.dns')
    con.commit()
    print("Limit set to {}".format(roll[99]))
    # Fill hostnames from DNS entries
    print("Solving DNS")
    updated = 0
    reverse = 0
    for row in c.execute('SELECT rowid,end,duration,src_ip,dest_ip FROM traffic WHERE details = 99 AND app_level_hostname = ""'):
        t = con.cursor()
        start = row[1] - row[2]
        t.execute('SELECT name FROM dns WHERE time < ? AND data = ? AND client = ? ORDER BY time DESC LIMIT 1', (start, row[4], row[3]))
        dns_entry = t.fetchone()
        name = None
        last_name = ""
        while dns_entry is not None and last_name != name:
            last_name = name
            name = dns_entry[0]
            t.execute('SELECT name FROM dns WHERE time < ? AND data = ? AND client = ? AND type = "CNAME" ORDER BY time DESC LIMIT 1', (start, name, row[3]))
            dns_entry = t.fetchone()
        if name is not None:
            t.execute('UPDATE traffic SET app_level_hostname = ? WHERE rowid = ?', (name, row[0]))
            updated = updated + 1
    print("Trying reverse lookups")
    con.commit()
    q_in = Queue(dns_threads)
    q_out = Queue(dns_threads)
    for i in range(0, dns_threads):
        tp = Process(target=reverse_lookup, args=(q_in,q_out))
        p.append(tp)
        tp.start()
    for row in c.execute('SELECT distinct(dest_ip) FROM traffic WHERE details = 99 AND app_level_hostname = ""'):
        if not q_in.full():
            q_in.put(row[0])
        else:
            res = q_out.get()
            t.execute('UPDATE traffic SET app_level_hostname = ? WHERE dest_ip = ? AND app_level_hostname = ""', (res[1], res[0]))
            updated = updated + t.rowcount
            reverse = reverse + 1
    killed_threads = 0
    print("Reverse lookup done, getting last results")
    while not q_out.empty() or not q_in.empty():
        if not q_out.empty():
            res = q_out.get()
            t.execute('UPDATE traffic SET app_level_hostname = ? WHERE dest_ip = ? AND app_level_hostname = ""', (res[1], res[0]))
            updated = updated + t.rowcount
            reverse = reverse + 1
        if not q_in.full() and killed_threads < dns_threads:
            q_in.put(None)
            killed_threads = killed_threads + 1
    print("Killing threads")
    for tp in p:
        tp.join()
    print("Filled {} hostname entries ({} from reverse DNS lookup)".format(updated, reverse))
    con.commit()
    c.execute('DELETE FROM dns WHERE time < ?', (roll[99] - 12 * 3600,))
    con.commit()
    last_details = 99
    print("Squashing")
    for det in window.keys():
        print("Squashing {} till {}".format(det, roll[last_details]))
        squash(last_details, det, window[det], roll[last_details], top[det])
        last_details = det 
        con.commit()

    c.execute('VACUUM')
    con.commit()
#    c.execute('DELETE FROM live.traffic WHERE end < ?)', (roll[99]))
#    c.execute('DELETE FROM live.dns WHERE time < ?)', (roll[99] - 36 * 3600))

except KeyboardInterrupt:
    exit_gracefully()

except IOError as e:
    if e.errno != errno.EINTR:
        raise
