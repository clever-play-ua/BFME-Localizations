"""
Copy the editor's UK column from a Google Sheets CSV export back into ../RotK_campaign_strings.xlsx.

Matches rows by «Переменная», so column order / sorting / filters in the exported sheet don't matter.
Only non-empty UK cells are copied; UK AI and everything else in the xlsx stay untouched.

Works for a CSV of any sheet: each label goes to the campaign sheet it is on (FotR/TTT/RotK/Angmar), the rest into «Усі рядки».

Run:  python import_uk_csv.py "F:\\ЗАГРУЗКИ\\RotK_campaign_strings.xlsx - RotK.csv"
then: python export_all_sheet.py   (refresh the campaign copies on «Усі рядки»)
      python build_uk_submod.py
"""
import collections, csv, os, sys
from openpyxl import load_workbook
from sheets import UK_SHEETS, XLSX


def main(csv_path):
    rows = list(csv.reader(open(csv_path, encoding='utf-8-sig', newline='')))
    head = rows[0]
    iv, iuk = head.index('Переменная'), head.index('UK')
    im = head.index('Задание') if 'Задание' in head else None
    new = {r[iv].lower(): (r[iuk].strip(), r[im] if im is not None else '') for r in rows[1:] if r[iv] and r[iuk].strip()}

    wb = load_workbook(XLSX)
    changed, per_mission, seen = 0, collections.Counter(), set()
    # campaign sheets first; «Усі рядки» only for labels on none of them (its campaign rows are copies)
    for name in UK_SHEETS:
        if name not in wb.sheetnames:
            continue
        ws = wb[name]
        cols = {c.value: c.column for c in ws[1]}
        cv, cuk = cols['Переменная'], cols['UK']
        for row in range(2, ws.max_row + 1):
            k = (ws.cell(row, cv).value or '').lower()
            if k in new and k not in seen:
                seen.add(k)
                text, mission = new[k]
                if ws.cell(row, cuk).value != text:
                    ws.cell(row, cuk).value = text
                    changed += 1
                per_mission[f'{name} {mission}'.strip()] += 1
    unknown = sorted(set(new) - seen)
    if unknown:
        sys.exit(f'labels in CSV but not in xlsx: {unknown[:10]}')

    wb.save(XLSX)
    print(f'UK rows in CSV: {len(new)}, changed in xlsx: {changed}')
    for m, n in sorted(per_mission.items()):
        print(f'  {m}: {n}')


if __name__ == '__main__':
    main(sys.argv[1])
