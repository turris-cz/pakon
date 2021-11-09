from xmlschema import validate as _validate, XMLSchema 

_SCHEMA_PATH = "schema/flow_new_destroy.xsd"
_SCHEMA_OBJ = XMLSchema(_SCHEMA_PATH)

def validate_xml(xml:str):
    return _validate(xml, _SCHEMA_OBJ)
