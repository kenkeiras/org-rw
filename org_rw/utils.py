import uuid

from .org_rw import (Bold, Code, Headline, Italic, Line, RawLine, ListItem, Strike, Text,
                     Underlined, Verbatim)

from .org_rw import dump_contents


def get_hl_raw_contents(doc: Headline) -> str:
    lines = []
    for content in doc.contents:
        lines.append(get_raw_contents(content))

    raw = "".join(lines)
    return raw


def get_rawline_contents(doc: RawLine) -> str:
    return doc.line


def get_span_contents(doc: Line) -> str:
    return doc.get_raw()


def get_text_contents(doc: Text) -> str:
    return doc.get_raw()


def get_raw_contents(doc) -> str:
    if isinstance(doc, Headline):
        return get_hl_raw_contents(doc)
    if isinstance(doc, RawLine):
        return get_rawline_contents(doc)
    if isinstance(doc, Line):
        return get_span_contents(doc)
    if isinstance(doc, list):
        return "".join([get_raw_contents(chunk) for chunk in doc])
    if isinstance(doc, (Text, Bold, Code, Italic, Strike, Underlined, Verbatim)):
        return doc.get_raw()
    if isinstance(doc, ListItem):
        return dump_contents(doc)[1]
    print("Unhandled type: " + str(doc))
    raise NotImplementedError("Unhandled type: " + str(doc))


def random_id() -> str:
    return str(uuid.uuid4())
