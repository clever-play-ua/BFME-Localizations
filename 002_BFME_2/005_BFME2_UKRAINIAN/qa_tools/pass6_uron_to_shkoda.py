"""
QA pass 6: replace the Russian calque "урон" (masc.) with proper Ukrainian
"шкода" (fem.) throughout - user-confirmed 2026-09-15. Unlike the earlier
name-normalization passes, this ISN'T a plain word swap: "урон" is masculine
and "шкода" is feminine, so any adjective agreeing with it, and the noun's own
case ending, both need to change correctly depending on the grammatical role
(examples found in the corpus, verified by reading the surrounding sentence
for every one of the ~183 distinct context patterns before writing this):

  - "завдає/завдають/завдаючи ... урон(а/у)?" -> always genitive "... шкоди"
    (завдати idiomatically governs genitive; this also fixes the ones that
    used a Russian-calqued accusative-looking "урон" instead of the correct
    Ukrainian genitive "урону" after завдати - both collapse to the same
    correct target).
  - "завдається ... урон" (passive) -> nominative "... шкода" (шкода is the
    grammatical subject of the passive verb, not shkoda's object).
  - "отримує/отримують ... урон" -> accusative "... шкоду" (отримати governs
    accusative).
  - bare "Знижує/Скорочує/Збільшує/Зменшує урон" (no adjective) -> accusative
    "... шкоду".
  - "Збільшення/Зменшення/Зниження/Скорочення/Підвищення/Завдання ... урону"
    -> genitive "... шкоди" (already genitive case, no adjective-agreement
    change needed beyond the noun itself).
  - standalone labels ("Урон в ближньому бою:", "Додатковий урон") ->
    nominative "Шкода"/"Додаткова шкода".
  - any remaining bare genitive "урону"/"урона" not caught by a more specific
    rule above (after a percentage, "більше/менше", a preposition, etc.) ->
    "шкоди" (genitive is genitive regardless of what governs it).

Prints every entry still containing "урон" after all rules run, so nothing
gets silently missed - the script does NOT save if anything is left over.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
UA_DIR = os.path.dirname(HERE)
STRINGS_PATH = os.path.join(UA_DIR, 'BFME2_strings_ua.json')

# masc (genitive -ого or nominative/accusative -ий/-ій) -> genitive fem (-ої),
# used after завдає/завдають/завдаючи (always target genitive).
GEN_FEM = {
    'невеликого': 'невеликої', 'невеликий': 'невеликої',
    'суттєвого': 'суттєвої', 'суттєвий': 'суттєвої',
    'величезного': 'величезної', 'величезний': 'величезної',
    'неймовірного': 'неймовірної', 'неймовірний': 'неймовірної',
    'помірного': 'помірної',
    'додаткового': 'додаткової', 'додатковий': 'додаткової',
    'великого': 'великої',
    'завданого': 'завданої', 'завданий': 'завданої',
    'звичайного': 'звичайної',
    'подвійний': 'подвійної',
    'більший': 'більшої', 'менший': 'меншої',
    'нанесеного': 'нанесеної',
}

# masc nominative/accusative -> nominative fem (-а), used after passive
# "завдається" (шкода is the subject) and for bare nominative labels.
NOM_FEM = {
    'величезний': 'величезна', 'невеликий': 'невелика', 'додатковий': 'додаткова',
    'суттєвий': 'суттєва', 'неймовірний': 'неймовірна',
}

# masc nominative/accusative -> accusative fem (-у), used after
# отримує/отримують (отримати governs accusative) and "збільшите" (2nd pers.).
ACC_FEM = {
    'суттєвий': 'суттєву', 'величезний': 'величезну', 'невеликий': 'невелику',
    'неймовірний': 'неймовірну', 'додатковий': 'додаткову', 'завданий': 'завдану',
}


def alt(d):
    return '|'.join(sorted(d, key=len, reverse=True))


def fix(text):
    # 1. passive "завдається [ADJ] урон" -> nominative "завдається [ADJ-fem] шкода"
    def passive_repl(m):
        verb, adj = m.group(1), m.group(2)
        fem = NOM_FEM.get(adj, adj) if adj else None
        return f'{verb} {fem} шкода' if fem else f'{verb} шкода'
    text = re.sub(
        rf'([Зз]авдається)(?:\s+({alt(NOM_FEM)}))?\s+урон[ау]?\b',
        passive_repl, text,
    )

    # 2. завдає/завдають/завдаючи [ADJ [mid words]] урон(а/у)? -> genitive "... шкоди"
    def deal_repl(m):
        verb, adj, mid = m.group(1), m.group(2), m.group(3) or ''
        if adj:
            return f'{verb} {GEN_FEM.get(adj, adj)}{mid} шкоди'
        return f'{verb}{mid} шкоди'
    text = re.sub(
        rf'([Зз]авда(?:є|ють|ючи))(?:\s+({alt(GEN_FEM)}))?((?:\s+\S+){{0,2}}?)\s+урон[ау]?\b',
        deal_repl, text,
    )

    # 3. отримує/отримують [ADJ] урон -> accusative "... шкоду"
    def receive_repl(m):
        verb, adj = m.group(1), m.group(2)
        fem = ACC_FEM.get(adj, adj) if adj else None
        return f'{verb} {fem} шкоду' if fem else f'{verb} шкоду'
    text = re.sub(
        rf'([Оо]тримує|[Оо]тримують)(?:\s+({alt(ACC_FEM)}))?\s+урон\b',
        receive_repl, text,
    )

    # 4. "збільшите завданий урон" -> "збільшите завдану шкоду"
    text = re.sub(r'([Зз]більшите)\s+завданий\s+урон\b', r'\1 завдану шкоду', text)

    # 5. bare verb + урон (no adjective) -> accusative "... шкоду"
    text = re.sub(
        r'((?:[Іі]стотно\s+)?(?:[Зз]нижує|[Сс]корочує|[Зз]більшує|[Зз]меншує))\s+урон\b',
        r'\1 шкоду', text,
    )

    # 6. standalone nominative labels
    text = text.replace('Урон в ближньому бою:', 'Шкода в ближньому бою:')
    text = text.replace('Урон в дальньому бою:', 'Шкода в дальньому бою:')
    text = re.sub(r'Додатковий урон\b', 'Додаткова шкода', text)
    text = re.sub(r'Урон\b(\s*,)', r'Шкода\1', text)  # "Урон, що ..."

    # 7. anything left with a genitive ending has no case ambiguity - just swap the noun.
    text = re.sub(r'\bурон[ау]\b', 'шкоди', text)

    return text


with open(STRINGS_PATH, encoding='utf-8') as f:
    data = json.load(f)

changed = 0
for entry in data['strings']:
    ua = entry.get('ua') or ''
    if not ua or not re.search(r'\bурон', ua, re.IGNORECASE):
        continue
    new_ua = fix(ua)
    if new_ua != ua:
        entry['ua'] = new_ua
        changed += 1

leftover = [
    (e['var'], e['ua']) for e in data['strings']
    if re.search(r'\b[Уу]рон\w*\b', e.get('ua') or '')
]

if leftover:
    print(f'STOPPING - {len(leftover)} entries still contain "урон" after all rules:')
    for var, ua in leftover:
        print(f'  {var}: {ua!r}')
    print('Not saving. Fix the rules above and re-run.')
else:
    with open(STRINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'Entries changed: {changed}')
    print('No leftover "урон" occurrences - saved cleanly.')
