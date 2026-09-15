"""
QA pass 4: three specific hero/place-name corrections requested directly by
the user (2026-09-15), each verified against the exact inflected forms
actually present in BFME2_strings_ua.json before writing the replacement map
(same technique as pass 3b - exact whole-word matches only, no broad letter
substitution that could touch unrelated words):

  1. Rohan: "Рохан" (х) -> "Роган" (г) - user's explicit call, overrides what
     the corpus itself consistently used until now.
  2. Faramir: "Фарамир" (и, Russian-style ending) -> "Фарамір" (і).
  3. Pippin: "Піппін" (prototype's own double-п spelling) -> "Піпін"
     (single-п, matching BFME1's already-established 20 uses).

Merry needed no fix - the corpus already uses "Меррі" everywhere (9/9), the
issue was only in this project's own glossary file (tolkien_glossary_ua.json),
already corrected there directly.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
UA_DIR = os.path.dirname(HERE)
STRINGS_PATH = os.path.join(UA_DIR, 'BFME2_strings_ua.json')

FIXES = {
    # Rohan: х -> г (all forms confirmed present via a direct corpus scan)
    'Рохан': 'Роган',
    'Рохана': 'Рогана',
    'Рохану': 'Рогану',
    'Рохані': 'Рогані',
    'Роханська': 'Роганська',
    'Роханський': 'Роганський',
    'Роханські': 'Роганські',
    'Роханский': 'Роганський',  # also fixes the missing "ь"/Russian "-ский" ending

    # Faramir: и -> і
    'Фарамир': 'Фарамір',
    'Фарамира': 'Фараміра',
    'Фарамиром': 'Фараміром',

    # Pippin: пп -> п
    'Піппін': 'Піпін',
    'Піппіна': 'Піпіна',
    'Піппіну': 'Піпіну',
}

pattern = re.compile(r'\b(' + '|'.join(re.escape(w) for w in sorted(FIXES, key=len, reverse=True)) + r')\b')

with open(STRINGS_PATH, encoding='utf-8') as f:
    data = json.load(f)

changed_entries = 0
total_swaps = 0
for entry in data['strings']:
    ua = entry.get('ua') or ''
    if not ua:
        continue
    new_ua, n = pattern.subn(lambda m: FIXES[m.group(0)], ua)
    if n:
        entry['ua'] = new_ua
        changed_entries += 1
        total_swaps += n

with open(STRINGS_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'Entries changed: {changed_entries}')
print(f'Total word occurrences fixed: {total_swaps}')
