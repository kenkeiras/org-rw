import collections
import unittest
from datetime import datetime

from org_rw import (Bold, Code, Italic, Line, Strike, Text, Underlined,
                    Verbatim, get_raw_contents)


def timestamp_to_datetime(ts):
    return datetime(ts.year, ts.month, ts.day, ts.hour, ts.minute)


def get_raw(doc):
    if isinstance(doc, str):
        return doc
    elif isinstance(doc, list):
        return "".join([get_raw(e) for e in doc])
    else:
        return doc.get_raw()


class Doc:
    def __init__(self, *, props=None, children=None):
        self.props = props
        self.children = children
        if isinstance(self.children, HL):
            self.children = [self.children]

    def assert_matches(self, test_case: unittest.TestCase, doc):
        # Check properties
        if self.props is None:
            test_case.assertEqual(len(doc.getProperties()), 0)
        else:
            doc_props = doc.getProperties()
            test_case.assertEqual(len(doc_props), len(self.props))

            for i, prop in enumerate(self.props):
                test_case.assertEqual(doc_props[i].key, prop[0])
                test_case.assertEqual(doc_props[i].value, prop[1])

        # @TODO: Check properties

        # Check children
        if self.children is None:
            test_case.assertEqual(len(doc.getTopHeadlines()), 0, "Top")
        else:
            doc_headlines = doc.getTopHeadlines()
            test_case.assertEqual(len(doc_headlines), len(self.children), "Top")

            for i, children in enumerate(self.children):
                children.assert_matches(test_case, doc_headlines[i])


class HL:
    def __init__(self, title, *, props=None, content=None, children=None):
        self.title = title
        self.props = props
        self.content = content
        self.children = children

    def assert_matches(self, test_case: unittest.TestCase, doc):
        test_case.assertEqual(self.title, doc.title)

        # Check properties
        if self.props is None:
            test_case.assertEqual(len(doc.properties), 0)
        else:
            doc_props = doc.properties
            test_case.assertEqual(len(doc_props), len(self.props))

            for i, prop in enumerate(self.props):
                test_case.assertEqual(doc_props[i].key, prop[0])
                if isinstance(prop[1], datetime):
                    test_case.assertEqual(
                        timestamp_to_datetime(doc_props[i].value), prop[1]
                    )

        test_case.assertEqual(get_raw_contents(doc), self.get_raw())

        # Check children
        if self.children is None:
            test_case.assertEqual(len(doc.children), 0)
        else:
            doc_headlines = doc.children
            test_case.assertEqual(len(doc_headlines), len(self.children), self.title)

            for i, children in enumerate(self.children):
                children.assert_matches(test_case, doc_headlines[i])

    def get_raw(self):
        return "".join(map(get_raw, self.content))


class SPAN:
    def __init__(self, *kwargs):
        self.contents = kwargs

    def get_raw(self):
        chunks = []
        for section in self.contents:
            if isinstance(section, str):
                chunks.append(section)
            elif isinstance(section, list):
                for subsection in section:
                    if isinstance(subsection, str):
                        chunks.append(subsection)
                    else:
                        chunks.append(subsection.get_raw())
            else:
                chunks.append(section.get_raw())

        return "".join(chunks)

    def assert_matches(self, test_case, doc):
        if not isinstance(doc, Line):
            return False
        for i, section in enumerate(self.contents):
            if isinstance(section, str):
                test_case.assertTrue(isinstance(doc.contents[i], Text))
                test_case.assertEqual(section, doc.contents[i].get_raw())
            else:
                section.assertEqual(test_case, doc.contents[i])


class BOLD:
    def __init__(self, text):
        self.text = text

    def get_raw(self):
        return "*{}*".format(get_raw(self.text))

    def assertEqual(self, test_case, other):
        test_case.assertTrue(isinstance(other, Bold))
        test_case.assertEqual(self.text, other.contents)


class CODE:
    def __init__(self, text):
        self.text = text

    def get_raw(self):
        return "~{}~".format(get_raw(self.text))

    def assertEqual(self, test_case, other):
        test_case.assertTrue(isinstance(other, Code))
        test_case.assertEqual(self.text, other.contents)


class ITALIC:
    def __init__(self, text):
        self.text = text

    def get_raw(self):
        return "/{}/".format(get_raw(self.text))

    def assertEqual(self, test_case, other):
        test_case.assertTrue(isinstance(other, Italic))
        test_case.assertEqual(self.text, other.contents)


class STRIKE:
    def __init__(self, text):
        self.text = text

    def get_raw(self):
        return "+{}+".format(get_raw(self.text))

    def assertEqual(self, test_case, other):
        test_case.assertTrue(isinstance(other, Strike))
        test_case.assertEqual(self.text, other.contents)


class UNDERLINED:
    def __init__(self, text):
        self.text = text

    def get_raw(self):
        return "_{}_".format(get_raw(self.text))

    def assertEqual(self, test_case, other):
        test_case.assertTrue(isinstance(other, Underlined))
        test_case.assertEqual(self.text, other.contents)


class VERBATIM:
    def __init__(self, text):
        self.text = text

    def get_raw(self):
        return "={}=".format(get_raw(self.text))

    def assertEqual(self, test_case, other):
        test_case.assertTrue(isinstance(other, Verbatim))
        test_case.assertEqual(self.text, other.contents)


class WEB_LINK:
    def __init__(self, text, link):
        self.text = text
        self.link = link

    def get_raw(self):
        if self.text:
            return "[[{}][{}]]".format(self.link, self.text)
        else:
            return "[[{}]]".format(self.link)

    def assertEqual(self, test_case, other):
        test_case.assertTrue(isinstance(other, WebLink))
        test_case.assertEqual(self.text, other.contents)
        test_case.assertEqual(self.link, other.link)


class Tokens:
    BOLD_END = "*"
    BOLD_START = "*"

    VERBATIM_START = "="
    VERBATIM_END = "="

    ITALIC_START = "/"
    ITALIC_END = "/"

    STRIKE_START = "+"
    STRIKE_END = "+"

    UNDERLINED_START = "_"
    UNDERLINED_END = "_"

    CODE_START = "~"
    CODE_END = "~"
