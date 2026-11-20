"""Print a community export as before -> after (word-level marks), for proofreading. python review_dump.py <file.json> > out.txt"""
import difflib, json, re, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))


def wdiff(a, b):
    A, B = re.findall(r'\S+|\n', a), re.findall(r'\S+|\n', b)
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, A, B).get_opcodes():
        if op == 'equal':
            out.append(' '.join(A[i1:i2]))
        else:
            if i1 < i2: out.append('[-' + ' '.join(A[i1:i2]) + '-]')
            if j1 < j2: out.append('{+' + ' '.join(B[j1:j2]) + '+}')
    return ' '.join(out).replace(' \n ', ' / ').replace('\n', ' / ')


for n, e in enumerate(d['edits'], 1):
    if e.get('follows'):
        continue
    print(f"#{n} {e['var']}  [{e['type']}]  {e['where']}")
    print('  EN :', e['en'].replace('\n', ' / '))
    print('  ΔUA:', wdiff(e['before'], e['uk']))
    print()
