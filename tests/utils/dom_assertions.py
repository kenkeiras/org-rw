import collections
import unittest
from datetime import datetime


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
        test_case.assertEqual(self.title, doc['title'])

        # Check properties
        if self.props is None:
            test_case.assertEqual(len(doc['properties']), 0)
        else:
            doc_props = doc['properties']
            test_case.assertEqual(len(doc_props), len(self.props))

            for i, prop in enumerate(self.props):
                test_case.assertEqual(doc_props[i].key, prop[0])
                if isinstance(prop[1], datetime):
                    test_case.assertEqual(
                        timestamp_to_datetime(doc_props[i].value), prop[1])

        # @TODO: Check properties

        # Check children
        if self.children is None:
            test_case.assertEqual(len(doc['children']), 0)
        else:
            doc_headlines = doc['children']
            test_case.assertEqual(len(doc_headlines), len(self.children),
                                  self.title)

            for i, children in enumerate(self.children):
                children.assert_matches(test_case, doc_headlines[i])
