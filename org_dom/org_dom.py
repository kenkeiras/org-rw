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
                                               'keyword_start', 'keyword',
                                               'priority_start', 'priority',
                                               'title_start', 'title',
                                               'tags_start', 'tags',
                                               'content',
                                               'children',
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

class OrgDom:
    def __init__(self, headlines, keywords, contents):
        self.headlines: List[Headline] = headlines
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

    def dump_contents(self, raw: RawLine):
        return (raw.linenum, raw.line)

    def dump_structural(self, structural: Tuple):
        return (structural[0], structural[1])

    def dump_headline(self, headline):
        yield headline['orig'].group('stars') + ' ' + headline['orig'].group('spacing') + headline['orig'].group('line')

        lines = []
        KW_T = 0
        CONTENT_T = 1
        PROPERTIES_T = 2
        STRUCTURAL_T = 3
        for keyword in headline['keywords']:
            lines.append((KW_T, self.dump_kw(keyword)))

        for content in headline['contents']:
            lines.append((CONTENT_T, self.dump_contents(content)))

        for prop in headline['properties']:
            lines.append((PROPERTIES_T, self.dump_property(prop)))

        for struct in headline['structural']:
            lines.append((STRUCTURAL_T, self.dump_structural(struct)))

        lines = sorted(lines, key=lambda x: x[1][0])

        structured_lines = []
        last_type = None
        for i, line in enumerate(lines):
            ltype = line[0]
            content = line[1][1]

            if ltype == PROPERTIES_T and last_type not in (STRUCTURAL_T, PROPERTIES_T):
                # No structural opening
                structured_lines.append(' ' * content.index(':') + ':PROPERTIES:')
                logging.warning("Added structural: ".format(line[1][0], structured_lines[-1].strip()))
            elif ltype not in (STRUCTURAL_T, PROPERTIES_T) and last_type == PROPERTIES_T:
                # No structural closing
                last_line = lines[i - 1][1][1]
                structured_lines.append(' ' * last_line.index(':') + ':END:')
                logging.warning("Added structural:{}: {}".format(line[1][0], structured_lines[-1].strip()))

            last_type = ltype
            structured_lines.append(content)

        yield from structured_lines

        for child in headline['children']:
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
        depth = len(stars) - 1

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

        while (depth - 1) > len(self.headline_hierarchy):
            # Introduce structural headlines
            self.headline_hierarchy.append(None)
        while depth < len(self.headline_hierarchy):
            self.headline_hierarchy.pop()

        if depth == 0:
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
    result = '\n'.join(doc.dump())
    return result
