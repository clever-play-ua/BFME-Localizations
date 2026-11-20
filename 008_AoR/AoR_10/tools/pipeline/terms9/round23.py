"""Round 23 (2026-11-11 evening, FoLD_MacOS campaign-hero proofread + user answers), GLOBAL over every text source:
 5 Shapeless Malice = «Безлика злоба» (all case forms)   6 Restless = «Невпокоєні» (кургани, воїни)
11 flat health bonus = «+N од. здоров'я» (percentages untouched).  --dry."""
import os, re
H = os.path.dirname(os.path.abspath(__file__))


def fix(var, en, ua):
    if not ua:
        return ua
    u = ua
    u = re.sub(r'([Бб])езформн(\w+) злоб', r'\1езлик\2 злоб', u)
    u = re.sub(r'([Нн])еспокійн(?=\w* (?:курган|воїн))', lambda m: m[1] + 'евпокоєн', u)  # not dialogue «неспокійно»
    u = re.sub(r"(\+\d+) здоров'я", r"\1 од. здоров'я", u)
    return u


if __name__ == '__main__':
    a9 = open(os.path.join(H, 'apply9.py'), encoding='utf-8').read()
    exec(a9.split('EX = [')[0]); walker = a9.split('log = []')[1]
    LOGNAME = 'round23_log.txt'
    exec('log = []' + walker)
