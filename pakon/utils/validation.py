from xmlschema import validate as _validate, XMLSchema 
from pakon import PROJECT_ROOT


_SCHEMA_PATH = PROJECT_ROOT / "schema/flow_new_destroy.xsd"
_SCHEMA_OBJ = XMLSchema(str(_SCHEMA_PATH))


def validate_xml(xml:str):
    """Helper function"""
    return _validate(xml, _SCHEMA_OBJ)
