import pytest

from pakon import ROOT_PATH, PROJECT_ROOT
from pakon_api.utils import load_leases


def test_path():
    assert ROOT_PATH == PROJECT_ROOT / "tests" / "root"


def test_leases():
    leases = load_leases()
    assert leases["192.168.1.218"]["mac"] == "40:e6:57:23:97:2c"
    _ = leases