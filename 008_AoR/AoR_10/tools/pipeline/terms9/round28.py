"""Round 28 (2026-11-19, movie subtitles review, user answer 3А): Bag End = «Беґ-Енд» everywhere (was «Торбин Кут»
in the AoR campaign dialogues; matches «Беґінз» and our BFME2 / RotWK translations).  --dry."""
import os, re
H = os.path.dirname(os.path.abspath(__file__))
FORMS = [('Торбиному Куті', 'Беґ-Енді'), ('Торбином Куті', 'Беґ-Енді'), ('Торбиного Кута', 'Беґ-Енду'),
         ('Торбиним Кутом', 'Беґ-Ендом'), ('Торбин Кут', 'Беґ-Енд')]


def fix(var, en, ua):
    if not ua:
        return ua
    for a, b in FORMS:
        ua = ua.replace(a, b)
    return ua


if __name__ == '__main__':
    a9 = open(os.path.join(H, 'apply9.py'), encoding='utf-8').read()
    exec(a9.split('EX = [')[0]); walker = a9.split('log = []')[1]
    LOGNAME = 'round28_log.txt'
    exec('log = []' + walker)
