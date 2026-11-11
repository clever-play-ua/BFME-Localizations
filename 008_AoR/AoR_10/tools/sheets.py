"""Sheets of ../RotK_campaign_strings.xlsx shared by the import / export / build scripts."""
import os

XLSX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'RotK_campaign_strings.xlsx')
# campaign sheets (Задание | Переменная | EN | RU | UK AI | UK | Тип); a label is on at most one of them
CAMPAIGN_SHEETS = ['FotR', 'TTT', 'RotK', 'Angmar']
ALL_SHEET = 'Усі рядки'  # every label; its campaign rows are copies (see export_all_sheet.py)
UK_SHEETS = CAMPAIGN_SHEETS + [ALL_SHEET]  # where translations are read from, in priority order
# menu / interface labels (APT, GUI, SIDE, ...): {var, group, en, ru, uk_ai, uk_ai_source, uk}; uk wins over uk_ai.
# Read after the campaign sheets and before «Усі рядки».
MENU_JSON = os.path.join(os.path.dirname(XLSX), 'menu_strings.json')
