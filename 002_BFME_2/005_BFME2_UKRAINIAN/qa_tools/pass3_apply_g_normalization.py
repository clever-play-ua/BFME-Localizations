"""
QA pass 3: apply the г -> ґ normalization the user confirmed (2026-09-15) for
Tolkien proper names, using the exact variant pairs pass 2 already found in
BFME2_ua_hg_consistency_report.json's corpus_only_findings.

For every finding group, whichever variant(s) do NOT contain 'ґ'/'Ґ' get
replaced (whole-word, case-preserving per occurrence) by the same word with
г->ґ / Г->Ґ swapped - i.e. the sibling spelling that's already used elsewhere
in the group for the same name, so no new spelling is invented, only the
inconsistent minority is folded into the group's ґ-form.

Idempotent: re-running after the fix finds nothing left to change.
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
UA_DIR = os.path.dirname(HERE)
STRINGS_PATH = os.path.join(UA_DIR, 'BFME2_strings_ua.json')
REPORT_PATH = os.path.join(UA_DIR, 'BFME2_ua_hg_consistency_report.json')

with open(REPORT_PATH, encoding='utf-8') as f:
    report = json.load(f)

replacements = {}
for group in report['corpus_only_findings']:
    variants = list(group['variants'].keys())
    has_g = [v for v in variants if 'ґ' in v.lower()]
    no_g = [v for v in variants if 'ґ' not in v.lower()]
    if not has_g or not no_g:
        continue
    for wrong in no_g:
        correct = wrong.replace('г', 'ґ').replace('Г', 'Ґ')
        replacements[wrong] = correct

print(f'Replacement rules built: {len(replacements)}')
for wrong, correct in sorted(replacements.items()):
    print(f'  {wrong} -> {correct}')

# Longest-first so e.g. "Ґондорські" (a compound) is matched before "Ґондор" would be
pattern = re.compile(
    r'\b(' + '|'.join(re.escape(w) for w in sorted(replacements, key=len, reverse=True)) + r')\b'
)


def fix(text):
    return pattern.sub(lambda m: replacements[m.group(0)], text)


with open(STRINGS_PATH, encoding='utf-8') as f:
    data = json.load(f)

changed_entries = 0
total_swaps = 0
for entry in data['strings']:
    ua = entry.get('ua') or ''
    if not ua:
        continue
    new_ua, n = pattern.subn(lambda m: replacements[m.group(0)], ua)
    if n:
        entry['ua'] = new_ua
        changed_entries += 1
        total_swaps += n

with open(STRINGS_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'\nEntries changed: {changed_entries}')
print(f'Total word occurrences normalized to ґ: {total_swaps}')
print(f'Saved: {STRINGS_PATH}')
