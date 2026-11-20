"""Round 20 (2026-11-10, FoLD's 18:16 export + user answers 1-20), GLOBAL over every text source:
 1 Builder = «Будівельник» everywhere          3 Pillage = «Мародерство»
 9 «~ ПАСИВНА ЗДІБНІСТЬ ~» for every standalone passive line
10 Recruit time: heroes «Час вербування», units «Час тренування»
12 Isengard Furnace = «Горнило»                13 «Придбати для загону «…»»
14 revive texts without «героя, / героїню, / отамана,»
15 building upgrades «+N од. міцності» (not здоров'я)
17 «Гнів Карадрасу»    18 «Біла леді»    19 «Західного краю»    20 «Три мисливці»
(2 «Армія, гідна Володаря» and 7 Isengard level lines without «до» live in round19/apply10.)  --dry."""
import json, os, re, sys
H = os.path.dirname(os.path.abspath(__file__))


def _key(en):
    t = re.sub(r'\s*\(&\w\)', '', (en or '').replace('\\n', '\n')).replace('&', '')
    return re.sub(r'\s+', ' ', t).strip().lower()


def fix(var, en, ua):
    if not ua:
        return ua
    u, v, e, k = ua, var.lower(), en or '', _key(en)
    # 1 Builder
    if k in ('builder', 'worker', 'builder / worker') and u.strip() == 'Майстер':
        u = u.replace('Майстер', 'Будівельник')
    # 3 Pillage
    if k == 'pillage' and u.strip() == 'Мародер':
        u = u.replace('Мародер', 'Мародерство')
    u = u.replace('«Мародер»', '«Мародерство»')
    # 9 passive line
    u = re.sub(r'(?m)^[ \t]*Пасивна здібність\.?[ \t]*$', '~ ПАСИВНА ЗДІБНІСТЬ ~', u)
    # 10 recruit time
    hero = 'recruit' in v and 'ship' not in v
    if hero:
        u = u.replace('Час тренування:', 'Час вербування:')
    elif re.search(r'(?i)recruit time', e) or v.startswith('controlbar:tooltipbuild'):
        u = u.replace('Час вербування:', 'Час тренування:')
    # 12 Furnace (Isengard) = Горнило
    if 'Furnace' in e:
        u = u.replace('Плавилень', 'Горнил').replace('Плавильні:', 'Горнила:').replace('Плавильня', 'Горнило')
    # 13 purchase for a squad
    u = u.replace('Придбати загону «', 'Придбати для загону «')
    # 14 revive
    u = re.sub(r'(Відродити полегл\w+ в бою),? (?:героя|героїню|отамана),? ', r'\1 ', u)
    u = re.sub(r'(Відродити полегл\w+ в бою), ', r'\1 ', u)
    # 15 building hit points
    if 'швидкості тренування' in u or 'швидкість тренування' in u:
        u = re.sub(r"\+(\d+) здоров'я", r'+\1 од. міцності', u)
    # 17-20
    u = u.replace('Гнів Карадраса', 'Гнів Карадрасу')
    u = u.replace('Біла Пані', 'Біла леді').replace('Білою Пані', 'Білою леді').replace('Білої Пані', 'Білої леді')
    u = u.replace('Західної Межі', 'Західного краю')
    u = u.replace('Троє мисливців', 'Три мисливці')
    return u


if __name__ == '__main__':
    a9 = open(os.path.join(H, 'apply9.py'), encoding='utf-8').read()
    exec(a9.split('EX = [')[0]); walker = a9.split('log = []')[1]
    LOGNAME = 'round20_log.txt'
    exec('log = []' + walker)
