"""
Small follow-up to pass 3: a handful of LOWERCASE adjectival/genitive forms
("гондорська", "назгулів", ...) weren't caught by pass 2's corpus-only scan,
which only looked at capitalized (proper-noun-shaped) words. Found by a direct
case-insensitive re-scan after pass 3 - see conversation for how these were
confirmed real (not the earlier false-positive "Роган"/"Рохан" mix-up, which
turned out to be a mis-transcribed glossary entry, not a real corpus issue,
and was correctly never touched).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UA_DIR = os.path.dirname(HERE)
STRINGS_PATH = os.path.join(UA_DIR, 'BFME2_strings_ua.json')

FIXES = {
    'гондорців': 'ґондорців',
    'гондорська': 'ґондорська',
    'гондорське': 'ґондорське',
    'гондорського': 'ґондорського',
    'назгулів': 'назґулів',
}

with open(STRINGS_PATH, encoding='utf-8') as f:
    data = json.load(f)

changed = 0
for entry in data['strings']:
    ua = entry.get('ua') or ''
    if not ua:
        continue
    new_ua = ua
    for wrong, correct in FIXES.items():
        new_ua = new_ua.replace(wrong, correct)
    if new_ua != ua:
        entry['ua'] = new_ua
        changed += 1

with open(STRINGS_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'entries changed: {changed}')
