from .org_dom import (
    Bold,
    Code,
    Headline,
    Italic,
    Line,
    RawLine,
    Strike,
    Text,
    Underlined,
    Verbatim,
)


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
    print("Unhandled type: " + str(doc))
    raise NotImplementedError("Unhandled type: " + str(doc))
