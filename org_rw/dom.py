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
        return "<Properties: {}>".format(len(self.children))


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


class Text:
    def __init__(self, content):
        self.content = content


class ListItem:
    def __init__(self, content):
        self.content = content


class BlockNode:
    def append(self, child):
        raise NotImplementedError()


class CodeBlock(BlockNode):
    def __init__(self, header):
        self.header = header
        self.lines = []

    def append(self, child):
        self.lines.append(child)

    def __repr__(self):
        return "<Code: {}>".format(len(self.lines))
