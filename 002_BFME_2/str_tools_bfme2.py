"""
BFME2-specific reader for data\\lotr.str.

Kept deliberately separate from 000_TOOLKIT/BFME-loc-toolkit/scripts/csf_tools.py's
read_str()/_STR_BLOCK_RE, which is BFME1's parser and must keep working exactly as
it does today. BFME2's own lotr.str uses two real format quirks BFME1's file never
has (found by inspecting the actual bytes of F:\\BFME2\\lang\\english.big and
F:\\BFME2\\lang\\englishpatch105.big, and the draft translation in
002_BFME_2/005_BFME2_UKRAINIAN/lang/ukrainianpatch105/lotr.str) — see
002_BFME_2/BFME2_structure.json -> text_system.CRITICAL_BUG_found_in_existing_toolkit_str_parser
and .second_format_quirk_found_in_real_localization for the full writeup:

  1. An optional '// ...' comment line (translator-facing, e.g. '// context: ...')
     between a label and its quoted text.
  2. Optional leading whitespace/tabs before the opening quote.

Each quirk gets its own function so a bug in one is easy to isolate/disable without
touching the other, and so BFME1's read_str() is never modified.

Usage:
    from str_tools_bfme2 import read_str_bfme2
    labels, order = read_str_bfme2(raw_bytes.decode('cp1252'))
"""

import os
import re
import sys

_TOOLKIT_SCRIPTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    '000_TOOLKIT', 'BFME-loc-toolkit', 'scripts',
)
sys.path.insert(0, _TOOLKIT_SCRIPTS)
from csf_tools import read_str  # BFME1's parser, reused as-is, never modified here


def build_str_bfme2(labels: dict, order: list) -> str:
    """Write BFME2 .str text back out. Deliberately NOT reusing BFME1's
    build_str()/_escape_str_value(): that helper replaces any literal '"'
    with "'" because BFME1's own .str has no real quote-escaping convention.
    BFME2's DOES - embedded quotes are already stored as a literal backslash
    followed by a quote (two characters, e.g. Вдосконалення \\"Вогняні
    стріли\\") - running BFME1's escaper over that would mangle the quote
    into \\' . Text here is written back byte-for-byte as already stored."""
    return ''.join(
        label + '\r\n"' + (labels.get(label) or '') + '"\r\nEND\r\n\r\n'
        for label in order
    )


_COMMENT_LINE_RE = re.compile(r'^[ \t]*//[^\r\n]*\r?\n', re.MULTILINE)


def strip_str_comments(text: str) -> str:
    """Remove '//'-prefixed comment lines (translator notes, header comments).

    These sit between a label and its quoted text often enough in BFME2's own
    lotr.str (~1200 occurrences, ~16% of all labels) that BFME1's read_str()
    regex — which expects the quote on the line immediately after the label —
    matches starting from the comment line instead, silently losing the real
    label. Stripping every comment line up front sidesteps that entirely.
    """
    return _COMMENT_LINE_RE.sub('', text)


_QUOTE_INDENT_RE = re.compile(r'(\r?\n)[ \t]+(?=")')


def normalize_str_quote_indent(text: str) -> str:
    """Strip leading whitespace/tabs before an opening quote.

    The stock English lotr.str never indents the quoted-text line, but the
    draft Ukrainian translation (002_BFME_2/005_BFME2_UKRAINIAN/lang/
    ukrainianpatch105/lotr.str) consistently writes `LABEL\\r\\n\\t"text"\\r\\nEND`
    with a tab. BFME1's read_str() regex requires the quote right after the
    newline, so it can't read that file without this normalization step.
    """
    return _QUOTE_INDENT_RE.sub(r'\1', text)


def read_str_bfme2(text: str):
    """BFME2 lotr.str reader: apply both quirk fixes, then hand off to BFME1's
    own read_str() for the actual LABEL/"text"/END parsing (unchanged)."""
    text = strip_str_comments(text)
    text = normalize_str_quote_indent(text)
    return read_str(text)
