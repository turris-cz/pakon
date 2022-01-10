from pathlib import Path
import pytest
from pakon import Config


from pakon.dns_cache.utils import LeasesCache, AliasMapping


def test_path():
    assert Config.ROOT_PATH == Path("/tmp/pakon_root")

def test_neighbours():
    neighbours_map = LeasesCache._load_neighs()
    assert neighbours_map["82:4a:1a:a0:3b:c5"] == "79f7:88ad:823c:9cf::cc3"


def test_leases():
    leases = LeasesCache()
    assert leases.ip_mapping["192.168.1.218"]["mac"] == "40:e6:57:23:97:2c"
    assert leases.mac_mapping["ff:68:00:22:18:8c"]["hostname"] == "Lenovo-G580"


def test_aliases():
    m = AliasMapping()
    mic = m.get("something.at.github.com")
    assert mic == "github.com"
