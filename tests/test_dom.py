import logging
import os
import unittest
from datetime import datetime as DT

from org_dom import dumps, load, loads
from utils.dom_assertions import (BOLD, CODE, HL, ITALIC, SPAN, STRIKE,
                                  UNDERLINED, VERBATIM, Dom)

DIR = os.path.dirname(os.path.abspath(__file__))


class TestSerde(unittest.TestCase):
    def test_simple_file_01(self):
        with open(os.path.join(DIR, '01-simple.org')) as f:
            doc = load(f)

        ex = Dom(props=[('TITLE', '01-Simple'),
                        ('DESCRIPTION', 'Simple org file'),
                        ('TODO', 'TODO(t) PAUSED(p) |  DONE(d)')],
                 children=(HL(
                     'First level',
                     props=[
                         ('ID', '01-simple-first-level-id'),
                         ('CREATED', DT(2020, 1, 1, 1, 1)),
                     ],
                     content='  First level content\n',
                     children=[
                         HL('Second level',
                            props=[('ID', '01-simple-second-level-id')],
                            content='\n   Second level content\n',
                            children=[
                                HL('Third level',
                                   props=[('ID', '01-simple-third-level-id')],
                                   content='\n    Third level content\n')
                            ])
                     ])))

        ex.assert_matches(self, doc)

    def test_mimic_write_file_01(self):
        """A goal of this library is to be able to update a file without changing parts not directly modified."""
        with open(os.path.join(DIR, '01-simple.org')) as f:
            orig = f.read()
            doc = loads(orig)

        self.assertEqual(dumps(doc), orig)

    def test_markup_file_02(self):
        with open(os.path.join(DIR, '02-markup.org')) as f:
            doc = load(f)

        ex = Dom(props=[('TITLE', '02-Markup'),
                        ('DESCRIPTION', 'Simple org file to test markup'),
                        ('TODO', 'TODO(t) PAUSED(p) |  DONE(d)')],
                 children=(HL('First level',
                              props=[
                                  ('ID', '02-markup-first-level-id'),
                                  ('CREATED', DT(2020, 1, 1, 1, 1)),
                              ],
                              content=[
                                  SPAN("  This is a ", BOLD("bold phrase"),
                                       "."),
                                  SPAN(""),
                                  SPAN("  This is a ",
                                       VERBATIM("verbatim phrase"), "."),
                                  SPAN(""),
                                  SPAN("  This is a ", ITALIC("italic phrase"),
                                       "."),
                                  SPAN(""),
                                  SPAN("  This is a ",
                                       STRIKE("strike-through phrase"), "."),
                                  SPAN(""),
                                  SPAN("  This is a ",
                                       UNDERLINED("underlined phrase"), "."),
                                  SPAN(""),
                                  SPAN("  This is a ", CODE("code phrase"),
                                       "."),
                                  SPAN(""),
                              ])))

        ex.assert_matches(self, doc)
