import logging
import os
import unittest
from datetime import date
from datetime import datetime as DT

from org_rw import MarkerToken, MarkerType, Timestamp, dumps, load, loads

from utils.assertions import (BOLD, CODE, HL, ITALIC, SPAN, STRIKE, UNDERLINED,
                              VERBATIM, WEB_LINK, Doc, Tokens)

DIR = os.path.dirname(os.path.abspath(__file__))


class TestSerde(unittest.TestCase):
    def test_simple_file_01(self):
        with open(os.path.join(DIR, "01-simple.org")) as f:
            doc = load(f)

        ex = Doc(
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

        ex = Doc(
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
        self.assertEqual(len(links), 7)
        self.assertEqual(links[0].value, "https://codigoparallevar.com/1")
        self.assertEqual(links[0].description, "web link")

        self.assertEqual(links[1].value, "https://codigoparallevar.com/2")
        self.assertEqual(links[1].description, "web link")

        self.assertEqual(links[2].value, "* First level")
        self.assertEqual(links[2].description, None)

        self.assertEqual(links[3].value, "id:03-markup-first-level-id")
        self.assertEqual(links[3].description, "a link to a section by id")

        self.assertEqual(links[4].value, "https://codigoparallevar.com/3")
        self.assertEqual(links[4].description, "web link")

        self.assertEqual(links[5].value, "https://codigoparallevar.com/4")
        self.assertEqual(links[5].description, "[tricky web link]\u200b")

        self.assertEqual(links[6].value, "https://codigoparallevar.com/5")
        self.assertEqual(links[6].description, "another tricky web link")

        ex = Doc(
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
                        SPAN("\n"),
                        SPAN(
                            "  This is a ",
                            WEB_LINK("web link", "https://codigoparallevar.com/3"),
                            " followed up with some text.\n",
                        ),
                        SPAN("\n"),
                        SPAN(
                            "  This is a ",
                            WEB_LINK("[tricky web link]\u200b", "https://codigoparallevar.com/4"),
                            " followed up with some text.\n",
                        ),
                        SPAN("\n"),
                        SPAN(
                            "  This is [",
                            WEB_LINK("another tricky web link", "https://codigoparallevar.com/5"),
                            "] followed up with some text.\n",
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
        self.assertEqual(len(links), 7)
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

        self.assertEqual(links[4].value, "https://codigoparallevar.com/3")
        self.assertEqual(links[4].description, "web link")
        links[4].value = "https://codigoparallevar.com/3-updated"
        links[4].description = "web link #3 with update"

        self.assertEqual(links[5].value, "https://codigoparallevar.com/4")
        self.assertEqual(links[5].description, "[tricky web link]\u200b")
        links[5].value = "https://codigoparallevar.com/4-updated"
        links[5].description = "[tricky web link #4 with update]"

        self.assertEqual(links[6].value, "https://codigoparallevar.com/5")
        self.assertEqual(links[6].description, "another tricky web link")
        links[6].value = "https://codigoparallevar.com/5-updated"
        links[6].description = "another tricky web link #5 with update"

        ex = Doc(
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
                        SPAN("\n"),
                        SPAN(
                            "  This is a ",
                            WEB_LINK(
                                "web link #3 with update",
                                "https://codigoparallevar.com/3-updated",
                            ),
                            " followed up with some text.\n",
                        ),
                        SPAN("\n"),
                        SPAN(
                            "  This is a ",
                            WEB_LINK(
                                "[tricky web link #4 with update]",
                                "https://codigoparallevar.com/4-updated",
                            ),
                            " followed up with some text.\n",
                        ),
                        SPAN("\n"),
                        SPAN(
                            "  This is [",
                            WEB_LINK(
                                "another tricky web link #5 with update",
                                "https://codigoparallevar.com/5-updated",
                            ),
                            "] followed up with some text.\n",
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

    def test_planning_info_file_05(self):
        with open(os.path.join(DIR, "05-dates.org")) as f:
            orig = f.read()
            doc = loads(orig)

        hl = doc.getTopHeadlines()[0]
        self.assertEqual(
            hl.scheduled.time, Timestamp(True, 2020, 12, 12, "Sáb", None, None)
        )
        self.assertEqual(
            hl.closed.time, Timestamp(True, 2020, 12, 13, "Dom", None, None)
        )
        self.assertEqual(
            hl.deadline.time, Timestamp(True, 2020, 12, 14, "Lun", None, None)
        )

        hl_schedule_range = hl.children[0]
        self.assertEqual(
            hl_schedule_range.scheduled.time, Timestamp(True, 2020, 12, 15, "Mar", 0, 5)
        )
        self.assertEqual(
            hl_schedule_range.scheduled.end_time,
            Timestamp(True, 2020, 12, 15, "Mar", 0, 10),
        )

        hl_schedule_range = hl.children[1]
        self.assertEqual(
            hl_schedule_range.scheduled.time,
            Timestamp(True, 2020, 12, 15, "Mar", 0, 5, '++1w')
        )
        self.assertEqual(
            hl_schedule_range.scheduled.end_time,
            Timestamp(True, 2020, 12, 15, "Mar", 0, 10),
        )
        self.assertEqual(
            hl_schedule_range.scheduled.repetition,
            '++1w',
        )

    def test_update_info_file_05(self):
        with open(os.path.join(DIR, "05-dates.org")) as f:
            orig = f.read()
            doc = loads(orig)

        hl = doc.getTopHeadlines()[0]
        hl.scheduled.time.day = 15
        hl.closed.time.day = 16
        hl.deadline.time.day = 17

        # Account for removeing 3 days-of-week + 1 space each
        self.assertEqual(len(dumps(doc)), len(orig) - (4) * 3)
        doc_updated = loads(dumps(doc))

        hl_up = doc_updated.getTopHeadlines()[0]
        self.assertEqual(
            hl.scheduled.time, Timestamp(True, 2020, 12, 15, None, None, None)
        )
        self.assertEqual(
            hl.closed.time, Timestamp(True, 2020, 12, 16, None, None, None)
        )
        self.assertEqual(
            hl.deadline.time, Timestamp(True, 2020, 12, 17, None, None, None)
        )

    def test_mimic_write_file_06(self):
        with open(os.path.join(DIR, "06-lists.org")) as f:
            orig = f.read()
            doc = loads(orig)

        self.assertEqual(dumps(doc), orig)

    def test_structure_file_06(self):
        with open(os.path.join(DIR, "06-lists.org")) as f:
            orig = f.read()
            doc = loads(orig)

        hl = doc.getTopHeadlines()[0]
        # ...
        lists = hl.getLists()
        self.assertEqual(len(lists), 3)
        self.assertEqual(lists[0][0].content, [" This is a simple list."])
        self.assertEqual(lists[0][0].bullet, "-")
        self.assertEqual(
            lists[0][1].content,
            [
                " This list has multiple elements, with ",
                MarkerToken(closing=False, tok_type=MarkerType.UNDERLINED_MODE),
                "markup",
                MarkerToken(closing=True, tok_type=MarkerType.UNDERLINED_MODE),
                ".",
            ],
        )

        self.assertEqual(lists[1][0].content, [" This is a simple list."])
        self.assertEqual(lists[1][0].bullet, "+")

        hl2 = doc.getTopHeadlines()[1]
        # ...
        lists2 = hl2.getLists()
        self.assertEqual(len(lists2), 2)

        self.assertEqual(lists2[0][0].content, [" First element"])
        self.assertEqual(lists2[0][0].counter, "1")
        self.assertEqual(lists2[0][0].counter_sep, ".")

        self.assertEqual(lists2[0][1].content, [" Second element"])
        self.assertEqual(lists2[0][1].counter, "2")
        self.assertEqual(lists2[0][1].counter_sep, ".")

        self.assertEqual(lists2[1][0].content, [" First element"])
        self.assertEqual(lists2[1][0].counter, "1")
        self.assertEqual(lists2[1][0].counter_sep, ")")

        self.assertEqual(lists2[1][1].content, [" Second element"])
        self.assertEqual(lists2[1][1].counter, "2")
        self.assertEqual(lists2[1][1].counter_sep, ")")

    def test_org_roam_07(self):
        with open(os.path.join(DIR, "07-org-roam-v2.org")) as f:
            orig = f.read()
            doc = loads(orig)

        self.assertEqual(doc.get_property("ID"), "515054a9-ced8-4119-a844-71726f80dedf")

        self.assertEqual(len(doc.getTopHeadlines()), 1)
        hl = doc.getTopHeadlines()[0]
        self.assertEqual(hl.get_property("ID"), "419f4651-21c8-4166-b8d5-692c34be9f93")
        self.assertEqual(len(hl.children), 1)

    def test_org_property_creation_08(self):
        with open(os.path.join(DIR, "08-property-creation.org")) as f:
            orig = f.read()
            doc = loads(orig)

        headline = doc.getTopHeadlines()[0]
        headline.id = "first"

        second = headline.children[0]
        second.id = "second"

        self.assertEqual(
            dumps(doc).strip(),
            """
 #+TITLE: 08-Property-creation

* Top headline
:PROPERTIES:
:ID: first
:END:
** Second headline
:PROPERTIES:
:ID: second
:END:

*** Third headline
            """.strip(),
        )


    def test_markup_file_09(self):
        with open(os.path.join(DIR, "09-markup-on-headline.org")) as f:
            doc = load(f)

        hl = doc.getTopHeadlines()[0]
        print(hl.title)
        self.assertEqual(hl.title.contents, [
            'Headline ',
            MarkerToken(closing=False, tok_type=MarkerType.UNDERLINED_MODE),
            'with',
            MarkerToken(closing=True, tok_type=MarkerType.UNDERLINED_MODE),
            ' markup',
        ])

    def test_mimic_write_file_10(self):
        with open(os.path.join(DIR, "10-tables.org")) as f:
            orig = f.read()
            doc = loads(orig)

        self.assertEqual(dumps(doc), orig)

    def test_tables_file_10(self):
        with open(os.path.join(DIR, "10-tables.org")) as f:
            doc = load(f)

        hl = doc.getTopHeadlines()[0]

        tables = hl.get_tables()
        first_table = tables[0]
        self.assertEqual(len(first_table), 4)

        print(first_table[0])
        self.assertEqual(len(first_table[0].cells), 3)
        self.assertEqual(first_table[0].cells[0].strip(), 'Header1')
        self.assertEqual(first_table[0].cells[1].strip(), 'Header2')
        self.assertEqual(first_table[0].cells[2].strip(), 'Header3')

