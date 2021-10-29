from typing import List, Tuple
from xml.etree import ElementTree as ET


# class Flow():
# pass
_prefix = """<?xml version="1.0"?>"""


def _cast_to_int(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return val


def _filter_split_layers(li: List[ET.Element]) -> Tuple[List[ET.Element], List[ET.Element]]:
    """If you need to seprate nodes with tags `layer[n]` from other nodes."""
    res = []
    rest = []
    for i, o in enumerate(li):
        if o.tag.startswith('layer'):
            res.append(o)
        else:
            rest.append(o)
    return res, rest


def _conform_children(li):
    return { i.tag : i.text
        for i in li
    }


class Base():
    """Base class to parse xml."""
    def __init__(self, root) -> None:
        self.root = root
        self.attribs = self.root.attrib
        self.name = self.root.tag
        
        self._attr_from_dict_(self.attribs)


    def __str__(self) -> str:
        return self.name
    
    def _attr_from_list_(self, children):
        for child in children:
            setattr(self, child.name, child)

    def _attr_from_dict_(self, dic):
        for key, val in dic.items():
            setattr(self, key, val)


class _ValueNode(Base):
    """End node with value."""
    def __init__(self, root) -> None:
        super().__init__(root)
        self.value = _cast_to_int(root.text)
    
    def value(self):
        return self.value

class _Layer(Base):
    """Layer node"""
    def __init__(self, root) -> None:
        super().__init__(root)
        self.data = [_ValueNode(i) for i in list(self.root)]

        self._attr_from_list_(self.data)


class _Meta(Base):
    """Meta node layer, name derived from direction xml attribute."""
    def __init__(self, root) -> None:
        super().__init__(root)
        _layers, _data = _filter_split_layers(list(self.root))
        self.layers =  [_Layer(i) for i in _layers]
        self.data = [_ValueNode(i) for i in _data]
        self.name = self.attribs['direction']

        self._attr_from_list_(self.layers)
        self._attr_from_list_(self.data)


    def __str__(self) -> str:
        self.attribs

class Flow(Base):
    """Base Flow class, resulting object."""
    def __init__(self, root) -> None:
        super().__init__(root)
        self.metas = [_Meta(i) for i in list(self.root)]

        self._attr_from_list_(self.metas)


xmls = []
with open('example.xml', 'r') as f:
    for line in f.readlines():
        et = ET.fromstring(_prefix + line)
        print(et)
        xmls.append(et)

if __name__ == "__main__":
    flow = Flow(xmls[0])
