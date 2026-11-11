"""fonts/Aniron.ttf + digits 0-9 from the stock Omnia LT Std -> fonts/Aniron_OmniaDigits.ttf.

Aniron's own figures are small and decorative; titles with numbers looked unlike the English game. The stock Omnia
outlines (both fonts are TrueType, so no curve conversion) are scaled by the cap-height ratio, so digits keep the
size they have next to Omnia's capitals. Copied glyphs lose their hinting; Aniron's kern table has no digit pairs.
"""
import os

from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'fonts', 'Aniron.ttf')
DIGITS_FROM = os.path.join(HERE, 'fonts', 'omnialtstd_stock.ttf')  # rotwk\Data1.big omnialtstd.ttf, untouched
OUT = os.path.join(HERE, 'fonts', 'Aniron_OmniaDigits.ttf')


def cap_height(font):
    return font['glyf'][font.getBestCmap()[ord('H')]].yMax


def main():
    dst, src = TTFont(SRC), TTFont(DIGITS_FROM)
    scale = cap_height(dst) / cap_height(src)
    dcmap, scmap = dst.getBestCmap(), src.getBestCmap()
    sglyphs = src.getGlyphSet()
    for ch in '0123456789':
        dname, sname = dcmap[ord(ch)], scmap[ord(ch)]
        pen = TTGlyphPen(None)
        sglyphs[sname].draw(TransformPen(pen, (scale, 0, 0, scale, 0, 0)))
        glyph = pen.glyph()
        glyph.recalcBounds(dst['glyf'])
        dst['glyf'][dname] = glyph
        dst['hmtx'][dname] = (round(src['hmtx'][sname][0] * scale), glyph.xMin)
    for tag in ('hdmx', 'LTSH', 'VDMX'):  # per-size hinting caches, stale after outline changes
        if tag in dst:
            del dst[tag]
    dst.save(OUT)
    print(f'scale {scale:.3f} -> {OUT}')


if __name__ == '__main__':
    main()
