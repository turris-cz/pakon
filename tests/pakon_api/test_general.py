import pytest
from pakon import Config


from pakon.utils import load_leases, load_neighs


def test_path():
    assert Config.ROOT_PATH == Config.PROJECT_ROOT / "tests" / "root"


def test_neighbours():
    neighbours_map = load_neighs()
    assert neighbours_map["79f7:88ad:823c:9cf::cc3"] == "82:4a:1a:a0:3b:c5"


def test_leases():
    leases = load_leases()
    assert leases["192.168.1.218"]["mac"] == "40:e6:57:23:97:2c"
    _ = leases
