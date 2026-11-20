"""One-off fixes on the proofread .uk.srt files (2026-11-19, user answers: keep «слідопит», keep «мілорде», no «пан»,
split the 81-character line). Edits the files in 008_AoR/.temp/movies_review in place; re-run import_movie_srt.py after."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from import_movie_srt import read, SRC
from build_movie_review import ts

FIX = {  # file prefix -> [(old, new)] on the cue text (whole file, exact substrings)
    '000_': [('Скоро я або здобу все чого прагнув.', 'Скоро я або здобуду все, чого прагнув,'),
             ('Або темрява поглине мене', 'або темрява поглине мене.'), ('Поверення Короля', 'Повернення Короля'),
             ('Розповідь що об', 'Розповідь, що об'), ('Ми будемо битися\n', 'Ми будемо битися.\n')],
    '001_': [('\nо контролює інші.', '\nщо контролює інші.'), ('перснів було дано людям.', 'перснів було дано людям,')],
    '002_': [('легко спокусити\n', 'легко спокусити,\n')],
    '005_': [('"Мій дорогесенький"', 'Мій дорогесенький.'), ('Але це все, Фродо\n', 'Але це все, Фродо.\n')],
    '006_': [('приспішник', 'поплічник'), ('пане Ґемджі', 'містере Ґемджі')],
    '009_': [('І лше там', 'І лише там')],
    '018_': [('О спасіть нас.', 'О, спасіть нас.')],
    '020_': [('як наче століття', 'наче століття')],
    '021_': [('прям біля мене', 'прямо біля мене'), ('Прошу\n', 'Прошу.\n')],
    '022_': [('відберете старого', 'відберете в старого')],
    '024_': [('Гельмів яр', 'Гельмів Яр')],
    '025_': [('А я оно тут', 'А я ось тут')],
    '026_': [('що десь у диких земля.', 'десь у диких землях.'), ('Гельмів яр', 'Гельмів Яр')],
    '035_': [('мені, щось не хочеться', 'мені щось не хочеться')],
    '045_': [('«Туди й назад.', '«Туди й назад».')],
    '046_': [("сер'озно", 'серйозно')],
}
SPLIT = {'027_': ('Люди ще не настільки слабкі, щоб зовсім', 13.85, 13.90,
                  'Люди ще не настільки слабкі,', 'щоб зовсім не могти опиратися волі Темного Володаря.')}

for name in sorted(os.listdir(SRC)):
    if not name.endswith('.uk.srt'):
        continue
    pre = name[:4]
    if pre not in FIX and pre not in SPLIT:
        continue
    path = os.path.join(SRC, name)
    cues = read(path)
    text = '\n\n'.join(t for _, _, t in cues) + '\n'
    for a, b in FIX.get(pre, []):
        if a not in text:
            print('  already fixed / not found:', name, repr(a))
    out = []
    for s, e, t in cues:
        t2 = t + '\n'
        for a, b in FIX.get(pre, []):
            t2 = t2.replace(a, b)
        t2 = t2.rstrip('\n')
        if pre in SPLIT and t.startswith(SPLIT[pre][0]):
            _, e1, s2, x1, x2 = SPLIT[pre]
            out += [(s, e1, x1), (s2, e, x2)]
        else:
            out.append((s, e, t2))
    with open(path, 'w', encoding='utf-8-sig', newline='\r\n') as o:
        o.write('\n'.join(f'{i}\n{ts(a)} --> {ts(b)}\n{t}\n' for i, (a, b, t) in enumerate(out, 1)))
    print(name, len(cues), '->', len(out))
