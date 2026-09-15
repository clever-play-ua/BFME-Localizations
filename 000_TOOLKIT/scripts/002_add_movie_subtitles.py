"""
Adds cinematic/tutorial subtitles to a rebuilt lang\\english.big and flags the
matching Video entries in video.ini so the engine actually looks for them.

Two things are required for movie subtitles to work -- both handled here:
  1. data\\english\\Movies\\<Name>.ini (SubTitleBlock) files, added to
     lang\\english.big. The 13 files in bfme1/movies/ (one level up from
     this scripts/ folder) are the FINAL tuned versions (FontName = Albertus MT,
     FontPitch scaled 1.5x from stock, Style = OUTLINED_FADE instead of the
     default SOLID_FADE black box) -- copy them as-is, no more edits needed.
  2. video.ini's Video blocks need "HasSubtitles = Yes" or the engine never
     even looks at the Movies\\*.ini above, no matter how correct they are.
     video.ini lives in data\\ini\\video.ini inside ini.big and/or whichever
     _patch*.big carries the currently-active copy -- check both, the patch
     archive's copy takes priority if it exists.

Usage:
    python 002_add_movie_subtitles.py --english-big path\\to\\english.big [--ini-big path\\to\\ini.big] [--patch-big path\\to\\_patchXXX.big]

Pass --ini-big and/or --patch-big for every archive that has its own
data\\ini\\video.ini copy (scan with the snippet in meta.movie_subtitles_HasSubtitles_WARNING
if unsure which ones do for a given install).
"""
import argparse
import glob
import os
import re

from pyBIG import Archive

HERE = os.path.dirname(os.path.abspath(__file__))
MOVIES_DIR = os.path.join(os.path.dirname(HERE), 'movies')
VIDEO_INI_PATH = r'data\ini\video.ini'
VIDEO_NAMES = [
    'Evil_AmonHen_Intro', 'Evil_Ithilien_Intro', 'Evil_NearHarad_Outro', 'Evil_ShelobsLair_Intro',
    'Good_Lothlorien_Intro', 'Good_ShelobsLair_Intro', 'Opening_Game_Cinematic',
    'TutorialBasesAndUnits', 'TutorialHeroes', 'TutorialMovesAndAttacks',
    'TutorialSpecialPowers', 'TutorialVeterancy', 'TutorialWorldMap',
]


def add_movie_inis(english_big_path):
    with open(english_big_path, 'rb') as f:
        src = Archive(f.read())
    header = open(english_big_path, 'rb').read(4).decode()

    targets = {}
    for fname in os.listdir(MOVIES_DIR):
        internal_path = r'data\english\Movies\%s' % fname
        with open(os.path.join(MOVIES_DIR, fname), 'rb') as f:
            targets[internal_path] = f.read()

    new_archive = Archive.empty(header=header)
    for name in src.file_list():
        if name in targets:
            continue
        new_archive.add_file(name, src.read_file(name))
    for internal_path, content in targets.items():
        new_archive.add_file(internal_path, content)
    new_archive.save(english_big_path)
    print(f'added {len(targets)} movie subtitle ini files to {english_big_path}')


def flag_has_subtitles(archive_path):
    with open(archive_path, 'rb') as f:
        src = Archive(f.read())
    header = open(archive_path, 'rb').read(4).decode()

    if VIDEO_INI_PATH not in src.file_list():
        print(f'{archive_path} has no {VIDEO_INI_PATH}, skipping')
        return

    text = src.read_file(VIDEO_INI_PATH).decode('utf-8', errors='replace')
    changed = 0
    for name in VIDEO_NAMES:
        pattern = re.compile(r'(Video ' + re.escape(name) + r'\r?\n(?:.*\r?\n)*?)(End)', re.MULTILINE)
        m = pattern.search(text)
        if not m:
            continue
        block = m.group(1)
        if 'HasSubtitles' in block:
            continue
        new_block = block + '\tHasSubtitles = Yes\r\n'
        text = text[:m.start()] + new_block + m.group(2) + text[m.end():]
        changed += 1

    if changed == 0:
        print(f'{archive_path}: no changes needed (already flagged or no matching videos)')
        return

    new_archive = Archive.empty(header=header)
    for name in src.file_list():
        if name == VIDEO_INI_PATH:
            continue
        new_archive.add_file(name, src.read_file(name))
    new_archive.add_file(VIDEO_INI_PATH, text.encode('utf-8', errors='replace'))
    new_archive.save(archive_path)
    print(f'flagged {changed} Video blocks with HasSubtitles = Yes in {archive_path}')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--english-big', required=True)
    parser.add_argument('--ini-big', default=None)
    parser.add_argument('--patch-big', action='append', default=[],
                         help='repeatable, one per _patch*.big that carries its own data\\ini\\video.ini')
    args = parser.parse_args()

    add_movie_inis(args.english_big)
    if args.ini_big:
        flag_has_subtitles(args.ini_big)
    for p in args.patch_big:
        flag_has_subtitles(p)


if __name__ == '__main__':
    main()
