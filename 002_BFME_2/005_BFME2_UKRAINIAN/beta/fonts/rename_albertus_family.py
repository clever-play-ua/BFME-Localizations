"""
Produces AlbertusMTUA.otf from 000_TOOLKIT/fonts/albertusmt_ua.otf by renaming
its internal font-family name (the 'name' table's nameID 1/3/4 records) from
"Albertus MT" to "AlbertusMTUA".

Why this is needed: albertusmt_ua.otf (the Cyrillic-glyph Albertus MT clone
already used by the BFME1 toolkit) is internally registered under the SAME
family name as the stock game font, "Albertus MT". Adding it as a second
LocalFontFile entry for that same family is ambiguous - BFME2 doesn't
reliably let the later declaration win (TOOLKIT_NOTES.md 3.7 documents this
as a known-ambiguous case for BFME1 too, not a dependable "last one wins"
rule). A real FontSubstitution rule (FontSubstitution "Albertus MT" -> X)
needs X to be a DIFFERENT family name than "Albertus MT" itself - hence the
rename.

sachawyntertight_ua.ttf needed no such treatment - it's already registered
under its own distinct family, "SachaWynterTight".

Run once; the output (AlbertusMTUA.otf) is committed alongside this script,
re-run only if the source font ever changes.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonttools_pkg'))
from fontTools.ttLib import TTFont

SRC = r'C:\Users\UserM\Documents\GitHub\BFME-Localizations\000_TOOLKIT\fonts\albertusmt_ua.otf'
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'AlbertusMTUA.otf')
NEW_NAME = 'AlbertusMTUA'

font = TTFont(SRC)
name_table = font['name']

for rec in name_table.names:
    text = rec.toUnicode()
    if 'Albertus MT' in text:
        new_text = text.replace('Albertus MT', NEW_NAME)
        if rec.nameID == 6:  # PostScript name: no spaces allowed
            new_text = new_text.replace(' ', '')
        name_table.setName(new_text, rec.nameID, rec.platformID, rec.platEncID, rec.langID)

font.save(DST)
print(f'saved {DST}')

# sanity check: re-open and confirm the rename stuck
check = TTFont(DST)
family = check['name'].getDebugName(1)
print(f'family name is now: {family!r}')
assert family == NEW_NAME
