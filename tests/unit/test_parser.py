from json.encoder import py_encode_basestring
import pytest
from conftest import FLOW1, FLOW2, FLOW3, FLOW4
from pakon.utils.xml_flow_parser import Parser

def test_whatever():
    flow_root = Parser()
    flow_root.parse(FLOW1)
    breakpoint()

def test_json():
    pass