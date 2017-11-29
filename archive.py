#!/usr/bin/env python3

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
import logging

__ARCHIVE_DB_PATH__ = "/srv/pakon/pakon-archive.db"

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
#logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

delimiter = '__uci__delimiter__'

def uci_get(opt):
    chld = subprocess.Popen(['/sbin/uci', '-d', delimiter, '-q', 'get', opt],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = chld.communicate()
    out = string.strip(out).encode('ascii','ignore')
    if out.find(delimiter) != -1:
        return out.split(delimiter)
    else:
        return out

if not os.path.isfile(__ARCHIVE_DB_PATH__):
	subprocess.call(['/usr/bin/python3', '/usr/libexec/pakon-light/create_db.py'])
con = sqlite3.connect(__ARCHIVE_DB_PATH__)
con.row_factory = sqlite3.Row

def squash(from_details, to_details, start, window):
    global con
    c = con.cursor()
    logging.debug("Squashing flows - from detail_level {} to detail_level {}".format(from_details, to_details))
    to_be_deleted = []
    for row in c.execute('SELECT rowid, start, (start+duration) AS end, duration, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, app_hostname FROM traffic WHERE details = ? AND start < ? ORDER BY start', (from_details, start,)):
        if row['rowid'] in to_be_deleted:
            continue
        logging.debug("trying:")
        logging.debug(tuple(row))
        current_start = float(row['start'])
        current_end = float(row['end'])
        current_bytes_send = int(row['bytes_send'])
        current_bytes_received = int(row['bytes_received'])
        src_ip = row['src_ip']
        src_port = row['src_port']
        dest_ip = row['dest_ip']
        app_proto = row['app_proto']
        app_hostname = row['app_hostname']
        tmp = con.cursor()
        first = True
        for entry in tmp.execute('SELECT rowid, start, (start+duration) AS end, duration, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, app_hostname FROM traffic WHERE details = ? AND start > ? AND start <= ? AND src_mac = ? AND dest_port = ? AND proto = ? ORDER BY start', (from_details, current_start, current_start+window, row['src_mac'], row['dest_port'], row['proto'])):
            #hostname comparison done here (not in SQL query) because of None values
            #we want to merge records with unknown hostname together (in python None==None)
            if entry['app_hostname']!=row['app_hostname']:
                continue
            logging.debug("joining with:")
            logging.debug(tuple(entry))
            current_end = max(current_end, float(entry['end']))
            current_bytes_send += int(entry['bytes_send'])
            current_bytes_received += int(entry['bytes_received'])
            if src_ip != entry['src_ip']:
                src_ip = ''
            if src_port != entry['src_port']:
                src_port = ''
            if dest_ip != entry['dest_ip']:
                dest_ip = ''
            if app_proto != entry['app_proto']:
                app_proto = ''
            if app_hostname != entry['app_hostname']:
                app_hostname = ''
            to_be_deleted.append(entry['rowid'])
        tmp.execute('UPDATE traffic SET details = ?, duration = ?, src_ip = ?, src_port = ?, dest_ip = ?, app_proto = ?, bytes_send = ?, bytes_received = ?, app_hostname = ? WHERE rowid = ?', (to_details, int(current_end-current_start), src_ip, src_port, dest_ip, app_proto, current_bytes_send, current_bytes_received, app_hostname, row['rowid']))
    for tbd in to_be_deleted:
        c.execute('DELETE FROM traffic WHERE rowid = ?', (tbd,))
    return len(to_be_deleted)

# Create database if it was empty
c = con.cursor()

# Main loop

now = int(time.mktime(datetime.datetime.utcnow().timetuple()))
start = now-3600*24 #move flows from live DB to archive after 24hours

c.execute('ATTACH DATABASE "/var/lib/pakon.db" AS live')
c.execute('INSERT INTO traffic SELECT start, duration, 99, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, app_hostname FROM live.traffic WHERE start < ? AND flow_id IS NULL', (start,))
logging.info("moved {} flows from live to archive".format(c.rowcount))
c.execute('DELETE FROM live.traffic WHERE start < ? AND flow_id IS NULL', (start,))
c.execute('VACUUM live')
con.commit()
#TODO: move constants to configuration
logging.info("squashed from 99 to 80 - deleted {}".format(squash(99,80,now-3600*24,60)))
logging.info("squashed from 80 to 70 - deleted {}".format(squash(80,70,now-3600*24*3,900)))
logging.info("squashed from 70 to 60 - deleted {}".format(squash(70,60,now-3600*24*7,1800)))
logging.info("squashed from 60 to 50 - deleted {}".format(squash(60,50,now-3600*24*14,3600)))
c.execute('DELETE FROM traffic WHERE start < ?', (3600*24*28,))
c.execute('VACUUM')
con.commit()

c.execute('SELECT COUNT(*) FROM live.traffic')
logging.info("{} flows in live database".format(c.fetchone()[0]))
c.execute('SELECT COUNT(*) FROM traffic WHERE details = 99')
logging.info("{} flows in archive on details level 99".format(c.fetchone()[0]))
c.execute('SELECT COUNT(*) FROM traffic WHERE details = 80')
logging.info("{} flows in archive on details level 80".format(c.fetchone()[0]))
c.execute('SELECT COUNT(*) FROM traffic WHERE details = 70')
logging.info("{} flows in archive on details level 70".format(c.fetchone()[0]))
c.execute('SELECT COUNT(*) FROM traffic WHERE details = 60')
logging.info("{} flows in archive on details level 60".format(c.fetchone()[0]))
c.execute('SELECT COUNT(*) FROM traffic WHERE details = 50')
logging.info("{} flows in archive on details level 50".format(c.fetchone()[0]))
