"""
Rebuilds the beta lang\\english.big / lang\\englishpatch105.big from scratch,
starting from a CLEAN (unpatched) copy of those two files from a real 1.05
BFME2 install. This is the reproducible version of the patching session
documented in BETA_PATCH_NOTES.md - run this instead of repeating the manual
steps by hand.

Usage:
    ..\\..\\..\\000_TOOLKIT\\BFME-loc-toolkit\\python\\python.exe build_beta_english_big.py --source "F:\\BFME2"

--source must point at a folder containing a pristine lang\\english.big and
lang\\englishpatch105.big (e.g. straight from lang_backup_original\\, or a
fresh install). Output is written next to this script (english.big,
englishpatch105.big) - it does NOT touch a live game install by itself.

What this does, in order (see BETA_PATCH_NOTES.md for why each step exists):
  1. Builds lotr.csf from BFME2_strings_ua.json - NOT data\\lotr.str (BFME2's
     plain-text .str is codepage-dependent and produced mojibake; a real
     official localization, e.g. the Chinese/Thai ones in this repo, always
     ships a binary CSF instead - same UTF-16 format BFME1 uses).
  2. Unescapes the .str-style '\\n'/'\\t'/'\\"' sequences into real
     characters before writing the CSF - CSF has no escape processing at
     all, so leaving them as literal text shows as visible "\\n" in-game.
  3. Removes data\\lotr.str from both archives (so the CSF is authoritative
     - same reasoning as BFME1's own "delete lotr.str, rely on the CSF"
     fix, TOOLKIT_NOTES.md 2.2/3.2).
  4. Adds our one Cyrillic font (AlbertusMTUA - see
     fonts\\rename_albertus_family.py for how AlbertusMTUA.otf was produced)
     and points BOTH FontSubstitution blocks ("SachaWynter" AND
     "Albertus MT") at that SAME single font - never two different font
     files, see OWN_FONTSUB's comment and BETA_PATCH_NOTES.md section 3
     ("Attempt 4") for the duplicate-text/green-tint bug that happens
     otherwise. The FontSubstitution technique itself is copied directly
     from EA's own official Thai localization (002_BFME_2/004_BFME2_THAI),
     confirmed by reading its shipped fontsubstitution.ini. Lives ONLY in
     lang\\english.big; ini.big/maps.big are never touched.
  5. Adds the localized textures found in
     005_BFME2_UKRAINIAN/prototype/lang/Ukrainian/art/compiledtextures/
     (confirmed genuinely different from stock via SHA1 first).
  6. Applies the "UA 0.1 Clever Play" version-string branding to
     Version:Format2/Format3.
"""
import argparse
import os
import re
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
UA_DIR = os.path.dirname(HERE)                    # 005_BFME2_UKRAINIAN
BFME2_DIR = os.path.dirname(UA_DIR)                # 002_BFME_2
TOOLKIT_DIR = os.path.join(os.path.dirname(BFME2_DIR), '000_TOOLKIT', 'BFME-loc-toolkit')

sys.path.insert(0, os.path.join(TOOLKIT_DIR, 'python'))
sys.path.insert(0, os.path.join(TOOLKIT_DIR, 'scripts'))
from pyBIG import Archive
from csf_tools import build_csf

STRINGS_JSON = os.path.join(UA_DIR, 'BFME2_strings_ua.json')
TEXTURES_DIR = os.path.join(UA_DIR, 'prototype', 'lang', 'Ukrainian', 'art', 'compiledtextures')
FONTS_DIR = os.path.join(HERE, 'fonts')

FONTSUB_PATH = 'data\\ini\\fontsubstitution.ini'
LOTR_CSF_PATH = 'lotr.csf'
LOTR_STR_PATH = 'data\\lotr.str'
NEW_ALBERTUS_NAME = 'AlbertusMTUA.otf'

TEXTURE_FILES = [
    ('art\\compiledtextures\\lm\\lm_text.dds', os.path.join(TEXTURES_DIR, 'lm', 'lm_text.dds')),
    ('art\\compiledtextures\\lo\\load_w_ea.jpg', os.path.join(TEXTURES_DIR, 'lo', 'load_w_ea.jpg')),
    ('art\\compiledtextures\\lo\\logowithshadow.tga', os.path.join(TEXTURES_DIR, 'lo', 'logowithshadow.tga')),
    ('art\\compiledtextures\\ti\\titlescreenuserinterface.jpg', os.path.join(TEXTURES_DIR, 'ti', 'titlescreenuserinterface.jpg')),
]

OWN_FONTSUB = (
    '; Added for the Ukrainian prototype - lives only in lang\\english.big.\r\n'
    '; Real FontSubstitution to OUR OWN embedded Cyrillic font, registered\r\n'
    '; under a distinct family name - AlbertusMTUA - so there is no ambiguous\r\n'
    '; same-family-different-file collision with the stock AlbertusMT.otf.\r\n'
    ';\r\n'
    '; BOTH roles point at the SAME font (AlbertusMTUA), not two different\r\n'
    '; fonts. Found the hard way (2026-09-20): pointing SachaWynter at a\r\n'
    '; SEPARATE font file (sachawyntertight_ua.ttf) produced a garbled\r\n'
    '; "duplicate line" glitch under readable text in several screens (and a\r\n'
    '; green tint) - almost certainly two different font files having\r\n'
    '; mismatched glyph IDs/metrics for whatever multi-pass text effect\r\n'
    '; overlays a main-text layer with a second layer. The proven, working\r\n'
    '; BFME1 Ukrainian localization (001_BFME_1/004_BFME1_UKRAINIAN/v3)\r\n'
    '; independently confirms this pattern - it points EVERY font role,\r\n'
    '; including SachaWynter, at one single font ("Noto Sans" there). Do not\r\n'
    '; reintroduce a second distinct font file for SachaWynter here.\r\n'
    'FontSubstitution "SachaWynter"\r\n'
    '    Size 8 = 12 "AlbertusMTUA"\r\n'
    '    Size 40 = 70 "AlbertusMTUA"\r\n'
    'End\r\n'
    '\r\n'
    'FontSubstitution "Albertus MT"\r\n'
    '    Size 8 = 8 "AlbertusMTUA"\r\n'
    '    Size 9 = 9 "AlbertusMTUA"\r\n'
    '    Size 10 = 10 "AlbertusMTUA"\r\n'
    '    Size 12 = 12 "AlbertusMTUA"\r\n'
    '    Size 14 = 14 "AlbertusMTUA"\r\n'
    '    Size 16 = 16 "AlbertusMTUA"\r\n'
    '    Size 18 = 18 "AlbertusMTUA"\r\n'
    '    Size 20 = 20 "AlbertusMTUA"\r\n'
    '    Size 22 = 22 "AlbertusMTUA"\r\n'
    '    Size 24 = 24 "AlbertusMTUA"\r\n'
    'End\r\n'
)

_ESCAPE_TO_CHAR = {'n': '\n', 't': '\t', '"': '"', '\\': '\\'}
_ESCAPE_RE = re.compile(r'\\([nt"\\])')


def unescape_for_csf(s):
    return _ESCAPE_RE.sub(lambda m: _ESCAPE_TO_CHAR[m.group(1)], s)


def build_csf_bytes():
    with open(STRINGS_JSON, encoding='utf-8') as f:
        entries = json.load(f)['strings']
    labels = {e['var']: unescape_for_csf(e['ua'] or e['en']) for e in entries}
    order = [e['var'] for e in entries]
    return build_csf(labels, order), len(order)


def save(path, archive):
    archive.save(path)
    with open(path, 'rb') as f:
        Archive(f.read())  # round-trip verify
    print(f'  saved + verified: {path}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True, help='folder with a pristine lang\\english.big + lang\\englishpatch105.big')
    args = ap.parse_args()

    csf_bytes, n = build_csf_bytes()
    print(f'Built lotr.csf: {n} labels, {len(csf_bytes)} bytes')

    src_english = os.path.join(args.source, 'lang', 'english.big')
    src_patch105 = os.path.join(args.source, 'lang', 'englishpatch105.big')
    out_english = os.path.join(HERE, 'english.big')
    out_patch105 = os.path.join(HERE, 'englishpatch105.big')

    print(f'\n--- {src_english} ---')
    with open(src_english, 'rb') as f:
        arc = Archive(f.read())
    fl = arc.file_list()

    if LOTR_STR_PATH in fl:
        arc.remove_file(LOTR_STR_PATH)
    arc.add_file(LOTR_CSF_PATH, csf_bytes)

    for internal_path, src_path in TEXTURE_FILES:
        with open(src_path, 'rb') as f:
            data = f.read()
        (arc.edit_file if internal_path in fl else arc.add_file)(internal_path, data)
    print(f'  added {len(TEXTURE_FILES)} localized textures')

    with open(os.path.join(FONTS_DIR, NEW_ALBERTUS_NAME), 'rb') as f:
        arc.add_file(NEW_ALBERTUS_NAME, f.read())
    print('  added AlbertusMTUA.otf (only - sachawyntertight_ua.ttf deliberately not used, see OWN_FONTSUB comment)')

    lang_ini = arc.read_file('language.ini').decode('latin-1')
    pattern = re.compile(r'^([ \t]*LocalFontFile\s*=\s*OmniaLTStd\.ttf[^\r\n]*)', re.MULTILINE)
    addition = '\r\n  LocalFontFile = ' + NEW_ALBERTUS_NAME + ' ;// Ukrainian Cyrillic Albertus MT, distinct family name'
    new_lang_ini = pattern.sub(lambda m: m.group(1) + addition, lang_ini, count=1)
    if new_lang_ini == lang_ini:
        raise RuntimeError('language.ini insertion point not found - is this really a stock 1.05 english.big?')

    # DO NOT set UnicodeFontName = "AlbertusMTUA" here. Tried once
    # (2026-09-20), ported over from RotWK's own UnicodeFontName discovery
    # as "cheap insurance" - it was NOT cheap insurance for BFME2, it broke
    # something: a garbled hash/lattice-pattern glitch appeared under the
    # main menu title (plus the whole screen took on a green tint) that had
    # never happened before in this project's history. Reverted immediately.
    # The user confirms BFME2 never had the RotWK-class ornate-title bug in
    # the first place, so there was nothing to fix here - only something to
    # break. Leave UnicodeFontName at its stock value for BFME2.

    arc.edit_file('language.ini', new_lang_ini.encode('latin-1'))
    print('  language.ini: added the 2 LocalFontFile lines')

    arc.add_file(FONTSUB_PATH, OWN_FONTSUB.encode('latin-1'))
    print('  added data\\ini\\fontsubstitution.ini (per-language only)')

    save(out_english, arc)

    print(f'\n--- {src_patch105} ---')
    with open(src_patch105, 'rb') as f:
        arc2 = Archive(f.read())
    if LOTR_STR_PATH in arc2.file_list():
        arc2.remove_file(LOTR_STR_PATH)
    arc2.add_file(LOTR_CSF_PATH, csf_bytes)
    save(out_patch105, arc2)

    print('\nDone. Drop english.big + englishpatch105.big into a stock 1.05 install\'s lang\\ folder.')


if __name__ == '__main__':
    main()
