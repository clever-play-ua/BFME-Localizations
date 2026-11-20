"""Hero pages: list untranslated rows (with EN) and rows that break our standards -> ../hero_lint.txt"""
import glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
HW = 'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_UK_WIP/heroes_web/'
slugs = open(os.path.join(HERE, '..', 'hero_slugs.txt')).read().split()
RULES = [
    (r'Потрібно: Рівень', 'Необхідно: Рівень'), (r'(?m)^\s*Пасивна здібність', '~ ПАСИВНА ЗДІБНІСТЬ ~'),
    (r'протягом \d+ сек\.(?! поступово)', 'на N сек.'), (r'прохідну ділянку', 'оберіть ділянку'), (r'ЛКМ|лівою кнопкою', 'Клікніть'),
    (r'Потребує \d+ рівня', 'Необхідно: Рівень N'), (r'\+\d+% до броні', '+N% броні'), (r'Придбати загону', 'Придбати для загону'),
    (r'[ыэъёЫЭЪЁ]', 'russian letter'), (r'ʼ', "apostrophe '"), (r'Оберіть, щоб активувати|Натисніть, щоб', 'Клікніть, щоб активувати'),
    (r'(?<!бонус )(?<![+-])\b\d+% до пошкоджень', 'check бонус'), (r'шкод[иуоа]\b', 'пошкодження'), (r'\bЗакликає\b|\bзакликає\b', 'прикликає?'),
    (r'Час перезарядки', 'Час відновлення'), (r'Сісти на коня|Спішитись\b', 'Сісти верхи / Спішитися'),
]
out_m, out_r = [], []
for s in slugs:
    p = HW + s + '.html'
    if not os.path.exists(p):
        continue
    D = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', open(p, encoding='utf-8').read(), re.S).group(1))
    for n in D['nodes']:
        for x in n['rows']:
            if x.get('ref') or x.get('dup'):
                continue
            ua = (x.get('uk') or '').replace('\\n', '\n')
            if x['st'] == 'missing' or not ua.strip():
                out_m.append(f"## {s} | {n['name']} | {x['v']} [{x.get('t')}]\n  EN: {x['en'].replace(chr(92)+'n', ' / ').replace(chr(10), ' / ')}")
                continue
            hits = [why for pat, why in RULES if re.search(pat, ua)]
            if hits:
                out_r.append(f"## {s} | {x['v']} [{x['st']}] {hits}\n  UA: {ua.replace(chr(10), ' / ')[:260]}")
with open(os.path.join(HERE, '..', 'hero_lint.txt'), 'w', encoding='utf-8') as o:
    o.write(f'===== MISSING ({len(out_m)})\n' + '\n'.join(out_m) + f'\n\n===== RULE HITS ({len(out_r)})\n' + '\n'.join(out_r) + '\n')
print(len(out_m), 'missing;', len(out_r), 'rule hits')
