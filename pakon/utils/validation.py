from xmlschema import validate as _validate, XMLSchema 
from pakon import ROOT_PATH


_SCHEMA_PATH = ROOT_PATH / "schema/flow_new_destroy.xsd"
_SCHEMA_OBJ = XMLSchema(str(_SCHEMA_PATH))


def validate_xml(xml:str):
    """Helper function"""
    return _validate(xml, _SCHEMA_OBJ)
