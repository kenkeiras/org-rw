import re
import collections
from typing import List

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

Property = collections.namedtuple('Property', ('name', 'value', 'options'))
TimeRange = collections.namedtuple('TimeRange', ('start_time', 'end_time'))
Timestamp = collections.namedtuple('Timestamp', ('year', 'month', 'day', 'dow', 'hour', 'minute'))


def parse_org_time(value):
    if m := ACTIVE_TIME_STAMP_RE.match(value):
        active = True
    elif m := INACTIVE_TIME_STAMP_RE.match(value):
        active = False
    else:
        return None

    if m.group('end_hour'):
        return TimeRange(Timestamp(int(m.group('year')), int(m.group('month')), int(m.group('day')), m.group('dow'), int(m.group('start_hour')), int(m.group('start_minute'))),
                         Timestamp(int(m.group('year')), int(m.group('month')), int(m.group('day')), m.group('dow'), int(m.group('end_hour')), int(m.group('end_minute'))))
    return Timestamp(int(m.group('year')), int(m.group('month')), int(m.group('day')), m.group('dow'), int(m.group('start_hour')), int(m.group('start_minute')))


class OrgDom:
    def __init__(self, headlines, keywords):
        self.headlines: List[Headline] = headlines
        self.keywords: List[Property] = keywords

    def serialize(self):
        raise NotImplementedError()


    ## Querying
    def getProperties(self):
        return [
            Property(name=kw.group('key'),
                     value=kw.group('value'),
                     options=kw.group('options'),
            )
            for kw in self.keywords
        ]

    def getTopHeadlines(self):
        return self.headlines

class OrgDomReader:

    def __init__(self):
        self.headlines: List[Headline] = []
        self.keywords: List[Property] = []
        self.headline_hierarchy: List[OrgDom] = []

    def finalize(self):
        return OrgDom(self.headlines, self.keywords)

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
        if len(self.headline_hierarchy) == 0:
            self.keywords.append(match)
        else:
            self.headline_hierarchy[-1]['keywords'].append('match')

    def add_raw_line(self, linenum: int, line: str) -> int:
        print('>>', line)
        pass

    def add_property_drawer_line(self, linenum: int, match: re.Match) -> int:
        self.current_drawer = self.headline_hierarchy[-1]['properties']

    def add_drawer_end_line(self, linenum: int, match: re.Match) -> int:
        self.current_drawer = None

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

        self.current_drawer.append(Property(key, value, None))

    def read(self, s, environment):
        lines = s.split('\n')
        reader = enumerate(lines)

        for linenum, line in reader:
            if m := RAW_LINE_RE.match(line):
                # TODO: Parse line
                self.add_raw_line(linenum, line)
            elif m := HEADLINE_RE.match(line):
                # TODO: Parse headline
                self.add_headline(linenum, m)
            elif m := KEYWORDS_RE.match(line):
                # TODO: Parse line
                self.add_keyword_line(linenum, m)
            elif m := PROPERTY_DRAWER_RE.match(line):
                # TODO: Parse line
                self.add_property_drawer_line(linenum, m)
            elif m := DRAWER_END_RE.match(line):
                # TODO: Parse line
                self.add_drawer_end_line(linenum, m)
            elif m := NODE_PROPERTIES_RE.match(line):
                # TODO: Parse line
                self.add_node_properties_line(linenum, m)
            else:
                raise NotImplementedError('{}: ‘{}’'.format(linenum, line))


def loads(s, environment=BASE_ENVIRONMENT):
    doc = OrgDomReader()
    doc.read(s, environment)
    return doc.finalize()


def load(f, environment=BASE_ENVIRONMENT):
    return loads(f.read(), environment)
