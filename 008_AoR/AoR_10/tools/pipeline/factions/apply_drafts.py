"""Validate tr_<faction>.py drafts against the untranslated rows and write AoR_UK_WIP/Factions/<Faction>_AI_drafts.json
(read by make_faction.py with the lowest priority). usage: python apply_drafts.py Isengard"""
import importlib, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
FACTION = sys.argv[1] if len(sys.argv) > 1 else 'Isengard'
T = importlib.import_module('tr_' + FACTION.lower()).T
todo = json.load(open(os.path.join(HERE, 'todo.json'), encoding='utf-8'))
BS = chr(92) + 'n'
LV = 'Кожен рівень підвищує показники'
problems, out = [], []
want = {r['var'] for r in todo}
for r in todo:
    v = r['var']
    if v not in T:
        problems.append(('MISSING', v, r['en'][:60])); continue
    en, ua = r['en'].replace(BS, '\n'), T[v]
    hk_en = re.findall(r'&([A-Za-z0-9])', en); hk_ua = re.findall(r'&([A-Za-z0-9])', ua)
    if hk_en != hk_ua or (hk_ua and not ua.rstrip().endswith(f'(&{hk_ua[0]})')):
        problems.append(('HOTKEY', v, ua))
    tok = lambda s: sorted(re.findall(r'%[sdi%]', s))
    if tok(en) != tok(ua):
        problems.append(('PLACEHOLDER', v, ua))
    ne, nu = len(en.strip().split('\n')), len(ua.strip().split('\n'))
    if LV in ua:
        nu -= 2
    if ne != nu:
        problems.append(('LINES', v, f'{ne} vs {nu}'))
    if 'ʼ' in ua or re.search(r'[ыэъёЫЭЪЁ]', ua):
        problems.append(('CHARS', v, ua))
    out.append({'var': v, 'en': r['en'], 'uk_ai': ua.replace('\n', BS)})
extra = set(T) - want
for p in problems:
    print(*p)
print(len(out), 'drafts;', len(problems), 'problems;', len(extra), 'unused:', sorted(extra)[:10])
dst = f'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_UK_WIP/Factions/{FACTION}_AI_drafts.json'
json.dump({'meta': {'faction': FACTION, 'note': 'AI drafts for rows that had no Ukrainian at all (lowest priority: any proofread text wins).'},
           'strings': out}, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(dst)
