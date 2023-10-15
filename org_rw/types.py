import re
from typing import List, TypedDict

class HeadlineDict(TypedDict):
    linenum: int
    orig: re.Match
    title: str
    contents: List
    children: List
    keywords: List
    properties: List
    logbook: List
    structural: List
    delimiters: List
    results: List  # TODO: Move to each specific code block?
    list_items: List
    table_rows: List
