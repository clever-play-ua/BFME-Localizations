# -*- coding: utf-8 -*-
r"""
RotWK (Rise of the Witch-king) Ukrainian localization -- apply_localization_rotwk.py

One-command installer. See ../../003_BFME_2_RoTWK/ROTWK_TEXT_AND_FONT_SYSTEM.md
for the full technical background on *why* this works the way it does --
this script just automates the recipe documented there.

Flow:
  1. Find the RotWK game folder (registry InstallPath, cached in
     scripts\rotwk_game_path.txt, or ask).
  2. Confirm/set the registry Language value to "French" -- RotWK's engine
     does not read the CSF text format at all when patching the "english"
     slot in place (confirmed by direct testing), but does read it
     correctly in any real named slot; this toolkit reuses "french" the
     same way the official Korean RotWK localization reuses it (see the
     technical doc, section 3). This means real French becomes unavailable
     on this install -- same trade-off Korean's own approach accepts.
  3. Make sure a PRISTINE (unpatched) lang\french.big + frenchpatch201.big
     exists to build from:
       - If lang_backup_original_ua\ already has them (from a previous run
         of this script), use those -- guaranteed pristine.
       - Else if the current lang\french.big looks pristine (no
         AlbertusMTUA.otf inside), back it up to lang_backup_original_ua\
         and use it.
       - Else (no backup, and the current file is already patched) --
         stop and explain: French needs to be reinstalled/repaired to get
         a pristine copy, this tool cannot reconstruct one from a patched
         archive.
  4. Build lotr.csf from RotWK_strings_ua.json (the Ukrainian translation),
     set its header language_id to 4 (French's real value, confirmed by
     reading an actual French 2.01 install's own lotr.csf).
  5. Add AlbertusMTUA.otf (bundled next to this script's data folder),
     register it via LocalFontFile, point UnicodeFontName at it, and add
     FontSubstitution rules for SachaWynter/Albertus MT -> AlbertusMTUA.
  6. Write the two rebuilt archives straight into the game's lang\ folder.

Zero third-party pip dependencies -- stdlib + the vendored pyBIG + the
vendored csf_tools.py, both already used by apply_localization.py (BFME1).
"""
import argparse
import json
import os
import re
import struct
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
TOOLKIT_ROOT = os.path.dirname(HERE)                     # .../000_TOOLKIT/BFME-loc-toolkit
REPO_ROOT = os.path.dirname(os.path.dirname(TOOLKIT_ROOT))  # .../BFME-Localizations
ROTWK_UA_DIR = os.path.join(REPO_ROOT, '003_BFME_2_RoTWK', '005_BFME2_RoTWK_UKRAINIAN')
LOGOS_UA_DIR = os.path.join(REPO_ROOT, '006_LOCALIZED_LOGOS', 'RoTWK_LOGOS', '009_UA')
FONTS_DIR = os.path.join(ROTWK_UA_DIR, 'release', 'fonts')
STRINGS_JSON = os.path.join(ROTWK_UA_DIR, 'RotWK_strings_ua.json')
GAME_PATH_CACHE = os.path.join(HERE, 'rotwk_game_path.txt')

sys.path.insert(0, os.path.join(TOOLKIT_ROOT, 'python'))
sys.path.insert(0, HERE)
from pyBIG import Archive          # noqa: E402
from csf_tools import build_csf    # noqa: E402

REG_KEY = r'SOFTWARE\WOW6432Node\Electronic Arts\Electronic Arts\The Lord of the Rings, The Rise of the Witch-king'
REG_KEY_NATIVE = r'SOFTWARE\Electronic Arts\Electronic Arts\The Lord of the Rings, The Rise of the Witch-king'

LANGUAGE_ID = 4  # French's real lotr.csf language_id, confirmed by direct byte inspection
NEW_ALBERTUS_NAME = 'AlbertusMTUA.otf'

TEXTURE_FILES = [
    (r'art\compiledtextures\lo\load_w_ea.jpg', os.path.join(LOGOS_UA_DIR, 'load_w_ea.jpg')),
    (r'art\compiledtextures\lo\logowithshadow.tga', os.path.join(LOGOS_UA_DIR, 'logowithshadow.tga')),
    (r'art\compiledtextures\ti\titlescreenuserinterface.jpg', os.path.join(LOGOS_UA_DIR, 'titlescreenuserinterface.jpg')),
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


# --- game folder discovery ---------------------------------------------------

def _is_valid_game_folder(path):
    return bool(path) and os.path.isfile(os.path.join(path, 'lotrbfme2ep1.exe'))


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
        path = input('Path to your RotWK folder (containing lotrbfme2ep1.exe): ').strip().strip('"')
        if _is_valid_game_folder(path):
            with open(GAME_PATH_CACHE, 'w', encoding='utf-8') as f:
                f.write(path)
            return path
        print('  -- lotrbfme2ep1.exe not found there. Is this a real RotWK install folder?')


def get_registry_language():
    try:
        import winreg
    except ImportError:
        return None
    for key in (REG_KEY, REG_KEY_NATIVE):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key) as k:
                value, _ = winreg.QueryValueEx(k, 'Language')
            return value
        except OSError:
            continue
    return None


def set_registry_language_french():
    import winreg
    last_err = None
    for key in (REG_KEY, REG_KEY_NATIVE):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key, 0, winreg.KEY_SET_VALUE) as k:
                winreg.SetValueEx(k, 'Language', 0, winreg.REG_SZ, 'French')
            return True
        except OSError as e:
            last_err = e
            continue
    warn(f'Could not write the registry Language value automatically ({last_err}).')
    warn(r'Set it by hand: HKLM\...\Electronic Arts\Electronic Arts\The Lord of the Rings, '
         r'The Rise of the Witch-king -> Language = "French" (or run this tool as Administrator).')
    return False


# --- archive helpers ----------------------------------------------------------

def archive_is_pristine(path):
    """True if this french.big has NOT already been patched by this tool
    (no AlbertusMTUA.otf inside it)."""
    with open(path, 'rb') as f:
        arc = Archive(f.read())
    return NEW_ALBERTUS_NAME not in arc.file_list()


def build_csf_bytes():
    with open(STRINGS_JSON, encoding='utf-8') as f:
        entries = json.load(f)['strings']
    labels = {e['var']: unescape_for_csf(e['ua'] or e['en']) for e in entries}
    order = [e['var'] for e in entries]
    csf_bytes = bytearray(build_csf(labels, order))
    struct.pack_into('<i', csf_bytes, 20, LANGUAGE_ID)
    return bytes(csf_bytes), len(order)


def patch_archive(src_path, out_path, csf_bytes, albertus_bytes, add_textures, add_fontsub):
    with open(src_path, 'rb') as f:
        arc = Archive(f.read())
    fl = arc.file_list()

    if r'data\lotr.str' in fl:
        arc.remove_file(r'data\lotr.str')
    (arc.edit_file if 'lotr.csf' in fl else arc.add_file)('lotr.csf', csf_bytes)

    if add_textures:
        for internal_path, tex_path in TEXTURE_FILES:
            if not os.path.exists(tex_path):
                warn(f'texture missing, skipped: {tex_path}')
                continue
            with open(tex_path, 'rb') as f:
                data = f.read()
            (arc.edit_file if internal_path in fl else arc.add_file)(internal_path, data)

        arc.add_file(NEW_ALBERTUS_NAME, albertus_bytes)

        lang_ini = arc.read_file('language.ini').decode('latin-1')
        pattern = re.compile(r'^([ \t]*LocalFontFile\s*=\s*\S*omnia\S*\.ttf[^\r\n]*)', re.MULTILINE | re.IGNORECASE)
        addition = '\r\n  LocalFontFile = ' + NEW_ALBERTUS_NAME + ' ;// Ukrainian Cyrillic Albertus MT, distinct family name'
        new_lang_ini = pattern.sub(lambda m: m.group(1) + addition, lang_ini, count=1)
        if new_lang_ini == lang_ini:
            raise RuntimeError('LocalFontFile insertion point not found in language.ini -- is this really a pristine French archive?')

        unicode_font_re = re.compile(r'(UnicodeFontName\s*=\s*)"[^"]*"')
        new_lang_ini, n_uf = unicode_font_re.subn(r'\1"AlbertusMTUA"', new_lang_ini)
        if n_uf != 1:
            raise RuntimeError(f'UnicodeFontName not found/replaced exactly once (found {n_uf})')
        arc.edit_file('language.ini', new_lang_ini.encode('latin-1'))

    if add_fontsub:
        arc.edit_file(r'data\ini\fontsubstitution.ini', FONTSUB.encode('latin-1'))

    arc.save(out_path)
    with open(out_path, 'rb') as f:
        Archive(f.read())  # round-trip verify


# --- main ----------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--target', help='RotWK install folder (skip auto-detection)')
    ap.add_argument('--yes', action='store_true', help='skip the confirmation prompt')
    args = ap.parse_args()

    print('RotWK Ukrainian localization installer')
    print('=' * 60)

    game_path = args.target.rstrip('\\/') if args.target else find_game_path()
    if not _is_valid_game_folder(game_path):
        fail(f'{game_path} does not look like a RotWK install (lotrbfme2ep1.exe not found).')
        sys.exit(1)
    ok(f'Game folder: {game_path}')

    lang_dir = os.path.join(game_path, 'lang')
    backup_dir = os.path.join(lang_dir, 'lang_backup_original_ua')
    src_french = os.path.join(lang_dir, 'french.big')
    src_patch = os.path.join(lang_dir, 'frenchpatch201.big')
    backup_french = os.path.join(backup_dir, 'french.big')
    backup_patch = os.path.join(backup_dir, 'frenchpatch201.big')

    if os.path.exists(backup_french) and os.path.exists(backup_patch):
        ok('Pristine French backup already exists from a previous run - using it.')
        pristine_french, pristine_patch = backup_french, backup_patch
    elif os.path.exists(src_french) and os.path.exists(src_patch):
        if not archive_is_pristine(src_french):
            fail('lang\\french.big exists but is already patched, and no pristine backup was found.')
            fail('Repair/reinstall the French language pack to get a clean copy, then re-run this tool.')
            sys.exit(1)
        os.makedirs(backup_dir, exist_ok=True)
        import shutil
        shutil.copy2(src_french, backup_french)
        shutil.copy2(src_patch, backup_patch)
        ok(f'Backed up pristine French archives to {backup_dir}')
        pristine_french, pristine_patch = backup_french, backup_patch
    else:
        fail('lang\\french.big / frenchpatch201.big not found.')
        fail('This tool patches the French language slot (see ROTWK_TEXT_AND_FONT_SYSTEM.md section 3')
        fail('for why) - install/repair the French language pack for RotWK first (EA App / Steam ->')
        fail('game properties -> language -> French), then re-run this tool.')
        sys.exit(1)

    reg_lang = get_registry_language()
    if reg_lang != 'French':
        warn(f'Registry Language is currently "{reg_lang}", not "French".')
        if not args.yes:
            resp = input('Switch it to "French" now so the game actually loads these files? (y/n): ').strip().lower()
            if resp != 'y':
                fail('Aborted - without Language="French" in the registry, the game will keep loading a different slot.')
                sys.exit(1)
        if set_registry_language_french():
            ok('Registry Language set to "French".')
    else:
        ok('Registry Language is already "French".')

    if not os.path.exists(STRINGS_JSON):
        fail(f'Translation data not found: {STRINGS_JSON}')
        sys.exit(1)
    if not os.path.exists(os.path.join(FONTS_DIR, NEW_ALBERTUS_NAME)):
        fail(f'Font not found: {os.path.join(FONTS_DIR, NEW_ALBERTUS_NAME)}')
        sys.exit(1)

    csf_bytes, n = build_csf_bytes()
    ok(f'Built lotr.csf: {n} labels, language_id={LANGUAGE_ID}')
    with open(os.path.join(FONTS_DIR, NEW_ALBERTUS_NAME), 'rb') as f:
        albertus_bytes = f.read()

    if not args.yes:
        print()
        print(f'About to write into: {lang_dir}')
        print('  french.big, frenchpatch201.big (built from the pristine backup above)')
        resp = input('Proceed? (y/n): ').strip().lower()
        if resp != 'y':
            print('Aborted, nothing written.')
            sys.exit(0)

    patch_archive(pristine_french, src_french, csf_bytes, albertus_bytes, add_textures=True, add_fontsub=True)
    ok(f'Wrote {src_french}')
    patch_archive(pristine_patch, src_patch, csf_bytes, albertus_bytes, add_textures=False, add_fontsub=False)
    ok(f'Wrote {src_patch}')

    print()
    ok('Done. Launch RotWK - it should come up fully in Ukrainian.')
    print('(Pristine originals are safely kept in lang\\lang_backup_original_ua\\ - re-run this')
    print(' tool any time RotWK_strings_ua.json changes, it always rebuilds from that backup.)')


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
