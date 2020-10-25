import logging
import re
import collections
from typing import List, Tuple

BASE_ENVIRONMENT = {
    'org-footnote-section': 'Footnotes',
    'org-options-keywords': (
        "ARCHIVE:",
        "AUTHOR:",
        "BIND:",
        "CATEGORY:",
        "COLUMNS:",
        "CREATOR:",
        "DATE:",
        "DESCRIPTION:",
        "DRAWERS:",
        "EMAIL:",
        "EXCLUDE_TAGS:",
        "FILETAGS:",
        "INCLUDE:",
        "INDEX:",
        "KEYWORDS:",
        "LANGUAGE:",
        "MACRO:",
        "OPTIONS:",
        "PROPERTY:",
        "PRIORITIES:",
        "SELECT_TAGS:",
        "SEQ_TODO:",
        "SETUPFILE:",
        "STARTUP:",
        "TAGS:"
        "TITLE:",
        "TODO:",
        "TYP_TODO:",
        "SELECT_TAGS:",
        "EXCLUDE_TAGS:"
    ),
}


HEADLINE_RE = re.compile(r'^(?P<stars>\*+) (?P<spacing>\s*)(?P<line>.*)$')
KEYWORDS_RE = re.compile(r'^(?P<indentation>\s*)#\+(?P<key>[^:\[]+)(\[(?P<options>[^\]]*)\])?:(?P<spacing>\s*)(?P<value>.*)$')
PROPERTY_DRAWER_RE = re.compile(r'^(?P<indentation>\s*):PROPERTIES:(?P<end_indentation>\s*)$')
DRAWER_END_RE = re.compile(r'^(?P<indentation>\s*):END:(?P<end_indentation>\s*)$')
NODE_PROPERTIES_RE = re.compile(r'^(?P<indentation>\s*):(?P<key>[^+:]+)(?P<plus>\+)?:(?P<spacing>\s*)(?P<value>.*)$')
RAW_LINE_RE = re.compile(r'^\s*([^\s#:*]|$)')
BASE_TIME_STAMP_RE = r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}) (?P<dow>[^ ]+)( (?P<start_hour>\d{1,2}):(?P<start_minute>\d{1,2})(--(?P<end_hour>\d{1,2}):(?P<end_minute>\d{1,2}))?)?'

ACTIVE_TIME_STAMP_RE = re.compile(r'<{}>'.format(BASE_TIME_STAMP_RE))
INACTIVE_TIME_STAMP_RE = re.compile(r'\[{}\]'.format(BASE_TIME_STAMP_RE))

# BASE_TIME_RANGE_RE = (r'(?P<start_year>\d{4})-(?P<start_month>\d{2})-(?P<start_day>\d{2}) (?P<start_dow>[^ ]+)((?P<start_hour>\d{1,2}):(?P<start_minute>\d{1,2}))?',
#                       r'(?P<end_year>\d{4})-(?P<end_month>\d{2})-(?P<end_day>\d{2}) (?P<end_dow>[^ ]+)((?P<end_hour>\d{1,2}):(?P<end_minute>\d{1,2}))?')

Headline = collections.namedtuple('Headline', ('start_line', 'depth',
                                               'orig',
                                               'properties', 'keywords',
                                               'priority_start', 'priority',
                                               'title_start', 'title',
                                               'tags_start', 'tags',
                                               'contents',
                                               'children',
                                               'structural',
))

RawLine = collections.namedtuple('RawLine', ('linenum', 'line'))
Keyword = collections.namedtuple('Keyword', ('linenum', 'match', 'key', 'value', 'options'))
Property = collections.namedtuple('Property', ('linenum', 'match', 'key', 'value', 'options'))

# @TODO How are [YYYY-MM-DD HH:mm--HH:mm] and ([... HH:mm]--[... HH:mm]) differentiated ?
# @TODO Consider recurrence annotations
TimeRange = collections.namedtuple('TimeRange', ('start_time', 'end_time'))
Timestamp = collections.namedtuple('Timestamp', ('active', 'year', 'month', 'day', 'dow', 'hour', 'minute'))

BEGIN_PROPERTIES = 'OPEN_PROPERTIES'
END_PROPERTIES = 'CLOSE_PROPERTIES'

def parse_org_time(value):
    if m := ACTIVE_TIME_STAMP_RE.match(value):
        active = True
    elif m := INACTIVE_TIME_STAMP_RE.match(value):
        active = False
    else:
        return None

    if m.group('end_hour'):
        return TimeRange(Timestamp(active, int(m.group('year')), int(m.group('month')), int(m.group('day')), m.group('dow'), int(m.group('start_hour')), int(m.group('start_minute'))),
                         Timestamp(active, int(m.group('year')), int(m.group('month')), int(m.group('day')), m.group('dow'), int(m.group('end_hour')), int(m.group('end_minute'))))
    return Timestamp(active, int(m.group('year')), int(m.group('month')), int(m.group('day')), m.group('dow'), int(m.group('start_hour')), int(m.group('start_minute')))

def timestamp_to_string(ts):
    date = '{year}-{month:02d}-{day:02d}'.format(
        year=ts.year,
        month=ts.month,
        day=ts.day
    )
    if ts.dow:
        date = date + ' ' + ts.dow

    if ts.hour is not None:
        base = '{date} {hour:02}:{minute:02d}'.format(date=date, hour=ts.hour, minute=ts.minute)
    else:
        base = date

    if ts.active:
        return '<{}>'.format(base)
    else:
        return '[{}]'.format(base)

def get_raw(doc):
    if isinstance(doc, str):
        return doc
    else:
        return doc.get_raw()

class Line:
    def __init__(self, linenum, contents):
        self.linenum = linenum
        self.contents = contents

    def get_raw(self):
        rawchunks = []
        for chunk in self.contents:
            if isinstance(chunk, str):
                rawchunks.append(chunk)
            else:
                rawchunks.append(chunk.get_raw())
        return ''.join(rawchunks) + '\n'

class Text:
    def __init__(self, contents, line):
        self.contents = contents
        self.linenum = line

    def get_raw(self):
        raw = ''.join(self.contents)
        return raw

class Bold:
    Marker = '*'

    def __init__(self, contents, line):
        self.contents = contents

    def get_raw(self):
        raw = ''.join(map(get_raw, self.contents))
        return f"{self.Marker}{raw}{self.Marker}"

class Code:
    Marker = '~'

    def __init__(self, contents, line):
        self.contents = contents

    def get_raw(self):
        raw = ''.join(map(get_raw, self.contents))
        return f"{self.Marker}{raw}{self.Marker}"

class Italic:
    Marker = '/'

    def __init__(self, contents, line):
        self.contents = contents

    def get_raw(self):
        raw = ''.join(map(get_raw, self.contents))
        return f"{self.Marker}{raw}{self.Marker}"

class Strike:
    Marker = '+'

    def __init__(self, contents, line):
        self.contents = contents

    def get_raw(self):
        raw = ''.join(map(get_raw, self.contents))
        return f"{self.Marker}{raw}{self.Marker}"

class Underlined:
    Marker = '_'

    def __init__(self, contents, line):
        self.contents = contents

    def get_raw(self):
        raw = ''.join(map(get_raw, self.contents))
        return f"{self.Marker}{raw}{self.Marker}"

class Verbatim:
    Marker = '='

    def __init__(self, contents, line):
        self.contents = contents

    def get_raw(self):
        raw = ''.join(map(get_raw, self.contents))
        return f"{self.Marker}{raw}{self.Marker}"


def is_pre(char: str) -> bool:
    if isinstance(char, str):
        return char in '\n\r\t -({\'"'
    else:
        return True

def is_marker(char: str) -> bool:
    if isinstance(char, str):
        return char in '*=/+_~'
    else:
        return False

def is_border(char: str) -> bool:
    if isinstance(char, str):
        return char not in '\n\r\t '
    else:
        return False

def is_body(char: str) -> bool:
    if isinstance(char, str):
        return True
    else:
        return False

def is_post(char: str) -> bool:
    if isinstance(char, str):
        return char in '-.,;:!?\')}["'
    else:
        return False

TOKEN_TYPE_TEXT = 0
TOKEN_TYPE_OPEN_MARKER = 1
TOKEN_TYPE_CLOSE_MARKER = 2

def tokenize_contents(contents: str):
    tokens = []
    last_char = None

    text = []
    closes = set()

    for i, char in enumerate(contents):
        has_changed = False

        if (
                (i not in closes)
                and is_marker(char)
                and is_pre(last_char)
                and ((i + 1 < len(contents))
                     and is_border(contents[i + 1]))):

            is_valid_mark = False
            # Check that is closed later
            text_in_line = True
            for j in range(i, len(contents) - 1):
                if contents[j] == '\n':
                    if not text_in_line:
                        break
                    text_in_line = False
                elif is_border(contents[j]) and contents[j + 1] == char:
                    is_valid_mark = True
                    closes.add(j + 1)
                    break
                else:
                    text_in_line |= is_body(contents[j])

            if is_valid_mark:
                if len(text) > 0:
                    tokens.append((TOKEN_TYPE_TEXT, ''.join(text)))
                    text = []
                tokens.append((TOKEN_TYPE_OPEN_MARKER, char))
                has_changed = True
        elif i in closes:
            if len(text) > 0:
                tokens.append((TOKEN_TYPE_TEXT, ''.join(text)))
                text = []
            tokens.append((TOKEN_TYPE_CLOSE_MARKER, char))
            has_changed = True

        if not has_changed:
            text.append(char)
        last_char = char

    if len(text) > 0:
        tokens.append((TOKEN_TYPE_TEXT, ''.join(text)))

    return tokens


def parse_contents(raw_contents:List[RawLine]):
    NO_MODE =         0b0
    BOLD_MODE =       0b1
    CODE_MODE =       0b10
    ITALIC_MODE =     0b100
    STRIKE_MODE =     0b1000
    UNDERLINED_MODE = 0b10000
    VERBATIM_MODE =   0b100000

    MARKERS = {
        '*': BOLD_MODE,
        '~': CODE_MODE,
        '/': ITALIC_MODE,
        '+': STRIKE_MODE,
        '_': UNDERLINED_MODE,
        '=': VERBATIM_MODE,
    }
    MODES = (
        (BOLD_MODE, Bold),
        (CODE_MODE, Code),
        (ITALIC_MODE, Italic),
        (STRIKE_MODE, Strike),
        (UNDERLINED_MODE, Underlined),
        (VERBATIM_MODE, Verbatim),
    )
    _MODES = {
        BOLD_MODE: Bold,
        CODE_MODE: Code,
        ITALIC_MODE: Italic,
        STRIKE_MODE: Strike,
        UNDERLINED_MODE: Underlined,
        VERBATIM_MODE: Verbatim,
    }

    mode = NO_MODE
    escaped = False

    chunk = []
    inline = []
    chunks = []

    linenum = start_linenum = raw_contents[0].linenum
    contents_buff = []
    for line in raw_contents:
        contents_buff.append(line.line)

    contents = '\n'.join(contents_buff)
    tokens = tokenize_contents(contents)

    # Use tokens to tag chunks of text with it's container type
    for (tok_type, tok_val) in tokens:
        if tok_type == TOKEN_TYPE_TEXT:
            chunks.append((mode, tok_val))
        elif tok_type == TOKEN_TYPE_OPEN_MARKER:
            mode = mode | MARKERS[tok_val]
        elif tok_type == TOKEN_TYPE_OPEN_MARKER:
            mode = mode ^ MARKERS[tok_val]

    # Convert those chunks to a tree
    def tree_for_tag(tag, in_mode):
        tree = []
        for (mask, mode) in MODES:
            if (mask & tag) and not (mask & in_mode):
                tree.append(mode)
        print(tree)
        if len(tree) == 0:
            return Text


    if len(raw_contents) > 0:
        current_line = raw_contents[0].linenum

    # tree = []
    # pos = []
    # print('\n'.join(map(str, chunks)))
    # for (tag, chunk) in chunks:
    #     if pos == []:
    #         tree.append(tree_for_tag(tag, NO_MODE)(chunk, line=current_line))
    #         pos.append(tree[-1])
    #     else:
    #         raise NotImplementedError()

    #     current_line += chunk.count('\n')


    tree = []
    mode_tree = []
    contents = []
    # Use tokens to tag chunks of text with it's container type
    for (tok_type, tok_val) in tokens:
        if tok_type == TOKEN_TYPE_TEXT:
            if len(mode_tree) == 0:
                tree.append(Text(tok_val, current_line))
            else:
                contents[-1].append(tok_val)

            current_line += chunk.count('\n')

        elif tok_type == TOKEN_TYPE_OPEN_MARKER:
            mode_tree.append(_MODES[MARKERS[tok_val]])
            contents.append([])

        elif tok_type == TOKEN_TYPE_CLOSE_MARKER:
            mode = _MODES[MARKERS[tok_val]]
            matching_mode = mode_tree.pop()
            assert mode == matching_mode
            value = mode(contents.pop(), current_line)
            current_line += chunk.count('\n')

            if len(mode_tree) == 0:  # Closed branch of tree
                tree.append(value)
            else:
                print("{} <- {}".format(mode_tree[-1], mode))
                contents[-1].append(value)

            current_line += chunk.count('\n')

    if len(tree) > 3:
        print("L", len(tree))
    print("F:", tree)
    return tree

def parse_headline(hl) -> Headline:
    stars = hl['orig'].group('stars')
    depth = len(stars)

    # TODO: Parse line for priority, cookies and tags
    line = hl['orig'].group('line')
    title = line.strip()
    contents = parse_contents(hl['contents'])

    return Headline(start_line=hl['linenum'],
                    depth=depth,
                    orig=hl['orig'],
                    title=title,
                    contents=contents,
                    children=[parse_headline(child) for child in hl['children']],
                    keywords=hl['keywords'],
                    properties=hl['properties'],
                    structural=hl['structural'],
                    title_start=None,
                    priority=None,
                    priority_start=None,
                    tags_start=None,
                    tags=None,
    )


class OrgDom:
    def __init__(self, headlines, keywords, contents):
        self.headlines: List[Headline] = list(map(parse_headline, headlines))
        self.keywords: List[Property] = keywords
        self.contents: List[RawLine] = contents

    def serialize(self):
        raise NotImplementedError()

    ## Querying
    def getProperties(self):
        return self.keywords

    def getTopHeadlines(self):
        return self.headlines

    # Writing
    def dump_kw(self, kw):
        options = kw.match.group('options')
        if not options:
            options = ''

        return (kw.linenum,
                '{indentation}#+{key}{options}:{spacing}{value}'.format(
                    indentation=kw.match.group('indentation'),
                    key=kw.key,
                    options=kw.options,
                    spacing=kw.match.group('spacing'),
                    value=kw.value,
                ))

    def dump_property(self, prop: Property):
        plus = prop.match.group('plus')
        if plus is None: plus = ''

        if isinstance(prop.value, Timestamp):
            value = timestamp_to_string(prop.value)
        else:
            value = prop.value

        return (prop.linenum, '{indentation}:{key}{plus}:{spacing}{value}'.format(
            indentation=prop.match.group('indentation'),
            key=prop.key,
            plus=plus,
            spacing=prop.match.group('spacing'),
            value=value,
        ))

    def dump_contents(self, raw):
        if isinstance(raw, RawLine):
            return (raw.linenum, raw.line)

        return (raw.linenum, raw.get_raw())

    def dump_structural(self, structural: Tuple):
        return (structural[0], structural[1])

    def dump_headline(self, headline):
        yield '*' * headline.depth + ' ' + headline.orig.group('spacing') + headline.title

        lines = []
        KW_T = 0
        CONTENT_T = 1
        PROPERTIES_T = 2
        STRUCTURAL_T = 3
        for keyword in headline.keywords:
            lines.append((KW_T, self.dump_kw(keyword)))

        for content in headline.contents:
            lines.append((CONTENT_T, self.dump_contents(content)))

        for prop in headline.properties:
            lines.append((PROPERTIES_T, self.dump_property(prop)))

        for struct in headline.structural:
            lines.append((STRUCTURAL_T, self.dump_structural(struct)))

        lines = sorted(lines, key=lambda x: x[1][0])

        structured_lines = []
        last_type = None
        for i, line in enumerate(lines):
            ltype = line[0]
            content = line[1][1]

            if ltype == PROPERTIES_T and last_type not in (STRUCTURAL_T, PROPERTIES_T):
                # No structural opening
                structured_lines.append(' ' * content.index(':') + ':PROPERTIES:\n')
                logging.warning("Added structural: ".format(line[1][0], structured_lines[-1].strip()))
            elif ltype not in (STRUCTURAL_T, PROPERTIES_T) and last_type == PROPERTIES_T:
                # No structural closing
                last_line = lines[i - 1][1][1]
                structured_lines.append(' ' * last_line.index(':') + ':END:\n')
                logging.warning("Added structural:{}: {}".format(line[1][0], structured_lines[-1].strip()))

            elif ltype != CONTENT_T:
                content = content + '\n'

            last_type = ltype
            structured_lines.append(content)

        yield ''.join(structured_lines)

        for child in headline.children:
            yield from self.dump_headline(child)

    def dump(self):
        lines = []
        for kw in self.keywords:
            lines.append(self.dump_kw(kw))

        for line in self.contents:
            lines.append(self.dump_contents(line))

        yield from map(lambda x: x[1], sorted(lines, key=lambda x: x[0]))

        for headline in self.headlines:
            yield from self.dump_headline(headline)

class OrgDomReader:

    def __init__(self):
        self.headlines: List[Headline] = []
        self.keywords: List[Property] = []
        self.headline_hierarchy: List[OrgDom] = []
        self.contents: List[RawLine] = []

    def finalize(self):
        return OrgDom(self.headlines, self.keywords, self.contents)

    ## Construction
    def add_headline(self, linenum: int, match: re.Match) -> int:
        # Position reader on the proper headline
        stars = match.group('stars')
        depth = len(stars)

        headline = {
            'linenum': linenum,
            'orig': match,
            'title': match.group('line'),
            'contents': [],
            'children': [],
            'keywords': [],
            'properties': [],
            'structural': [],
        }

        while (depth - 2) > len(self.headline_hierarchy):
            # Introduce structural headlines
            self.headline_hierarchy.append(None)
        while depth < len(self.headline_hierarchy):
            self.headline_hierarchy.pop()

        if depth == 1:
            self.headlines.append(headline)
        else:
            self.headline_hierarchy[-1]['children'].append(headline)
        self.headline_hierarchy.append(headline)


    def add_keyword_line(self, linenum: int, match: re.Match) -> int:
        options = match.group('options')
        kw = Keyword(linenum, match, match.group('key'), match.group('value'), options if options is not None else '')
        if len(self.headline_hierarchy) == 0:
            self.keywords.append(kw)
        else:
            self.headline_hierarchy[-1]['keywords'].append(kw)

    def add_raw_line(self, linenum: int, line: str) -> int:
        raw = RawLine(linenum, line)
        if len(self.headline_hierarchy) == 0:
            self.contents.append(raw)
        else:
            self.headline_hierarchy[-1]['contents'].append(raw)

    def add_property_drawer_line(self, linenum: int, line: str, match: re.Match) -> int:
        self.current_drawer = self.headline_hierarchy[-1]['properties']
        self.headline_hierarchy[-1]['structural'].append((linenum, line))

    def add_drawer_end_line(self, linenum: int, line: str, match: re.Match) -> int:
        self.current_drawer = None
        self.headline_hierarchy[-1]['structural'].append((linenum, line))

    def add_node_properties_line(self, linenum: int, match: re.Match) -> int:
        key = match.group('key')
        value = match.group('value').strip()

        if (value.count('>--<') == 1) or (value.count(']--[') == 1):
            # Time ranges with two different dates
            # @TODO properly consider "=> DURATION" section
            chunks = value.split('=').split('--')
            as_time_range = parse_org_time(chunks[0], chunks[1])
            if (as_time_range[0] is not None) and (as_time_range[1] is not None):
                value = TimeRange(as_time_range[0], as_time_range[1])
        elif as_time := parse_org_time(value):
            value = as_time

        self.current_drawer.append(Property(linenum, match, key, value, None))

    def read(self, s, environment):
        lines = s.split('\n')
        reader = enumerate(lines)

        for linenum, line in reader:
            if m := RAW_LINE_RE.match(line):
                self.add_raw_line(linenum, line)
            elif m := HEADLINE_RE.match(line):
                self.add_headline(linenum, m)
            elif m := KEYWORDS_RE.match(line):
                self.add_keyword_line(linenum, m)
            elif m := PROPERTY_DRAWER_RE.match(line):
                self.add_property_drawer_line(linenum, line, m)
            elif m := DRAWER_END_RE.match(line):
                self.add_drawer_end_line(linenum, line, m)
            elif m := NODE_PROPERTIES_RE.match(line):
                self.add_node_properties_line(linenum, m)
            else:
                raise NotImplementedError('{}: ‘{}’'.format(linenum, line))


def loads(s, environment=BASE_ENVIRONMENT, extra_cautious=False):
    doc = OrgDomReader()
    doc.read(s, environment)
    dom = doc.finalize()
    if extra_cautious:  # Check that all options can be properly re-serialized
        if dumps(dom) != s:
            raise NotImplementedError("Error re-serializing, file uses something not implemented")
    return dom


def load(f, environment=BASE_ENVIRONMENT, extra_cautious=False):
    return loads(f.read(), environment, extra_cautious)


def dumps(doc):
    dump = list(doc.dump())
    result = '\n'.join(dump)
    print(result)
    return result
