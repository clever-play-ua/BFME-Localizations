# -*- coding: utf-8 -*-
r"""
BFME2 (The Battle for Middle-earth II, 1.05/1.06) Ukrainian localization --
apply_localization_bfme2.py

One-command installer. See
../../002_BFME_2/005_BFME2_UKRAINIAN/BETA_PATCH_NOTES.md for the full
technical background -- this script just automates the recipe documented
there (and, for UnicodeFontName specifically, the discovery made while
localizing RotWK: ../../003_BFME_2_RoTWK/ROTWK_TEXT_AND_FONT_SYSTEM.md
section 6).

Unlike RotWK, BFME2's own engine reads a CSF placed directly in the
"english" slot correctly (confirmed by screenshot) -- no French-slot
workaround needed here. This installer patches lang\english.big /
lang\englishpatch105.big in place; no registry changes.

Flow:
  1. Find the BFME2 game folder (registry InstallPath, cached in
     scripts\bfme2_game_path.txt, or ask).
  2. Make sure a PRISTINE (unpatched) lang\english.big +
     lang\englishpatch105.big exists to build from:
       - If lang\lang_backup_original_ua\ already has them (from a
         previous run), use those.
       - Else if the current lang\english.big looks pristine (no
         AlbertusMTUA.otf inside), back it up and use it.
       - Else -- stop and explain: repair/reinstall to get a pristine copy.
  3. Build lotr.csf from BFME2_strings_ua.json.
  4. Add AlbertusMTUA.otf ONLY (register via LocalFontFile), add
     FontSubstitution rules pointing BOTH "SachaWynter" and "Albertus MT"
     at AlbertusMTUA (never two different font files -- see
     BETA_PATCH_NOTES.md section 3, "Attempt 4"), add the localized
     textures. UnicodeFontName is left at its stock value -- setting it
     broke things here (BFME2 never had the RotWK-class bug it would fix).
  5. Write the two rebuilt archives straight into the game's lang\ folder.

Zero third-party pip dependencies -- stdlib + the vendored pyBIG + the
vendored csf_tools.py.
"""
import argparse
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
CHECK = '[OK]'
WARN = '[!]'
FAIL = '[X]'


def ok(msg):
    print(f'{GREEN}{CHECK} {msg}{RESET}')


def warn(msg):
    print(f'{YELLOW}{WARN} {msg}{RESET}')


def fail(msg):
    print(f'{RED}{FAIL} {msg}{RESET}')


HERE = os.path.dirname(os.path.abspath(__file__))
TOOLKIT_ROOT = os.path.dirname(HERE)                        # .../000_TOOLKIT/BFME-loc-toolkit
REPO_ROOT = os.path.dirname(os.path.dirname(TOOLKIT_ROOT))  # .../BFME-Localizations
BFME2_UA_DIR = os.path.join(REPO_ROOT, '002_BFME_2', '005_BFME2_UKRAINIAN')
TEXTURES_DIR = os.path.join(BFME2_UA_DIR, 'prototype', 'lang', 'Ukrainian', 'art', 'compiledtextures')
FONTS_DIR = os.path.join(BFME2_UA_DIR, 'beta', 'fonts')
STRINGS_JSON = os.path.join(BFME2_UA_DIR, 'BFME2_strings_ua.json')
GAME_PATH_CACHE = os.path.join(HERE, 'bfme2_game_path.txt')

sys.path.insert(0, os.path.join(TOOLKIT_ROOT, 'python'))
sys.path.insert(0, HERE)
from pyBIG import Archive          # noqa: E402
from csf_tools import build_csf    # noqa: E402

REG_KEY = r'SOFTWARE\WOW6432Node\Electronic Arts\Electronic Arts\The Battle for Middle-earth II'
REG_KEY_NATIVE = r'SOFTWARE\Electronic Arts\Electronic Arts\The Battle for Middle-earth II'

NEW_ALBERTUS_NAME = 'AlbertusMTUA.otf'

TEXTURE_FILES = [
    (r'art\compiledtextures\lm\lm_text.dds', os.path.join(TEXTURES_DIR, 'lm', 'lm_text.dds')),
    (r'art\compiledtextures\lo\load_w_ea.jpg', os.path.join(TEXTURES_DIR, 'lo', 'load_w_ea.jpg')),
    (r'art\compiledtextures\lo\logowithshadow.tga', os.path.join(TEXTURES_DIR, 'lo', 'logowithshadow.tga')),
    (r'art\compiledtextures\ti\titlescreenuserinterface.jpg', os.path.join(TEXTURES_DIR, 'ti', 'titlescreenuserinterface.jpg')),
]

FONTSUB = (
    # Both roles point at the SAME font (AlbertusMTUA), not two different
    # font files - pointing SachaWynter at a separate file
    # (sachawyntertight_ua.ttf) caused a garbled duplicate-text glitch
    # (2026-09-20). See build_beta_english_big.py's OWN_FONTSUB comment and
    # 001_BFME_1/004_BFME1_UKRAINIAN/v3 (which independently uses one
    # single font, "Noto Sans", for everything) for the full story.
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


# --- game folder discovery ---------------------------------------------------

def _is_valid_game_folder(path):
    return bool(path) and os.path.isfile(os.path.join(path, 'lotrbfme2.exe'))


def find_game_path_from_registry():
    try:
        import winreg
    except ImportError:
        return None
    for key in (REG_KEY, REG_KEY_NATIVE):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key) as k:
                path, _ = winreg.QueryValueEx(k, 'InstallPath')
            path = path.rstrip('\\/')
            if _is_valid_game_folder(path):
                return path
        except OSError:
            continue
    return None


def find_game_path():
    reg_path = find_game_path_from_registry()
    if reg_path:
        with open(GAME_PATH_CACHE, 'w', encoding='utf-8') as f:
            f.write(reg_path)
        return reg_path

    if os.path.exists(GAME_PATH_CACHE):
        with open(GAME_PATH_CACHE, encoding='utf-8') as f:
            cached = f.read().strip()
        if _is_valid_game_folder(cached):
            return cached

    while True:
        path = input('Path to your BFME2 folder (containing lotrbfme2.exe): ').strip().strip('"')
        if _is_valid_game_folder(path):
            with open(GAME_PATH_CACHE, 'w', encoding='utf-8') as f:
                f.write(path)
            return path
        print('  -- lotrbfme2.exe not found there. Is this a real BFME2 install folder?')


# --- archive helpers ----------------------------------------------------------

def archive_is_pristine(path):
    with open(path, 'rb') as f:
        arc = Archive(f.read())
    return NEW_ALBERTUS_NAME not in arc.file_list()


def build_csf_bytes():
    with open(STRINGS_JSON, encoding='utf-8') as f:
        entries = json.load(f)['strings']
    labels = {e['var']: unescape_for_csf(e['ua'] or e['en']) for e in entries}
    order = [e['var'] for e in entries]
    return build_csf(labels, order), len(order)


def patch_archive(src_path, out_path, csf_bytes, albertus_bytes, add_extras):
    with open(src_path, 'rb') as f:
        arc = Archive(f.read())
    fl = arc.file_list()

    if r'data\lotr.str' in fl:
        arc.remove_file(r'data\lotr.str')
    (arc.edit_file if 'lotr.csf' in fl else arc.add_file)('lotr.csf', csf_bytes)

    if add_extras:
        for internal_path, tex_path in TEXTURE_FILES:
            if not os.path.exists(tex_path):
                warn(f'texture missing, skipped: {tex_path}')
                continue
            with open(tex_path, 'rb') as f:
                data = f.read()
            (arc.edit_file if internal_path in fl else arc.add_file)(internal_path, data)

        arc.add_file(NEW_ALBERTUS_NAME, albertus_bytes)
        # sachawyntertight_ua.ttf deliberately NOT added - see FONTSUB comment.

        lang_ini = arc.read_file('language.ini').decode('latin-1')
        pattern = re.compile(r'^([ \t]*LocalFontFile\s*=\s*OmniaLTStd\.ttf[^\r\n]*)', re.MULTILINE)
        addition = '\r\n  LocalFontFile = ' + NEW_ALBERTUS_NAME + ' ;// Ukrainian Cyrillic Albertus MT, distinct family name'
        new_lang_ini = pattern.sub(lambda m: m.group(1) + addition, lang_ini, count=1)
        if new_lang_ini == lang_ini:
            raise RuntimeError('LocalFontFile insertion point not found - is this really a pristine 1.05 archive?')
        # Do NOT set UnicodeFontName here - tried once (2026-09-20), broke
        # something else (see build_beta_english_big.py's comment). BFME2
        # never had the RotWK-class bug this would have fixed anyway.
        arc.edit_file('language.ini', new_lang_ini.encode('latin-1'))

    if add_extras:
        arc.add_file(r'data\ini\fontsubstitution.ini', FONTSUB.encode('latin-1'))

    arc.save(out_path)
    with open(out_path, 'rb') as f:
        Archive(f.read())  # round-trip verify


# --- main ----------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--target', help='BFME2 install folder (skip auto-detection)')
    ap.add_argument('--yes', action='store_true', help='skip the confirmation prompt')
    args = ap.parse_args()

    print('BFME2 Ukrainian localization installer')
    print('=' * 60)

    game_path = args.target.rstrip('\\/') if args.target else find_game_path()
    if not _is_valid_game_folder(game_path):
        fail(f'{game_path} does not look like a BFME2 install (lotrbfme2.exe not found).')
        sys.exit(1)
    ok(f'Game folder: {game_path}')

    lang_dir = os.path.join(game_path, 'lang')
    backup_dir = os.path.join(lang_dir, 'lang_backup_original_ua')
    src_english = os.path.join(lang_dir, 'english.big')
    src_patch = os.path.join(lang_dir, 'englishpatch105.big')
    backup_english = os.path.join(backup_dir, 'english.big')
    backup_patch = os.path.join(backup_dir, 'englishpatch105.big')

    if os.path.exists(backup_english) and os.path.exists(backup_patch):
        ok('Pristine English backup already exists from a previous run - using it.')
        pristine_english, pristine_patch = backup_english, backup_patch
    elif os.path.exists(src_english) and os.path.exists(src_patch):
        if not archive_is_pristine(src_english):
            fail('lang\\english.big exists but is already patched, and no pristine backup was found.')
            fail('Repair/reinstall BFME2 to get a clean copy, then re-run this tool.')
            sys.exit(1)
        os.makedirs(backup_dir, exist_ok=True)
        import shutil
        shutil.copy2(src_english, backup_english)
        shutil.copy2(src_patch, backup_patch)
        ok(f'Backed up pristine English archives to {backup_dir}')
        pristine_english, pristine_patch = backup_english, backup_patch
    else:
        fail('lang\\english.big / englishpatch105.big not found - is this a real 1.05/1.06 BFME2 install?')
        sys.exit(1)

    if not os.path.exists(STRINGS_JSON):
        fail(f'Translation data not found: {STRINGS_JSON}')
        sys.exit(1)
    if not os.path.exists(os.path.join(FONTS_DIR, NEW_ALBERTUS_NAME)):
        fail(f'Font not found: {os.path.join(FONTS_DIR, NEW_ALBERTUS_NAME)}')
        sys.exit(1)

    csf_bytes, n = build_csf_bytes()
    ok(f'Built lotr.csf: {n} labels')
    with open(os.path.join(FONTS_DIR, NEW_ALBERTUS_NAME), 'rb') as f:
        albertus_bytes = f.read()

    if not args.yes:
        print()
        print(f'About to write into: {lang_dir}')
        print('  english.big, englishpatch105.big (built from the pristine backup above)')
        resp = input('Proceed? (y/n): ').strip().lower()
        if resp != 'y':
            print('Aborted, nothing written.')
            sys.exit(0)

    patch_archive(pristine_english, src_english, csf_bytes, albertus_bytes, add_extras=True)
    ok(f'Wrote {src_english}')
    patch_archive(pristine_patch, src_patch, csf_bytes, albertus_bytes, add_extras=False)
    ok(f'Wrote {src_patch}')

    print()
    ok('Done. Launch BFME2 - it should come up fully in Ukrainian.')
    print('(Pristine originals are safely kept in lang\\lang_backup_original_ua\\ - re-run this')
    print(' tool any time BFME2_strings_ua.json changes, it always rebuilds from that backup.)')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        fail(f'Unexpected error: {e}')
        raise
    finally:
        try:
            input('\nPress Enter to exit...')
        except EOFError:
            pass
