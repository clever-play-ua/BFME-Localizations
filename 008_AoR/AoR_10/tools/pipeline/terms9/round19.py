"""Round 19 (2026-11-10, FoLD's Isengard proofread + user answers).
GLOBAL: spell-book names (shared by the evil factions) + their «quoted» mentions.
ISENGARD (labels shown on the Isengard page): «Необхідно: Рівень N», «~ ПАСИВНА ЗДІБНІСТЬ ~», «Клікніть для активації»
for "Select to activate", level lines with a slash, hero role «Посилює», «Спеціалізація», building names
(Стійбище, Варґове лігво, Облогова майстерня, Сторожова вежа, Загін сторожових варґів, Міномет). --dry."""
import json, os, re, sys
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
ISEN = 'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_UK_WIP/Factions/Isengard_AoR_UA.json'

SPELLS = {  # English name -> new Ukrainian name ; old name (for «quoted» mentions)
    'crebain from dunland': ('Чорні круки Дунланду', 'Кребайни з Дунланду'),
    'war chant': ('Воєнний клич', 'Бойова пісня'),
    'tainted land': ('Спотворена земля', 'Проклята земля'),
    'fires of industry': ('Третя зміна', 'Вогні виробництва'),
    'fuel the fires': ('Піддати жару', 'Розпалити вогонь'),
    'build me an army': ('Армія, гідна Володаря', 'Гідна армія'),  # round20 (was «Гідна армія»)
    'fell storm': ('Зловісний шторм', 'Лиха буря'),
}


def _key(en):
    t = re.sub(r'\s*\(&\w\)', '', (en or '').replace('\\n', '\n')).replace('&', '')
    return re.sub(r'\s+', ' ', t).strip().lower()


def _rows(n, out):
    out.update(r['var'].lower() for r in n.get('рядки', []) if 'див' not in r)
    for k in ('прибудови', 'юніти'):
        for c in n.get(k, []):
            _rows(c, out)


_d = json.load(open(ISEN, encoding='utf-8'))
ISEN_VARS = set()
_rows(_d['Фортеця'], ISEN_VARS); [_rows(b, ISEN_VARS) for b in _d['Будівлі']]; [_rows(h, ISEN_VARS) for h in _d['Герої']]
_rows(_d['Книга сил'], ISEN_VARS)

ISEN_SUBS = [
    (r'Потрібно: Рівень (\d+)', r'Необхідно: Рівень \1'),
    (r'(?m)^\s*Пасивна здібність\.?\s*$', '~ ПАСИВНА ЗДІБНІСТЬ ~'),
    (r"\+(\d+)% (?:до )?здоров'я(?:,| та| і|/)\s*\+(\d+)% (?:до )?пошкоджень", r"+\1% здоров'я/+\2% пошкоджень"),  # round20: no «до»
    (r'(?m)^Підтримує ', 'Посилює '),
    (r'Зосередження:', 'Спеціалізація:'), (r'лише одне зосередження', 'лише одна спеціалізація'),
    (r'Кланова садиба', 'Стійбище'), (r'кланову садибу', 'стійбище'), (r'Кланової садиби', 'Стійбища'), (r'кланової садиби', 'стійбища'),
    (r'Лігво варґів', 'Варґове лігво'), (r'лігво варґів', 'варґове лігво'), (r'лігва варґів', 'варґового лігва'),
    (r'(?<![Оо]блогова )Майстерня (\d) рівня', r'Облогова майстерня \1 рівня'),
    (r'покращити майстерню', 'покращити облогову майстерню'), (r'Покращити майстерню', 'Покращити облогову майстерню'),
    (r'Спостережна вежа', 'Сторожова вежа'),
    (r'до кожного вартового варґа', 'до кожного загону сторожових варґів'),
    (r'Мінокидач', 'Міномет'), (r'мінокидач', 'міномет'),
    (r'  +', ' '),
]


def fix(var, en, ua):
    if not ua:
        return ua
    u, k = ua, _key(en)
    if k in SPELLS:  # the spell's own name label
        hk = re.search(r'&(\w)', en or '')
        u = SPELLS[k][0] + (f' (&{hk.group(1)})' if hk else '')
    for new, old in SPELLS.values():
        u = u.replace('«' + old + '»', '«' + new + '»')
    if var.lower() in ISEN_VARS:
        if (en or '').strip().lower().startswith('select to activate'):
            u = re.sub(r'^(Оберіть|Клікніть), щоб активувати', 'Клікніть для активації', u)
        for a, b in ISEN_SUBS:
            u = re.sub(a, b, u)
    return u


if __name__ == '__main__':
    a9 = open(os.path.join(H, 'apply9.py'), encoding='utf-8').read()
    exec(a9.split('EX = [')[0]); walker = a9.split('log = []')[1]
    LOGNAME = 'round19_log.txt'
    exec('log = []' + walker)
