"""Round 27 (2026-11-17, FoLD_MacOS Misty Mountains proofread + user answers), GLOBAL over every text source:
 2 resource buildings «based on available terrain» = the 0.13 standard (also Erebor / Dol Guldur)
 5 Intimidation = «Пригнічення»   6 Purchase upgrades and additional defenses for the Fortress = «Придбання покращень та укріплення оборони»
 + his Misty Mountains names wherever they occur (гірські орки-розвідники / орки-бугаї, Лігво зміїв, Ґоблінська скарбниця,
   Трофейні клинки / обладунки).  --dry."""
import os, re
H = os.path.dirname(os.path.abspath(__file__))
TERRAIN = 'Видобуває ресурси, що ближче стоять інші\nресурсні споруди, то менше ресурсів видобувається.'
SUBS = [
    ('Розвідники гірських орків', 'Гірські орки-розвідники'), ('розвідників гірських орків', 'гірських орків-розвідників'),
    ('Розвідник гірських орків', 'Гірський орк-розвідник'),
    ('Гірські орки-громили', 'Гірські орки-бугаї'), ('Гірський орк-громила', 'Гірський орк-бугай'),
    ('Лігво змія', 'Лігво зміїв'), ('лігво змія', 'лігво зміїв'),
    ('Ґоблінський скарб', 'Ґоблінська скарбниця'), ('ґоблінський скарб', 'ґоблінська скарбниця'),
    ('Здобуті клинки', 'Трофейні клинки'), ('Здобуті обладунки', 'Трофейні обладунки'), ('здобутими обладунками', 'трофейними обладунками'),
    ('«Трофейна броня»', '«Трофейні обладунки»'),
]


def fix(var, en, ua):
    if not ua:
        return ua
    u, e = ua, (en or '').lower()
    for a, b in SUBS:
        u = u.replace(a, b)
    # 2
    if 'based on available terrain' in e and TERRAIN not in u:
        u = re.sub(r'(?m)^Видобуває[^\n]*$', TERRAIN, u, count=1)
    # 5
    if re.sub(r'\s*\(&\w\)\s*$', '', e).strip() == 'intimidation':
        hk = re.search(r'\s*\(&\w\)\s*$', u)
        u = 'Пригнічення' + (hk.group(0) if hk else '')
    # 6
    if e.strip() == 'purchase upgrades and additional defenses for the fortress':
        u = 'Придбання покращень та укріплення оборони'
    return u


if __name__ == '__main__':
    a9 = open(os.path.join(H, 'apply9.py'), encoding='utf-8').read()
    exec(a9.split('EX = [')[0]); walker = a9.split('log = []')[1]
    LOGNAME = 'round27_log.txt'
    exec('log = []' + walker)
