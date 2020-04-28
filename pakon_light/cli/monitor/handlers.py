#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

import datetime
import logging
import re
import time

from pakon_light.models.traffic import Traffic
from pakon_light.cli.monitor.utils import get_dev_mac


def handle_flow_start(data, allowed_interfaces, dns_cache, domain_replace):
    dev, mac = get_dev_mac(data['src_ip'])
    if data['proto'] not in ['TCP', 'UDP']:
        return None
    if 'app_proto' not in data.keys() or data['app_proto'] == 'failed':
        data['app_proto'] = '?'
    if data['app_proto'] == 'dns':
        return None
    if dev not in allowed_interfaces:
        logging.debug("This flow is not from allowed interface")
        return None
    hostname = dns_cache.get(mac, data['dest_ip'])
    if hostname:
        logging.debug('Got hostname from cached DNS: {}'.format(hostname))
        hostname = domain_replace.replace(hostname.lower())

    return Traffic(
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


def handle_flow(data):
    if data['proto'] not in ['TCP', 'UDP']:
        return None

    return {
        'duration': int(timestamp2unixtime(data['flow']['end']) - timestamp2unixtime(data['flow']['start'])),
        'app_proto': data['app_proto'],
        'bytes_send': data['flow']['bytes_toserver'],
        'bytes_received': data['flow']['bytes_toclient'],
        'flow_id': None
    }


def handle_tls(data, domain_replace):
    hostname = ''
    if 'sni' in data['tls'].keys():
        hostname = data['tls']['sni']
    elif 'subject' in data['tls'].keys():
        # get only CN from subject
        match = re.search('(?<=CN=)[^,]*', data['tls']['subject'])
        if match:
            hostname = match.group(0)

    if not hostname:
        return None

    return {
        'app_hostname': domain_replace.replace(hostname),
        'app_proto': "tls",
    }


def handle_http(data, domain_replace):
    if 'hostname' not in data['http'].keys():
        return None

    return {
        'app_hostname': domain_replace.replace(data['http']['hostname']),
        'app_proto': "http",
    }


def timestamp2unixtime(timestamp):
    # converts textual timestamp to unixtime
    # time string is always assumed to be in local time, the timezone part in string is ignored
    # reason is that mktime ignores timezone in datetime object and I don't see any easy way how
    # to do it properly (without pytz)
    dt = datetime.datetime.strptime(timestamp[:-5], '%Y-%m-%dT%H:%M:%S.%f')
    timestamp = float(time.mktime(dt.timetuple())) + float(dt.microsecond) / 1000000
    return timestamp
