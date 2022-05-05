import json
import time
import datetime

from pakon import ROOT_PATH, PROJECT_ROOT
from subprocess import Popen, PIPE



def _call_ubus_leases():
    proc = Popen(["ubus", "call", "dhcp", "ipv6leases"], stdout=PIPE)
    leases, err = proc.communicate()
    if err:
        # handle error
        res = None
    else:
        decoded = leases.decode()
        res = json.loads(decoded)
    return res


def json_query(query):
    """Helper function to conform time format and also provide json in string format with newline"""
    js = json.dumps(query, indent=2) + "\n"
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
            leases[ip] = {"hostname": hostname, "mac": mac}
    ipv6_leases = _call_ubus_leases()
    ipv6_leases = ipv6_leases.get("device").get(network).get("leases")
    for lease in ipv6_leases:
        _duid = lease.get("duid")
        addresses = lease.get("ipv6-addr")
        if not addresses:
            addresses = lease.get("ipv6-prefix")
        for address in addresses:
            if address:
                leases[address.get("address")] = {
                    "hostname": lease.get("hostname"),
                    "duid": _duid,
                }
    return leases
