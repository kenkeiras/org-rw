import collections
import unittest
from datetime import datetime

from org_dom import Line, Text, Bold, Code, Italic, Strike, Underlined, Verbatim, get_raw_contents


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
            if len(doc.contents) != len(self.content):
                print("Contents:", doc.contents)
                print("Expected:", self.content)
            test_case.assertEqual(len(doc.contents), len(self.content))
            for i, content in enumerate(self.content):
                content.assert_matches(test_case, doc.contents[i])

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

    def to_raw(self):
        return '*{}*'.format(self.text)

    def assertEqual(self, test_case, other):
        test_case.assertTrue(isinstance(other, Bold))
        test_case.assertEqual(self.text, other.contents)


class CODE:
    def __init__(self, text):
        self.text = text

    def to_raw(self):
        return '~{}~'.format(self.text)

    def assertEqual(self, test_case, other):
        test_case.assertTrue(isinstance(other, Code))
        test_case.assertEqual(self.text, other.contents)

class ITALIC:
    def __init__(self, text):
        self.text = text

    def to_raw(self):
        return '/{}/'.format(self.text)

    def assertEqual(self, test_case, other):
        test_case.assertTrue(isinstance(other, Italic))
        test_case.assertEqual(self.text, other.contents)

class STRIKE:
    def __init__(self, text):
        self.text = text

    def to_raw(self):
        return '+{}+'.format(self.text)

    def assertEqual(self, test_case, other):
        test_case.assertTrue(isinstance(other, Strike))
        test_case.assertEqual(self.text, other.contents)


class UNDERLINED:
    def __init__(self, text):
        self.text = text

    def to_raw(self):
        return '_{}_'.format(self.text)

    def assertEqual(self, test_case, other):
        test_case.assertTrue(isinstance(other, Underlined))
        test_case.assertEqual(self.text, other.contents)

class VERBATIM:
    def __init__(self, text):
        self.text = text

    def to_raw(self):
        return '={}='.format(self.text)

    def assertEqual(self, test_case, other):
        test_case.assertTrue(isinstance(other, Verbatim))
        test_case.assertEqual(self.text, other.contents)
