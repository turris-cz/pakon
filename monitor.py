#!/usr/bin/env python3

import fileinput
import json
import socket
import os, os.path
import string
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

# converts textual timestamp to unixtime
# time string is always assumed to be in local time, the timezone part in string is ignored
# reason is that mktime ignores timezone in datetime object and I don't see any easy way how to do it properly (without pytz)
def timestamp2unixtime(timestamp):
    dt = datetime.datetime.strptime(timestamp[:-5],'%Y-%m-%dT%H:%M:%S.%f')
    timestamp = float(time.mktime(dt.timetuple())) + float(dt.microsecond)/1000000
    return timestamp

def handle_dns(data, c):
    if data['dns']['type'] == 'answer' and 'rrtype' in data['dns'].keys() and data['dns']['rrtype'] in ('A', 'AAAA', 'CNAME'):
        logging.debug('Saving DNS data')
        c.execute('INSERT INTO dns VALUES (?,?,?,?,?)',
                    (timestamp2unixtime(data['timestamp']),
                    data['dest_ip'], data['dns']['rrname'], data['dns']['rrtype'],
                    data['dns']['rdata']))

def handle_flow(data, c):
    if data['proto'] not in ['TCP', 'UDP']:
        return
    if 'app_proto' not in data.keys():
        data['app_proto'] = '?'
    if data['app_proto'] in ['failed', 'dns'] or int(data['flow']['bytes_toserver'])==0 or int(data['flow']['bytes_toclient'])==0:
        c.execute('DELETE FROM traffic WHERE flow_id = ?', (data['flow_id'],))
        if c.rowcount!=1:
            logging.debug("Can't delete flow")
    else:
        c.execute('UPDATE traffic SET duration = ?, app_proto = ?, bytes_send = ?, bytes_received = ?, flow_id = NULL WHERE flow_id = ?', (int(timestamp2unixtime(data['flow']['end'])-timestamp2unixtime(data['flow']['start'])), data['app_proto'], data['flow']['bytes_toserver'], data['flow']['bytes_toclient'], data['flow_id']))
        if c.rowcount!=1:
            logging.debug("Can't update flow")

def handle_tls(data, c):
    hostname = ''
    if 'sni' in data['tls'].keys():
        hostname = data['tls']['sni']
    elif 'subject' in data['tls'].keys():
        #get only CN from suject
        m = re.search('(?<=CN=)[^,]*', data['tls']['subject'])
        if m:
                hostname = m.group(0)
    if not hostname:
        return
    c.execute('UPDATE traffic SET app_hostname = ?, app_proto = "tls" WHERE flow_id = ?', (hostname, data['flow_id']))
    if c.rowcount!=1:
        logging.debug("Can't update flow")

def handle_http(data, c):
    if 'hostname' not in data['http'].keys():
        return
    c.execute('UPDATE traffic SET app_hostname = ?, app_proto = "http" WHERE flow_id = ?', (data['http']['hostname'], data['flow_id']))
    if c.rowcount!=1:
        logging.debug("Can't update flow")

def handle_flow_start(data, c):
    if data['proto'] not in ['TCP', 'UDP']:
        return
    if 'app_proto' not in data.keys():
        data['app_proto'] = '?'
    if data['app_proto'] in ['failed', 'dns']:
        return
    c.execute('INSERT INTO traffic (flow_id, start, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (data['flow_id'], timestamp2unixtime(data['flow']['start']),
                data['ether']['src'], data['src_ip'],
                data['src_port'], data['dest_ip'], data['dest_port'],
                data['proto'], data['app_proto']))

def exit_gracefully(signum, frame):
    global con, conntrack
    conntrack.terminate()
    time.sleep(1)
    if not con:
        return
    con.commit()
    if con:
         con.close()
    conntrack.kill()
    sys.exit(0)

if not os.path.isfile('/var/lib/pakon.db'):
    subprocess.call(['/usr/bin/python3', '/usr/libexec/pakon-light/create_db.py'])
con = sqlite3.connect('/var/lib/pakon.db')

c = con.cursor()
# flow_ids are only unique (and meaningful) during one run of this script
try:
    c.execute('UPDATE traffic SET flow_id = NULL, duration = 0, bytes_send = 0, bytes_received = 0 WHERE flow_id IS NOT NULL')
    con.commit()
except:
    logging.debug('Error cleaning flow_id')

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)
conntrack=None

devnull = open(os.devnull, 'w')

try:
    conntrack = subprocess.Popen(["/usr/bin/python3","/usr/bin/suricata_conntrack_flows.py","/var/run/pakon.sock"], shell=False, stdout=subprocess.PIPE, stderr=devnull)
except Exception as e:
    logging.error("Can't run flows_conntrack.py")
    logging.error(e)
    sys.exit(1)

logging.debug("Listening...")


while True:
    try:
        logging.debug('Getting data...')
        line = conntrack.stdout.readline().decode()
        if not line:
            break
        line = line.strip()
        logging.debug(line)
        if not line:
            continue
        try:
            data = json.loads(line)
        except ValueError:
            logging.warn("Error decoding json")
            continue
        if 'ether' not in data.keys() or 'src' not in data['ether'].keys():
            data['ether']={}
            data['ether']['src']=''
        if data['event_type'] == 'dns' and data['dns']:
            handle_dns(data, c)
        elif data['event_type'] == 'flow' and data['flow']:
            handle_flow(data, c)
        elif data['event_type'] == 'tls' and data['tls']:
            handle_tls(data, c)
        elif data['event_type'] == 'http' and data['http']:
            handle_http(data, c)
        elif data['event_type'] == 'flow_start' and data['flow']:
            handle_flow_start(data, c)
        else:
            logging.warn("Unknown event type")
        con.commit()

    except KeyboardInterrupt:
        exit_gracefully()

    except IOError as e:
        if e.errno != errno.EINTR:
            raise
