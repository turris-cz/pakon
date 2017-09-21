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

con = sqlite3.connect('/var/lib/pakon-archive.db')

def get_row_data(entry):
    current_entry = entry
    current_entry[0]=int(current_entry[0])
    current_entry[1]=int(current_entry[1])
    current_entry[2]=int(current_entry[2])
    current_entry[10]=int(current_entry[10])
    current_entry[11]=int(current_entry[11])
    return current_entry

def merge_row(current_entry, entry):
    #array: end, duration, connections, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, app_hostname
    if current_entry[1] < current_entry[0] - (int(entry[0]) - int(entry[1])):
        current_entry[1] = current_entry[0] - (int(entry[0]) - int(entry[1]))
        current_entry[2] = current_entry[2] + entry[2]
        for i in (4,5,6,7,8,9):
            if(entry[i] != current_entry[i]):
                current_entry[i] = ''
        current_entry[10] = current_entry[10] + entry[10]
        current_entry[11] = current_entry[11] + entry[11]
    return current_entry

def squash(from_details, to_details, start, window):
    global con
    c = con.cursor()
    print("Squashing flows - from detail_level {} to detail_level {}".format(from_details, to_details))
    to_be_deleted = []
    for row in c.execute('SELECT rowid, start, (start+duration) AS end, duration, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, app_hostname FROM traffic WHERE details = ? AND start < ? ORDER BY start', (from_details, start,)):
        if row[0] in to_be_deleted:
            continue
        #print("trying:")
        #print(row)
        current_start = float(row[1])
        current_end = float(row[2])
        current_bytes_send = int(row[11])
        current_bytes_received = int(row[12])
        mac = row[4]
        src_ip = row[5]
        src_port = row[6]
        dest_ip = row[7]
        dest_port = row[8]
        count = 0
        tmp = con.cursor()
        for entry in tmp.execute('SELECT rowid, start, (start+duration) AS end, duration, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, app_hostname FROM traffic WHERE details = ? AND start > ? AND start <= ? AND src_mac = ? AND app_hostname = ? ORDER BY start', (from_details, current_start, current_start+window, mac, row[13])):
            #print("joining with:")
            #print(entry)
            current_end = max(current_end, float(entry[2]))
            current_bytes_send += int(entry[11])
            current_bytes_received += int(entry[12])
            if src_ip!=entry[5]:
                src_ip = ''
            if src_port!=entry[6]:
                src_port = ''
            if dest_ip!=entry[7]:
                dest_ip = ''
            if dest_port!=entry[8]:
                dest_port = ''
            count += 1
            to_be_deleted.append(entry[0])
        tmp.execute('UPDATE traffic SET details = ?, duration = ?, src_ip = ?, src_port = ?, dest_ip = ?, dest_port = ?, bytes_send = ?, bytes_received = ? WHERE rowid = ?', (to_details, int(current_end-current_start), src_ip, src_port, dest_ip, dest_port, current_bytes_send, current_bytes_received, row[0]))
    for tbd in to_be_deleted:
        c.execute('DELETE FROM traffic WHERE rowid = ?', (tbd,))
    con.commit()
    return len(to_be_deleted)



#def squash(from_details, to_details, window, start, top):
    #global con
    #mac_cur = con.cursor()
    #squashed = 0
    #over_the_top = 0
    #squashed_checked = 0
    #print("Squashing from {} to {} - starting from {}".format(from_details, to_details, start))
    #for mac_row in mac_cur.execute('SELECT distinct(src_mac) FROM traffic WHERE details = ? AND start < ?', (from_details, start)):
        #print("Squashing entries with mac {}".format(mac_row[0]))
        #host_cur = con.cursor()
        #for host_row in host_cur.execute('SELECT distinct(app_level_hostname) FROM traffic WHERE details = ? AND start < ? AND src_mac = ?', (from_details, start, mac_row[0])):
            #tmp = con.cursor()
            #current_entry = None
            #for entry in tmp.execute('SELECT (start+duration) AS end, duration, connections, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, app_hostname '
                                     #'FROM traffic WHERE details = ? AND end < ? AND src_mac = ? AND app_level_hostname = ? ORDER BY end DESC', (from_details, end, mac_row[0], host_row[0])):
                #squashed_checked = squashed_checked + 1
                #if current_entry is None:
                    #current_entry = get_row_data(entry)
                #else:
                    #if (current_entry[0] - current_entry[1]) - entry[0] < window:
                        #squashed = squashed + 1
                        #current_entry = merge_row(current_entry, entry)
                    #else:
                        #con.cursor().execute('INSERT INTO traffic VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(
                                              #current_entry[0], current_entry[1], to_details, current_entry[2], current_entry[3], current_entry[4], current_entry[5],
                                              #current_entry[6], current_entry[7], current_entry[8], current_entry[9], current_entry[10], host_row[0]))
                        #current_entry = get_row_data(entry)
            #if current_entry is not None:
                #tmp.execute('SELECT end, duration, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, rowid '
                            #'FROM traffic WHERE details = ? AND end < ? AND src_mac = ? AND app_level_hostname = ? ORDER BY end DESC LIMIT 1', (to_details, current_entry[0], mac_row[0], host_row[0]))
                #entry = tmp.fetchone()
                #if entry is not None and (current_entry[0] - current_entry[1]) - entry[0] < window:
                    #squashed = squashed + 1
                    #current_entry = merge_row(current_entry, entry)
                    #tmp.execute('DELETE FROM traffic WHERE rowid = ?', (entry[11]))
                #con.cursor().execute('INSERT INTO traffic VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(
                                      #current_entry[0], current_entry[1], to_details, current_entry[2], current_entry[3], current_entry[4], current_entry[5],
                                      #current_entry[6], current_entry[7], current_entry[8], current_entry[9], current_entry[10], host_row[0]))
        #if(top is not None and top > 0):
            #print("Limiting entries for mac {} to_details top {}".format(mac_row[0], top))
            #host_cur.execute('SELECT end, duration, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, rowid FROM traffic '
                             #'WHERE details = ? AND src_mac = ? AND app_level_hostname = ""', (to_details, mac_row[0]))
            #row = host_cur.fetchone()
            #to_details_delete = []
            #if row is not None:
                #current_entry = get_row_data(row)
                #to_details_delete.append((row[11],))
            #else:
                #current_entry = None
            #for row in host_cur.execute('SELECT end, duration, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, rowid FROM traffic '
                                    #'WHERE src_mac = ? AND '
                                    #'rowid NOT IN (select rowid from traffic order by duration desc limit -1 offset ?) AND '
                                    #'rowid NOT IN (select rowid from traffic order by bytes_send desc limit -1 offset ?) AND '
                                    #'rowid NOT IN (select rowid from traffic order by bytes_received desc limit -1 offset ?)', (
                                     #mac_row[0],top,top,top)):
                #to_details_delete.append((row[11],))
                #over_the_top = over_the_top + 1
                #if current_entry is not None:
                    #current_entry = merge_row(current_entry, row)
                #else:
                    #current_entry = get_row_data(row)
            #if current_entry is not None:
                #host_cur.execute('INSERT INTO traffic VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(
                                      #current_entry[0], current_entry[1], to_details, current_entry[2], current_entry[3], current_entry[4], current_entry[5],
                                      #current_entry[6], current_entry[7], current_entry[8], current_entry[9], current_entry[10], ""))
                #host_cur.executemany('DELETE FROM traffic WHERE rowid = ?', to_details_delete)
    #print("Squashed {} entries (checked {})".format(squashed, squashed_checked))
    #print("{} entries over the top".format(over_the_top))
    #mac_cur.execute('DELETE FROM traffic WHERE details = ? AND end < ?', (from_details, end))
    #print("Deleted {} entries".format(mac_cur.rowcount))

# Create database if it was empty
c = con.cursor()
try:
    c.execute('CREATE TABLE traffic '
                '(start real, duration integer, details integer,'
                'src_mac text, src_ip text, src_port integer, dest_ip text, dest_port integer, '
                'proto text, app_proto text, bytes_send integer, '
                'bytes_received integer, app_hostname text)')
except:
     print('Table "traffic" already exists')
try:
    c.execute('CREATE INDEX traffic_lookup ON traffic(details, start, src_mac)')
except:
    print('Index "traffic_lookup" already exists')

# Main loop

def exit_gracefully(signum, frame):
    global c, con, p
    if not con:
        return
    con.commit()
    con.close()
    sys.exit(0)

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)

interval = 3600*3
now = int(time.mktime(datetime.datetime.utcnow().timetuple()))
start = now-interval

try:
    c.execute('ATTACH DATABASE "/var/lib/pakon.db" AS live')
    c.execute('INSERT INTO traffic SELECT start, duration, 99, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, app_hostname FROM live.traffic WHERE start < ? AND flow_id IS NULL', (start,))
    print("moved {} to archive".format(c.rowcount))
    #c.execute('DELETE FROM live.traffic WHERE start < ? AND flow_id IS NULL', (start,))
    con.commit()
    print("squashed from 99 to 80 - deleted {}".format(squash(99,80,now-3600*3,60)))
    con.commit()
    print("squashed from 80 to 70 - deleted {}".format(squash(80,70,now-3600*6,300)))
    con.commit()
    #squash(80,70,now-3600*6,300)
    #print("Limit set to {}".format(roll[99]))
    #last_details = 99
    #print("Squashing")
    #for det in window.keys():
        #print("Squashing {} till {}".format(det, roll[last_details]))
        #squash(last_details, det, window[det], roll[last_details], top[det])
        #last_details = det 
        #con.commit()

    #c.execute('VACUUM')
    #con.commit()
#    c.execute('DELETE FROM live.dns WHERE time < ?)', (roll[99] - 36 * 3600))

except KeyboardInterrupt:
    exit_gracefully()

except IOError as e:
    if e.errno != errno.EINTR:
        raise
