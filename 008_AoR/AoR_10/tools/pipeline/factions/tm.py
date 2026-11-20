"""Line-level translation memory from every EN/UA pair the build knows (same line count), most frequent UA wins."""
import collections, json, re, sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import importlib.util


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def build():
    spec = importlib.util.spec_from_file_location('mf_ua', os.path.join(HERE, 'mf_ua.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    STR, UA = m.STR, m.UA
    whole, line = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    for k, (ua, st, src) in UA.items():
        if k not in STR or not STR[k]['en']:
            continue
        en = STR[k]['en'].replace('\n', '\n'); u = ua.replace('\n', '\n')
        whole[norm(en)][u] += 1
        el = [x for x in en.split('\n')]; ul = [x for x in u.split('\n')]
        if len(el) == len(ul):
            for a, b in zip(el, ul):
                if norm(a) and norm(b):
                    line[norm(a)][b.strip()] += 1
    return STR, UA, whole, line
