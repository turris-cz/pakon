import subprocess
import json

from pakon import Config


def _call_ubus_leases():
    proc = subprocess.Popen([str(Config.ROOT_PATH / "bin" / "ubus"),"call","dhcp","ipv6leases"], stdout=subprocess.PIPE)
    leases, err = proc.communicate()
    if err:
        # handle error
        res = None
    else:
        decoded = leases.decode()
        res = json.loads(decoded)
    return res


class Objson:  # json -> object
    """Dict structure to Object with attributes"""
    def __init__(self, __data) -> None:
        self.__dict__= {
            key: Objson(val) if isinstance(val,dict)
            else val for key, val in __data.items()
        }

    def __repr__(self) -> str:
        return str(self.__dict__)


def load_leases(network="br-lan", ipv6=False):
    """Source for both ipv4 leases and ipv6"""
    leases = {}
    
    with open(str(Config.ROOT_PATH / "tmp" / "dhcp.leases"), "r") as f: # ipv4 leases
        for line in f.readlines():
            timestamp, mac, ip, hostname, _ = line.strip().split(" ")
            leases[ip] = {"hostname": hostname, "mac": mac}
    
    if ipv6:  # ipv6 leases
        ipv6_leases = _call_ubus_leases()
        ipv6_leases = ipv6_leases.get("device").get(network).get("leases")  # TODO: we may filter all the networks
        neighs = load_neighs()
        for lease in ipv6_leases:
            _duid = lease.get("duid")  # if no mac address
            addresses = lease.get("ipv6-addr")
            if not addresses:  # if there is no address, at least there is prefix
                addresses = lease.get("ipv6-prefix")
            for address in addresses:
                if address:
                    mac = neighs.get(address.get("address"), _duid)
                    leases[address.get("address")] = {
                        "hostname": lease.get("hostname"),
                        "mac": mac,
                    }
    return leases


def load_neighs():
    """Obtain mac address for ipv6 address using `/etc/hotplug.d/neigh/pakon-neigh.sh`"""
    addresses = {}
    with open(str(Config.ROOT_PATH / "var" / "run" / "pakon" / "neigh.cache")) as f:
        for line in f.readlines():
            k, v = line.strip().split(',')
            addresses.update({k:v})
    return addresses
