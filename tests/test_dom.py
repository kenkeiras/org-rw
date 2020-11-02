import logging
import os
import unittest
from datetime import datetime as DT

from org_dom import dumps, load, loads
from utils.dom_assertions import (BOLD, CODE, HL, ITALIC, SPAN, STRIKE,
                                  UNDERLINED, VERBATIM, WEB_LINK, Dom, Tokens)

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
        self.maxDiff = 10000
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
                                       ".\n"),
                                  SPAN("\n"),
                                  SPAN("  This is a ",
                                       VERBATIM("verbatim phrase"), ".\n"),
                                  SPAN("\n"),
                                  SPAN("  This is a ", ITALIC("italic phrase"),
                                       ".\n"),
                                  SPAN("\n"),
                                  SPAN("  This is a ",
                                       STRIKE("strike-through phrase"), ".\n"),
                                  SPAN("\n"),
                                  SPAN("  This is a ",
                                       UNDERLINED("underlined phrase"), ".\n"),
                                  SPAN("\n"),
                                  SPAN("  This is a ", CODE("code phrase"),
                                       ".\n"),

                                  SPAN("\n"),
                                  SPAN("  This is a nested ", BOLD(["bold ", VERBATIM(["verbatim ", ITALIC(["italic ", STRIKE(["strike ", UNDERLINED(["underlined ", CODE("code ."), " ."]), " ."]), " ."]), " ."]), " ."])),
                                  SPAN("\n"),

                                  SPAN("\n"),
                                  # THIS IS INTERLEAVED, not nested
                                  SPAN(["  This is a interleaved ",
                                        Tokens.BOLD_START,
                                        "bold ",
                                        Tokens.VERBATIM_START,
                                        "verbatim ",
                                        Tokens.ITALIC_START,
                                        "italic ",
                                        Tokens.STRIKE_START,
                                        "strike ",
                                        Tokens.UNDERLINED_START,
                                        "underlined ",
                                        Tokens.CODE_START,
                                        "code .",
                                        Tokens.BOLD_END,
                                        " .",
                                        Tokens.VERBATIM_END,
                                        " .",
                                        Tokens.ITALIC_END,
                                        " .",
                                        Tokens.STRIKE_END,
                                        " .",
                                        Tokens.UNDERLINED_END,
                                        " .",
                                        Tokens.CODE_END,
                                        "\n"]),

                                  SPAN("\n"),
                                  SPAN("  This is a _ non-underlined phrase because an incorrectly placed content _.\n"),
                                  SPAN("\n"),

                                  SPAN("  This is a _ non-underlined phrase because an incorrectly placed content beginning_.\n"),
                                  SPAN("\n"),

                                  SPAN(""),
                                  SPAN("  This is a _non-underlined phrase because an incorrectly placed content end _.\n"),
                                  SPAN("\n"),

                                  SPAN(""),
                                  SPAN("  This is a _non-underlined phrase because the lack of an end.\n"),
                                  SPAN("\n"),

                                  SPAN("\n"),
                                  SPAN("  This is a _non-underlined phrase because an empty line between beginning and\n"),
                                  SPAN("\n"),

                                  SPAN(""),
                                  SPAN("  end._\n"),
                              ])))

        ex.assert_matches(self, doc)

    def test_links_file_03(self):
        with open(os.path.join(DIR, '03-links.org')) as f:
            doc = load(f)

        links = list(doc.get_links())
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].value, 'https://codigoparallevar.com/1')
        self.assertEqual(links[0].description, 'web link')

        self.assertEqual(links[1].value, 'https://codigoparallevar.com/2')
        self.assertEqual(links[1].description, 'web link')
        ex = Dom(props=[('TITLE', '03-Links'),
                        ('DESCRIPTION', 'Simple org file to test links'),
                        ('TODO', 'TODO(t) PAUSED(p) |  DONE(d)')],
                 children=(HL('First level',
                              props=[
                                  ('ID', '03-markup-first-level-id'),
                                  ('CREATED', DT(2020, 1, 1, 1, 1)),
                              ],
                              content=[
                                  SPAN("  This is a ", WEB_LINK("web link", "https://codigoparallevar.com/1"),
                                       ".\n"),
                                  SPAN("\n"),
                                  SPAN("  This is a ",  ITALIC(["italized ", WEB_LINK("web link", "https://codigoparallevar.com/2")]),
                                       ".\n"),
                              ])))

        ex.assert_matches(self, doc)
