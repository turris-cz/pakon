from json.encoder import py_encode_basestring
import pytest
import xmlschema
from conftest import FLOW1, FLOW2, FLOW3, FLOW4, FLOW5, JSON1, JSON2, JSON3, JSON4
from pakon.utils.xml_flow_parser import Parser, Array

from pakon.utils.validation import validate_xml
from xmlschema import XMLSchemaValidationError


def test_attributes():
    """Test if parser parses flow to object with  necessary attributes"""
    xml = Parser()
    xml.parse(FLOW1)
    assert xml.root.flow.type == "new"
    assert isinstance(xml.root.flow.meta, Array)
    assert xml.root.flow.original.layer3.protoname == "ipv4"
    assert xml.root.flow.reply.layer3.src.value == "192.168.16.255"
    assert xml.root.flow.original.layer3.protoname == "ipv4"
    assert xml.root.flow.independent.id.value == 1657073971
    assert xml.root.flow.independent.unreplied.value == ""
    assert xml.root.flow.independent.timeout.value == 30


def test_port_attributes():
    """Test port attributes"""
    xml = Parser()
    xml.parse(FLOW3)
    assert xml.root.flow.reply.layer4.sport.value == 21027
    assert xml.root.flow.reply.layer4.dport.value == 60308


def test_counter_attributes():
    xml = Parser()
    xml.parse(FLOW4)
    assert xml.root.flow.original.counters.packets.value == 1
    assert xml.root.flow.original.counters.bytes.value == 648


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
    flow_dict = xml.dictify()['flow']
    assert {"meta","type"} == set(flow_dict.keys())
    meta0_layer3 = flow_dict["meta"][0]["layer3"]
    assert {"src","dst","protonum","protoname"} == set(meta0_layer3.keys())


def test_validation_error():
    with pytest.raises(XMLSchemaValidationError) as e:
        res = validate_xml(FLOW5)
    assert str(e.value) == 'failed validating \'icmp\' with XsdEnumerationFacets([\'tcp\', \'udp\']):\n\nReason: attribute protoname=\'icmp\': value must be one of [\'tcp\', \'udp\']\n\nSchema:\n\n  <xs:enumeration xmlns:xs="http://www.w3.org/2001/XMLSchema" value="tcp" />\n\nInstance:\n\n  <layer4 protonum="1" protoname="icmp" />\n\nPath: /flow/meta[1]/layer4\n'
    