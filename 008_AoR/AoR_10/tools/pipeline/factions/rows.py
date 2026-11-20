import json
def rows_of(d):
    rows=[]
    def walk(n):
        for r in n.get('рядки', []): rows.append(r)
        for k in ('прибудови','юніти'):
            for c in n.get(k, []): walk(c)
    walk(d['Фортеця']); [walk(b) for b in d['Будівлі']]; [walk(h) for h in d['Герої']]; walk(d['Книга сил']); rows.extend(d['Загальні кнопки'])
    return rows
