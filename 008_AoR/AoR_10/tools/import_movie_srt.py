"""Read the proofread subtitles back: 008_AoR/.temp/movies_review/NNN_<Video>.uk.srt (and .en.srt) -> movie_subtitles/edited.json
{video: [{start, end, start_frame, end_frame, uk|en}]}. Frames = seconds * that video's own fps (movie_subtitles/fps.json), the unit
of the game's movie subtitle INIs. Timings, text, added or removed cues in the .srt are all taken as they are.
usage: python import_movie_srt.py"""
import glob, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
MS = os.path.join(HERE, '..', 'movie_subtitles')
SRC = os.path.join(HERE, '..', '..', '.temp', 'movies_review')
FPS = json.load(open(os.path.join(MS, 'fps.json')))


def sec(t):
    h, m, s = t.replace(',', '.').split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)


def read(path):
    txt = open(path, encoding='utf-8-sig').read().replace('\r\n', '\n')
    out = []
    for block in re.split(r'\n\s*\n', txt.strip()):
        lines = block.split('\n')
        m = re.match(r'(\S+)\s*-->\s*(\S+)', lines[1] if len(lines) > 1 else '')
        if m:
            out.append((sec(m.group(1)), sec(m.group(2)), '\n'.join(lines[2:]).strip()))
    return out


def main():
    data = {}
    for path in sorted(glob.glob(os.path.join(SRC, '*.srt'))):
        name = os.path.basename(path)
        m = re.match(r'\d+_(.+)\.(uk|en)\.srt$', name)
        if not m:
            continue
        v, lang = m.groups(); fps = FPS.get(v, 24.0)
        cues = data.setdefault(v, {}).setdefault(lang, [])
        for a, b, t in read(path):
            cues.append({'start': round(a, 3), 'end': round(b, 3), 'start_frame': int(round(a * fps)),
                         'end_frame': int(round(b * fps)), 'text': t})
    json.dump(data, open(os.path.join(MS, 'edited.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(data), 'videos;', sum(len(x.get('uk', [])) for x in data.values()), 'UA cues')


if __name__ == '__main__':
    main()
