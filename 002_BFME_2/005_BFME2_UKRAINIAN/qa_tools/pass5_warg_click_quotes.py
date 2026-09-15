"""
QA pass 5: three more fixes found by direct manual review of the file
(2026-09-15):

  1. "варг" (г) -> "варґ" (ґ) - same OBJECT:/CONTROLBAR: (г) vs Map:/SCRIPT:/
     DIALOGEVENT: (ґ) split pattern already fixed for Gondor/Gimli/etc in
     pass 3, just missed there because "варг" is only 4 letters and pass 2's
     corpus-only scanner only looked at words >= 5 letters long.
  2. "клацн-" (Click, old-style verb stem) -> "клікн-" - matches the
     terminology switch BFME1's own UA translation already established
     (TOOLKIT_NOTES.md: "Клацніть->Клікніть"); BFME2 currently uses only
     "клацн-" (364 occurrences) and zero "клікн-".
  3. Escaped straight quotes (\\") around an inline phrase -> proper Ukrainian
     guillemets « » (opening/closing alternate within each string).
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
UA_DIR = os.path.dirname(HERE)
STRINGS_PATH = os.path.join(UA_DIR, 'BFME2_strings_ua.json')

WARG_FIXES = {
    'Варг': 'Варґ', 'Варги': 'Варґи',
    'варг': 'варґ', 'варга': 'варґа', 'варгах': 'варґах',
    'варги': 'варґи', 'варгів': 'варґів',
}
warg_pattern = re.compile(r'\b(' + '|'.join(re.escape(w) for w in sorted(WARG_FIXES, key=len, reverse=True)) + r')\b')

click_pattern = re.compile(r'([Кк])лацн')


def fix_warg(text):
    return warg_pattern.sub(lambda m: WARG_FIXES[m.group(0)], text)


def fix_click(text):
    return click_pattern.sub(lambda m: m.group(1) + 'лікн', text)


def fix_quotes(text):
    """Replace paired \\" ... \\" with « ... » (odd occurrence = opening «,
    even = closing »). Skips a trailing unpaired \\" (leaves it alone rather
    than guessing)."""
    parts = text.split('\\"')
    if len(parts) == 1:
        return text
    out = parts[0]
    for i, part in enumerate(parts[1:], start=1):
        mark = '«' if i % 2 == 1 else '»'  # « / »
        out += mark + part
    if len(parts) % 2 == 0:
        # odd number of \" total -> last one had no partner, put it back as-is
        out = text
    return out


with open(STRINGS_PATH, encoding='utf-8') as f:
    data = json.load(f)

warg_changed = click_changed = quote_changed = 0
for entry in data['strings']:
    ua = entry.get('ua') or ''
    if not ua:
        continue
    new_ua = fix_warg(ua)
    if new_ua != ua:
        warg_changed += 1
    ua = new_ua

    new_ua = fix_click(ua)
    if new_ua != ua:
        click_changed += 1
    ua = new_ua

    new_ua = fix_quotes(ua)
    if new_ua != ua:
        quote_changed += 1
    ua = new_ua

    entry['ua'] = ua

with open(STRINGS_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'варг->варґ: {warg_changed} entries changed')
print(f'клацн->клікн: {click_changed} entries changed')
print(f'straight quotes -> «»: {quote_changed} entries changed')
