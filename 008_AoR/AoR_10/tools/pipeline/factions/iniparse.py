"""INI index: objects / parents / command sets / buttons / upgrades / specialpowers (cached in ini_idx.pkl).
#include files are expanded in place (relative to the including file)."""
import glob, os, pickle, re
AOR = r'F:/BFME-AgeoftheRing/aotr'
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'ini_idx.pkl')
DECL = re.compile(r'^[ \t]*(Object|ObjectReskin|ChildObject|CommandSet|CommandButton|Upgrade|SpecialPower|Science)'
                  r'[ \t]+([^\s=]+)(?:[ \t]+([^\s=]+))?[ \t]*$', re.M)
INC = re.compile(r'^[ \t]*#include[ \t]+"([^"]+)"', re.M | re.I)
_cache = {}


def read(p, depth=0):
    p = os.path.normpath(p)
    if p.lower() not in _cache:
        try:
            t = open(p, encoding='cp1252', errors='replace').read()
        except OSError:
            t = ''
        _cache[p.lower()] = t
    t = _cache[p.lower()]
    if depth > 8:
        return t
    d = os.path.dirname(p)
    return INC.sub(lambda m: read(os.path.join(d, m.group(1).replace('\\', '/')), depth + 1), t)


def load():
    if os.path.exists(CACHE):
        return pickle.load(open(CACHE, 'rb'))
    D = {k: {} for k in ('Object', 'CommandSet', 'CommandButton', 'Upgrade', 'SpecialPower', 'Science')}
    parent, defines = {}, {}
    for p in glob.glob(AOR + '/data/ini/**/*.ini', recursive=True):
        t = read(p)
        for m in re.finditer(r'^[ \t]*#define[ \t]+(\w+)[ \t]+(.*)$', t, re.M):
            defines[m.group(1).upper()] = m.group(2).split(';')[0].strip()
        t = re.sub(r';.*|//.*', '', t)
        ms = list(DECL.finditer(t))
        for i, m in enumerate(ms):
            end = ms[i + 1].start() if i + 1 < len(ms) else len(t)
            kind, name, par = m.group(1), m.group(2), m.group(3)
            if kind in ('ObjectReskin', 'ChildObject'):
                parent[name] = par; kind = 'Object'
            if name not in D[kind]:  # first definition wins (the engine rejects duplicates)
                D[kind][name] = t[m.end():end]
    D['parent'] = parent; D['defines'] = defines
    pickle.dump(D, open(CACHE, 'wb'))
    return D
