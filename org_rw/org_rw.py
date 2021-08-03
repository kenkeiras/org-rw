from __future__ import annotations

import collections
import difflib
import logging
import os
import re
import sys
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Generator, List, Tuple, Union

BASE_ENVIRONMENT = {
    "org-footnote-section": "Footnotes",
    "org-options-keywords": (
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
        "TAGS:" "TITLE:",
        "TODO:",
        "TYP_TODO:",
        "SELECT_TAGS:",
        "EXCLUDE_TAGS:",
    ),
}

DEFAULT_TODO_KEYWORDS = ["TODO"]
DEFAULT_DONE_KEYWORDS = ["DONE"]

HEADLINE_TAGS_RE = re.compile(r"((:(\w|[0-9_@#%])+)+:)\s*$")
HEADLINE_RE = re.compile(r"^(?P<stars>\*+)(?P<spacing>\s*)(?P<line>.*?)$")
KEYWORDS_RE = re.compile(
    r"^(?P<indentation>\s*)#\+(?P<key>[^:\[]+)(\[(?P<options>[^\]]*)\])?:(?P<spacing>\s*)(?P<value>.*)$"
)
DRAWER_START_RE = re.compile(r"^(?P<indentation>\s*):([^:]+):(?P<end_indentation>\s*)$")
DRAWER_END_RE = re.compile(r"^(?P<indentation>\s*):END:(?P<end_indentation>\s*)$", re.I)
NODE_PROPERTIES_RE = re.compile(
    r"^(?P<indentation>\s*):(?P<key>[^ ()+:]+)(?P<plus>\+)?:(?P<spacing>\s*)(?P<value>.+)$"
)
RAW_LINE_RE = re.compile(r"^\s*([^\s#:*]|$)")
BASE_TIME_STAMP_RE = r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})( ?(?P<dow>[^ ]+))?( (?P<start_hour>\d{1,2}):(?P<start_minute>\d{1,2})(-+(?P<end_hour>\d{1,2}):(?P<end_minute>\d{1,2}))?)?(?P<repetition> (?P<rep_mark>(\+|\+\+|\.\+|-|--))(?P<rep_value>\d+)(?P<rep_unit>[hdwmy]))?"
CLEAN_TIME_STAMP_RE = r"\d{4}-\d{2}-\d{2}( ?([^ ]+))?( (\d{1,2}):(\d{1,2})(-+(\d{1,2}):(\d{1,2}))?)?( (\+|\+\+|\.\+|-|--)\d+[hdwmy])?"

ACTIVE_TIME_STAMP_RE = re.compile(r"<{}>".format(BASE_TIME_STAMP_RE))
INACTIVE_TIME_STAMP_RE = re.compile(r"\[{}\]".format(BASE_TIME_STAMP_RE))
PLANNING_RE = re.compile(
    r"(?P<indentation>\s*)"
    + r"(SCHEDULED:\s*(?P<scheduled>[<\[]"
    + CLEAN_TIME_STAMP_RE
    + r"[>\]](--[<\[]"
    + CLEAN_TIME_STAMP_RE
    + r"[>\]])?)\s*"
    + r"|CLOSED:\s*(?P<closed>[<\[]"
    + CLEAN_TIME_STAMP_RE
    + r"[>\]](--[<\[]"
    + CLEAN_TIME_STAMP_RE
    + r"[>\]])?)\s*"
    + r"|DEADLINE:\s*(?P<deadline>[<\[]"
    + CLEAN_TIME_STAMP_RE
    + r"[>\]](--[<\[]"
    + CLEAN_TIME_STAMP_RE
    + r"[>\]])?)\s*"
    r")+\s*"
)
LIST_ITEM_RE = re.compile(
    r"(?P<indentation>\s*)((?P<bullet>[*\-+])|((?P<counter>\d|[a-zA-Z])(?P<counter_sep>[.)])))((?P<checkbox_indentation>)\[(?P<checkbox_value>[ Xx])\])?((?P<tag_indentation>\s*)(?P<tag>.*?)::)?(?P<content>.*)"
)

# Org-Babel
BEGIN_SRC_RE = re.compile(r"^\s*#\+BEGIN_SRC(?P<content>.*)$", re.I)
END_SRC_RE = re.compile(r"^\s*#\+END_SRC\s*$", re.I)
RESULTS_DRAWER_RE = re.compile(r"^\s*:results:\s*$", re.I)
CodeSnippet = collections.namedtuple("CodeSnippet", ("name", "content", "result"))


def get_tokens(value):
    if isinstance(value, Text):
        return value.contents
    if isinstance(value, RawLine):
        return [value.line]
    raise Exception("Unknown how to get tokens from: {}".format(value))


class RangeInRaw:
    def __init__(self, content, start_token, end_token):
        self._content = content
        self._start_id = id(start_token)
        self._end_id = id(end_token)

    def update_range(self, new_contents):
        # Find start token
        for start_idx, tok in enumerate(self._content.contents):
            if id(tok) == self._start_id:
                break
        else:
            raise Exception("Start token not found")

        # Find end token
        for offset, tok in enumerate(self._content.contents[start_idx:]):
            if id(tok) == self._end_id:
                break
        else:
            raise Exception("End token not found")

        # Remove old contents
        for i in range(1, offset):
            self._content.contents.pop(start_idx + 1)

        # Add new ones
        for i, element in enumerate(new_contents):
            self._content.contents.insert(start_idx + i + 1, element)


def get_links_from_content(content):
    in_link = False
    in_description = False
    link_value = []
    link_description = []

    for i, tok in enumerate(get_tokens(content)):
        if isinstance(tok, LinkToken):
            if tok.tok_type == LinkTokenType.OPEN_LINK:
                in_link = True
                open_link_token = tok
            elif tok.tok_type == LinkTokenType.OPEN_DESCRIPTION:
                in_description = True
            elif tok.tok_type == LinkTokenType.CLOSE:
                rng = RangeInRaw(content, open_link_token, tok)
                yield Link(
                    "".join(link_value),
                    "".join(link_description) if in_description else None,
                    rng,
                )
                in_link = False
                in_description = False
                link_value = []
                link_description = []
        elif isinstance(tok, str) and in_link:
            if in_description:
                link_description.append(tok)
            else:
                link_value.append(tok)


class Headline:
    def __init__(
        self,
        start_line,
        depth,
        orig,
        properties,
        keywords,
        priority_start,
        priority,
        title_start,
        title,
        state,
        tags_start,
        tags,
        contents,
        children,
        structural,
        delimiters,
        list_items,
        parent,
        is_todo,
        is_done,
        spacing,
    ):
        self.start_line = start_line
        self.depth = depth
        self.orig = orig
        self.properties = properties
        self.keywords = keywords
        self.priority_start = priority_start
        self.priority = priority
        self.title_start = title_start
        self.title = title
        self.state = state
        self.tags_start = tags_start
        self.shallow_tags = tags
        self.contents = contents
        self.children = children
        self.structural = structural
        self.delimiters = delimiters
        self.list_items = list_items
        self.parent = parent
        self.is_todo = is_todo
        self.is_done = is_done
        self.scheduled = None
        self.deadline = None
        self.closed = None
        self.spacing = spacing

        # Read planning line
        planning_line = self.get_element_in_line(start_line + 1)

        # Ignore if not found or is a structural line
        if planning_line is None or isinstance(planning_line, tuple):
            return

        if m := PLANNING_RE.match(planning_line.get_raw()):
            self._planning_indendation = m.group("indentation")
            self._planning_order = []

            keywords = ["SCHEDULED", "CLOSED", "DEADLINE"]
            plan = planning_line.get_raw().split("\n")[0]
            indexes = [(kw, plan.find(kw)) for kw in keywords]

            self._planning_order = [
                kw
                for (kw, idx) in sorted(
                    filter(lambda v: v[1] >= 0, indexes), key=lambda v: v[1]
                )
            ]

            if scheduled := m.group("scheduled"):
                self.scheduled = parse_time(scheduled)
            if closed := m.group("closed"):
                self.closed = parse_time(closed)
            if deadline := m.group("deadline"):
                self.deadline = parse_time(deadline)

            # Remove from contents
            self._remove_element_in_line(start_line + 1)

    def getLists(self):
        lists = []
        last_line = None

        for li in self.list_items:
            if last_line == li.linenum - 1:
                lists[-1].append(li)
            else:
                lists.append([li])

            last_line = li.linenum
        return lists

    def get_planning_line(self):
        if self.scheduled is None and self.closed is None and self.deadline is None:
            return None

        contents = [self._planning_indendation]

        for el in self._planning_order:
            if el == "SCHEDULED" and self.scheduled is not None:
                contents.append("SCHEDULED: {} ".format(self.scheduled.to_raw()))

            elif el == "CLOSED" and self.closed is not None:
                contents.append("CLOSED: {} ".format(self.closed.to_raw()))

            elif el == "DEADLINE" and self.deadline is not None:
                contents.append("DEADLINE: {} ".format(self.deadline.to_raw()))

        # Consider elements added (not present on planning order)
        if ("SCHEDULED" not in self._planning_order) and (self.scheduled is not None):
            contents.append("SCHEDULED: {} ".format(self.scheduled.to_raw()))

        if ("CLOSED" not in self._planning_order) and (self.closed is not None):
            contents.append("CLOSED: {} ".format(self.closed.to_raw()))

        if ("DEADLINE" not in self._planning_order) and (self.deadline is not None):
            contents.append("DEADLINE: {} ".format(self.deadline.to_raw()))

        return "".join(contents).rstrip()

    @property
    def id(self):
        return self.get_property("ID")

    @id.setter
    def id(self, value):
        self.set_property("ID", value)

    @property
    def clock(self):
        times = []
        for chunk in self.contents:
            for line in chunk.get_raw().split("\n"):
                content = line.strip()
                if not content.startswith("CLOCK:"):
                    continue

                time_seg = content[len("CLOCK:") :].strip()

                if "--" in time_seg:
                    # TODO: Consider duration
                    start, end = time_seg.split("=")[0].split("--")
                    as_time_range = parse_org_time_range(start, end)
                    parsed = as_time_range
                else:
                    parsed = OrgTime.parse(time_seg)
                times.append(parsed)

        return times

    @property
    def tags(self):
        if isinstance(self.parent, OrgDoc):
            return list(self.shallow_tags)
        else:
            return list(self.shallow_tags) + self.parent.tags

    def get_property(self, name: str, default=None):
        for prop in self.properties:
            if prop.key == name:
                return prop.value

        return default

    def set_property(self, name: str, value: str):
        for prop in self.properties:

            # A matching property is found, update it
            if prop.key == name:
                prop.value = value
                return

        # No matching property found, add it
        else:
            if len(self.properties) > 0:
                last_prop = self.properties[-1]
                last_line = last_prop.linenum
                last_match = last_prop.match
            else:
                last_line = 0
                last_match = None
            self.properties.append(
                Property(
                    linenum=last_line,
                    match=last_match,
                    key=name,
                    value=value,
                    options=None,
                )
            )

    def get_links(self):
        for content in self.contents:
            yield from get_links_from_content(content)

    def get_lines_between(self, start, end):
        for line in self.contents:
            if start <= line.linenum < end:
                yield "".join(line.contents)

    def get_contents(self, format):
        if format == "raw":
            lines = []
            for line in self.contents:
                lines.append(dump_contents(line))

            yield from map(lambda x: x[1], sorted(lines, key=lambda x: x[0]))
        else:
            raise NotImplementedError()

    def get_element_in_line(self, linenum):
        for line in self.contents:
            if linenum == line.linenum:
                return line

        for (s_lnum, struc) in self.structural:
            if linenum == s_lnum:
                return ("structural", struc)

    def _remove_element_in_line(self, linenum):
        found = None
        for i, line in enumerate(self.contents):
            if linenum == line.linenum:
                found = i
                break

        assert found is not None
        el = self.contents[found]
        assert isinstance(el, Text)

        raw = el.get_raw()
        if "\n" not in raw:
            # Remove the element found
            self.contents.pop(found)
        else:
            # Remove the first line
            self.contents[found] = parse_content_block(
                [RawLine(self.contents[found].linenum + 1, raw.split("\n", 1)[1])]
            )

    def get_structural_end_after(self, linenum):
        for (s_lnum, struc) in self.structural:
            if s_lnum > linenum and struc.strip().upper() == ":END:":
                return (s_lnum, struc)

    def get_code_snippets(self):
        inside_code = False

        sections = []

        for delimiter in self.delimiters:
            if delimiter.delimiter_type == DelimiterLineType.BEGIN_SRC:
                line_start = delimiter.linenum
                inside_code = True
            elif delimiter.delimiter_type == DelimiterLineType.END_SRC:
                inside_code = False
                start, end = line_start, delimiter.linenum

                lines = self.get_lines_between(start + 1, end)
                contents = "\n".join(lines)
                if contents.endswith("\n"):
                    # This is not ideal, but to avoid having to do this maybe
                    # the content parsing must be re-thinked
                    contents = contents[:-1]

                sections.append(
                    {
                        "line_first": start + 1,
                        "line_last": end - 1,
                        "content": contents,
                    }
                )
                line_start = None

        for kword in self.keywords:
            if kword.key.upper() == "RESULTS":
                for snippet in sections:
                    if kword.linenum > snippet["line_last"]:
                        result_first = self.get_element_in_line(kword.linenum + 1)

                        if isinstance(result_first, Text):
                            result = "\n".join(result_first.contents)
                            snippet["result"] = result

                            if result.strip().startswith(": "):
                                # Split lines and remove ':'
                                lines = result.split("\n")
                                s_result = []
                                for line in lines:
                                    if ": " not in line:
                                        break
                                    s_result.append(line.lstrip(" ")[2:])
                                snippet["result"] = "\n".join(s_result)
                        elif (
                            isinstance(result_first, tuple)
                            and len(result_first) == 2
                            and result_first[0] == "structural"
                            and result_first[1].strip().upper() == ":RESULTS:"
                        ):

                            (end_line, _) = self.get_structural_end_after(
                                kword.linenum + 1
                            )
                            contents = "\n".join(
                                self.get_lines_between(kword.linenum + 1, end_line)
                            )
                            indentation = result_first[1].index(":")
                            dedented = "\n".join(
                                [line[indentation:] for line in contents.split("\n")]
                            )
                            if dedented.endswith("\n"):
                                dedented = dedented[:-1]

                            snippet["result"] = dedented

                        break

        results = []
        for section in sections:
            name = None
            content = section["content"]
            code_result = section.get("result", None)
            results.append(CodeSnippet(name=name, content=content, result=code_result))

        return results


RawLine = collections.namedtuple("RawLine", ("linenum", "line"))
Keyword = collections.namedtuple(
    "Keyword", ("linenum", "match", "key", "value", "options")
)
Property = collections.namedtuple(
    "Property", ("linenum", "match", "key", "value", "options")
)

ListItem = collections.namedtuple(
    "ListItem",
    (
        "linenum",
        "match",
        "indentation",
        "bullet",
        "counter",
        "counter_sep",
        "checkbox_indentation",
        "checkbox_value",
        "tag_indentation",
        "tag",
        "content",
    ),
)

# @TODO How are [YYYY-MM-DD HH:mm--HH:mm] and ([... HH:mm]--[... HH:mm]) differentiated ?
# @TODO Consider recurrence annotations
class Timestamp:
    def __init__(self, active, year, month, day, dow, hour, minute, repetition=None):
        self.active = active
        self._year = year
        self._month = month
        self._day = day
        self.dow = dow
        self.hour = hour
        self.minute = minute
        self.repetition = repetition

    def to_datetime(self) -> Union[datetime, date]:
        if self.hour is not None:
            return datetime(self.year, self.month, self.day, self.hour, self.minute)
        else:
            return datetime(self.year, self.month, self.day, 0, 0)

    def __add__(self, delta: timedelta):
        as_dt = self.to_datetime()
        to_dt = as_dt + delta

        return Timestamp(
            self.active,
            year=to_dt.year,
            month=to_dt.month,
            day=to_dt.day,
            dow=None,
            hour=to_dt.hour if self.hour is not None or to_dt.hour != 0 else None,
            minute=to_dt.minute
            if self.minute is not None or to_dt.minute != 0
            else None,
            repetition=self.repetition,
        )

    def __eq__(self, other):
        if not isinstance(other, Timestamp):
            return False
        return (
            (self.active == other.active)
            and (self.year == other.year)
            and (self.month == other.month)
            and (self.day == other.day)
            and (self.dow == other.dow)
            and (self.hour == other.hour)
            and (self.minute == other.minute)
            and (self.repetition == other.repetition)
        )

    def __lt__(self, other):
        if not isinstance(other, Timestamp):
            return False
        return self.to_datetime() < other.to_datetime()

    def __gt__(self, other):
        if not isinstance(other, Timestamp):
            return False
        return self.to_datetime() > other.to_datetime()

    def __repr__(self):
        return timestamp_to_string(self)

    # Properties whose modification changes the Day-Of-Week
    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, value):
        self._year = value
        self.dow = None

    @property
    def month(self):
        return self._month

    @month.setter
    def month(self, value):
        self._month = value
        self.dow = None

    @property
    def day(self):
        return self._day

    @day.setter
    def day(self, value):
        self._day = value
        self.dow = None


class DelimiterLineType(Enum):
    BEGIN_SRC = 1
    END_SRC = 2


DelimiterLine = collections.namedtuple(
    "DelimiterLine", ("linenum", "line", "delimiter_type")
)


class MarkerType(Enum):
    NO_MODE = 0b0
    BOLD_MODE = 0b1
    CODE_MODE = 0b10
    ITALIC_MODE = 0b100
    STRIKE_MODE = 0b1000
    UNDERLINED_MODE = 0b10000
    VERBATIM_MODE = 0b100000


MARKERS = {
    "*": MarkerType.BOLD_MODE,
    "~": MarkerType.CODE_MODE,
    "/": MarkerType.ITALIC_MODE,
    "+": MarkerType.STRIKE_MODE,
    "_": MarkerType.UNDERLINED_MODE,
    "=": MarkerType.VERBATIM_MODE,
}

ModeToMarker = {}

for tok, mode in MARKERS.items():
    ModeToMarker[mode] = tok

MarkerToken = collections.namedtuple("MarkerToken", ("closing", "tok_type"))
LinkToken = collections.namedtuple("LinkToken", ("tok_type"))


class LinkTokenType(Enum):
    OPEN_LINK = 3
    OPEN_DESCRIPTION = 5
    CLOSE = 4


BEGIN_PROPERTIES = "OPEN_PROPERTIES"
END_PROPERTIES = "CLOSE_PROPERTIES"


def token_from_type(tok_type):
    return ModeToMarker[tok_type]


class TimeRange:
    def __init__(self, start_time: OrgTime, end_time: OrgTime):
        self.start_time = start_time
        self.end_time = end_time

    def to_raw(self) -> str:
        return timerange_to_string(self)

    @property
    def duration(self) -> timedelta:
        delta = self.end - self.start
        return delta

    @property
    def start(self) -> datetime:
        return self.start_time.time.to_datetime()

    @property
    def end(self) -> datetime:
        return self.end_time.time.to_datetime()


def parse_time(value: str) -> Union[None, TimeRange, OrgTime]:
    if (value.count(">--<") == 1) or (value.count("]--[") == 1):
        # Time ranges with two different dates
        # @TODO properly consider "=> DURATION" section
        start, end = value.split("=")[0].split("--")
        as_time_range = parse_org_time_range(start, end)
        if (as_time_range.start_time is not None) and (
            as_time_range.end_time is not None
        ):
            return as_time_range
        else:
            raise Exception("Unknown time range format: {}".format(value))
    elif as_time := OrgTime.parse(value):
        return as_time
    else:
        return None


def parse_org_time_range(start, end) -> TimeRange:
    return TimeRange(OrgTime.parse(start), OrgTime.parse(end))


class OrgTime:
    def __init__(self, ts: Timestamp, end_time: Union[Timestamp, None] = None):
        assert ts is not None
        self.time = ts
        self.end_time = end_time

    @property
    def duration(self):
        if self.end_time is None:
            return timedelta()  # No duration
        else:
            return self.end_time.to_datetime() - self.time.to_datetime()

    def to_raw(self):
        return timestamp_to_string(self.time, self.end_time)

    def __repr__(self):
        return f"OrgTime({self.to_raw()})"

    @classmethod
    def parse(self, value: str) -> OrgTime:
        if m := ACTIVE_TIME_STAMP_RE.match(value):
            active = True
        elif m := INACTIVE_TIME_STAMP_RE.match(value):
            active = False
        else:
            return None

        if m.group("end_hour"):
            return OrgTime(
                Timestamp(
                    active,
                    int(m.group("year")),
                    int(m.group("month")),
                    int(m.group("day")),
                    m.group("dow"),
                    int(m.group("start_hour")),
                    int(m.group("start_minute")),
                ),
                Timestamp(
                    active,
                    int(m.group("year")),
                    int(m.group("month")),
                    int(m.group("day")),
                    m.group("dow"),
                    int(m.group("end_hour")),
                    int(m.group("end_minute")),
                ),
            )

        return OrgTime(
            Timestamp(
                active,
                int(m.group("year")),
                int(m.group("month")),
                int(m.group("day")),
                m.group("dow"),
                int(m.group("start_hour")) if m.group("start_hour") else None,
                int(m.group("start_minute")) if m.group("start_minute") else None,
                m.group("repetition").strip() if m.group("repetition") else None,
            )
        )


def time_from_str(s: str) -> OrgTime:
    return OrgTime.parse(s)


def timerange_to_string(tr: TimeRange):
    return tr.start_time.to_raw() + "--" + tr.end_time.to_raw()


def timestamp_to_string(ts: Timestamp, end_time: Union[Timestamp, None] = None) -> str:
    date = "{year}-{month:02d}-{day:02d}".format(
        year=ts.year, month=ts.month, day=ts.day
    )
    if ts.dow:
        date = date + " " + ts.dow

    if ts.hour is not None:
        base = "{date} {hour:02}:{minute:02d}".format(
            date=date, hour=ts.hour, minute=ts.minute
        )
    else:
        base = date

    if end_time is not None:
        assert end_time.hour is not None
        assert end_time.minute is not None
        base = "{base}-{hour:02}:{minute:02d}".format(
            base=base, hour=end_time.hour, minute=end_time.minute
        )

    if ts.repetition:
        base = base + " " + ts.repetition

    if ts.active:
        return "<{}>".format(base)
    else:
        return "[{}]".format(base)


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
        return "".join(rawchunks) + "\n"


class Link:
    def __init__(self, value: str, description: str, origin: RangeInRaw):
        self._value = value
        self._description = description
        self._origin = origin

    def get_raw(self):
        if self.description:
            return "[[{}][{}]]".format(self.value, self.description)
        else:
            return "[[{}]]".format(self.value)

    def _update_content(self):
        new_contents = []
        new_contents.append(self._value)
        if self._description:
            new_contents.append(LinkToken(LinkTokenType.OPEN_DESCRIPTION))
            new_contents.append(self._description)
        self._origin.update_range(new_contents)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
        self._update_content()

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, new_description):
        self._description = new_description
        self._update_content()


class Text:
    def __init__(self, contents, line):
        self.contents = contents
        self.linenum = line

    def __repr__(self):
        return "{{Text line: {}; content: {} }}".format(self.linenum, self.contents)

    def get_raw(self):
        contents = []
        for chunk in self.contents:
            if isinstance(chunk, str):
                contents.append(chunk)
            elif isinstance(chunk, LinkToken):
                if chunk.tok_type == LinkTokenType.OPEN_LINK:
                    contents.append("[[")
                elif chunk.tok_type == LinkTokenType.OPEN_DESCRIPTION:
                    contents.append("][")
                else:
                    assert chunk.tok_type == LinkTokenType.CLOSE
                    contents.append("]]")
            else:
                assert isinstance(chunk, MarkerToken)
                contents.append(token_from_type(chunk.tok_type))
        return "".join(contents)


class Bold:
    Marker = "*"

    def __init__(self, contents, line):
        self.contents = contents

    def get_raw(self):
        raw = "".join(map(get_raw, self.contents))
        return f"{self.Marker}{raw}{self.Marker}"


class Code:
    Marker = "~"

    def __init__(self, contents, line):
        self.contents = contents

    def get_raw(self):
        raw = "".join(map(get_raw, self.contents))
        return f"{self.Marker}{raw}{self.Marker}"


class Italic:
    Marker = "/"

    def __init__(self, contents, line):
        self.contents = contents

    def get_raw(self):
        raw = "".join(map(get_raw, self.contents))
        return f"{self.Marker}{raw}{self.Marker}"


class Strike:
    Marker = "+"

    def __init__(self, contents, line):
        self.contents = contents

    def get_raw(self):
        raw = "".join(map(get_raw, self.contents))
        return f"{self.Marker}{raw}{self.Marker}"


class Underlined:
    Marker = "_"

    def __init__(self, contents, line):
        self.contents = contents

    def get_raw(self):
        raw = "".join(map(get_raw, self.contents))
        return f"{self.Marker}{raw}{self.Marker}"


class Verbatim:
    Marker = "="

    def __init__(self, contents, line):
        self.contents = contents

    def get_raw(self):
        raw = "".join(map(get_raw, self.contents))
        return f"{self.Marker}{raw}{self.Marker}"


def is_pre(char: str) -> bool:
    if isinstance(char, str):
        return char in "\n\r\t -({'\""
    else:
        return True


def is_marker(char: str) -> bool:
    if isinstance(char, str):
        return char in "*=/+_~"
    else:
        return False


def is_border(char: str) -> bool:
    if isinstance(char, str):
        return char not in "\n\r\t "
    else:
        return False


def is_body(char: str) -> bool:
    if isinstance(char, str):
        return True
    else:
        return False


def is_post(char: str) -> bool:
    if isinstance(char, str):
        return char in "-.,;:!?')}[\""
    else:
        return False


TOKEN_TYPE_TEXT = 0
TOKEN_TYPE_OPEN_MARKER = 1
TOKEN_TYPE_CLOSE_MARKER = 2
TOKEN_TYPE_OPEN_LINK = 3
TOKEN_TYPE_CLOSE_LINK = 4
TOKEN_TYPE_OPEN_DESCRIPTION = 5


def tokenize_contents(contents: str):
    tokens = []
    last_char = None

    text = []
    closes = set()
    in_link = False
    in_link_description = False
    last_link_start = 0

    def cut_string():
        nonlocal text
        nonlocal tokens

        if len(text) > 0:
            tokens.append((TOKEN_TYPE_TEXT, "".join(text)))
            text = []

    cursor = enumerate(contents)
    for i, char in cursor:
        has_changed = False

        # Possible link opening
        if char == "[":
            if (
                len(contents) > i + 3
                # At least 3 characters more to open and close a link
                and contents[i + 1] == "["
            ):
                close = contents.find("]", i)

                if close != -1 and contents[close + 1] == "]":
                    # Link with no description
                    cut_string()

                    in_link = True
                    tokens.append((TOKEN_TYPE_OPEN_LINK, None))
                    assert "[" == (next(cursor)[1])
                    last_link_start = i
                    continue
                if close != -1 and contents[close + 1] == "[":
                    # Link with description?

                    close = contents.find("]", close + 1)
                    if close != -1 and contents[close + 1] == "]":
                        # No match here means this is not an Org link
                        cut_string()

                        in_link = True
                        tokens.append((TOKEN_TYPE_OPEN_LINK, None))
                        assert "[" == (next(cursor)[1])
                        last_link_start = i
                        continue

        # Possible link close or open of description
        if char == "]" and in_link:
            if contents[i + 1] == "]":
                cut_string()

                tokens.append((TOKEN_TYPE_CLOSE_LINK, None))
                assert "]" == (next(cursor)[1])
                in_link = False
                in_link_description = False
                continue

            if contents[i + 1] == "[" and not in_link_description:
                cut_string()

                tokens.append((TOKEN_TYPE_OPEN_DESCRIPTION, None))
                assert "[" == (next(cursor)[1])
                continue

            raise Exception(
                "Link cannot contain ']' not followed by '[' or ']'. Starting with {}".format(
                    contents[last_link_start : i + 10]
                )
            )

        if in_link and not in_link_description:
            # Link's pointer have no formatting
            pass

        elif (
            (i not in closes)
            and is_marker(char)
            and is_pre(last_char)
            and ((i + 1 < len(contents)) and is_border(contents[i + 1]))
        ):

            is_valid_mark = False
            # Check that is closed later
            text_in_line = True
            for j in range(i, len(contents) - 1):
                if contents[j] == "\n":
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
                cut_string()
                tokens.append((TOKEN_TYPE_OPEN_MARKER, char))
                has_changed = True
        elif i in closes:
            cut_string()
            tokens.append((TOKEN_TYPE_CLOSE_MARKER, char))
            has_changed = True

        if not has_changed:
            text.append(char)
        last_char = char

    if len(text) > 0:
        tokens.append((TOKEN_TYPE_TEXT, "".join(text)))

    return tokens


def parse_contents(raw_contents: List[RawLine]):
    if len(raw_contents) == 0:
        return []

    blocks = []
    current_block = []

    for line in raw_contents:
        if len(current_block) == 0:
            # Seed the first block
            current_line = line.linenum
            current_block.append(line)
        else:
            if line.linenum == current_line + 1:
                # Continue with the current block
                current_line = line.linenum
                current_block.append(line)
            else:
                # Split the blocks
                blocks.append(current_block)
                current_line = line.linenum
                current_block = [line]

    # Check that the current block is not left behind
    if len(current_block) > 0:
        blocks.append(current_block)

    return [parse_content_block(block) for block in blocks]


def parse_content_block(raw_contents: List[RawLine]):
    contents_buff = []
    for line in raw_contents:
        contents_buff.append(line.line)

    contents = "\n".join(contents_buff)
    tokens = tokenize_contents(contents)
    current_line = raw_contents[0].linenum

    contents = []
    # Use tokens to tag chunks of text with it's container type
    for (tok_type, tok_val) in tokens:
        if tok_type == TOKEN_TYPE_TEXT:
            contents.append(tok_val)
        elif tok_type == TOKEN_TYPE_OPEN_MARKER:
            contents.append(MarkerToken(False, MARKERS[tok_val]))
        elif tok_type == TOKEN_TYPE_CLOSE_MARKER:
            contents.append(MarkerToken(True, MARKERS[tok_val]))
        elif tok_type == TOKEN_TYPE_OPEN_LINK:
            contents.append(LinkToken(LinkTokenType.OPEN_LINK))
        elif tok_type == TOKEN_TYPE_OPEN_DESCRIPTION:
            contents.append(LinkToken(LinkTokenType.OPEN_DESCRIPTION))
        elif tok_type == TOKEN_TYPE_CLOSE_LINK:
            contents.append(LinkToken(LinkTokenType.CLOSE))

    return Text(contents, current_line)


def dump_contents(raw):
    if isinstance(raw, RawLine):
        return (raw.linenum, raw.line)

    elif isinstance(raw, ListItem):
        return (raw.linenum, raw.match.group(0))

    return (raw.linenum, raw.get_raw())


def parse_headline(hl, doc, parent) -> Headline:
    stars = hl["orig"].group("stars")
    depth = len(stars)
    spacing = hl["orig"].group("spacing")

    # TODO: Parse line for priority, cookies and tags
    line = hl["orig"].group("line")
    hl_tags = HEADLINE_TAGS_RE.search(line)

    if hl_tags is None:
        tags = []
    else:
        tags = hl_tags.group(0)[1:-1].split(":")
        line = HEADLINE_TAGS_RE.sub("", line)

    hl_state = None
    title = line
    is_done = is_todo = False
    for state in doc.todo_keywords or []:
        if title.startswith(state + " "):
            hl_state = state
            title = title[len(state + " ") :]
            is_todo = True
            break
    else:
        for state in doc.done_keywords or []:
            if title.startswith(state + " "):
                hl_state = state
                title = title[len(state + " ") :]
                is_done = True
                break

    contents = parse_contents(hl["contents"])

    headline = Headline(
        start_line=hl["linenum"],
        depth=depth,
        orig=hl["orig"],
        title=title,
        state=hl_state,
        contents=contents,
        children=None,
        keywords=hl["keywords"],
        properties=hl["properties"],
        structural=hl["structural"],
        delimiters=hl["delimiters"],
        list_items=hl["list_items"],
        title_start=None,
        priority=None,
        priority_start=None,
        tags_start=None,
        tags=tags,
        parent=parent,
        is_todo=is_todo,
        is_done=is_done,
        spacing=spacing,
    )

    headline.children = [
        parse_headline(child, doc, headline) for child in hl["children"]
    ]
    return headline


class OrgDoc:
    def __init__(
        self, headlines, keywords, contents, list_items, structural, properties
    ):
        self.todo_keywords = DEFAULT_TODO_KEYWORDS
        self.done_keywords = DEFAULT_DONE_KEYWORDS

        for keyword in keywords:
            if keyword.key == "TODO":
                todo_kws, done_kws = re.sub(r"\(.\)", "", keyword.value).split("|", 1)

                self.todo_keywords = re.sub(r"\s{2,}", " ", todo_kws.strip()).split()
                self.done_keywords = re.sub(r"\s{2,}", " ", done_kws.strip()).split()

        self.keywords: List[Property] = keywords
        self.contents: List[RawLine] = contents
        self.list_items: List[ListItem] = list_items
        self.structural: List = structural
        self.properties: List = properties
        self._path = None
        self.headlines: List[Headline] = list(
            map(lambda hl: parse_headline(hl, self, self), headlines)
        )

    @property
    def path(self):
        return self._path

    ## Querying
    def get_links(self):
        for headline in self.headlines:
            yield from headline.get_links()

        for content in self.contents:
            yield from get_links_from_content(content)

    def get_keywords(self, name: str, default=None):
        for prop in self.keywords:
            if prop.key == name:
                return prop.value

        return default

    def get_property(self, name: str, default=None):
        for prop in self.properties:
            if prop.key == name:
                return prop.value

        return default

    def getProperties(self):
        return self.keywords

    def getTopHeadlines(self):
        return self.headlines

    def getAllHeadlines(self) -> Generator[Headline]:
        todo = self.headlines[::-1]  # We go backwards, to pop/append and go depth-first
        while len(todo) != 0:
            hl = todo.pop()
            todo.extend(hl.children[::-1])

            yield hl

    def get_code_snippets(self):
        for headline in self.headlines:
            yield from headline.get_code_snippets()

    # Writing
    def dump_kw(self, kw):
        options = kw.match.group("options")
        if not options:
            options = ""

        return (
            kw.linenum,
            "{indentation}#+{key}{options}:{spacing}{value}".format(
                indentation=kw.match.group("indentation"),
                key=kw.key,
                options=kw.options,
                spacing=kw.match.group("spacing"),
                value=kw.value,
            ),
        )

    def dump_property(self, prop: Property):
        plus = ""
        indentation = ""
        spacing = " "
        if prop.match is not None:
            plus = prop.match.group("plus")
            if plus is None:
                plus = ""
            indentation = prop.match.group("indentation")
            spacing = prop.match.group("spacing")

        if isinstance(prop.value, TimeRange):
            value = timerange_to_string(prop.value)
        elif isinstance(prop.value, OrgTime):
            value = prop.value.to_raw()
        else:
            value = prop.value

        return (
            prop.linenum,
            "{indentation}:{key}{plus}:{spacing}{value}".format(
                indentation=indentation,
                key=prop.key,
                plus=plus,
                spacing=spacing,
                value=value,
            ),
        )

    def dump_structural(self, structural: Tuple):
        return (structural[0], structural[1])

    def dump_delimiters(self, line: DelimiterLine):
        return (line.linenum, line.line)

    def dump_headline(self, headline):

        tags = ""
        if len(headline.shallow_tags) > 0:
            tags = ":" + ":".join(headline.shallow_tags) + ":"

        state = ""
        if headline.state:
            state = headline.state + " "

        yield "*" * headline.depth + headline.spacing + state + headline.title + tags

        planning = headline.get_planning_line()
        if planning is not None:
            yield planning

        lines = []
        KW_T = 0
        CONTENT_T = 1
        PROPERTIES_T = 2
        STRUCTURAL_T = 3
        for keyword in headline.keywords:
            lines.append((KW_T, self.dump_kw(keyword)))

        for content in headline.contents:
            lines.append((CONTENT_T, dump_contents(content)))

        for li in headline.list_items:
            lines.append((CONTENT_T, dump_contents(li)))

        for prop in headline.properties:
            lines.append((PROPERTIES_T, self.dump_property(prop)))

        for struct in headline.structural:
            lines.append((STRUCTURAL_T, self.dump_structural(struct)))

        for content in headline.delimiters:
            lines.append((STRUCTURAL_T, self.dump_delimiters(content)))

        lines = sorted(lines, key=lambda x: x[1][0])

        structured_lines = []
        last_type = None
        for i, line in enumerate(lines):
            ltype = line[0]
            content = line[1][1]

            if ltype == PROPERTIES_T and last_type not in (STRUCTURAL_T, PROPERTIES_T):
                # No structural opening
                structured_lines.append(" " * content.index(":") + ":PROPERTIES:\n")
                logging.warning(
                    "Added structural: ".format(
                        line[1][0], structured_lines[-1].strip()
                    )
                )
            elif (
                ltype not in (STRUCTURAL_T, PROPERTIES_T) and last_type == PROPERTIES_T
            ):
                # No structural closing
                last_line = lines[i - 1][1][1]
                structured_lines.append(" " * last_line.index(":") + ":END:\n")
                logging.warning(
                    "Added structural:{}: {}".format(
                        line[1][0], structured_lines[-1].strip()
                    )
                )

            content = content + "\n"
            last_type = ltype
            structured_lines.append(content)

        if len(structured_lines) > 0:
            content = "".join(structured_lines)

            # Remove the last line jump, which will be accounted for by the "yield operation"
            assert content.endswith("\n")
            content = content[:-1]
            yield content

        for child in headline.children:
            yield from self.dump_headline(child)

    def dump(self):
        lines = []
        for prop in self.properties:
            lines.append(self.dump_property(prop))

        for struct in self.structural:
            lines.append(self.dump_structural(struct))

        for kw in self.keywords:
            lines.append(self.dump_kw(kw))

        for line in self.contents:
            lines.append(dump_contents(line))

        for li in self.list_items:
            lines.append(dump_contents(li))

        yield from map(lambda x: x[1], sorted(lines, key=lambda x: x[0]))

        for headline in self.headlines:
            yield from self.dump_headline(headline)


class OrgDocReader:
    def __init__(self):
        self.headlines: List[Headline] = []
        self.keywords: List[Property] = []
        self.headline_hierarchy: List[OrgDoc] = []
        self.contents: List[RawLine] = []
        self.delimiters: List[DelimiterLine] = []
        self.list_items: List[ListItem] = []
        self.structural: List = []
        self.properties: List = []

    def finalize(self):
        return OrgDoc(
            self.headlines,
            self.keywords,
            self.contents,
            self.list_items,
            self.structural,
            self.properties,
        )

    ## Construction
    def add_headline(self, linenum: int, match: re.Match) -> int:
        # Position reader on the proper headline
        stars = match.group("stars")
        depth = len(stars)

        headline = {
            "linenum": linenum,
            "orig": match,
            "title": match.group("line"),
            "contents": [],
            "children": [],
            "keywords": [],
            "properties": [],
            "logbook": [],
            "structural": [],
            "delimiters": [],
            "results": [],  # TODO: Move to each specific code block?
            "list_items": [],
        }

        while (depth - 2) > len(self.headline_hierarchy):
            # Introduce structural headlines
            self.headline_hierarchy.append(None)
        while depth < len(self.headline_hierarchy):
            self.headline_hierarchy.pop()

        if depth == 1:
            self.headlines.append(headline)
        else:
            self.headline_hierarchy[-1]["children"].append(headline)
        self.headline_hierarchy.append(headline)

    def add_list_item_line(self, linenum: int, match: re.Match) -> int:
        li = ListItem(
            linenum,
            match,
            match.group("indentation"),
            match.group("bullet"),
            match.group("counter"),
            match.group("counter_sep"),
            match.group("checkbox_indentation"),
            match.group("checkbox_value"),
            match.group("tag_indentation"),
            match.group("tag"),
            match.group("content"),
        )

        if len(self.headline_hierarchy) == 0:
            self.list_items.append(li)
        else:
            self.headline_hierarchy[-1]["list_items"].append(li)

    def add_keyword_line(self, linenum: int, match: re.Match) -> int:
        options = match.group("options")
        kw = Keyword(
            linenum,
            match,
            match.group("key"),
            match.group("value"),
            options if options is not None else "",
        )
        if len(self.headline_hierarchy) == 0:
            self.keywords.append(kw)
        else:
            self.headline_hierarchy[-1]["keywords"].append(kw)

    def add_raw_line(self, linenum: int, line: str) -> int:
        raw = RawLine(linenum, line)
        if len(self.headline_hierarchy) == 0:
            self.contents.append(raw)
        else:
            self.headline_hierarchy[-1]["contents"].append(raw)

    def add_begin_src_line(self, linenum: int, match: re.Match) -> int:
        line = DelimiterLine(linenum, match.group(0), DelimiterLineType.BEGIN_SRC)
        if len(self.headline_hierarchy) == 0:
            self.delimiters.append(line)
        else:
            self.headline_hierarchy[-1]["delimiters"].append(line)

    def add_end_src_line(self, linenum: int, match: re.Match) -> int:
        line = DelimiterLine(linenum, match.group(0), DelimiterLineType.END_SRC)
        if len(self.headline_hierarchy) == 0:
            self.delimiters.append(line)
        else:
            self.headline_hierarchy[-1]["delimiters"].append(line)

    def add_property_drawer_line(self, linenum: int, line: str, match: re.Match) -> int:
        if len(self.headline_hierarchy) == 0:
            self.current_drawer = self.properties
            self.structural.append((linenum, line))
        else:
            self.current_drawer = self.headline_hierarchy[-1]["properties"]
            self.headline_hierarchy[-1]["structural"].append((linenum, line))

    def add_results_drawer_line(self, linenum: int, line: str, match: re.Match) -> int:
        self.current_drawer = self.headline_hierarchy[-1]["results"]
        self.headline_hierarchy[-1]["structural"].append((linenum, line))

    def add_logbook_drawer_line(self, linenum: int, line: str, match: re.Match) -> int:
        self.current_drawer = self.headline_hierarchy[-1]["logbook"]
        self.headline_hierarchy[-1]["structural"].append((linenum, line))

    def add_drawer_end_line(self, linenum: int, line: str, match: re.Match) -> int:
        self.current_drawer = None
        self.headline_hierarchy[-1]["structural"].append((linenum, line))

    def add_node_properties_line(self, linenum: int, match: re.Match) -> int:
        key = match.group("key")
        value = match.group("value").strip()

        if as_time := parse_time(value):
            value = as_time

        try:
            self.current_drawer.append(Property(linenum, match, key, value, None))
        except:
            if "current_drawer" not in dir(self):  # Throw a better error on this case
                raise Exception(
                    "Found properties before :PROPERTIES: line. Error on Org file?"
                )
            else:
                raise  # Let the exception pass

    def read(self, s, environment):
        lines = s.split("\n")
        line_count = len(lines)
        reader = enumerate(lines)

        for lnum, line in reader:
            linenum = lnum + 1
            try:
                if m := HEADLINE_RE.match(line):
                    self.add_headline(linenum, m)
                elif m := LIST_ITEM_RE.match(line):
                    self.add_list_item_line(linenum, m)
                elif m := RAW_LINE_RE.match(line):
                    self.add_raw_line(linenum, line)
                # Org-babel
                elif m := BEGIN_SRC_RE.match(line):
                    self.add_begin_src_line(linenum, m)
                elif m := END_SRC_RE.match(line):
                    self.add_end_src_line(linenum, m)
                # Generic properties
                elif m := KEYWORDS_RE.match(line):
                    self.add_keyword_line(linenum, m)
                elif m := DRAWER_START_RE.match(line):
                    self.add_property_drawer_line(linenum, line, m)
                elif m := DRAWER_END_RE.match(line):
                    self.add_drawer_end_line(linenum, line, m)
                elif m := RESULTS_DRAWER_RE.match(line):
                    self.add_results_drawer_line(linenum, line, m)
                elif m := NODE_PROPERTIES_RE.match(line):
                    self.add_node_properties_line(linenum, m)
                # Not captured
                else:
                    self.add_raw_line(linenum, line)
            except:
                logging.error("Error line {}: {}".format(linenum + 1, line))
                raise


def loads(s, environment=BASE_ENVIRONMENT, extra_cautious=True):
    reader = OrgDocReader()
    reader.read(s, environment)
    doc = reader.finalize()
    if extra_cautious:  # Check that all options can be properly re-serialized
        after_dump = dumps(doc)
        if after_dump != s:
            diff = list(
                difflib.Differ().compare(
                    s.splitlines(keepends=True), after_dump.splitlines(keepends=True)
                )
            )

            sys.stderr.writelines(diff)
            # print("---\n" + after_dump + "\n---")

            raise Exception("Difference found between existing version and dumped")
    return doc


def load(f, environment=BASE_ENVIRONMENT, extra_cautious=False):
    doc = loads(f.read(), environment, extra_cautious)
    doc._path = os.path.abspath(f.name)
    return doc


def dumps(doc):
    dump = list(doc.dump())
    result = "\n".join(dump)
    # print(result)
    return result


def dump(doc, fp):
    it = doc.dump()

    # Write first line separately
    line = next(it)
    fp.write(line)

    # Write following ones preceded by line jump
    for line in it:
        fp.write("\n" + line)
