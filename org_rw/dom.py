class PropertyDrawerNode:
    def __init__(self):
        self.children = []

    def append(self, child):
        self.children.append(child)

    def __repr__(self):
        return "<Properties: {}>".format(len(self.children))


class LogbookDrawerNode:
    def __init__(self):
        self.children = []

    def append(self, child):
        self.children.append(child)

    def __repr__(self):
        return "<LogBook: {}>".format(len(self.children))


class ResultsDrawerNode:
    def __init__(self):
        self.children = []

    def append(self, child):
        self.children.append(child)

    def __repr__(self):
        return "<Results: {}>".format(len(self.children))


class PropertyNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return "{{{}: {}}".format(self.key, self.value)


class ListGroupNode:
    def __init__(self):
        self.children = []

    def append(self, child):
        self.children.append(child)

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


class ListItem:
    def __init__(self, tag, content, orig=None):
        self.tag = tag
        self.content = content
        self.orig = orig


class BlockNode:
    def append(self, child):
        raise NotImplementedError()


class CodeBlock(BlockNode):
    def __init__(self, header, subtype):
        self.header = header
        self.lines = None
        self.subtype = subtype

    def set_lines(self, lines):
        self.lines = lines

    def __repr__(self):
        return "<Code: {}>".format(len(self.lines))
