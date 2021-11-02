from json.encoder import py_encode_basestring
import pytest
from conftest import FLOW1, FLOW2, FLOW3, FLOW4, JSON1, JSON2, JSON3, JSON4
from pakon.utils.xml_flow_parser import Parser, Array


def test_attributes():
    """Test if parser parses flow to object with  necessary attributes"""
    xml = Parser()
    xml.parse(FLOW1)
    assert xml.root.flow.type == "new"
    assert isinstance(xml.root.flow.meta, Array)
    assert xml.root.flow.meta[0].direction == "original"
    assert xml.root.flow.meta[0].layer3.protonum == "2"
    assert xml.root.flow.meta[1].layer3.src.value == "192.168.16.255"
    assert xml.root.flow.meta[2].id.value == 1657073971
    assert xml.root.flow.meta[2].unreplied.value == True
    assert xml.root.flow.meta[2].timeout.value == 30


def test_port_attributes():
    """Test port attributes"""
    xml = Parser()
    xml.parse(FLOW3)
    assert xml.root.flow.meta[1].layer4.sport.value == 21027
    assert xml.root.flow.meta[1].layer4.dport.value == 60308


def test_counter_attributes():
    xml = Parser()
    xml.parse(FLOW4)
    assert xml.root.flow.meta[0].counters.packets.value == 1
    assert xml.root.flow.meta[0].counters.bytes.value == 648


@pytest.mark.parametrize(
    "source,target", [(FLOW1, JSON1), (FLOW2, JSON2), (FLOW3, JSON3), (FLOW4, JSON4)]
)
def test_json(source, target):
    """Test Pareser.jsonify"""
    xml = Parser()
    xml.parse(source)
    assert xml.jsonify() == target


def test_dictify():
    """Testing Parser ability to make dictionary of result."""
    xml = Parser()
    xml.parse(FLOW1)
    flow = xml.dictify()['flow']
    assert {"meta","type"} == set(flow.keys())
    meta0_layer3 = flow["meta"][0]["layer3"]
    assert {"src","dst","protonum","protoname"} == set(meta0_layer3.keys())
    breakpoint()