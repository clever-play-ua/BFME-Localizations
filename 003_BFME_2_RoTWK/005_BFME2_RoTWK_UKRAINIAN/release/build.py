"""
RotWK Ukrainian localization - manual/advanced build script.

For normal use, prefer the one-command installer instead:
    000_TOOLKIT/BFME-loc-toolkit/apply-localization-rotwk.bat
(or scripts/apply_localization_rotwk.py directly) - it auto-detects the
game folder, backs up pristine files automatically, and re-runs safely any
number of times. This script is the manual equivalent, useful for building
output without touching a live game install (e.g. to inspect the result,
or to build from an arbitrary --source folder instead of an installed game).

Patches the "french" language slot (not "english") with a CSF (not .str),
plus UnicodeFontName pointed at a custom Cyrillic font. See
../../ROTWK_TEXT_AND_FONT_SYSTEM.md for the full "why" - this is just the
implementation.

Usage:
    ..\\..\\..\\000_TOOLKIT\\BFME-loc-toolkit\\python\\python.exe build.py --source "F:\\RotWK"

--source must point at a folder containing a pristine lang\\french.big and
lang\\frenchpatch201.big (a real, unpatched French 2.01 install, or
reference_french/ moved under a lang\\ subfolder). Output is written next
to this script.
"""
import argparse
import os
import re
import sys
import json
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
ROTWK_UA_DIR = os.path.dirname(HERE)                     # 005_BFME2_RoTWK_UKRAINIAN
ROTWK_DIR = os.path.dirname(ROTWK_UA_DIR)                # 003_BFME_2_RoTWK
REPO_ROOT = os.path.dirname(ROTWK_DIR)
TOOLKIT_DIR = os.path.join(REPO_ROOT, '000_TOOLKIT', 'BFME-loc-toolkit')
FONTS_DIR = os.path.join(HERE, 'fonts')
LOGOS_UA_DIR = os.path.join(REPO_ROOT, '006_LOCALIZED_LOGOS', 'RoTWK_LOGOS', '009_UA')

sys.path.insert(0, os.path.join(TOOLKIT_DIR, 'python'))
sys.path.insert(0, os.path.join(TOOLKIT_DIR, 'scripts'))
from pyBIG import Archive
from csf_tools import build_csf

STRINGS_JSON = os.path.join(ROTWK_UA_DIR, 'RotWK_strings_ua.json')
LANGUAGE_ID = 4  # French's real lotr.csf language_id, confirmed by direct byte inspection
NEW_ALBERTUS_NAME = 'AlbertusMTUA.otf'

TEXTURE_FILES = [
    (r'art\compiledtextures\lo\load_w_ea.jpg', os.path.join(LOGOS_UA_DIR, 'load_w_ea.jpg')),
    (r'art\compiledtextures\lo\logowithshadow.tga', os.path.join(LOGOS_UA_DIR, 'logowithshadow.tga')),
    (r'art\compiledtextures\ti\titlescreenuserinterface.jpg', os.path.join(LOGOS_UA_DIR, 'titlescreenuserinterface.jpg')),
    # NOTE: no art\compiledtextures\lm\lm_text.dds here - never localized.
    # Loading-screen text stays English until someone builds that asset.
]

FONTSUB = (
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
    csf_bytes = bytearray(build_csf(labels, order))
    struct.pack_into('<i', csf_bytes, 20, LANGUAGE_ID)
    return bytes(csf_bytes), len(order)


def save(path, archive):
    archive.save(path)
    with open(path, 'rb') as f:
        Archive(f.read())  # round-trip verify
    print(f'  saved + verified: {path}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True, help=r'folder with a pristine lang\french.big + lang\frenchpatch201.big')
    args = ap.parse_args()

    csf_bytes, n = build_csf_bytes()
    print(f'Built lotr.csf: {n} labels, language_id={LANGUAGE_ID}')

    with open(os.path.join(FONTS_DIR, NEW_ALBERTUS_NAME), 'rb') as f:
        albertus_bytes = f.read()

    src_french = os.path.join(args.source, 'lang', 'french.big')
    src_patch = os.path.join(args.source, 'lang', 'frenchpatch201.big')
    out_french = os.path.join(HERE, 'french.big')
    out_patch = os.path.join(HERE, 'frenchpatch201.big')

    print(f'\n--- {src_french} ---')
    with open(src_french, 'rb') as f:
        arc = Archive(f.read())
    fl = arc.file_list()

    if r'data\lotr.str' in fl:
        arc.remove_file(r'data\lotr.str')
    (arc.edit_file if 'lotr.csf' in fl else arc.add_file)('lotr.csf', csf_bytes)

    for internal_path, tex_path in TEXTURE_FILES:
        with open(tex_path, 'rb') as f:
            data = f.read()
        (arc.edit_file if internal_path in fl else arc.add_file)(internal_path, data)
    print(f'  added {len(TEXTURE_FILES)} localized textures')

    arc.add_file(NEW_ALBERTUS_NAME, albertus_bytes)

    lang_ini = arc.read_file('language.ini').decode('latin-1')
    pattern = re.compile(r'^([ \t]*LocalFontFile\s*=\s*\S*omnia\S*\.ttf[^\r\n]*)', re.MULTILINE | re.IGNORECASE)
    addition = '\r\n  LocalFontFile = ' + NEW_ALBERTUS_NAME + ' ;// Ukrainian Cyrillic Albertus MT, distinct family name'
    new_lang_ini = pattern.sub(lambda m: m.group(1) + addition, lang_ini, count=1)
    if new_lang_ini == lang_ini:
        raise RuntimeError('LocalFontFile insertion point not found - is this really a pristine French archive?')

    unicode_font_re = re.compile(r'(UnicodeFontName\s*=\s*)"[^"]*"')
    new_lang_ini, n_uf = unicode_font_re.subn(r'\1"AlbertusMTUA"', new_lang_ini)
    if n_uf != 1:
        raise RuntimeError(f'UnicodeFontName not found/replaced exactly once (found {n_uf})')

    arc.edit_file('language.ini', new_lang_ini.encode('latin-1'))
    print('  language.ini: registered AlbertusMTUA, UnicodeFontName -> AlbertusMTUA')

    arc.edit_file(r'data\ini\fontsubstitution.ini', FONTSUB.encode('latin-1'))
    print('  fontsubstitution.ini: SachaWynter + Albertus MT -> AlbertusMTUA')

    save(out_french, arc)

    print(f'\n--- {src_patch} ---')
    with open(src_patch, 'rb') as f:
        arc2 = Archive(f.read())
    fl2 = arc2.file_list()
    if r'data\lotr.str' in fl2:
        arc2.remove_file(r'data\lotr.str')
    (arc2.edit_file if 'lotr.csf' in fl2 else arc2.add_file)('lotr.csf', csf_bytes)
    save(out_patch, arc2)

    print('\nDone. Copy french.big + frenchpatch201.big into a French 2.01 install\'s lang\\ folder')
    print('(and make sure registry Language = "French" - already the case if French was ever installed).')


if __name__ == '__main__':
    main()
