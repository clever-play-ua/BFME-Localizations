"""Dump untranslated faction rows; mark lines the translation memory already knows."""
import json, sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tm
from rows import rows_of

BS = chr(92) + 'n'
FACTION = sys.argv[1] if len(sys.argv) > 1 else 'Isengard'
STR, UA, whole, line = tm.build()
d = json.load(open(f'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_UK_WIP/Factions/{FACTION}_AoR_UA.json', encoding='utf-8'))
todo = [r for r in rows_of(d) if 'див' not in r and r['status'] == 'немає перекладу']
known, unknown = {}, collections.Counter()
for r in todo:
    for l in r['en'].split(BS):
        k = tm.norm(l)
        if not k:
            continue
        if k in line:
            known[k] = line[k].most_common(1)[0][0]
        else:
            unknown[k] += 1
json.dump({'known': known, 'unknown': sorted(unknown)}, open(os.path.join(HERE, 'tm_cov.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump([{'var': r['var'], 'type': r['type'], 'en': r['en']} for r in todo], open(os.path.join(HERE, 'todo.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(todo), 'rows;', len(known), 'known lines;', len(unknown), 'unknown lines')
with open(os.path.join(HERE, 'todo.txt'), 'w', encoding='utf-8') as f:
    for r in todo:
        f.write(f"## {r['var']} [{r['type']}]\n")
        for l in r['en'].split(BS):
            k = tm.norm(l)
            f.write(('  = ' + known[k] if k in known else '  ? ' + k) + '\n')
