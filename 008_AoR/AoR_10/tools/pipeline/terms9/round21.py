"""Round 21 (2026-11-11, FoLD's Rohan proofread + cross-faction check, user answers), GLOBAL over every text source:
 1 «Необхідно: Рівень N» everywhere (was «Потрібно: Рівень N» outside Isengard)
 3 «based on available terrain» -> FoLD's standard line   4 small resources -> «Періодично виробляє трохи ресурсів»
 5/6 upgrade research/equipment lines = Isengard (FoLD) set     7 siege repair = «лагодить»
 8 Arrow Tower Expansion = «Вежа лучників»   10 weather-cancel line   11 «оберіть ділянку» (no «прохідну»)
12 target battalion -> «оберіть загін»       13 bow / stealth / swordsmen-and-archers / «Обрані союзники»
 А Riddermark = «Ріддермарк» (gen. «Ріддермарку»)   В Windmill = «Млин»   Г «Статуя Еорла»   Е «Вестфолду»
 Ж Rohan oaths = «присяга»   + «мундбурзької», «рогірими», requirement lines «N рівня» (no «-го»).  --dry."""
import os, re
H = os.path.dirname(os.path.abspath(__file__))

TERRAIN = 'Видобуває ресурси, що ближче стоять інші\nресурсні споруди, то менше ресурсів видобувається.'
SMALLRES = 'Періодично виробляє трохи ресурсів'
WEATHER = 'Скасовує ефекти погоди: «Крижаний дощ», «Благословення Улмо», «Згасання світла», «Білу зиму» й «Пітьму»'
KEEP = {'controlbar:tooltippurchasetechnologyrohanfirearrows'}  # user kept FoLD's wording (item 7)


def per_line(var, en, ua):
    """EN-line templates, applied only when EN and UA have the same number of lines."""
    el, ul = en.split('\n'), ua.split('\n')
    if len(el) != len(ul):
        return ua
    v = var.lower()
    out = []
    for a, b in zip(el, ul):
        s = a.strip().lower()
        lead = re.match(r'[ \t]*', b).group(0)
        new = None
        if 'small amount of resources' in s and s.startswith('generates'):
            new = SMALLRES
        elif s.startswith('when equipped, significantly reduces the amount of damage taken') and 'from' not in s:
            new = 'Після оснащення значно зменшує отримувані пошкодження'
        elif s.startswith('when equipped, significantly reduces the amount of damage taken from'):
            new = 'Після оснащення значно зменшує пошкодження від лучників і пікінерів' if 'archers' in s or 'arrows' in s else None
        elif s == 'when equipped, increases the damage done by melee weapons':
            new = 'Після оснащення збільшує пошкодження в ближньому бою'
        elif s == 'when equipped, significantly increases the damage done by arrows':
            new = 'Після оснащення значно збільшує пошкодження стріл'
        elif re.fullmatch(r'when equipped, increases this (battalion|horde) to level 2', s):
            new = 'Після оснащення підвищує рівень загону до 2'
        elif re.fullmatch(r'increases a (battalion|horde) to level 2', s):
            new = 'Підвищує рівень загону до 2'
        elif s == 'will upgrade all patrols instantly once upgrade is purchased':
            what = 'зброю' if 'forgedblades' in v else 'обладунки' if 'heavyarmor' in v else 'стріли' if 'firearrows' in v else None
            if what:
                new = f'Після дослідження миттєво покращує {what} всіх патрулів навколо будівель'
        elif s == 'heals nearby damaged siege machines':
            new = 'Лагодить пошкоджені облогові машини поблизу'
        elif s == 'increased healing to nearby damaged siege machines':
            new = 'Швидше лагодить пошкоджені облогові машини поблизу'
        elif re.fullmatch(r'at rank (\d), repairs nearby siege engines', s):
            new = 'На ' + re.search(r'\d', s).group(0) + ' рівні лагодить облогові машини поблизу'
        elif s.startswith('cancels freezing rain, blessing of ulmo, lights go out, white winter and darkness'):
            new = WEATHER
        elif s == 'can only use with bow equipped':
            new = 'Доступно лише з луком'
        elif s == 'detects stealth':
            new = 'Виявляє невидимі загони'
        elif s.startswith('strong vs. swordsmen and archers'):
            b = b.replace('мечників та лучників', 'мечників і лучників')
        elif re.search(r'target battalion\s*$', s):
            b = re.sub(r'оберіть потрібн(і загони|ий загін)\s*$', 'оберіть загін', b)
        if new is not None and v not in KEEP:
            b = lead + new
        out.append(b)
    return '\n'.join(out)


def fix(var, en, ua):
    if not ua:
        return ua
    u, v, e = ua, var.lower(), en or ''
    # 3 resources from the ground (FoLD's line)
    u = re.sub(r'Видобуває ресурси, ?(?:чим|що) ближче стоять інші\s*\n?\s*ресурсні споруди, (?:тим|то) менше ресурсів видобувається\.?[ \t]*',
               TERRAIN, u)
    if re.search(r'(?i)based on available terrain', e):
        u = re.sub(r'Виготовляє товсті обладунки й широкі\s*\n?\s*щити як ресурс залежно від доступної місцевості', TERRAIN, u)
        u = re.sub(r'(?m)^[ \t]*[^\n]*?(?:залежно\s*\n?\s*від доступної місцевості|залежить від ландшафту|на основі доступної місцевості)[^\n]*$',
                   TERRAIN, u, count=1)
        u = re.sub(r'(?m)^[ \t]*(?:Виробляє ресурси|Виробництво хліба як ресурсів)[ \t]*$', TERRAIN, u, count=1)
    # 4 (lines whose EN alignment broke)
    if re.search(r'(?i)generates a small amount of resources', e):
        u = re.sub(r'(?m)^[ \t]*(?:Дає трохи ресурсів|Виробляє невелику кількість ресурсів|Генерує невелику кількість ресурсів|'
                   r'Періодично генерує трохи ресурсів|Виробництво ресурсів з урахуванням місцевості, що є в наявності|'
                   r'Виробництво ресурсів залежно від доступної місцевості)[ \t]*$', SMALLRES, u)
    u = per_line(var, e, u)
    # 5 Rohan requirement lines -> the common wording
    if v not in KEEP:
        for a, b in [('Досліджується у Казармах', 'Придбайте покращення в «Казармах», щоб відкрити це спорядження'),
                     ('Досліджується на Стрільбищі', 'Придбайте покращення на «Стрільбищі», щоб відкрити це спорядження'),
                     ('Досліджується у Конюшнях', 'Придбайте покращення в «Конюшнях», щоб відкрити це спорядження'),
                     ('Значно зменшує отримувані пошкодження', 'Після оснащення значно зменшує отримувані пошкодження'),
                     ('Збільшує пошкодження загону в ближньому бою', 'Після оснащення збільшує пошкодження в ближньому бою'),
                     ('Значно збільшує пошкодження від стріл', 'Після оснащення значно збільшує пошкодження стріл'),
                     ('Загін отримує рівень 2', 'Після оснащення підвищує рівень загону до 2'),
                     ('Зменшує пошкодження, яких загону завдають лучники та пікінери', 'Після оснащення значно зменшує пошкодження від лучників і пікінерів'),
                     ('Дозволяє споряджати загони Вогняними стрілами', 'Дає змогу кожному загону придбати покращення «Вогняні стріли»'),
                     ('Після придбання підвищує рівень загону до 2', 'Підвищує рівень загону до 2')]:
            u = re.sub(r'(?m)^([ \t]*)' + re.escape(a) + r'\.?[ \t]*$', lambda m: m.group(1) + b, u)
        u = u.replace('Дає змогу купувати загонам покращення «', 'Дає змогу кожному загону придбати покращення «')
    # 7 unaligned siege lines
    u = u.replace('Ремонтує облогову зброю, що знаходиться поряд', 'Лагодить пошкоджені облогові машини поблизу')
    u = re.sub(r'На (\d)-му рівні автоматично ремонтує облогову зброю, що поряд', r'На \1 рівні лагодить облогові машини поблизу', u)
    u = re.sub(r'На (\d) рівні ремонтує облогові машини поблизу', r'На \1 рівні лагодить облогові машини поблизу', u)
    # 8 arrow tower expansion
    if re.search(r'(?i)arrow tower expansion', e) or re.search(r'(?i)^\s*Arrow Tower\s*$', e):
        u = re.sub(r'^(?:Оборонна вежа|Прибудувати вежу лучників|Вежа лучників)(?= \(&\w\)|$)', 'Вежа лучників', u.strip()) if '\n' not in u else u
    # 10 weather (lines with broken alignment)
    u = re.sub(r'Скасовує (?:інші |наступні )?(?:ефекти погоди: |ефекти )?«Крижаний дощ», «Благословення Улмо», «Згасання світла», «Білу зиму»,? й? ?«Пітьму»',
               WEATHER, u)
    u = u.replace('Зупиняє ефекти погоди: «Крижаний дощ», «Благословення Улмо», «Згасання світла», «Білу зиму», «Пітьму»', WEATHER)
    # 11
    u = u.replace('оберіть прохідну ділянку', 'оберіть ділянку').replace('— прохідну ділянку', '— ділянку')
    # 13
    if 'Targeted allies' in e:
        u = u.replace('Вказані союзники', 'Обрані союзники')
    # 1 rank requirement
    u = re.sub(r'Потрібно: Рівень (\d+)', r'Необхідно: Рівень \1', u)
    # requirement lines without «-го»
    u = re.sub(r'(Необхідно: [^\n]*?\d)-го рівня', r'\1 рівня', u)
    # А Riddermark
    if 'riddermark' in e.lower():
        for a, b in [('принца Рогану, Другого маршала Марки', 'принца Ріддермарку'), ('маршала Марки', 'маршала Ріддермарку'),
                     ('Принц Марки', 'Принц Ріддермарку'), ('Стяг Марки', 'Стяг Ріддермарку'), ('воїнів Марки', 'воїнів Ріддермарку'),
                     ('Ріддермарка', 'Ріддермарку')]:
            u = u.replace(a, b)
    # В windmill = млин
    if re.search(r'(?i)windmill', e):
        u = re.sub(r'([Вв])ітряк', lambda m: ('М' if m[1] == 'В' else 'м') + 'лин', u)
    # Г, Е, Ж
    u = u.replace('Статуя Рогану', 'Статуя Еорла')
    u = u.replace('Вестфолда', 'Вестфолду')
    if re.search(r'(?i)oath', e):
        u = u.replace('Клятви дотримано', 'Присяги дотримано').replace('Ви складали клятви — тепер', 'Ви складали присяги — тепер')
    # spelling
    u = re.sub(r'([Мм])ундбургськ', r'\1ундбурзьк', u)
    u = re.sub(r'([Рр])огіріми\b', r'\1огірими', u)
    return u


if __name__ == '__main__':
    a9 = open(os.path.join(H, 'apply9.py'), encoding='utf-8').read()
    exec(a9.split('EX = [')[0]); walker = a9.split('log = []')[1]
    LOGNAME = 'round21_log.txt'
    exec('log = []' + walker)
