from xmlschema import validate as _validate, XMLSchema
from pakon import Config


_SCHEMA_PATH = Config.PROJECT_ROOT / "pakon/schema/flow_new_destroy.xsd"
_SCHEMA_OBJ = XMLSchema(str(_SCHEMA_PATH))


def validate_xml(xml: str):
    """Helper function"""
    return _validate(xml, _SCHEMA_OBJ)
