import json
import time
import datetime

from pakon import ROOT_PATH, PROJECT_ROOT
from subprocess import Popen, PIPE

_PATTERNS = ["%d-%m-%YT%H:%M:%S", "%d-%m-%Y"]


def _call_ubus_leases():
    proc = Popen(["ubus", "call", "dhcp", "ipv6leases"], stdout=PIPE)
    leases, err = proc.communicate()
    if err:
        #handle error
        res = None
    else:
        decoded = leases.decode()
        res = json.loads(decoded)
    return res


def _datetime_parse(string, fmt):
    """Parse to pattern in specific manner"""
    try:
        dt = datetime.datetime.strptime(string, fmt)
        return True, int(time.mktime(dt.timetuple()))
    except ValueError:
        return False, None


def _try_parse(timestr):
    """Iteratively figure out what pattern suits the situation"""
    for pat in _PATTERNS:
        success, retval = _datetime_parse(timestr, pat)
        if success:
            return retval
    return None


def json_query(query):
    """Helper function to conform time format and also provide json in string format with newline"""
    for key in ("start", "end"):
        if key in query:
            query[key] = _try_parse(query[key])
    js = json.dumps(query) + "\n"
    query = js.encode()
    return query


def load_schema():
    """Helper function to load query schema"""
    rv = {}
    with open(str(PROJECT_ROOT / "schema" / "pakon_query.json"), "r") as f:
        rv = json.load(f)
    return rv


def load_leases(network="br-lan"):
    leases = {}
    with open(str(ROOT_PATH / "tmp" / "dhcp.leases"), "r") as f:
        for line in f.readlines():
            timestamp, mac, ip, hostname, _ = line.strip().split(" ")
            leases[ip] = {
                        "hostname": hostname,
                        "mac": mac
                        }
    ipv6_leases = _call_ubus_leases()
    ipv6_leases = ipv6_leases.get('device').get(network).get("leases")
    for lease in ipv6_leases:
        _duid = lease.get('duid')
        addresses = lease.get('ipv6-addr')
        if not addresses:
            addresses = lease.get('ipv6-prefix')
        for address in addresses:
            if address:
                leases[address.get("address")] = {
                    "hostname": lease.get('hostname'),
                    "duid": _duid
                }
    return leases
