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
import glob
import collections
import queue

#logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = collections.OrderedDict()

    def get(self, key):
        try:
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        except KeyError:
            return None

    def set(self, key, value):
        try:
            self.cache.pop(key)
        except KeyError:
            if len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
        self.cache[key] = value

class DNSCache:
    def __init__(self):
        self.cache = LRUCache(1000)

    def set(self, src_ip, question, answer):
        self.cache.set(src_ip+":"+answer, question)

    def get(self, src_ip, answer):
        return self.cache.get(src_ip+":"+answer)

class MultiReplace:
    "perform replacements specified by regex and adict all at once"
    " The regex is constructed such that it matches the whole string (.* in the beginnin and end),"
    " the actual key from adict is the first group of match (ignoring possible prefix and suffix)."
    " The whole string is then replaced (the replacement is specified by adict)"
    def __init__(self, adict={}):
        self.setup(adict)

    def setup(self, adict):
        self.adict = adict
        self.rx = re.compile("^.*("+'|'.join(map(re.escape, adict))+").*$")

    def replace(self, text):
        def one_xlat(match):
            return self.adict[match.group(1)]
        return self.rx.sub(one_xlat, text)

def get_dns_hostname(src_ip, dest_ip):
    global dns_cache
    name = None
    while True:
        name_ = dns_cache.get(src_ip, name or dest_ip)
        if not name_:
            return name
        name = name_


def load_domain_replaces():
    adict={}
    try:
        for fn in glob.glob("/usr/share/pakon-light/domains_replace/*.conf"):
            with open(fn) as f:
                for line in f:
                    match = re.match('\s*"([^"]+)"\s*:\s*"([^"]+)"\s*', line)
                    if not match:
                        if re.match('\s*', line): #ignore empty lines
                            continue
                        print("invalid line: "+line)
                        continue
                    adict[match.group(1)]=match.group(2)
    except IOError as e:
        print("can't load domains_services file")
        print(e)
    return adict

# converts textual timestamp to unixtime
# time string is always assumed to be in local time, the timezone part in string is ignored
# reason is that mktime ignores timezone in datetime object and I don't see any easy way how to do it properly (without pytz)
def timestamp2unixtime(timestamp):
    dt = datetime.datetime.strptime(timestamp[:-5],'%Y-%m-%dT%H:%M:%S.%f')
    timestamp = float(time.mktime(dt.timetuple())) + float(dt.microsecond)/1000000
    return timestamp

def handle_dns(data, c):
    global dns_cache
    if data['dns']['type'] == 'answer' and 'rrtype' in data['dns'].keys() and data['dns']['rrtype'] in ('A', 'AAAA', 'CNAME'):
        logging.debug('Saving DNS data')
        dns_cache.set(data['dest_ip'],data['dns']['rrname'],data['dns']['rdata'])

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
    global domain_replace
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
    c.execute('UPDATE traffic SET app_hostname = ?, app_proto = "tls" WHERE flow_id = ?', (domain_replace.replace(hostname), data['flow_id']))
    if c.rowcount!=1:
        logging.debug("Can't update flow")

def handle_http(data, c):
    global domain_replace
    if 'hostname' not in data['http'].keys():
        return
    c.execute('UPDATE traffic SET app_hostname = ?, app_proto = "http" WHERE flow_id = ?', (domain_replace.replace(data['http']['hostname']), data['flow_id']))
    if c.rowcount!=1:
        logging.debug("Can't update flow")

def handle_flow_start(data, c):
    global domain_replace
    if data['proto'] not in ['TCP', 'UDP']:
        return
    if 'app_proto' not in data.keys():
        data['app_proto'] = '?'
    if data['app_proto'] in ['failed', 'dns']:
        return
    hostname = get_dns_hostname(data['src_ip'], data['dest_ip'])
    if hostname:
        hostname = domain_replace.replace(hostname)
    c.execute('INSERT INTO traffic (flow_id, start, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, app_hostname) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (data['flow_id'], timestamp2unixtime(data['flow']['start']),
                data['ether']['src'], data['src_ip'],
                data['src_port'], data['dest_ip'], data['dest_port'],
                data['proto'], data['app_proto'], hostname))

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

def reload_replaces(signum, frame):
    global domain_replace
    domain_replace.set(load_domain_replaces())

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

dns_cache = DNSCache()
domain_replace = MultiReplace(load_domain_replaces())
conntrack=None
try:
    devnull = open(os.devnull, 'w')
    conntrack = subprocess.Popen(["/usr/bin/python3","/usr/bin/suricata_conntrack_flows.py","/var/run/pakon.sock"], shell=False, stdout=subprocess.PIPE, stderr=devnull)
except Exception as e:
    logging.error("Can't run flows_conntrack.py")
    logging.error(e)
    sys.exit(1)
if not os.path.isfile('/var/lib/pakon.db'):
    subprocess.call(['/usr/bin/python2', '/usr/libexec/pakon-light/create_db.py'])
con = sqlite3.connect('/var/lib/pakon.db')
c = con.cursor()
try:
    c.execute('UPDATE traffic SET flow_id = NULL, duration = 0, bytes_send = 0, bytes_received = 0 WHERE flow_id IS NOT NULL')
    con.commit()
except:
    logging.debug('Error cleaning flow_id')

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)
signal.signal(signal.SIGUSR1, reload_replaces)

def main():
    # flow_ids are only unique (and meaningful) during one run of this script
    logging.debug("Listening...")
    while True:
        try:
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

if __name__ == "__main__":
    main()
