import subprocess
import json

from pakon import Config


class Objson:  # json -> object
    """Dict structure to Object with attributes, used for handle dhcp traffic data."""

    def __init__(self, __data) -> None:
        self.__dict__ = {
            key: Objson(val) if isinstance(val, dict) else val
            for key, val in __data.items()
        }

    def __repr__(self) -> str:
        return str(self.__dict__)


def _generate_ip_mapping(mac_mapping):
    retval = {}
    for mac, data in mac_mapping.items():
        ipv4 = data.get("ipv4")
        if ipv4:
            retval[ipv4] = {"mac": mac, "hostname": data.get("hostname")}
        ipv6 = data.get("ipv6", [])
        if ipv6:
            for address in ipv6:
                retval[address] = {"mac": mac, "hostname": data.get("hostname")}
    return retval


class LeasesCache:
    """Provides `mac` <-> `ip` mapping both ways.
    Conntrack only shows ip addresses in flow, so we use ip as key to get mac address.
    In context of preparing the data for above we need to have mac address as starting point."""

    @staticmethod
    def _load_ipv6_leases():
        """This is actually not used, neccessary info lies in neighs"""
        proc = subprocess.Popen(
            [str(Config.ROOT_PATH / "bin" / "ubus"), "call", "dhcp", "ipv6leases"],
            stdout=subprocess.PIPE,
        )
        leases, err = proc.communicate()
        if err:
            # handle error
            res = None
        else:
            decoded = leases.decode()
            res = json.loads(decoded)
        return res

    @staticmethod
    def _load_ipv4_leases():
        with open(str(Config.ROOT_PATH / "tmp" / "dhcp.leases"), "r") as f:
            leases = {}
            for line in f.readlines():
                _, mac, ip, hostname, _ = line.strip().split(" ")
                leases[mac] = {"hostname": hostname, "ipv4": ip}
            return leases

    @staticmethod
    def _load_neighs():
        """Obtain mac address for ipv6 address using `/etc/hotplug.d/neigh/pakon-neigh.sh`"""
        addresses = {}
        with open(str(Config.ROOT_PATH / "var" / "run" / "pakon" / "neigh.cache")) as f:
            for line in f.readlines():
                v, k = line.strip().split(",")
                if v.find(":") > 0:  # dirty filter only ipv6
                    addresses[k] = v
        return addresses

    def __init__(self):
        self.mac_mapping = {}
        self.ip_mapping = {}
        self.update_data()

    def __generate_ip_mapping(self):
        self.ip_mapping = _generate_ip_mapping(self.mac_mapping)

    def update_data(self):
        # first and most reliable source is contemporary the `/tmp/dhcp.leases`
        self.mac_mapping = LeasesCache._load_ipv4_leases()
        # assign to each mac address corresponding ipv6 address `/var/run/pakon/neigh.cache`
        neighs = LeasesCache._load_neighs()
        for mac, ipv6 in neighs.items():
            current = self.mac_mapping.get(mac, {"ipv6": []}).get(
                "ipv6", []
            )  # do not override other addresses
            if mac in self.mac_mapping.keys():  # mac is already in ipv4 leases
                self.mac_mapping[mac]["ipv6"] = [*current, ipv6]
            else:
                self.mac_mapping[mac] = {"ipv6": [ipv6]}
        # than generate maping with `ip` addresses as keys
        self.__generate_ip_mapping()
