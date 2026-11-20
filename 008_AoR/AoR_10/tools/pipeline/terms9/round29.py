"""Round 29 (2026-11-19): AoR 10.0.2 changed a few English campaign lines -> follow them in UA.
masteratarms013 was rewritten («That's enough of that» -> «I expected more from you.»), Pippin's line now ends with «!»,
four lines gained a final full stop.  --dry."""
import os, re
H = os.path.dirname(os.path.abspath(__file__))
REPLACE = {
    'SCRIPT:mgfotr_masteratarms013': ('Досить', 'Я чекав від тебе більшого.'),
    'SCRIPT:mgfotr_pippin016': ('Піпін: Це ж те дерево...', 'Піпін: Це ж те дерево!'),
}
FULL_STOP = {'SCRIPT:Dialogue_Eaves_Eomer Scouts 03', 'DIALOGEVENT:mgfotr_halbarad014', 'SCRIPT:mgfotr_gimli093',
             'SCRIPT:mgfotr_kod022'}


def fix(var, en, ua):
    if not ua:
        return ua
    if var in REPLACE and ua.strip() == REPLACE[var][0]:
        return REPLACE[var][1]
    if var in FULL_STOP and not re.search(r'[.!?…»]\s*$', ua):
        return ua.rstrip() + '.'
    return ua


if __name__ == '__main__':
    a9 = open(os.path.join(H, 'apply9.py'), encoding='utf-8').read()
    exec(a9.split('EX = [')[0]); walker = a9.split('log = []')[1]
    LOGNAME = 'round29_log.txt'
    exec('log = []' + walker)
