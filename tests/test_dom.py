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
        with open(os.path.join(DIR, "01-simple.org")) as f:
            doc = load(f)

        ex = Dom(
            props=[
                ("TITLE", "01-Simple"),
                ("DESCRIPTION", "Simple org file"),
                ("TODO", "TODO(t) PAUSED(p) |  DONE(d)"),
            ],
            children=(
                HL(
                    "First level",
                    props=[
                        ("ID", "01-simple-first-level-id"),
                        ("CREATED", DT(2020, 1, 1, 1, 1)),
                    ],
                    content="  First level content\n",
                    children=[
                        HL(
                            "Second level",
                            props=[("ID", "01-simple-second-level-id")],
                            content="\n   Second level content\n",
                            children=[
                                HL(
                                    "Third level",
                                    props=[("ID", "01-simple-third-level-id")],
                                    content="\n    Third level content\n",
                                )
                            ],
                        )
                    ],
                )
            ),
        )

        ex.assert_matches(self, doc)

    def test_mimic_write_file_01(self):
        """A goal of this library is to be able to update a file without changing parts not directly modified."""
        with open(os.path.join(DIR, "01-simple.org")) as f:
            orig = f.read()
            doc = loads(orig)

        self.assertEqual(dumps(doc), orig)

    def test_mimic_write_file_01_second(self):
        """A goal of this library is to be able to update a file without changing parts not directly modified."""
        with open(os.path.join(DIR, "01-simple-2.org")) as f:
            orig = f.read()
            doc = loads(orig)

        self.assertEqual(dumps(doc), orig)

    def test_markup_file_02(self):
        with open(os.path.join(DIR, "02-markup.org")) as f:
            doc = load(f)

        ex = Dom(
            props=[
                ("TITLE", "02-Markup"),
                ("DESCRIPTION", "Simple org file to test markup"),
                ("TODO", "TODO(t) PAUSED(p) |  DONE(d)"),
            ],
            children=(
                HL(
                    "First level",
                    props=[
                        ("ID", "02-markup-first-level-id"),
                        ("CREATED", DT(2020, 1, 1, 1, 1)),
                    ],
                    content=[
                        SPAN("  This is a ", BOLD("bold phrase"), ".\n"),
                        SPAN("\n"),
                        SPAN("  This is a ", VERBATIM("verbatim phrase"), ".\n"),
                        SPAN("\n"),
                        SPAN("  This is a ", ITALIC("italic phrase"), ".\n"),
                        SPAN("\n"),
                        SPAN("  This is a ", STRIKE("strike-through phrase"), ".\n"),
                        SPAN("\n"),
                        SPAN("  This is a ", UNDERLINED("underlined phrase"), ".\n"),
                        SPAN("\n"),
                        SPAN("  This is a ", CODE("code phrase"), ".\n"),
                        SPAN("\n"),
                        SPAN(
                            "  This is a nested ",
                            BOLD(
                                [
                                    "bold ",
                                    VERBATIM(
                                        [
                                            "verbatim ",
                                            ITALIC(
                                                [
                                                    "italic ",
                                                    STRIKE(
                                                        [
                                                            "strike ",
                                                            UNDERLINED(
                                                                [
                                                                    "underlined ",
                                                                    CODE("code ."),
                                                                    " .",
                                                                ]
                                                            ),
                                                            " .",
                                                        ]
                                                    ),
                                                    " .",
                                                ]
                                            ),
                                            " .",
                                        ]
                                    ),
                                    " .",
                                ]
                            ),
                        ),
                        SPAN("\n"),
                        SPAN("\n"),
                        # THIS IS INTERLEAVED, not nested
                        SPAN(
                            [
                                "  This is a interleaved ",
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
                                "\n",
                            ]
                        ),
                        SPAN("\n"),
                        SPAN(
                            "  This is a _ non-underlined phrase because an incorrectly placed content _.\n"
                        ),
                        SPAN("\n"),
                        SPAN(
                            "  This is a _ non-underlined phrase because an incorrectly placed content beginning_.\n"
                        ),
                        SPAN("\n"),
                        SPAN(""),
                        SPAN(
                            "  This is a _non-underlined phrase because an incorrectly placed content end _.\n"
                        ),
                        SPAN("\n"),
                        SPAN(""),
                        SPAN(
                            "  This is a _non-underlined phrase because the lack of an end.\n"
                        ),
                        SPAN("\n"),
                        SPAN("\n"),
                        SPAN(
                            "  This is a _non-underlined phrase because an empty line between beginning and\n"
                        ),
                        SPAN("\n"),
                        SPAN(""),
                        SPAN("  end._\n"),
                    ],
                )
            ),
        )

        ex.assert_matches(self, doc)

    def test_links_file_03(self):
        with open(os.path.join(DIR, "03-links.org")) as f:
            doc = load(f)

        links = list(doc.get_links())
        self.assertEqual(len(links), 4)
        self.assertEqual(links[0].value, "https://codigoparallevar.com/1")
        self.assertEqual(links[0].description, "web link")

        self.assertEqual(links[1].value, "https://codigoparallevar.com/2")
        self.assertEqual(links[1].description, "web link")

        self.assertEqual(links[2].value, "* First level")
        self.assertEqual(links[2].description, None)

        self.assertEqual(links[3].value, "id:03-markup-first-level-id")
        self.assertEqual(links[3].description, "a link to a section by id")

        ex = Dom(
            props=[
                ("TITLE", "03-Links"),
                ("DESCRIPTION", "Simple org file to test links"),
                ("TODO", "TODO(t) PAUSED(p) |  DONE(d)"),
            ],
            children=(
                HL(
                    "First level",
                    props=[
                        ("ID", "03-markup-first-level-id"),
                        ("CREATED", DT(2020, 1, 1, 1, 1)),
                    ],
                    content=[
                        SPAN(
                            "  This is a ",
                            WEB_LINK("web link", "https://codigoparallevar.com/1"),
                            ".\n",
                        ),
                        SPAN("\n"),
                        SPAN(
                            "  This is a ",
                            ITALIC(
                                [
                                    "italized ",
                                    WEB_LINK(
                                        "web link", "https://codigoparallevar.com/2"
                                    ),
                                ]
                            ),
                            ".\n",
                        ),
                        SPAN("\n"),
                        SPAN(
                            "  This is a link with no description to ",
                            WEB_LINK(None, "* First level"),
                            ".\n",
                        ),
                        SPAN("\n"),
                        SPAN(
                            "  This is ",
                            WEB_LINK(
                                "a link to a section by id",
                                "id:03-markup-first-level-id",
                            ),
                            ".\n",
                        ),
                    ],
                )
            ),
        )

        ex.assert_matches(self, doc)

    def test_update_links_file_03(self):
        with open(os.path.join(DIR, "03-links.org")) as f:
            doc = load(f)

        links = list(doc.get_links())
        self.assertEqual(len(links), 4)
        self.assertEqual(links[0].value, "https://codigoparallevar.com/1")
        self.assertEqual(links[0].description, "web link")
        links[0].value = "https://codigoparallevar.com/1-updated"
        links[0].description = "web link #1 with update"

        self.assertEqual(links[1].value, "https://codigoparallevar.com/2")
        self.assertEqual(links[1].description, "web link")
        links[1].value = "https://codigoparallevar.com/2-updated"
        links[1].description = "web link #2 with update"

        self.assertEqual(links[2].value, "* First level")
        self.assertEqual(links[2].description, None)
        links[2].value = "* Non-existent level"
        links[2].description = "a description now"

        self.assertEqual(links[3].value, "id:03-markup-first-level-id")
        self.assertEqual(links[3].description, "a link to a section by id")
        links[3].value = "id:03-markup-non-existent-level-id"
        links[3].description = None

        ex = Dom(
            props=[
                ("TITLE", "03-Links"),
                ("DESCRIPTION", "Simple org file to test links"),
                ("TODO", "TODO(t) PAUSED(p) |  DONE(d)"),
            ],
            children=(
                HL(
                    "First level",
                    props=[
                        ("ID", "03-markup-first-level-id"),
                        ("CREATED", DT(2020, 1, 1, 1, 1)),
                    ],
                    content=[
                        SPAN(
                            "  This is a ",
                            WEB_LINK(
                                "web link #1 with update",
                                "https://codigoparallevar.com/1-updated",
                            ),
                            ".\n",
                        ),
                        SPAN("\n"),
                        SPAN(
                            "  This is a ",
                            ITALIC(
                                [
                                    "italized ",
                                    WEB_LINK(
                                        "web link #2 with update",
                                        "https://codigoparallevar.com/2-updated",
                                    ),
                                ]
                            ),
                            ".\n",
                        ),
                        SPAN("\n"),
                        SPAN(
                            "  This is a link with no description to ",
                            WEB_LINK("a description now", "* Non-existent level"),
                            ".\n",
                        ),
                        SPAN("\n"),
                        SPAN(
                            "  This is ",
                            WEB_LINK(
                                None,
                                "id:03-markup-non-existent-level-id",
                            ),
                            ".\n",
                        ),
                    ],
                )
            ),
        )

        ex.assert_matches(self, doc)

    def test_mimic_write_file_04(self):
        with open(os.path.join(DIR, "04-code.org")) as f:
            orig = f.read()
            doc = loads(orig)

        self.assertEqual(dumps(doc), orig)

    def test_code_file_04(self):
        with open(os.path.join(DIR, "04-code.org")) as f:
            doc = load(f)

        snippets = list(doc.get_code_snippets())
        self.assertEqual(len(snippets), 2)
        self.assertEqual(
            snippets[0].content,
            'echo "This is a test"\n'
            + 'echo "with two lines"\n'
            + "exit 0 # Exit successfully",
        )
        self.assertEqual(
            snippets[0].result,
            "This is a test\n" + "with two lines",
        )

        self.assertEqual(
            snippets[1].content,
            'echo "This is another test"\n'
            + 'echo "with two lines too"\n'
            + "exit 0 # Comment",
        )
        self.assertEqual(
            snippets[1].result, "This is another test\n" + "with two lines too"
        )

    def test_mimic_write_file_05(self):
        with open(os.path.join(DIR, "05-dates.org")) as f:
            orig = f.read()
            doc = loads(orig)

        self.assertEqual(dumps(doc), orig)
