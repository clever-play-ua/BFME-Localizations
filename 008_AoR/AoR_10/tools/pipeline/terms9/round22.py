"""Round 22 (2026-11-11, FoLD's Mordor proofread + user answers 1-13), GLOBAL over every text source:
 1 Siege Works (Mordor/Gondor) = «Велика майстерня»   2 Orcish Stronghold = «Ороча фортеця»   3 «Мордорська вежа»
 4 Slave Farm = «Ферма з рабами»   5 Horde Bonus = «Отримують бонуси від кількості» (all factions)
 6 «якщо зібрані в кількості N і більше»   7 requirement line «Придбайте покращення в «X», щоб відкрити це спорядження»
11 slash damage = «ріжучі пошкодження»   12 «великих звірів» lowercase in running text   13 «Барад-дуру».  --dry."""
import os, re
H = os.path.dirname(os.path.abspath(__file__))


def fix(var, en, ua):
    if not ua:
        return ua
    u, e = ua, en or ''
    # 1
    u = u.replace('Велика облогова майстерня', 'Велика майстерня').replace('Великої облогової майстерні', 'Великої майстерні')
    if 'Siege Works' in e and 'isengard' not in var.lower():  # Isengard keeps «Облогова майстерня»
        u = re.sub(r'(?<!Велика )(?<!Облогова )\bМайстерня\b', 'Велика майстерня', u)
    # 2
    for a, b in [('Ороча твердиня', 'Ороча фортеця'), ('ороча твердиня', 'ороча фортеця'), ('Орочої твердині', 'Орочої фортеці'),
                 ('орочої твердині', 'орочої фортеці'), ('ороччу твердиню', 'орочу фортецю'), ('Ороччу твердиню', 'Орочу фортецю'),
                 ('орочу твердиню', 'орочу фортецю'), ('орочі твердині', 'орочі фортеці'), ('Орочі твердині', 'Орочі фортеці')]:
        u = u.replace(a, b)
    # 3
    u = u.replace('Вежа Мордору', 'Мордорська вежа')
    if 'Mordor Towers' in e or 'Towers of Mordor' in e:
        u = u.replace('Вежі Мордору', 'Мордорські вежі')
    # 4
    for a, b in [('Рабська ферма', 'Ферма з рабами'), ('рабська ферма', 'ферма з рабами'), ('Рабські ферми', 'Ферми з рабами'),
                 ('Рабських ферм', 'Ферм з рабами'), ('рабських ферм', 'ферм з рабами')]:
        u = u.replace(a, b)
    # 5
    el, ul = e.split('\n'), u.split('\n')
    if len(el) == len(ul):
        u = '\n'.join(('Отримують бонуси від кількості' if a.strip().lower() == 'horde bonus' else b) for a, b in zip(el, ul))
    u = re.sub(r'Отримують бонуси від кількості[ \t]*\n[ \t]*\n(?=[ \t]*Тип ефекту)', 'Отримують бонуси від кількості\n', u)
    u = re.sub(r'Отримують бонуси від кількості[ \t]+(?=\n|$)', 'Отримують бонуси від кількості', u)
    # 6
    u = re.sub(r'коли їх зібрано (\d+) або більше', r'якщо зібрані в кількості \1 і більше', u)
    u = re.sub(r'в кількості (\d+) од\. і більше', r'в кількості \1 і більше', u)
    # 7
    u = re.sub(r'Спочатку придбайте покращення в («[^»]+»), щоб мати змогу робити поліпшення для окремих загонів',
               r'Придбайте покращення в \1, щоб відкрити це спорядження', u)
    # 11
    if 'slash damage' in e.lower():
        u = re.sub(r'рубальн\w* пошкодж\w*|ріжуче пошкодження', 'ріжучі пошкодження', u)
    # 12 (names at the start of a line stay capitalised)
    if 'Great Beast' in e:
        u = re.sub(r'(?<=[^\n\s] )Велик(\w+) звір', lambda m: 'велик' + m[1] + ' звір', u)
    # 13
    u = u.replace('Барад-дура', 'Барад-дуру')
    return u


if __name__ == '__main__':
    a9 = open(os.path.join(H, 'apply9.py'), encoding='utf-8').read()
    exec(a9.split('EX = [')[0]); walker = a9.split('log = []')[1]
    LOGNAME = 'round22_log.txt'
    exec('log = []' + walker)
