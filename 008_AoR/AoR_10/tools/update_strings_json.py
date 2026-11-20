"""After an AoR game update: compare the installed aotr/data/lotr.str + aotr/maps/*/map.str with ../strings.json and
update the English texts that really changed (escaping differences such as \\" are ignored). Translations are not
touched: changed lines are listed so their UA can be checked (see pipeline/terms9/round29.py for 10.0.2).
usage: python update_strings_json.py 10.0.2 [--dry]"""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
STRINGS = os.path.join(os.path.dirname(HERE), 'strings.json')
GAME = 'F:/BFME-AgeoftheRing/aotr/'
BS, NL, QQ = chr(92), chr(10), chr(34)


def parse(text):
    """str file -> [(label, text)]; text keeps the file's escapes (backslash-n etc.)."""
    out, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        l = lines[i].strip()
        if not l or l.startswith('//') or l.upper() == 'END' or l.startswith(QQ):
            i += 1; continue
        lab = l.split('//')[0].strip(); i += 1; buf = []
        while i < len(lines) and lines[i].strip().upper() != 'END':
            if not lines[i].strip().startswith('//'):
                buf.append(lines[i])
            i += 1
        t = NL.join(buf).strip()
        a, b = t.find(QQ), t.rfind(QQ)
        out.append((lab, t[a + 1:b] if a != -1 and b > a else t)); i += 1
    return out


def unescape(t):
    """str escapes -> the form strings.json keeps: backslash-n = newline, backslash-quote = quote."""
    return t.replace(BS + 'n', NL).replace(BS + QQ, QQ)


def load_game():
    new = {}
    for lab, t in parse(open(GAME + 'data/lotr.str', encoding='cp1252').read()):
        new[lab.lower()] = (lab, unescape(t))
    for p in sorted(glob.glob(GAME + 'maps/*/map.str')):
        for lab, t in parse(open(p, encoding='utf-8', errors='replace').read()):
            new.setdefault(lab.lower(), (lab, unescape(t)))
    return new


def main():
    version, dry = sys.argv[1], '--dry' in sys.argv
    new = load_game()
    d = json.load(open(STRINGS, encoding='utf-8'))
    old = {s['var'].lower() for s in d['strings']}
    changed = []
    for s in d['strings']:
        k = s['var'].lower()
        if k in new and new[k][1] != s['en']:
            changed.append((s['var'], s['en'], new[k][1]))
            s['en'] = new[k][1]
    added = [new[k][0] for k in new if k not in old]
    removed = [s['var'] for s in d['strings'] if s['var'].lower() not in new]
    for v, a, b in changed:
        print('~', v, '|', repr(a[:90]), '->', repr(b[:90]))
    print('changed', len(changed), '| new labels (not added, check by hand):', added[:20], '| gone from the game:', removed[:20])
    if not dry and changed:
        d['meta']['source'] = f'Age of the Ring {version}: aotr/data/lotr.str (cp1252) + aotr/maps/*/map.str (utf-8)'
        d['meta'].setdefault('updates', []).append({'version': version, 'changed_en': [v for v, _, _ in changed]})
        raw = open(STRINGS, 'rb').read(64)
        eol = chr(13) + NL if raw.find(b'\r\n') != -1 else NL  # keep the file's line endings
        second = raw.replace(b'\r\n', b'\n').split(b'\n')[1]
        indent = (len(second) - len(second.lstrip(b' '))) or None  # keep the file's indent (2 spaces now)
        json.dump(d, open(STRINGS, 'w', encoding='utf-8', newline=eol), ensure_ascii=False, indent=indent)
        print('written', STRINGS)


if __name__ == '__main__':
    main()
