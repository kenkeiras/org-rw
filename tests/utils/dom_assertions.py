import collections
import unittest
from datetime import datetime

from org_dom import get_raw_contents


def timestamp_to_datetime(ts):
    return datetime(ts.year, ts.month, ts.day, ts.hour, ts.minute)


class Dom:
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
            test_case.assertEqual(len(doc_headlines), len(self.children),
                                  "Top")

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
                        timestamp_to_datetime(doc_props[i].value), prop[1])

        if isinstance(self.content, str):
            test_case.assertEqual(get_raw_contents(doc), self.content)
        else:
            test_case.assertEqual(len(doc.contents), len(self.content))
            for i, content in enumerate(self.content):
                test_case.assertEqual(get_raw_contents(doc.contents[i]),
                                      content.to_raw())

        # Check children
        if self.children is None:
            test_case.assertEqual(len(doc.children), 0)
        else:
            doc_headlines = doc.children
            test_case.assertEqual(len(doc_headlines), len(self.children),
                                  self.title)

            for i, children in enumerate(self.children):
                children.assert_matches(test_case, doc_headlines[i])


class SPAN:
    def __init__(self, *kwargs):
        self.contents = kwargs

    def to_raw(self):
        chunks = []
        for section in self.contents:
            if isinstance(section, str):
                chunks.append(section)
            else:
                chunks.append(section.to_raw())

        return ''.join(chunks)


class BOLD:
    def __init__(self, text):
        self.text = text

    def to_raw(self):
        return '*{}*'.format(self.text)


class CODE:
    def __init__(self, text):
        self.text = text

    def to_raw(self):
        return '~{}~'.format(self.text)


class ITALIC:
    def __init__(self, text):
        self.text = text

    def to_raw(self):
        return '/{}/'.format(self.text)


class STRIKE:
    def __init__(self, text):
        self.text = text

    def to_raw(self):
        return '+{}+'.format(self.text)


class UNDERLINED:
    def __init__(self, text):
        self.text = text

    def to_raw(self):
        return '_{}_'.format(self.text)


class VERBATIM:
    def __init__(self, text):
        self.text = text

    def to_raw(self):
        return '={}='.format(self.text)
