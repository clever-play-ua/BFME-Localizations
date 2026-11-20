"""0.9 term decisions (1-18) applied to every text source the build reads (+ old JSON copies). --dry: count only."""
import json, re, os, sys, glob, shutil, collections
from openpyxl import load_workbook
H = os.path.dirname(os.path.abspath(__file__))
B = 'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/'
W = B + 'AoR_UK_WIP/'
DRY = '--dry' in sys.argv
LOGNAME = 'apply9_log.txt'

EX = [  # exact phrase replacements (applied everywhere)
 # 3 gate = брама
 ('Головні ворота; можуть відкриватися та закриватися', 'Головна брама; може відкриватися та закриватися'),
 ('поблизу Чорних Воріт', 'поблизу Чорної брами'), ('Ворота фортеці', 'Брама фортеці'), ('Укріплені ворота', 'Укріплена брама'),
 ('Знищте всі ворота й укріплення', 'Знищте всі брами й укріплення'), ('наближаєшся до воріт короля Рогану', 'наближаєшся до брами короля Рогану'),
 ('Утримуйте ворота ще:', 'Утримуйте браму ще:'), ('Щоб зачинити ворота,', 'Щоб зачинити браму,'), ('перед моїми воротами', 'перед моєю брамою'),
 ('до воріт Ізенґарду', 'до брами Ізенґарду'), ('бачу ворота Ізенґарду', 'бачу браму Ізенґарду'),
 ('Захистіть ворота до', 'Захистіть браму до'), ('Захищайте ворота якомога довше', 'Захищайте браму якомога довше'),
 # 4 postern = потайна брама
 ('через бічні ворота', 'через потайні брами'), ('На півночі є бічні ворота, через них', 'На півночі є потайна брама, через неї'),
 ('до бічних воріт', 'до потайної брами'),
 ('ворота забарикадовано, їх не відчинити', 'браму забарикадовано, її не відчинити'),
 # 5 wall hub = стінна вежа
 ('Башточка', 'Стінна вежа'), ('Стінна башта', 'Стінна вежа'),
 # 6 recruit heroes = вербувати
 ('Навчання будівельників, заклик героїв', 'Навчання будівельників, вербування героїв'),
 ('Навчання будівельників, найм героїв', 'Навчання будівельників, вербування героїв'),
 ('Наймає будівельників і героїв', 'Навчає будівельників і вербує героїв'),
 ('вартість найму героїв', 'вартість вербування героїв'), ('потрібно найняти Буродапана', 'потрібно завербувати Буродапана'),
 ('наймати Фарамира', 'наймати Фараміра'),
 # 7 revive = відродити
 ('Воскресити полеглого', 'Відродити полеглого'), ('воскресіння героїв', 'відродження героїв'), ('ви можете лише воскресити', 'ви можете лише відродити'),
 # 8 upgrade = покращення
 ('придбати поліпшення', 'придбати покращення'),
 # 9 self repair
 ('Автоматичне відновлення', 'Автоматичний ремонт'),
 # 10 Gathering of the Hosts
 ('для Військової ради', 'для Збору воїнств'),
 # 11 soldiers / spearmen
 ('Солдати Мінас-Тіріта', 'Воїни Мінас-Тіріта'), ('Загін солдатів Мінас-Тіріта', 'Загін воїнів Мінас-Тіріта'),
 ('Тренувати солдатів Мінас-Тіріта', 'Тренувати воїнів Мінас-Тіріта'),
 ('Дозволяє тренувати Солдатів і Списників Мінас-Тіріта', 'Дозволяє тренувати воїнів і списоносців Мінас-Тіріта'),
 ('Лицарі, Піхотинці та Вартові Цитаделі', 'Лицарі, воїни та вартові Цитаделі'),
 ('Списники Лінхіра', 'Списоносці Лінхіра'), ('Списники Мінас-Тіріта', 'Списоносці Мінас-Тіріта'),
 ('племінних сокирників, лучників і списників', 'племінних сокирників, лучників і списоносців'),
 ('постійних списників, лучників і вершників Гарондору', 'постійних списоносців, лучників і вершників Гарондору'),
 # 12 Мінас-Тіріта (genitive)
 ('лучники Мінас-Тіріту', 'лучники Мінас-Тіріта'), ('Воїни Мінас-Тіріту', 'Воїни Мінас-Тіріта'),
 ('списоносців Мінас-Тіріту', 'списоносців Мінас-Тіріта'), ('лицарів Мінас-Тіріту', 'лицарів Мінас-Тіріта'), ('до Мінас-Тіріту', 'до Мінас-Тіріта'),
 # 14 maximum of
 ('Не більше трьох одночасно', 'Максимум три одночасно'), ('Не більше семи одночасно', 'Максимум сім одночасно'),
 ('Не більше чотирьох назґулів одночасно', 'Максимум чотири назґули одночасно'),
 ('Не більше 3 кобальтових уламків одночасно', 'Максимум 3 кобальтові уламки одночасно'),
 ('Не більше 3 тотемів одночасно', 'Максимум 3 тотеми одночасно'), ('Не більше 1 Рогу Карни одночасно', 'Максимум 1 Ріг Карни одночасно'),
 # 15 command points: «ОК (очок командування)» superseded 2026-11-09 (round17) -> plain «очок командування»
 ('Досягнуто максимум очок командування', 'Досягнуто максимуму очок командування'),
 # 16 left click
 ('Зробіть ЛКМ та перемістіть її, щоб побудувати стіну', 'Клікніть і потягніть мишу, щоб побудувати стіну'),
 ('Зробіть лівий клік мишею та перемістіть її, щоб побудувати стіну', 'Клікніть і потягніть мишу, щоб побудувати стіну'),
 ('Клікніть мишкою та перемістіть її, щоб побудувати стіну', 'Клікніть і потягніть мишу, щоб побудувати стіну'),
 ('Клікніть ЛКМ, щоб придбати', 'Клікніть, щоб придбати'),
 # 18 unit names lowercase mid-sentence
 ('Дозволяє тренувати Слідопитів Ітілієну', 'Дозволяє тренувати слідопитів Ітілієну'),
 ('Дозволяє тренувати Лицарів Мінас-Тіріта', 'Дозволяє тренувати лицарів Мінас-Тіріта'),
 ('Дозволяє Слідопитам Ітілієну', 'Дозволяє слідопитам Ітілієну'),
 ('пасивно розблоковує Гвардійців та Лицарів Дол-Амрота', 'пасивно розблоковує латників і Лицарів Лебедя'),
 ('Лицарі-Лебеді', 'Лицарі Лебедя'), ('наймати Вартових Фонтану', 'наймати вартових фонтану'),
]
WHOLE = {'Ворота': 'Брама', 'Бічні ворота': 'Потайна брама'}  # whole-text matches


def lines_fix(var, en, ua):
    el, ul = en.split('\n'), ua.split('\n')
    if len(el) != len(ul):
        return ua
    v = var.lower()
    out = []
    for a, b in zip(el, ul):
        # 1 Build X = Побудувати X
        # superseded 2026-11-09 (round16): build buttons show the building name only, no «Побудувати»
        # 2 stables = конюшні
        if re.search(r'(?i)stable', a):
            b = re.sub(r'стаєнь', 'конюшень', b); b = re.sub(r'Стайн', 'Конюшн', b); b = re.sub(r'стайн', 'конюшн', b)
        # 6 recruit hero
        if re.match(r'\s*Recruit\b', a) and ('recruit' in v and 'ship' not in v or 'purchasehighpass' in v):
            b = re.sub(r'\bНайняти ', 'Завербувати ', b)
        if re.match(r'\s*Recruit time', a):
            b = b.replace('Час найму:', 'Час вербування:')
        # 14 limited to N
        if re.search(r'Limited to \d', a):
            b = re.sub(r'(?:[Нн]е більше|Максимальний ліміт|[Мм]аксимум) (\d+)(?: одночасно)?', r'Максимум \1 одночасно', b)
        # 17 inn + capitalised list items in map descriptions
        if v.startswith('map:') and re.match(r"\s*(Захоплюван|Лігва:)", b):
            b = re.sub(r"Захоплюваний об'єкт:", "Захоплювані об'єкти:", b)
            b = b.replace('трактир', 'корчма')
            head, _, items = b.partition(':')
            items = ', '.join(x.strip()[:1].upper() + x.strip()[1:] for x in items.split(','))
            b = f'{head}: {items}'.replace('Гоблін', 'Ґоблін').replace('Варги', 'Варґи')
        out.append(b)
    return '\n'.join(out)


def fix(var, en, ua):
    if not ua:
        return ua
    u = ua
    if u.strip() in WHOLE:
        u = u.replace(u.strip(), WHOLE[u.strip()])
    for o, n in EX:
        if var.lower() == 'controlbar:tooltipconstructmenfortress' and 'ОК (' in n:
            continue  # round16: the user chose the editor's wording without «ОК»
        u = u.replace(o, n)
    u = lines_fix(var, en or '', u)
    u = u.replace('ОК (ОК (очок командування))', 'ОК (очок командування)')
    return u


log = []
def touch(src, var, en, old, new):
    if new != old:
        log.append((src, var, old, new))
    return new

# ---- JSON sources ----
def json_files():
    for f in sorted(glob.glob(W + 'heroes/*.json')) + sorted(glob.glob(W + 'Skirmish/*.json')):
        yield f, ('Кампанія', 'Битва'), ('uk_ai', 'uk')
    for f in sorted(glob.glob(W + 'RoTK/*.json')):
        yield f, ('strings',), ('uk', 'uk_ai')
    yield W + 'Serhii_strings.json', ('strings',), ('sergii',)
    for n in ('Menu_tooltips_strings.json', 'RingPowers_Campaign_strings.json', 'RingPowers_Skirmish_strings.json',
              'Fellowship_strings.json', 'FotR_strings.json', 'TTT_strings.json', 'TTT_dialogs_strings.json'):
        yield W + n, ('strings',), ('uk', 'uk_ai')
    yield B + 'AoR_10/menu_strings.json', ('strings',), ('uk', 'uk_ai')
    for f in sorted(glob.glob(W + 'Factions/*_serhii.json')):
        yield f, ('strings',), ('sergii',)
    for f in sorted(glob.glob(W + 'Factions/*_AI_drafts.json')):
        yield f, ('strings',), ('uk_ai',)
    for f in sorted(glob.glob(W + 'Factions/*_reviewed.json')):
        yield f, ('strings',), ('uk',)

bak = os.path.join(H, 'bak');
for f, secs, fields in json_files():
    if not os.path.exists(f): continue
    d = json.load(open(f, encoding='utf-8')); dirty = False
    for s in secs:
        for r in d.get(s, []):
            for fl in fields:
                if r.get(fl):
                    raw = r[fl]; lit = '\\n' in raw and '\n' not in raw
                    t = raw.replace('\\n', '\n') if lit else raw
                    nt = fix(r['var'], (r.get('en') or '').replace('\\n', '\n'), t)
                    if nt != t:
                        touch(os.path.basename(f), r['var'], r.get('en'), t, nt)
                        r[fl] = nt.replace('\n', '\\n') if lit else nt; dirty = True
    if dirty and not DRY:
        os.makedirs(bak, exist_ok=True)
        json.dump(d, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)

# ---- xlsx (UK, UK AI columns; literal \n) ----
X = B + 'AoR_10/RotK_campaign_strings.xlsx'
wb = load_workbook(X); xdirty = False
for ws in wb.worksheets:
    rows = ws.iter_rows()
    head = [c.value for c in next(rows)]
    if 'Переменная' not in head or 'EN' not in head: continue
    iv, ie = head.index('Переменная'), head.index('EN')
    cols = [head.index(c) for c in ('UK', 'UK AI') if c in head]
    for row in rows:
        var = row[iv].value
        if not var: continue
        en = (row[ie].value or '').replace('\\n', '\n')
        for ci in cols:
            cell = row[ci]
            if isinstance(cell.value, str) and cell.value:
                t = cell.value.replace('\\n', '\n')
                nt = fix(var, en, t)
                if nt != t:
                    touch('xlsx:' + ws.title, var, en, t, nt); cell.value = nt.replace('\n', '\\n'); xdirty = True
if xdirty and not DRY:
    os.makedirs(bak, exist_ok=True)
    wb.save(X)

c = collections.Counter(s for s, *_ in log)
print('changed', len(log), dict(c))
with open(os.path.join(H, LOGNAME), 'w', encoding='utf-8') as o:
    for s, v, a, b in log:
        al, bl = a.split('\n'), b.split('\n')
        o.write(f'## {s} {v}\n')
        for x, y in zip(al, bl):
            if x != y: o.write(f'  - {x.strip()}\n  + {y.strip()}\n')
