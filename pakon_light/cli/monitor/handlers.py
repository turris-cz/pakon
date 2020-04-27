#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

import datetime
import logging
import re
import subprocess
import time

from cachetools import cached, TTLCache


def handle_dns(data, dns_cache):
    if data['dns']['type'] == 'answer' and 'rrtype' in data['dns'].keys() and data['dns']['rrtype'] in (
            'A', 'AAAA', 'CNAME'
    ):
        logging.debug('Saving DNS data')
        dev, mac = get_dev_mac(data['dest_ip'])
        dns_cache.set(mac, data['dns']['rrname'], data['dns']['rdata'])


def handle_flow(data, traffic):
    if data['proto'] not in ['TCP', 'UDP']:
        return
    if 'app_proto' not in data.keys() or data['app_proto'] == 'failed':
        data['app_proto'] = '?'

    if data['app_proto'] == 'dns' or int(data['flow']['bytes_toserver']) == 0 or int(
            data['flow']['bytes_toclient']) == 0:
        return traffic.delete().where(traffic.c.flow_id == data['flow_id'])
    else:
        return traffic.update().values(
            duration=int(timestamp2unixtime(data['flow']['end']) - timestamp2unixtime(data['flow']['start'])),
            app_proto=data['app_proto'],
            bytes_send=data['flow']['bytes_toserver'],
            bytes_received=data['flow']['bytes_toclient'],
            flow_id=None,
        ).where(
            traffic.c.flow_id == data['flow_id']
        )


def handle_tls(data, domain_replace, traffic):
    hostname = ''
    if 'sni' in data['tls'].keys():
        hostname = data['tls']['sni']
    elif 'subject' in data['tls'].keys():
        # get only CN from subject
        match = re.search('(?<=CN=)[^,]*', data['tls']['subject'])
        if match:
            hostname = match.group(0)

    if not hostname:
        return

    return traffic.update().values(
        app_hostname=domain_replace.replace(hostname),
        app_proto="tls",
    ).where(
        traffic.c.flow_id == data['flow_id']
    )


def handle_http(data, domain_replace, traffic):
    if 'hostname' not in data['http'].keys():
        return

    return traffic.update().values(
        app_hostname=domain_replace.replace(data['http']['hostname']),
        app_proto="http",
    ).where(
        traffic.c.flow_id == data['flow_id']
    )


def handle_flow_start(data, allowed_interfaces, dns_cache, domain_replace, traffic):
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
    hostname = dns_cache.get(mac, data['dest_ip'])
    if hostname:
        logging.debug('Got hostname from cached DNS: {}'.format(hostname))
        hostname = domain_replace.replace(hostname.lower())

    return traffic.insert().values(
        flow_id=data['flow_id'],
        start=timestamp2unixtime(data['flow']['start']),
        src_mac=mac,
        src_ip=data['src_ip'],
        src_port=data['src_port'],
        dest_ip=data['dest_ip'],
        dest_port=data['dest_port'],
        proto=data['proto'],
        app_proto=data['app_proto'],
        app_hostname=hostname,
    )


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
