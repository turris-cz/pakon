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

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
#logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

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

def uci_get_time(opt, default = None):
    ret = 0
    text = uci_get(opt)
    if not text:
        text = default
    if text[-1:].upper() == 'M':
        ret = int(text[:-1]) * 60
    elif text[-1:].upper() == 'H':
        ret = int(text[:-1]) * 3600
    elif text[-1:].upper() == 'D':
        ret = int(text[:-1]) * 24 * 3600
    elif text[-1:].upper() == 'W':
        ret = int(text[:-1]) * 7 * 24 * 3600
    else:
        ret = int(text)
    return ret

archive_path = uci_get('pakon.archive.path') or '/srv/pakon/pakon-archive.db'
con = sqlite3.connect(archive_path)
con.row_factory = sqlite3.Row

def squash(from_details, to_details, up_to, window, size_threshold):
    global con
    now = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    start = now - up_to
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
            if entry['app_hostname']!=row['app_hostname']:
                continue
            #if hostname is Null, we only want to merge flows with equal dest_ip
            if not entry['app_hostname'] and entry['dest_ip']!=row['dest_ip']:
                continue
            logging.debug("merging with:")
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
        if current_bytes_send + current_bytes_received > size_threshold:
            tmp.execute('UPDATE traffic SET details = ?, duration = ?, src_ip = ?, src_port = ?, dest_ip = ?, app_proto = ?, bytes_send = ?, bytes_received = ?, app_hostname = ? WHERE rowid = ?', (to_details, int(current_end-current_start), src_ip, src_port, dest_ip, app_proto, current_bytes_send, current_bytes_received, app_hostname, row['rowid']))
        else:
            to_be_deleted.append(row['rowid'])
    for tbd in to_be_deleted:
        c.execute('DELETE FROM traffic WHERE rowid = ?', (tbd,))
    con.commit()
    return len(to_be_deleted)

def load_archive_rules():
    rules = []
    i = 0
    while uci_get("pakon.@archive_rule[{}].up_to".format(i)):
        up_to = uci_get_time("pakon.@archive_rule[{}].up_to".format(i))
        window = uci_get_time("pakon.@archive_rule[{}].window".format(i))
        size_threshold = int(uci_get("pakon.@archive_rule[{}].size_threshold".format(i)) or 0)
        rules.append( { "up_to": up_to, "window": window, "size_threshold": size_threshold })
        i = i + 1
    if not rules: #if there is no rule (old configuration?) - add one default rule
        rules.append( { "up_to": 86400, "window": 60, "size_threshold": 4096 })
        logging.info('no rules in configuration - using default {}'.format(str(rules[0])))
    sorted(rules, key=lambda r: r["up_to"])
    return rules

# Create database if it was empty
c = con.cursor()
now = int(time.mktime(datetime.datetime.utcnow().timetuple()))
start = now-3600*24 #move flows from live DB to archive after 24hours

c.execute('ATTACH DATABASE "/var/lib/pakon.db" AS live')
c.execute('INSERT INTO traffic SELECT start, duration, 0, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, app_hostname FROM live.traffic WHERE start < ? AND flow_id IS NULL', (start,))
logging.info("moved {} flows from live to archive".format(c.rowcount))
c.execute('DELETE FROM live.traffic WHERE start < ? AND flow_id IS NULL', (start,))
con.commit()

#workaround for a bug in Python 3.6
#https://bugs.python.org/issue28518
con.isolation_level = None
con.execute('VACUUM live')
con.isolation_level = ''

rules = load_archive_rules()

#if the rules changed (there is detail level that can't be generated using current rules)
#reset everything to detail level 0 -> perform the whole archivation again
c.execute('SELECT DISTINCT(details) FROM traffic WHERE details > ?', (len(rules),))
if c.fetchall():
    logging.info('resetting all detail levels to 0')
    c.execute('UPDATE traffic SET details = 0')

for i in range(len(rules)):
    deleted = squash(i, i+1, rules[i]["up_to"], rules[i]["window"], rules[i]["size_threshold"])
    logging.info("squashed from {} to {} - deleted {}".format(i, i+1, deleted))
c.execute('DELETE FROM traffic WHERE start < ?', (now - uci_get_time('pakon.archive.keep', '4w'),))

#c.execute('VACUUM')
#performing it every time is bad - it causes the whole database file to be rewritten
#TODO: think about when to do it, perform it once in a while?

con.commit()
c.execute('SELECT COUNT(*) FROM live.traffic')
logging.info("{} flows in live database".format(c.fetchone()[0]))
for i in range(len(rules)+1):
    c.execute('SELECT COUNT(*) FROM traffic WHERE details = ?', (i,))
    logging.info("{} flows in archive on details level {}".format(c.fetchone()[0], i))
