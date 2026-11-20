import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
OB = "об'єкт"
def show(n, ind=0):
    rs = n.get('рядки', []); own = sum(1 for r in rs if 'див' not in r); ref = len(rs) - own
    print('  ' * ind + '%s [%s] own=%d ref=%d' % (n.get('назва'), n.get(OB, ''), own, ref))
    for k in ('прибудови', 'юніти'):
        for c in n.get(k, []): show(c, ind + 1)
print('== Фортеця'); show(d['Фортеця'])
print('== Будівлі'); [show(b) for b in d['Будівлі']]
print('== Герої'); [show(h) for h in d['Герої']]
print('== Книга', len(d['Книга сил']['рядки']), '== Загальні', len(d['Загальні кнопки']))
print([r['en'] for r in d['Загальні кнопки']])
