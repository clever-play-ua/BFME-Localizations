"""ButtonImage names -> {name: data:image/webp;base64,...} (icons.json); 64x64 crops from the game's texture atlases."""
import base64, glob, io, json, os, re, sys
from PIL import Image
AOR = 'F:/BFME-AgeoftheRing/aotr'
HERE = os.path.dirname(os.path.abspath(__file__))
MI = {}
for p in glob.glob(AOR + '/data/ini/mappedimages/**/*.ini', recursive=True):
    t = open(p, encoding='cp1252', errors='replace').read()
    for m in re.finditer(r'^\s*MappedImage\s+(\S+)(.*?)^\s*End', t, re.M | re.S | re.I):
        b = m.group(2)
        tex = re.search(r'Texture\s*=\s*(\S+)', b, re.I)
        c = re.search(r'Left:\s*(\d+)\s+Top:\s*(\d+)\s+Right:\s*(\d+)\s+Bottom:\s*(\d+)', b, re.I)
        tw = re.search(r'TextureWidth\s*=\s*(\d+)', b, re.I); th = re.search(r'TextureHeight\s*=\s*(\d+)', b, re.I)
        if tex and c and m.group(1).lower() not in MI:
            MI[m.group(1).lower()] = (tex.group(1), tuple(map(int, c.groups())), int(tw.group(1)) if tw else 0, int(th.group(1)) if th else 0)
_tex = {}
# textures and mapped images that live inside .big archives (AoR first, then RotWK, then BFME2 - the game's load order)
import struct
BIGS, BIGTEX = [], {}


def _big_index():
    if BIGS:
        return
    for root in ('F:/BFME-AgeoftheRing/aotr', 'F:/BFME-AgeoftheRing/rotwk', 'F:/BFME-AgeoftheRing/bfme2'):
        for path in sorted(glob.glob(root + '/*.big')):
            low = os.path.basename(path).lower()
            if any(k in low for k in ('audio', 'music', 'speech', 'ambient', 'maps', 'terrain', 'shaders', 'w3d')):
                continue
            with open(path, 'rb') as f:
                h = f.read(16)
                if h[:4] not in (b'BIGF', b'BIG4'):
                    continue
                n = struct.unpack('>I', h[8:12])[0]; first = struct.unpack('>I', h[12:16])[0]
                idx = f.read(first - 16); p = 0
                for _ in range(n):
                    off, size = struct.unpack('>II', idx[p:p + 8]); p += 8
                    e = idx.index(b'\0', p); name = idx[p:e].decode('latin1').replace(chr(92), '/'); p = e + 1
                    BIGS.append((path, off, size, name))
                    ln = name.lower()
                    if ln.startswith('art/') and ln.endswith(('.dds', '.tga')):
                        BIGTEX.setdefault(os.path.splitext(os.path.basename(ln))[0], (path, off, size))
                    elif ln.endswith('.ini') and 'mappedimages' in ln:
                        f2 = open(path, 'rb'); f2.seek(off); t = f2.read(size).decode('cp1252', 'replace'); f2.close()
                        for m in re.finditer(r'^\s*MappedImage\s+(\S+)(.*?)^\s*End', t, re.M | re.S | re.I):
                            b = m.group(2)
                            tex = re.search(r'Texture\s*=\s*(\S+)', b, re.I)
                            c = re.search(r'Left:\s*(\d+)\s+Top:\s*(\d+)\s+Right:\s*(\d+)\s+Bottom:\s*(\d+)', b, re.I)
                            tw = re.search(r'TextureWidth\s*=\s*(\d+)', b, re.I); th = re.search(r'TextureHeight\s*=\s*(\d+)', b, re.I)
                            if tex and c and m.group(1).lower() not in MI:
                                MI[m.group(1).lower()] = (tex.group(1), tuple(map(int, c.groups())), int(tw.group(1)) if tw else 0, int(th.group(1)) if th else 0)


def _big_texture(base):
    _big_index()
    hit = BIGTEX.get(base)
    if not hit:
        return None
    path, off, size = hit
    with open(path, 'rb') as f:
        f.seek(off); data = f.read(size)
    try:
        return Image.open(io.BytesIO(data)).convert('RGBA')
    except Exception:
        return None


def texture(name):
    base = os.path.splitext(name)[0].lower()
    if base not in _tex:
        _tex[base] = None
        for root in (AOR + '/art/compiledtextures', AOR + '/art/textures', 'F:/BFME-AgeoftheRing/rotwk/art/compiledtextures'):
            for ext in ('.dds', '.tga'):
                for cand in (f'{root}/{base[:2]}/{base}{ext}', f'{root}/{base}{ext}'):
                    hits = glob.glob(cand) or [f for f in glob.glob(os.path.dirname(cand) + '/*' + ext) if os.path.basename(f).lower() == base + ext]
                    if hits:
                        _tex[base] = Image.open(hits[0]).convert('RGBA'); return _tex[base]
        _tex[base] = _big_texture(base)
    return _tex[base]


def icon(name, size=64):
    mi = MI.get(name.lower())
    if not mi:
        _big_index()
        low = name.lower()  # unused/renamed variants of the same picture (e.g. HIKhamulNew -> HiKhamulNewUnused)
        for alt in (low + 'unused', re.sub(r'new$', '', low), low.replace('new', ''), low + '_res'):
            if MI.get(alt):
                mi = MI[alt]; break
    if not mi:
        return None
    tex, (l, t, r, b), tw, th = mi
    im = texture(tex)
    if im is None:
        return None
    sx, sy = (im.width / tw if tw else 1), (im.height / th if th else 1)
    crop = im.crop((round(l * sx), round(t * sy), round(r * sx), round(b * sy))).resize((size, size), Image.LANCZOS)
    buf = io.BytesIO(); crop.save(buf, 'WEBP', quality=82, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode()


if __name__ == '__main__':
    need = json.load(open(sys.argv[1]))
    out, miss = {}, []
    for n in need:
        v = icon(n)
        if v: out[n] = v
        else: miss.append(n)
    json.dump(out, open(sys.argv[2], 'w'))
    print(len(out), 'ok,', len(miss), 'missing', miss[:20], sum(len(v) for v in out.values()) // 1024, 'KB')
