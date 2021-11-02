from xml.sax.handler import ContentHandler
from xml.sax import parseString

import json


def _cast_to_int(val):
    """Try to cast value to <int>, return string otherwise."""
    try:
        return int(val), int
    except ValueError:
        return val, str


class Array(list):
    """Helper class that enables to call ``dump()`` onto its elements."""
    def __init__(self, li) -> None:
        super().__init__(li)

    def dump(self):
        return [i.dump() for i in self]


class Element:
    """XML element basic class."""

    def __init__(self, parent, name="", attrs=None, def_val=None) -> None:
        self.name = name
        self.parent = parent
        self.children = {}
        if attrs:
            self.attrs = dict(attrs)
        self.value = def_val

    def __repr__(self) -> str:
        _value = ""
        """Debug purposes"""
        try:
            _attrs = f", attrs: {self.attrs}"
        except AttributeError:
            _attrs = ""
        if self.value:
            _value = f", value: {self.value}"
        return f"<Element {self.name}{_attrs}, {self.children.keys()}{_value}>"

    def dump(self):
        """Output json like structure."""
        if self.value or self.value == 0:
            return self.value
        else:
            retval = {key: val.dump() for key, val in self.children.items()}
            try:
                if self.attrs:
                    retval.update(self.attrs)
            except AttributeError:
                pass
            return retval

    def append_self_to_parent(self):
        if self.parent:
            self.parent.update_children(self)

    def update_children(self, item):
        _name = item.name
        if item.name in self.children.keys():
            # key is already present in children dict
            _child = self.children[_name]
            if isinstance(_child, Array):
                # value is already Array type (do not use list, we need to dump the result)
                _child.append(item)
            elif isinstance(_child, Element):
                # value is not a list, conform the value to list than
                previous = _child
                del _child
                self.children[_name] = Array([previous, item])
        else:
            self.children[_name] = item

    def set_children_as_attributes(self):
        """Allows to access children via class attributes
        example: ``Element.key`` is the same as ``Element.children[key]``."""
        try:
            if self.attrs:
                for k, v in self.attrs.items():
                    self.__setattr__(k, v)
        except AttributeError:  # self.attribs may not be present, refer to __init__()
            pass

        if self.children:
            for k, v in self.children.items():
                self.__setattr__(k, v)


class FlowHandler(ContentHandler):
    """Handler parses elements to hirerarchy of `Element` classes."""

    def __init__(self, callback) -> None:
        super().__init__()
        self.current = callback

    def startElement(self, name, attrs):  # handle start of an alement
        parent = self.current  # set current element to intermediate variable
        if name == "unreplied":  # this element requires special handling
            self.current = Element(parent, name, def_val=True)
        else:
            self.current = Element(parent, name, attrs)
        self.current.append_self_to_parent()  # assign current element as child to parent

    def endElement(self, name):  # handle end of an element
        self.current = self.current.parent
        self.current.set_children_as_attributes()

    def characters(self, content):
        _content = content.strip().strip("\n")
        if _content == "":  # formatted XML presents issue with non empty content
            pass
        else:
            self.current.value, self.value_type = _cast_to_int(_content)


class Parser():
    """Class to help parse the xml, holds the parsing process result."""
    def __init__(self):
        self.root = Element(None, "XML")  # essantial class that is exposed to user
    
    def parse(self, xmlstring):
        parseString(xmlstring, FlowHandler(self.root))

    def jsonify(self, indent=2):
        return json.dumps(self.root.dump(), indent=indent)
    
    def dictify(self):
        return json.loads(self.jsonify())
    

if __name__ == "__main__":
    with open("example.xml", "r") as f:
        p = Parser()
        p.parse(f.readlines()[0])
        print(p.jsonify())
