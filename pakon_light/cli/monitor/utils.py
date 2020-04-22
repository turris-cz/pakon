#  Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#  This is free software, licensed under the GNU General Public License v3.
#  See /LICENSE for more information.

import ctypes
import datetime
import glob
import logging
import re
import subprocess
import sys
import threading
import time
from ctypes.util import find_library

from cachetools import TTLCache, cached

libc = ctypes.CDLL(find_library('c'))

PR_SET_PDEATHSIG = 1
SIGKILL = 9


def set_death_signal():
    libc.prctl(PR_SET_PDEATHSIG, SIGKILL)


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


class MultiReplace:
    "perform replacements specified by regex and adict all at once"
    " The regex is constructed such that it matches the whole string (.* in the beginnin and end),"
    " the actual key from adict is the first group of match (ignoring possible prefix and suffix)."
    " The whole string is then replaced (the replacement is specified by adict)"

    def __init__(self, adict={}):
        self.setup(adict)

    def setup(self, adict):
        self.adict = adict
        self.rx = re.compile("^.*(" + '|'.join(map(re.escape, adict)) + ").*$")

    def replace(self, text):
        def one_xlat(match):
            return self.adict[match.group(1)]

        return self.rx.sub(one_xlat, text)


def load_replaces():
    adict = {}
    try:
        for fn in glob.glob("/usr/share/pakon-light/domains_replace/*.conf"):
            with open(fn) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    match = re.match('"([^"]+)"\s*:\s*"([^"]+)"', line)
                    if not match:
                        print("invalid line: " + line)
                        continue
                    adict[match.group(1)] = match.group(2)
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
        return "", ""
    res = re.search(r"dev\s+([^\s]+)\s+.*lladdr\s+((?:[a-f\d]{1,2}\:){5}[a-f\d]{1,2})", s)
    if not res:
        logging.warning("no match for dev&mac in output of `ip neigh show {}`: {}".format(ip, s))
        return "", ""
    dev = res.groups()[0]
    mac = res.groups()[1]
    return dev, mac


def timestamp2unixtime(timestamp):
    # converts textual timestamp to unixtime
    # time string is always assumed to be in local time, the timezone part in string is ignored
    # reason is that mktime ignores timezone in datetime object and I don't see any easy way how
    # to do it properly (without pytz)
    dt = datetime.datetime.strptime(timestamp[:-5], '%Y-%m-%dT%H:%M:%S.%f')
    timestamp = float(time.mktime(dt.timetuple())) + float(dt.microsecond) / 1000000
    return timestamp


def new_device_notify(mac, iface):
    def new_device_notify_thread(mac, iface):
        time.sleep(5)
        try:
            cmd = ["/usr/libexec/pakon-light/notify_new_device.sh", mac, iface]
            subprocess.call([arg.encode('utf-8') for arg in cmd])
        except OSError:
            logging.error("failed to create notification")

    thread = threading.Thread(target=new_device_notify_thread, args=(mac, iface,))
    thread.daemon = True
    thread.start()


def handle_dns(data, dns_cache):
    if data['dns']['type'] == 'answer' and 'rrtype' in data['dns'].keys() and data['dns']['rrtype'] in (
            'A', 'AAAA', 'CNAME'):
        logging.debug('Saving DNS data')
        dev, mac = get_dev_mac(data['dest_ip'])
        dns_cache.set(mac, data['dns']['rrname'], data['dns']['rdata'])


def handle_flow(data, con):
    if data['proto'] not in ['TCP', 'UDP']:
        return
    if 'app_proto' not in data.keys() or data['app_proto'] == 'failed':
        data['app_proto'] = '?'
    if data['app_proto'] == 'dns' or int(data['flow']['bytes_toserver']) == 0 or int(
            data['flow']['bytes_toclient']) == 0:
        con.execute('DELETE FROM traffic WHERE flow_id = ?', (data['flow_id'],))
    else:
        con.execute(
            'UPDATE traffic SET duration = ?, app_proto = ?, bytes_send = ?, bytes_received = ?, flow_id = NULL WHERE flow_id = ?',
            (
                int(timestamp2unixtime(data['flow']['end']) - timestamp2unixtime(data['flow']['start'])),
                data['app_proto'],
                data['flow']['bytes_toserver'], data['flow']['bytes_toclient'], data['flow_id']
            )
        )


def handle_tls(data, con, domain_replace):
    hostname = ''
    if 'sni' in data['tls'].keys():
        hostname = data['tls']['sni']
    elif 'subject' in data['tls'].keys():
        # get only CN from suject
        m = re.search('(?<=CN=)[^,]*', data['tls']['subject'])
        if m:
            hostname = m.group(0)
    if not hostname:
        return
    con.execute('UPDATE traffic SET app_hostname = ?, app_proto = "tls" WHERE flow_id = ?',
                (domain_replace.replace(hostname), data['flow_id']))


def handle_http(data, con, domain_replace):
    if 'hostname' not in data['http'].keys():
        return
    con.execute('UPDATE traffic SET app_hostname = ?, app_proto = "http" WHERE flow_id = ?',
                (domain_replace.replace(data['http']['hostname']), data['flow_id']))


def handle_flow_start(data, notify_new_devices, con, allowed_interfaces, known_devices, dns_cache, domain_replace):
    dev, mac = get_dev_mac(data['src_ip'])
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
    con.execute(
        'INSERT INTO traffic (flow_id, start, src_mac, src_ip, src_port, dest_ip, dest_port, proto, app_proto, app_hostname) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (
            data['flow_id'], timestamp2unixtime(data['flow']['start']), mac, data['src_ip'], data['src_port'],
            data['dest_ip'], data['dest_port'],
            data['proto'], data['app_proto'], hostname
        )
    )


def exit_gracefully(con, data_source, dns_cache):
    data_source.close()
    if con:
        con.commit()
        con.close()
    dns_cache.dump()
    sys.exit(0)


def reload_replaces(domain_replace):
    settings.logger.info("reloading domain replaces")
    domain_replace.setup(load_replaces())
