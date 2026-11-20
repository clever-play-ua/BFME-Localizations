"""Round 24 (2026-11-13, FoLD heroes batch 3 + user answers), GLOBAL over every text source:
 3 В «Поєднується / Не поєднується» (no «Бонус …»)   4 Б damage over time = «періодичні пошкодження»
 5 Б monsters = «істоти» (only where the English says Monster)   + «Ґаладріель» undeclined, «Біле Місто».  --dry."""
import os, re
H = os.path.dirname(os.path.abspath(__file__))


def fix(var, en, ua):
    if not ua:
        return ua
    u, e = ua, (en or '').lower()
    # 3
    u = re.sub(r'(?m)^Бонуси? (?:поєднується|поєднуються) (з|із)', r'Поєднується \1', u)
    u = u.replace('Поєднується '+chr(1), 'Поєднується із')  # repair of an earlier bad run
    u = re.sub(r'(?m)^Бонус не (?:сумується|поєднується)', 'Не поєднується', u)
    # 4
    u = re.sub(r'поступово (отриму(?:ють|є)) пошкодження', r'\1 періодичні пошкодження', u)
    u = re.sub(r'(?<![А-Яа-яІіЇїЄєҐґ])Поступово (отриму(?:ють|є)) пошкодження', lambda m: m[1].capitalize() + ' періодичні пошкодження', u)
    u = re.sub(r'поступово завдають пошкоджень', 'завдають періодичних пошкоджень', u)
    u = u.replace('поступові пошкодження', 'періодичні пошкодження').replace('поступових пошкоджень', 'періодичних пошкоджень')
    # 5
    if 'monster' in e:
        for a, b in [('Обране створіння', 'Обрана істота'), ('чи створіння,', 'чи істоту,'), ('героям і створінням', 'героям та істотам'), ('створіннями', 'істотами'), ('створінням', 'істотам'),
                     ('створіннях', 'істотах'), ('створінь', 'істот'), ('створіння', 'істоти')]:
            u = u.replace(a, b)
    # Ґаладріель is not declined; the White City
    u = u.replace('Ґаладріелі', 'Ґаладріель').replace('Білого міста', 'Білого Міста')
    return u


if __name__ == '__main__':
    a9 = open(os.path.join(H, 'apply9.py'), encoding='utf-8').read()
    exec(a9.split('EX = [')[0]); walker = a9.split('log = []')[1]
    LOGNAME = 'round24_log.txt'
    exec('log = []' + walker)
