"""
Rebuilds lang\\english.big with the Ukrainian text from bfme1_localization.json.

Usage:
    pip install pyBIG
    python 001_build_localized_big.py --source path\\to\\original\\english.big --out path\\to\\output\\english.big

What it does:
  1. Reads bfme1_localization.json (var/en/ua array) from the parent folder
     (bfme1/, one level up from this scripts/ folder).
  2. Opens --source (any existing english.big — vanilla or another translation's
     package) and reads every file inside it EXCEPT lotr.csf, keeping them as-is
     (fonts, headertemplate.ini, language.ini, movies, etc. — whatever it already has).
  3. Rebuilds lang\\english\\lotr.csf using "ua" text where available for a label,
     falling back to the archive's own existing CSF text, then to the JSON's "en" text.
  4. Saves the result to --out.

This does NOT by itself fix fonts or the CSF/.str conflict — read meta.font_WARNING
and meta.text_source_priority_WARNING in the JSON first and handle those for your
specific install (they usually need per-archive fixes, e.g. duplicated fontsubstitution.ini
inside a patch .big, or a stray data\\lotr.str overriding the CSF).
"""

import argparse
import json
import os

from pyBIG import Archive
from csf_tools import read_csf, build_csf

CSF_PATH = r'lang\english\lotr.csf'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--source', required=True, help='existing english.big to use as a base (its non-CSF files are kept as-is)')
    parser.add_argument('--out', required=True, help='where to save the rebuilt english.big')
    parser.add_argument('--json', default=None, help='path to bfme1_localization.json (default: bfme1/, one level up from this script)')
    args = parser.parse_args()

    json_path = args.json or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bfme1_localization.json')
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    entries = data['strings'] if isinstance(data, dict) and 'strings' in data else data
    print(f'loaded {len(entries)} entries from {json_path}')

    with open(args.source, 'rb') as f:
        src_data = f.read()
    src = Archive(src_data)

    try:
        existing_csf = src.read_file(CSF_PATH)
        existing_labels, existing_order = read_csf(existing_csf)
    except KeyError:
        existing_labels, existing_order = {}, []
    print(f'source archive already has {len(existing_order)} labels in its own CSF')

    # merge: start from the source archive's own order/text, then overlay our
    # translated entries (using "ua", falling back to "en" if "ua" is empty),
    # and append any brand-new labels the JSON has that the source doesn't.
    final_labels = dict(existing_labels)
    final_order = list(existing_order)

    added = 0
    updated = 0
    for entry in entries:
        label = entry['var']
        text = entry.get('ua') or entry.get('en') or ''
        if label not in final_labels:
            final_order.append(label)
            added += 1
        elif final_labels.get(label) != text:
            updated += 1
        final_labels[label] = text

    print(f'labels updated: {updated}, labels newly added: {added}, total: {len(final_order)}')

    csf_bytes = build_csf(final_labels, final_order)

    new_archive = Archive.empty(header='BIG4')
    for name in src.file_list():
        if name == CSF_PATH:
            continue
        new_archive.add_file(name, src.read_file(name))
    new_archive.add_file(CSF_PATH, csf_bytes)
    new_archive.save(args.out)
    print(f'saved {args.out}')

    # quick verify
    with open(args.out, 'rb') as f:
        verify_data = f.read()
    v_labels, v_order = read_csf(Archive(verify_data).read_file(CSF_PATH))
    print(f'verify OK: {len(v_order)} labels readable from the saved archive')


if __name__ == '__main__':
    main()
