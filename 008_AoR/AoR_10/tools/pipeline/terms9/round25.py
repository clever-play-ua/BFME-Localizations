"""Round 25 (2026-11-13, Dol Guldur draft): genitive «Дол-Ґулдуру / Ґулдуру» everywhere (like «Барад-дуру», round 22). --dry."""
import os, re
H = os.path.dirname(os.path.abspath(__file__))


def fix(var, en, ua):
    if not ua:
        return ua
    return re.sub(r'Ґулдура\b', 'Ґулдуру', ua)


if __name__ == '__main__':
    a9 = open(os.path.join(H, 'apply9.py'), encoding='utf-8').read()
    exec(a9.split('EX = [')[0]); walker = a9.split('log = []')[1]
    LOGNAME = 'round25_log.txt'
    exec('log = []' + walker)
