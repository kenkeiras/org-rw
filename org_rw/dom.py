from typing import List, Optional, Union


class DrawerNode:
    def __init__(self):
        self.children = []

    def append(self, child):
        self.children.append(child)


class PropertyDrawerNode(DrawerNode):
    def __repr__(self):
        return "<Properties: {}>".format(len(self.children))


class LogbookDrawerNode(DrawerNode):
    def __repr__(self):
        return "<LogBook: {}>".format(len(self.children))


class ResultsDrawerNode(DrawerNode):
    def __repr__(self):
        return "<Results: {}>".format(len(self.children))


class PropertyNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return "{{{}: {}}}".format(self.key, self.value)


class ListGroupNode:
    def __init__(self):
        self.children = []

    def append(self, child):
        self.children.append(child)

    def get_raw(self):
        return '\n'.join([c.get_raw() for c in self.children])

    def __repr__(self):
        return "<List: {}>".format(len(self.children))

class TableNode:
    def __init__(self):
        self.children = []

    def append(self, child):
        self.children.append(child)

    def __repr__(self):
        return "<Table: {}>".format(len(self.children))

class TableSeparatorRow:
    def __init__(self, orig=None):
        self.orig = orig

class TableRow:
    def __init__(self, cells, orig=None):
        self.cells = cells
        self.orig = orig

class Text:
    def __init__(self, content):
        self.content = content

    def get_raw(self):
        return ''.join(self.content.get_raw())


class ListItem:
    def __init__(self, tag, content, orig=None):
        self.tag = tag
        self.content = content
        self.orig = orig

    def get_raw(self):
        return get_raw_contents(self.orig)


class BlockNode:
    def __init__(self):
        self.children = []

    def append(self, child):
        self.children.append(child)


class CodeBlock(BlockNode):
    def __init__(self, header, subtype, arguments):
        super().__init__()
        self.header = header
        self.lines: Optional[List] = None
        self.subtype = subtype
        self.arguments = arguments

    def set_lines(self, lines):
        self.lines = lines

    def __repr__(self):
        return "<Code: {}>".format(len(self.lines or []))

DomNode = Union[DrawerNode,
                PropertyNode,
                ListGroupNode,
                TableNode,
                TableSeparatorRow,
                TableRow,
                Text,
                ListItem,
                BlockNode,
                ]

ContainerDomNode = Union[DrawerNode,
                         ListGroupNode,
                         TableNode,
                         BlockNode,
                         ]

from .utils import get_raw_contents
