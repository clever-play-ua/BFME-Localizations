"""
(Re)build the «Усі рядки» sheet of ../RotK_campaign_strings.xlsx: every label of AoR 10.0 in one place.

    Категорія | Джерело | Переменная | EN | RU | UK AI | UK | Кампанія

    EN, Джерело     ../strings.json (data/lotr.str + all maps/*/map.str)
    RU              ../strings.json ru (RU submod 9.3.1, 008_AoR/ru)
    UK AI, UK       rows on a campaign sheet (sheets.CAMPAIGN_SHEETS) or in menu_strings.json: copied from there, edit them there
                    (Кампанія = sheet / mission)
                    all other rows: kept from the previous «Усі рядки» sheet, so translations typed here survive a rerun
Literal \\n = line break, as on the campaign sheets. build_uk_submod.py reads UK/UK AI from all of them.

Run:  python export_all_sheet.py      (rerun after importing editor CSVs, to refresh the campaign copies)
"""
import json, os
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from sheets import ALL_SHEET as SHEET, CAMPAIGN_SHEETS, MENU_JSON, XLSX

AOR10 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD = ['Категорія', 'Джерело', 'Переменная', 'EN', 'RU', 'UK AI', 'UK', 'Кампанія']


def lit(s):
    return (s or '').replace('\n', '\\n')


def rows_of(ws):
    it = ws.iter_rows(values_only=True)
    head = list(next(it))
    return [dict(zip(head, r)) for r in it]


def main():
    strings = json.load(open(os.path.join(AOR10, 'strings.json'), encoding='utf-8'))['strings']
    wb = load_workbook(XLSX)
    rotk = {}  # label -> its campaign-sheet row
    for name in CAMPAIGN_SHEETS:
        if name in wb.sheetnames:
            for r in rows_of(wb[name]):
                if r['Переменная']:
                    rotk[r['Переменная'].lower()] = dict(r, Кампанія=f"{name} / {r['Задание']}")
    if os.path.exists(MENU_JSON):  # menu labels are edited in menu_strings.json: shown here as copies too
        for m in json.load(open(MENU_JSON, encoding='utf-8'))['strings']:
            rotk.setdefault(m['var'].lower(), {'UK AI': lit(m['uk_ai']), 'UK': lit(m['uk']), 'Кампанія': 'Меню (menu_strings.json)'})
    kept = {}
    if SHEET in wb.sheetnames:
        kept = {(r['Переменная'] or '').lower(): r for r in rows_of(wb[SHEET]) if r['Переменная']}
        del wb[SHEET]
    ws = wb.create_sheet(SHEET, len([n for n in wb.sheetnames if n in CAMPAIGN_SHEETS]))
    ws.append(HEAD)

    n_ru = n_uk = 0
    for s in strings:
        k = s['var'].lower()
        src = 'map.str: ' + ', '.join(s['maps']) if s.get('maps') else 'lotr.str'
        r = rotk.get(k) or kept.get(k) or {}
        ws.append([s['var'].split(':')[0].upper() if ':' in s['var'] else '', src, s['var'], lit(s['en']), lit(s.get('ru')),
                   r.get('UK AI') or None, r.get('UK') or None, rotk[k]['Кампанія'] if k in rotk else None])
        n_ru += bool(s.get('ru'))
        n_uk += bool(r.get('UK') or r.get('UK AI'))

    grey, green, yellow = (PatternFill('solid', fgColor=c) for c in ('D9D9D9', 'E2EFDA', 'FFF2CC'))
    for c in ws[1]:
        c.font, c.fill = Font(bold=True), grey
    for col, w in zip('ABCDEFGH', (13, 24, 42, 60, 60, 60, 60, 30)):
        ws.column_dimensions[col].width = w
    top = Alignment(vertical='top', wrap_text=True)
    for row in ws.iter_rows(min_row=2, min_col=4, max_col=7):
        for c in row:
            c.alignment = top
        row[2].fill, row[3].fill = green, yellow
    ws.freeze_panes = 'D2'
    ws.auto_filter.ref = f'A1:H{ws.max_row}'
    wb.save(XLSX)
    print(f'{SHEET}: {len(strings)} rows, RU {n_ru}, UK/UK AI {n_uk}, on campaign sheets {sum(s["var"].lower() in rotk for s in strings)}')


if __name__ == '__main__':
    main()
