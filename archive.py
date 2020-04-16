#!/usr/bin/env python3

import datetime
import logging
import sqlite3
import subprocess
import sys
import time

logging.basicConfig(stream=sys.stderr, level=logging.INFO)


# logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# TODO: replace with uci bindings - once available
def uci_get(opt):
    delimiter = '__uci__delimiter__'
    child = subprocess.Popen(['/sbin/uci', '-d', delimiter, '-q', 'get', opt],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = child.communicate()
    out = out.strip().decode('ascii', 'ignore')
    if out.find(delimiter) != -1:
        return out.split(delimiter)
    else:
        return out


def uci_get_time(opt, default=None):
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
con = sqlite3.connect(archive_path, isolation_level=None, timeout=30.0)
con.row_factory = sqlite3.Row


def squash(from_details, to_details, rules):
    global con
    c = con.cursor()
    now = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    start = now - rules['up_to']
    inserted = 0
    deleted = 0
    if from_details == 'live':
        for row_mac in c.execute('SELECT DISTINCT src_mac FROM live.traffic WHERE start < ? AND flow_id IS NULL',
                                 (start,)):
            src_mac = row_mac['src_mac']
            c2 = con.cursor()
            for row_hostname in c2.execute(
                    'SELECT DISTINCT COALESCE(app_hostname,dest_ip) AS hostname FROM live.traffic WHERE src_mac = ? AND start < ? AND flow_id IS NULL',
                    (src_mac, start)):
                hostname = row_hostname['hostname']
                (i, d) = squash_for_mac_and_hostname(src_mac, hostname, from_details, to_details, start, rules)
                inserted += i
                deleted += d
        con.execute('DELETE FROM live.traffic WHERE start < ? AND flow_id IS NULL', (start,))
    else:
        for row_mac in c.execute('SELECT DISTINCT src_mac FROM traffic WHERE details = ? AND start < ?',
                                 (from_details, start,)):
            src_mac = row_mac['src_mac']
            c2 = con.cursor()
            for row_hostname in c2.execute(
                    'SELECT DISTINCT COALESCE(app_hostname,dest_ip) AS hostname FROM traffic WHERE details = ? AND src_mac = ? AND start < ?',
                    (from_details, src_mac, start)):
                hostname = row_hostname['hostname']
                (i, d) = squash_for_mac_and_hostname(src_mac, hostname, from_details, to_details, start, rules)
                inserted += i
                deleted += d
    logging.info('deleted %d flows from detail level %s, inserted %d flows to detail level %d', deleted,
                 str(from_details), inserted, to_details)


def squash_for_mac_and_hostname(src_mac, hostname, from_details, to_details, start, rules):
    def add_to_insert(flow):
        if flow['bytes_send'] + flow['bytes_received'] < rules['size_threshold']:
            return
        flow['detail'] = to_details
        to_insert.append(flow)

    def merge_flows(flow1, flow2):
        if flow2['end'] > flow1['end']:
            flow1['end'] = flow2['end']
            flow1['duration'] = int(flow1['end'] - flow1['start'])
        flow1['bytes_send'] += flow2['bytes_send']
        flow1['bytes_received'] += flow2['bytes_received']
        if flow1['src_ip'] != flow2['src_ip']:
            flow1['src_ip'] = ''
        if flow1['dest_ip'] != flow2['dest_ip']:
            flow1['dest_ip'] = ''
        if flow1['app_proto'] != flow2['app_proto']:
            flow1['app_proto'] = ''
        if flow1['app_hostname'] != flow2['app_hostname']:
            flow1['app_hostname'] = ''

    global con
    c = con.cursor()
    if from_details == 'live':
        result = c.execute(
            'SELECT rowid, (start+duration) AS end, * FROM live.traffic WHERE src_mac = ? AND COALESCE(app_hostname,dest_ip) = ? AND start < ? AND flow_id IS NULL ORDER BY dest_port, start',
            (src_mac, hostname, start))
    else:
        result = c.execute(
            'SELECT rowid, (start+duration) AS end, * FROM traffic WHERE details = ? AND src_mac = ? AND COALESCE(app_hostname,dest_ip) = ? AND start < ? ORDER BY dest_port, start',
            (from_details, src_mac, hostname, start))
    to_delete = []
    to_insert = []
    current_flow = None
    for row in result:
        to_delete.append((row['rowid'],))
        row = dict(row)
        row['start'] = float(row['start'])
        row['end'] = float(row['end'])
        row['bytes_send'] = int(row['bytes_send'])
        row['bytes_received'] = int(row['bytes_received'])
        if not current_flow:
            current_flow = row
        elif current_flow['dest_port'] == row['dest_port'] and current_flow['end'] + int(rules['window']) > row[
            'start']:
            merge_flows(current_flow, row)
        else:
            add_to_insert(current_flow)
            current_flow = row
    add_to_insert(current_flow)
    con.execute('BEGIN')
    con.executemany(
        'INSERT INTO traffic (start, duration, details, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_received, app_hostname)'
        'VALUES (:start, :duration, :detail, :src_mac, :src_ip, :src_port, :dest_ip, :dest_port, :proto, :app_proto, :bytes_send, :bytes_received, :app_hostname)',
        to_insert)
    if from_details != 'live':
        con.executemany('DELETE FROM traffic WHERE rowid = ?', to_delete)
    # if we're moving data from live, don't delete them individually, they will
    # be deleted all at once in the end. The transaction cannot be atomic anyway,
    # the database is in tmpfs, so try to delete them fast and backup live ASAP.
    con.execute('COMMIT')
    return (len(to_insert), len(to_delete))


def load_archive_rules():
    rules = []
    i = 0
    while uci_get("pakon.@archive_rule[{}].up_to".format(i)):
        up_to = uci_get_time("pakon.@archive_rule[{}].up_to".format(i))
        window = uci_get_time("pakon.@archive_rule[{}].window".format(i))
        size_threshold = int(uci_get("pakon.@archive_rule[{}].size_threshold".format(i)) or 0)
        rules.append({"up_to": up_to, "window": window, "size_threshold": size_threshold})
        i = i + 1
    if not rules:  # if there is no rule (old configuration?) - add one default rule
        rules.append({"up_to": 86400, "window": 60, "size_threshold": 4096})
        logging.info('no rules in configuration - using default {}'.format(str(rules[0])))
    sorted(rules, key=lambda r: r["up_to"])
    return rules


con.execute('ATTACH DATABASE "/var/lib/pakon.db" AS live')
start = 3600 * 24  # move flows from live DB to archive after 24hours
squash('live', 0, {"up_to": start, "window": 1, "size_threshold": 0})

# maximum number of records in the live database - to prevent filling all available space
# it's recommended not to touch this, unless you know really well what you're doing
# filling up all available space may break your router
hard_limit = int(uci_get('pakon.archive.database_limit') or 10000000)

c = con.cursor()
c.execute('SELECT COUNT(*) FROM live.traffic')
logging.info("{} flows remaining in live database".format(c.fetchone()[0]))

# all changes in live database is done, backup it
con.execute('DETACH DATABASE live')
subprocess.call(["/usr/libexec/pakon-light/backup_sqlite.sh", "/var/lib/pakon.db", "/srv/pakon/pakon.db.xz"])

c.execute('SELECT COUNT(*) FROM traffic')
count = int(c.fetchone()[0])
if count > hard_limit:
    logging.warning('over {} records in the archive database ({}) -> deleting', hard_limit, count)
    con.execute('DELETE FROM traffic WHERE ROWID IN (SELECT ROWID FROM traffic ORDER BY ROWID DESC LIMIT -1 OFFSET ?)',
                hard_limit)

rules = load_archive_rules()

# if the rules changed (there is detail level that can't be generated using current rules)
# reset everything to detail level 0 -> perform the whole archivation again
c.execute('SELECT DISTINCT(details) FROM traffic WHERE details > ?', (len(rules),))
if c.fetchall():
    logging.info('resetting all detail levels to 0')
    c.execute('UPDATE traffic SET details = 0')

for i in range(len(rules)):
    squash(i, i + 1, rules[i])
now = int(time.mktime(datetime.datetime.utcnow().timetuple()))
c.execute('DELETE FROM traffic WHERE start < ?', (now - uci_get_time('pakon.archive.keep', '4w'),))

# c.execute('VACUUM')
# performing it every time is bad - it causes the whole database file to be rewritten
# TODO: think about when to do it, perform it once in a while?

for i in range(len(rules) + 1):
    c.execute('SELECT COUNT(*) FROM traffic WHERE details = ?', (i,))
    logging.info("{} flows remaining in archive on details level {}".format(c.fetchone()[0], i))
