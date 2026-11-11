"""
Make "Albertus MT UA" = the game's own Albertus MT (rotwk Data1.big albertusmt.otf, has all Russian Cyrillic but
none of Ґ Є І Ї ґ є і ї) + the 8 Ukrainian letters, drawn from the font's own glyphs so the style matches:

    І і Ї ї   -> same glyphs as Latin I i Ï ï (identical letterforms)
    Є є       -> Э э mirrored horizontally
    Ґ ґ       -> Г г plus an upturn on the right end of the top bar

Family is renamed to "Albertus MT UA" (a substitution target must not share the stock family name - BFME2 lesson).

Run:  python make_albertus_ua.py      -> lang_Ukrainian/AlbertusMT_UA.otf
"""
import os
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.areaPen import AreaPen

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'fonts', 'albertusmt_stock.otf')
OUT = os.path.join(HERE, 'lang_Ukrainian', 'AlbertusMT_UA.otf')
FAMILY, PS_NAME = 'Albertus MT UA', 'AlbertusMTUA'

f = TTFont(SRC)
gs = f.getGlyphSet()
cmap = f.getBestCmap()
top = f['CFF '].cff.topDictIndex[0]
cs = top.CharStrings
priv = top.Private
hmtx = f['hmtx']


def add_glyph(name, width, draw):
    pen = T2CharStringPen(width, gs)
    draw(pen)
    charstring = pen.getCharString(private=priv, globalSubrs=f['CFF '].cff.GlobalSubrs)
    cs.charStringsIndex.append(charstring)
    cs.charStrings[name] = len(cs.charStringsIndex) - 1
    top.charset.append(name)  # this list *is* the font's glyph order for a CFF font - don't append twice
    assert f.getGlyphOrder().count(name) == 1
    bp = BoundsPen(gs); draw(bp)
    hmtx[name] = (width, int(bp.bounds[0]) if bp.bounds else 0)


def mirrored(src_name):
    w = hmtx[src_name][0]
    return w, lambda pen: gs[src_name].draw(TransformPen(ReverseContourPen(pen), (-1, 0, 0, 1, w, 0)))


def with_upturn(src_name, stem_name):
    """Г/г + a vertical tick rising from the right end of the top bar, same winding as the outer contour."""
    w = hmtx[src_name][0]
    bp = BoundsPen(gs); gs[src_name].draw(bp)
    x0, y0, x1, y1 = bp.bounds
    sp = BoundsPen(gs); gs[stem_name].draw(sp)
    stem = (sp.bounds[2] - sp.bounds[0]) * 0.55          # tick a bit thinner than a full stem
    rise = (y1 - y0) * 0.20
    ap = AreaPen(gs); gs[src_name].draw(ap)
    ccw = ap.value > 0                                      # match the glyph's own contour direction
    pts = [(x1 - stem, y1 - stem), (x1, y1 - stem), (x1, y1 + rise), (x1 - stem, y1 + rise)]
    if not ccw:
        pts = pts[::-1]

    def draw(pen):
        gs[src_name].draw(pen)
        pen.moveTo(pts[0])
        for p in pts[1:]:
            pen.lineTo(p)
        pen.closePath()
    return w, draw


add_glyph('uni0404', *mirrored(cmap[ord('Э')]))
add_glyph('uni0454', *mirrored(cmap[ord('э')]))
add_glyph('uni0490', *with_upturn(cmap[ord('Г')], 'I'))
add_glyph('uni0491', *with_upturn(cmap[ord('г')], 'l'))

new_map = {0x0404: 'uni0404', 0x0454: 'uni0454', 0x0490: 'uni0490', 0x0491: 'uni0491',
           0x0406: cmap[ord('I')], 0x0456: cmap[ord('i')], 0x0407: cmap[ord('Ï')], 0x0457: cmap[ord('ï')]}
for t in f['cmap'].tables:
    if t.isUnicode():
        t.cmap.update(new_map)

for rec in f['name'].names:
    if rec.nameID in (1, 16, 4):
        rec.string = FAMILY
    elif rec.nameID == 6:
        rec.string = PS_NAME
    elif rec.nameID == 3:
        rec.string = '1.000;UA;' + PS_NAME
top.FamilyName, top.FullName = FAMILY, FAMILY
f['CFF '].cff.fontNames = [PS_NAME]

f.save(OUT)
check = TTFont(OUT).getBestCmap()
missing = [c for c in 'ҐЄІЇґєіїАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя' if ord(c) not in check]
print('saved', OUT, '| missing Cyrillic:', missing or 'none')
