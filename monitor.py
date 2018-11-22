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
import threading
import gzip
import ctypes
from ctypes.util import find_library
from cachetools import LRUCache, TTLCache, cached

libc = ctypes.CDLL(find_library('c'))
PR_SET_PDEATHSIG = 1
SIGKILL = 9

def set_death_signal():
    libc.prctl(PR_SET_PDEATHSIG, SIGKILL)

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

class everyN:
    def __init__(self, cnt):
        self.cnt = cnt
        self.cur = 0
    def __bool__(self):
        self.cur += 1
        if self.cnt == self.cur:
            self.cur = 0
            return True
        return False

class DNSCache:
    """DNS cache internally uses 2 types of cache.
    One (fast_cache)is smaller, with short TTL and there can be a lot of garbage - NS servers A/AAAA, CNAMEs
    The second one (used_cache) is LRU and there are just records that were used at least once - might be used again
    """
    __DB_DUMP_PATH__ = "/srv/pakon/dns_cache.json.gz"
    def __init__(self):
        self.fast_cache = TTLCache(maxsize=1000, ttl=3600)
        self.used_cache = LRUCache(maxsize=2000)

    def dump(self):
        """dump used_cache to __DB_DUMP_PATH__ - so it can survive restart"""
        cache = collections.OrderedDict()
        for item in self.__popitem():
            cache[item[0]] = item[1]
        try:
            with gzip.open(DNSCache.__DB_DUMP_PATH__, 'wb') as f:
                f.write(json.dumps(cache).encode('utf-8'))
        except IOError:
            pass

    def try_load(self):
        """try restoring used_cache from __DB_DUMP_PATH__ - do nothing if it doesn't exist"""
        if os.path.isfile(DNSCache.__DB_DUMP_PATH__):
            try:
                cache = {}
                with gzip.open(DNSCache.__DB_DUMP_PATH__, 'rb') as f:
                    cache = json.loads(f.read().decode('utf-8'), object_pairs_hook=collections.OrderedDict)
                for k,v in cache.items():
                    self.used_cache[k] = v
            except (ValueError, IOError):
                pass

    def __popitem(self):
        while self.used_cache:
            yield self.used_cache.popitem()

    def set(self, src_mac, question, answer):
        """called by handle_dns, adds record to fast_cache"""
        self.fast_cache[src_mac+":"+answer] = question

    def get(self, src_mac, dest_ip):
        """get name for IP address
        Try used_cache first, if it's not there, try fast_cache
        In fast_cache are also CNAMEs, so it might follow CNAMEs to get the user-requested name.
        If record is found in fast_cache, it's added to used_cache then.
        """
        used = self.used_cache.get(src_mac+":"+dest_ip)
        if used:
            return used
        name = None
        while True:
            name_ = self.fast_cache.get(src_mac+":"+(name or dest_ip))
            if not name_:
                if name:
                    self.used_cache[src_mac+":"+dest_ip] = name
                return name
            name = name_

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



def load_replaces():
    adict={}
    try:
        for fn in glob.glob("/usr/share/pakon-light/domains_replace/*.conf"):
            with open(fn) as f:
                for line in f:
                    line=line.strip()
                    if not line:
                        continue
                    match = re.match('"([^"]+)"\s*:\s*"([^"]+)"', line)
                    if not match:
                        print("invalid line: "+line)
                        continue
                    adict[match.group(1)]=match.group(2)
    except IOError as e:
        print("can't load domains_services file")
        print(e)
    return adict

@cached(TTLCache(maxsize=256, ttl=3600))
def get_dev_mac(ip):
    pid = subprocess.Popen(["ip", "neigh", "show", ip], stdout=subprocess.PIPE)
    s = pid.communicate()[0].decode()
    if not s:
        logging.debug("no entry in `ip neigh show` for {}".format(ip))
        return ("", "")
    res = re.search(r"dev\s+([^\s]+)\s+.*lladdr\s+((?:[a-f\d]{1,2}\:){5}[a-f\d]{1,2})", s)
    if not res:
        logging.warn("no match for dev&mac in output of `ip neigh show {}`: {}".format(ip,s))
        return ("", "")
    dev = res.groups()[0]
    mac = res.groups()[1]
    return dev, mac

def timestamp2unixtime(timestamp):
    # converts textual timestamp to unixtime
    # time string is always assumed to be in local time, the timezone part in string is ignored
    # reason is that mktime ignores timezone in datetime object and I don't see any easy way how to do it properly (without pytz)
    dt = datetime.datetime.strptime(timestamp[:-5],'%Y-%m-%dT%H:%M:%S.%f')
    timestamp = float(time.mktime(dt.timetuple())) + float(dt.microsecond)/1000000
    return timestamp


def new_device_notify(mac, iface):
    def new_device_notify_thread(mac, iface):
        time.sleep(5)
        try:
            cmd = ["/usr/libexec/pakon-light/notify_new_device.sh", mac, iface]
            subprocess.call([arg.encode('utf-8') for arg in cmd])
        except OSError:
            logging.error("failed to create notification")
    thread = threading.Thread(target=new_device_notify_thread, args=(mac, iface, ))
    thread.daemon = True
    thread.start()

def handle_dns(data, con):
    if data['dns']['type'] == 'answer' and 'rrtype' in data['dns'].keys() and data['dns']['rrtype'] in ('A', 'AAAA', 'CNAME'):
        logging.debug('Saving DNS data')
        dev, mac=get_dev_mac(data['dest_ip'])
        dns_cache.set(mac, data['dns']['rrname'], data['dns']['rdata'])

def handle_flow(data, con):
    if data['proto'] not in ['TCP', 'UDP']:
        return
    if 'app_proto' not in data.keys() or data['app_proto'] == 'failed':
        data['app_proto'] = '?'
    if data['app_proto'] == 'dns' or int(data['flow']['bytes_toserver'])==0 or int(data['flow']['bytes_toclient'])==0:
        con.execute('DELETE FROM traffic WHERE flow_id = ?', (data['flow_id'],))
    else:
        con.execute('UPDATE traffic SET duration = ?, app_proto = ?, bytes_send = ?, bytes_received = ?, flow_id = NULL WHERE flow_id = ?', (int(timestamp2unixtime(data['flow']['end'])-timestamp2unixtime(data['flow']['start'])), data['app_proto'], data['flow']['bytes_toserver'], data['flow']['bytes_toclient'], data['flow_id']))

def handle_tls(data, con):
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
    con.execute('UPDATE traffic SET app_hostname = ?, app_proto = "tls" WHERE flow_id = ?', (domain_replace.replace(hostname), data['flow_id']))

def handle_http(data, con):
    if 'hostname' not in data['http'].keys():
        return
    con.execute('UPDATE traffic SET app_hostname = ?, app_proto = "http" WHERE flow_id = ?', (domain_replace.replace(data['http']['hostname']), data['flow_id']))

def handle_flow_start(data, notify_new_devices, con):
    dev, mac=get_dev_mac(data['src_ip'])
    if data['proto'] not in ['TCP', 'UDP']:
        return
    if 'app_proto' not in data.keys() or data['app_proto'] == 'failed':
        data['app_proto'] = '?'
    if data['app_proto'] == 'dns':
        return
    if dev not in allowed_interfaces:
        logging.debug("This flow is not from allowed interface")
        return
    if notify_new_devices and mac not in known_devices:
        known_devices.add(mac)
        new_device_notify(mac, dev)
    hostname = dns_cache.get(mac, data['dest_ip'])
    if hostname:
        logging.debug('Got hostname from cached DNS: {}'.format(hostname))
        hostname = domain_replace.replace(hostname.lower())
    con.execute('INSERT INTO traffic (flow_id, start, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, app_hostname) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
               (data['flow_id'], timestamp2unixtime(data['flow']['start']), mac, data['src_ip'], data['src_port'], data['dest_ip'], data['dest_port'],
                data['proto'], data['app_proto'], hostname))

def exit_gracefully(signum, frame):
    data_source.close()
    if con:
        con.commit()
        con.close()
    dns_cache.dump()
    sys.exit(0)

dns_cache = DNSCache()
domain_replace = MultiReplace(load_replaces())
allowed_interfaces = []
known_devices=set()
data_source = None
con = None

class Source:
    def __init__(self):
        pass

    def get_message(self):
        pass

    def close(self):
        pass


class ConntrackScriptSource(Source):
    def __init__(self):
        try:
            self.devnull = open(os.devnull, 'w')
            self.conntrack = subprocess.Popen(["/usr/bin/python3","/usr/libexec/suricata_conntrack_flows.py","/var/run/pakon.sock"], shell=False, stdout=subprocess.PIPE, stderr=self.devnull, preexec_fn=set_death_signal)
        except OSError as e:
            logging.error("Can't run flows_conntrack.py")
            logging.error(e)
            sys.exit(1)

    def get_message(self):
        return self.conntrack.stdout.readline().decode()

    def close(self):
        self.conntrack.terminate()


class UnixSocketSource(Source):
    def __init__(self):
        try:
            os.unlink("/var/run/pakon.sock")
        except OSError:
            pass
        try:
            self.client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            self.client.bind("/var/run/pakon.sock")
        except OSError as e:
            logging.error("Can't read socket")
            logging.error(e)
            sys.exit(1)

    def get_message(self):
        return self.client.makefile().readline()

    def close(self):
        self.client.close()

def reload_replaces(signum, frame):
    logging.info("reloading domain replaces")
    domain_replace.setup(load_replaces())

def main():
    global allowed_interfaces, data_source
    archive_path = uci_get('pakon.archive.path') or '/srv/pakon/pakon-archive.db'
    dns_cache.try_load()
    # isolation_level=None for autocommit mode - we dont want long-lasting transactions
    con = sqlite3.connect('/var/lib/pakon.db', isolation_level=None)
    # flow_ids are only unique (and meaningful) during one run of this script
    # flows with flow_id are incomplete, delete them
    try:
        con.execute('DELETE FROM traffic WHERE flow_id IS NOT NULL')
    except:
        logging.debug('Error cleaning flow_id')
    notify_new_devices = int(uci_get('pakon.monitor.notify_new_devices'))
    if notify_new_devices:
        con.execute('ATTACH ? AS archive', (archive_path,))
        for row in con.execute('SELECT DISTINCT(src_mac) FROM traffic UNION SELECT DISTINCT(src_mac) FROM archive.traffic'):
            known_devices.add(row[0])
        con.execute('DETACH archive')
    if uci_get('pakon.monitor.mode').strip() == 'filter':
        data_source = ConntrackScriptSource()
    else:
        data_source = UnixSocketSource()
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    signal.signal(signal.SIGUSR1, reload_replaces)
    allowed_interfaces = uci_get('pakon.monitor.interface')
    logging.debug("Listening...")
    # maximum number of records in the live database - to prevent filling all available space
    # it's recommended not to touch this, unless you know really well what you're doing
    # filling all available space in /var/lib (tmpfs) will probably break your router
    hard_limit = int(uci_get('pakon.monitor.database_limit') or 3000000)
    run_check = everyN(100000)
    while True:
        try:
            line = data_source.get_message()
            if not line:
                break
            logging.debug(line)
            try:
                data = json.loads(line)
            except ValueError:
                logging.warn("Error decoding json")
                continue
            if 'ether' not in data.keys() or 'src' not in data['ether'].keys():
                data['ether']={}
                data['ether']['src']=''
            if data['event_type'] == 'dns' and data['dns']:
                handle_dns(data, con)
            elif data['event_type'] == 'flow' and data['flow']:
                handle_flow(data, con)
            elif data['event_type'] == 'tls' and data['tls']:
                handle_tls(data, con)
            elif data['event_type'] == 'http' and data['http']:
                handle_http(data, con)
            elif data['event_type'] == 'flow_start' and data['flow']:
                handle_flow_start(data, notify_new_devices, con)
            else:
                logging.warn("Unknown event type")
            if run_check:
                c = con.cursor()
                c.execute('SELECT COUNT(*) FROM traffic')
                count = int(c.fetchone()[0])
                if count > hard_limit:
                    logging.warning('over {} records in the live database ({}) -> deleting', hard_limit, count)
                    con.execute('DELETE FROM traffic WHERE ROWID IN (SELECT ROWID FROM traffic ORDER BY ROWID DESC LIMIT -1 OFFSET ?)', hard_limit)
        except KeyboardInterrupt:
            exit_gracefully()
        except IOError as e:
            if e.errno != errno.EINTR:
                raise
        except sqlite3.DatabaseError as e:
            logging.warn("Database error: "+str(e))

if __name__ == "__main__":
    main()
