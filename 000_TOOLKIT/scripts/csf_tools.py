"""
Reusable tools for editing BFME1 (.big / CSF / .str) localization files.
Requires: pip install pyBIG

Covers everything documented in bfme1_localization.json -> meta.archive_format.

Quick usage to read an existing archive:
    from pyBIG import Archive
    with open('english.big', 'rb') as f:
        data = f.read()
    archive = Archive(data)
    csf_bytes = archive.read_file(r'lang\\english\\lotr.csf')
    labels, order = read_csf(csf_bytes)

Quick usage to write a new archive:
    csf_bytes = build_csf(labels, order)
    new_archive = Archive.empty(header='BIG4')
    new_archive.add_file(r'lang\\english\\lotr.csf', csf_bytes)
    # ...add every other file you want to keep (fonts, ini, tga, etc.)...
    new_archive.save('english.big')
"""

import struct
import re


# ---------------------------------------------------------------------------
# CSF (binary, UTF-16, bit-inverted bytes) — the primary/authoritative format.
# ---------------------------------------------------------------------------

def read_csf(data: bytes):
    """Parse CSF bytes -> (labels: dict[str, str], order: list[str])."""
    pos = 0
    magic, version, num_labels, num_strings, _skip1, _skip2 = struct.unpack_from('<4siiiii', data, pos)
    if magic != b' FSC':
        raise ValueError(f'not a CSF file, bad magic: {magic!r}')
    pos += 24

    labels, order = {}, []
    for _ in range(num_labels):
        pos += 4  # b' LBL'
        nstrings, = struct.unpack_from('<i', data, pos); pos += 4
        namelen, = struct.unpack_from('<i', data, pos); pos += 4
        name = data[pos:pos + namelen].decode('ascii'); pos += namelen

        value = None
        for _ in range(nstrings):
            smagic = data[pos:pos + 4]; pos += 4
            slen, = struct.unpack_from('<i', data, pos); pos += 4
            raw = data[pos:pos + slen * 2]; pos += slen * 2
            # CSF stores UTF-16LE text with every byte bit-inverted (~byte & 0xFF).
            inv = bytes((~b) & 0xFF for b in raw)
            text = inv.decode('utf-16-le')
            if smagic == b'WRTS':
                # rare variant: an extra blob follows the string, skip it
                extralen, = struct.unpack_from('<i', data, pos); pos += 4
                pos += extralen
            value = text
        labels[name] = value
        order.append(name)
    return labels, order


def build_csf(labels: dict, order: list) -> bytes:
    """Build CSF bytes from a labels dict and an explicit label order."""
    out = bytearray()
    out += b' FSC'
    out += struct.pack('<i', 3)            # version
    out += struct.pack('<i', len(order))   # num_labels
    out += struct.pack('<i', len(order))   # num_strings (1:1, one string per label)
    out += struct.pack('<i', 0)
    out += struct.pack('<i', 0)
    for label in order:
        text = labels.get(label) or ''
        name_b = label.encode('ascii')
        out += b' LBL'
        out += struct.pack('<i', 1)
        out += struct.pack('<i', len(name_b))
        out += name_b
        out += b' RTS'
        out += struct.pack('<i', len(text))
        raw = text.encode('utf-16-le')
        inv = bytes((~b) & 0xFF for b in raw)
        out += inv
    return bytes(out)


# ---------------------------------------------------------------------------
# .str (plain text, single-byte codepage) — legacy override format.
# See meta.text_source_priority_WARNING before touching this one:
# it's read via the OS's single-byte ANSI codepage, not Unicode, and it
# TAKES PRIORITY over the CSF when present. For non-Latin languages the
# usual fix is to delete data\lotr.str from whatever patch .big ships it,
# not to "fix" its encoding.
# ---------------------------------------------------------------------------

# END must match case-insensitively -- some blocks in real .str files use
# lowercase/mixed-case 'End' (confirmed for e.g. OBJECT:HordeGondorRangerSword,
# OBJECT:Grishnakh, CONTROLBAR:ShatteredHope/WretchedFate). Missing this
# silently desyncs the parse: it skips to the next END/End occurrence,
# which can be pages away, splicing unrelated labels' text together.
# Also tolerate stray whitespace between the closing quote and the
# END line (confirmed for e.g. CONTROLBAR:ToolTipBuildGondorRangerHorde,
# which ships as '..."  \r\nEND' with a trailing space) -- same desync
# failure mode, just a different cause.
# Also tolerate stray whitespace AFTER 'END'/'End' itself, before the line
# break (confirmed for e.g. Color:Marsala, Map:MAPMPFordsofIsenWinter,
# CONTROLBAR:ShatteredHope/WretchedFate, Map:MAPMPDorwinion*/Desc, which
# ship as 'END \r\n' / 'End \r\n' with a trailing space after END) -- same
# desync failure mode again, just yet another whitespace placement. This one
# is sneaky because it doesn't just corrupt the misparsed label itself: the
# re-extraction that check_build_health() runs on every apply will treat the
# resulting garbage as "genuinely rewritten content" and silently stomp a
# perfectly good existing translation with it (see the reconciliation
# docstring, case 5) -- confirmed happening for real when testing an
# Italian-base install, so this isn't just a cosmetic parsing nicety.
_STR_BLOCK_RE = re.compile(r'^(?P<label>[^\r\n]+?)\r?\n"(?P<text>.*?)"[ \t]*\r?\n[Ee][Nn][Dd][ \t]*\r?\n', re.MULTILINE | re.DOTALL)


def read_str(text: str):
    """Parse decoded .str text -> (labels: dict[str, str], order: list[str])."""
    labels, order = {}, []
    for m in _STR_BLOCK_RE.finditer(text):
        # labels can have stray trailing whitespace in the source file
        # (confirmed for e.g. 'SCRIPT:scout1 ', 'CONTROLBAR:BanneroftheSilverSwan ')
        # -- the game itself looks these up WITHOUT that whitespace, so an
        # entry stored under the untrimmed key is invisible to the game
        # (shows as MISSING) even though it exists in the CSF.
        label = m.group('label').rstrip()
        labels[label] = m.group('text')
        order.append(label)
    return labels, order


def _escape_str_value(v: str) -> str:
    v = v or ''
    v = v.replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '\\n')
    v = v.replace('"', "'")  # .str has no real quote-escaping convention
    return v


def build_str(labels: dict, order: list) -> str:
    """Build .str plain text (still needs .encode(<codepage>) before writing to an archive)."""
    return ''.join(
        label + '\n"' + _escape_str_value(labels.get(label)) + '"\nEND\n\n'
        for label in order
    )


# ---------------------------------------------------------------------------
# small self-test when run directly
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    sample_labels = {'GUI:Hello': 'Привіт, світ!'}
    sample_order = ['GUI:Hello']
    csf = build_csf(sample_labels, sample_order)
    back, order2 = read_csf(csf)
    assert back == sample_labels and order2 == sample_order
    print('csf_tools self-test OK')
