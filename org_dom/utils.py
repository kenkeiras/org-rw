from .org_dom import Headline, RawLine


def get_hl_raw_contents(doc: Headline) -> str:
    lines = []

    for content in doc.contents:
        lines.append(get_raw_contents(content))

    return '\n'.join(lines)


def get_rawline_contents(doc: RawLine) -> str:
    return doc.line


def get_raw_contents(doc) -> str:
    if isinstance(doc, Headline):
        return get_hl_raw_contents(doc)
    if isinstance(doc, RawLine):
        return get_rawline_contents(doc)
    raise NotImplementedError('Unhandled type: ' + str(doc))
