"""
One-off diagnostic: scan EVERY .big archive in the game folder (root AND
lang\\) for ANY entry ending in language.ini / fontsubstitution.ini /
headertemplate.ini, and dump the FULL TEXT of each one found. We already
patch the first two everywhere they appear; headertemplate.ini we've never
touched at all, and it's the most likely place the remaining broken
"small header / subtitle" font is declared (it defines named text STYLES
used all over the UI, separate from language.ini's fixed font-role list).

Output goes to BOTH the console AND a text file next to this script
(font_scan_output.txt) -- just send that file back.

Usage: python scan_fonts.py "C:\\path\\to\\your\\BFME1 folder"
(or just run it with no arg and it'll ask)
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from pyBIG import Archive

game_path = sys.argv[1] if len(sys.argv) > 1 else input('Path to your BFME1 folder: ').strip().strip('"')

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'font_scan_output.txt')
out_lines = []


def out(*args):
    line = ' '.join(str(a) for a in args)
    print(line)
    out_lines.append(line)


targets = ('language.ini', 'fontsubstitution.ini', 'headertemplate.ini')
found_any = False


def scan_big(full_path, label):
    global found_any
    try:
        with open(full_path, 'rb') as f:
            data = f.read()
        arc = Archive(data)
    except Exception as e:
        out(f'{label}: could not open ({e})')
        return
    hits = [name for name in arc.entries if name.lower().endswith(targets)]
    for h in hits:
        found_any = True
        out(f'=== {label} :: {h} ===')
        try:
            txt = arc.read_file(h).decode('latin-1')
        except Exception as e:
            out(f'  (could not decode: {e})')
            continue
        out(txt)
        out(f'--- end {h} ---')
        out()


for fname in sorted(os.listdir(game_path)):
    if fname.lower().endswith('.big'):
        scan_big(os.path.join(game_path, fname), fname)

lang_dir = os.path.join(game_path, 'lang')
if os.path.isdir(lang_dir):
    for fname in sorted(os.listdir(lang_dir)):
        if fname.lower().endswith('.big'):
            scan_big(os.path.join(lang_dir, fname), f'lang\\{fname}')

if not found_any:
    out('No language.ini / fontsubstitution.ini / headertemplate.ini found anywhere '
        '-- unexpected, double check the game path.')

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_lines))

print()
print(f'Saved full output to: {OUT_PATH}')
print('Send me that file.')
input('Press Enter to exit...')
