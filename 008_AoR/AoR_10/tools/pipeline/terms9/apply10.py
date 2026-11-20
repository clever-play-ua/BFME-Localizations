"""Editor-round term decisions (2026-11-09) over every source; reuses apply9's source walker. --dry: count only."""
import re, sys, os
H = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(H, 'apply9.py'), encoding='utf-8').read()
head = src.split('EX = [')[0]
walker = src.split("log = []")[1]
exec(head)
LOGNAME = 'apply10_log.txt'

EX = [
 # 1/2 oath
 ('Прикликає військо клятвопорушників', 'Прикликає військо порушників присяги'),
 ('Виконайте свою клятву!', 'Виконайте свою присягу!'), ('Тож виконайте свою присягу!', 'Виконайте свою присягу!'),
 # 3 dismounted
 ('лише коли спішений', 'лише пішки'),
 # 6 Hadhod
 ('Пильне Око', 'Пильне око'),
 # 7 siege
 ('Майстер облоги', 'Експерт з облоги'),
 # 14 willow
 ('Старий Верболіз', 'Стара верба'), ('Старого Верболоза', 'стару вербу'),
]
OATH = [('клятвозлочинці', 'порушники присяги'), ('клятвозлочинців', 'порушників присяги'), ('клятвозлочинцям', 'порушникам присяги'),
        ('клятвозлочинцями', 'порушниками присяги'), ('Клятвозлочинці', 'Порушники присяги'), ('вершників-клятвозлочинців', 'вершників-порушників присяги')]


def lines_fix(var, en, ua):
    el, ul = en.split('\n'), ua.split('\n')
    if len(el) != len(ul):
        return ua
    out = []
    for a, b in zip(el, ul):
        if re.search(r'Oathbreaker', a):
            for o, n in sorted(OATH, key=lambda x: -len(x[0])): b = b.replace(o, n)
        # 4 «протягом N сек.» -> «на N сек.» (damage over time -> «N сек. поступово»)
        b = re.sub(r'протягом (\d+) сек\. (поступово )?(отриму\w+) пошкодження', r'\1 сек. поступово \3 пошкодження', b)
        b = re.sub(r'(отрутою|поступов\w+ пошкоджен\w+(?: отрутою)?) протягом (\d+) сек', r'\1 ПРОТЯГОМ \2 сек', b)
        b = re.sub(r'протягом (\d+) сек\.', r'на \1 сек.', b)
        b = b.replace('ПРОТЯГОМ', 'протягом')
        b = re.sub(r'триває на (\d+) сек\.', r'триває \1 сек.', b).replace('лишається на полі бою на ', 'лишається на полі бою ')
        # 8 chieftain = отаман
        if re.search(r'Chieftain', a):
            b = re.sub(r'([Вв])атаж(ок|ка|ком|ку)\b', lambda m: ('О' if m[1] == 'В' else 'о') + 'таман' + {'ок': '', 'ка': 'а', 'ком': 'ом', 'ку': 'у'}[m[2]], b)
        # 9 Morgul Blades = морґульські мечники
        if re.search(r'Morgul Blade', a):
            b = re.sub(r'(морґульськ\w+ )клинк(и|ів|ам|ами|ах)\b', lambda m: m[1] + 'мечник' + m[2], b)
            b = re.sub(r'(Морґульськ\w+ )клинк(и|ів|ам|ами|ах)\b', lambda m: m[1] + 'мечник' + m[2], b)
        # 10 Broken Rabble = зломлена наволоч
        if re.search(r'Broken Rabble', a):
            b = re.sub(r'наймати зламаний набрід', 'наймати зломлену наволоч', b)
            b = re.sub(r'[Зз]ламаний набрід', lambda m: ('З' if m[0][0] == 'З' else 'з') + 'ломлена наволоч', b)
            b = b.replace('обраний зломлена наволоч', 'обрану зломлену наволоч')
        # 11 ranged = на відстані
        if re.search(r'(?i)\branged\b|range avoidance', a):
            b = b.replace('з відстані', 'на відстані')
        # 13 champion = чемпіон
        if re.search(r'Champion', a):
            b = re.sub(r'([Пп])оборник(\w*)', lambda m: ('Ч' if m[1] == 'П' else 'ч') + 'емпіон' + m[2], b)
        out.append(b)
    return '\n'.join(out)


def fix(var, en, ua):
    if not ua:
        return ua
    u = ua
    for o, n in EX:
        u = u.replace(o, n)
    u = lines_fix(var, en or '', u)
    # 5 orcish = ороч-
    u = re.sub(r'([Оо])рківськ', lambda m: m[1] + 'роч', u)
    u = re.sub(r'([Оо])ркськ', lambda m: m[1] + 'роч', u)
    # 12 «+N% до пошкоджень»
    # round20: Isengard level lines «+N% здоров'я/+N% пошкоджень» stay without «до»
    u = re.sub(r"(?<!завдає )(?<!завдають )(?<!завдає ще )(?<!здоров'я/)(\+\d+%) пошкоджень", r'\1 до пошкоджень', u)
    u = u.replace('стає умертвієм', 'стає привидом').replace('стають умертвіями', 'стають привидами')
    return u


exec("log = []" + walker)
