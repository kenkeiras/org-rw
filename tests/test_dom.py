import logging
import os
import sys
import unittest
from datetime import datetime as DT

from org_dom import load, loads
from utils.dom_assertions import HL, Dom

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
                     content='First level content',
                     children=[
                         HL('Second level',
                            props=[('ID', '01-simple-second-level-id')],
                            content='Second level content',
                            children=[
                                HL('Third level',
                                   props=[('ID', '01-simple-third-level-id')],
                                   content='Third level content')
                            ])
                     ])))

        ex.assert_matches(self, doc)
