"""Review pack of AoR's story videos: video (.vp6, embedded audio chunks stripped) + voice (DialogEvent mp3) -> mp4,
named NNN_<VideoName>.mp4 in story order (000 = intro shown at game start), with NNN_<VideoName>.en.srt / .uk.srt beside.
Subtitles come from AoR_10/movie_subtitles/final_en.py (+ final_uk.py when present); also writes movie_subtitles/final.json
(cues with seconds and frames at each video's fps, for the in-game movie INIs later).
usage: python build_movie_review.py [--subs-only]"""
import json, os, re, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
MS = os.path.join(HERE, '..', 'movie_subtitles')
sys.path.insert(0, MS); sys.path.insert(0, HERE)
import final_en as F
import ea_vp6_tool
try:
    import final_uk as U
except ImportError:
    U = None
AOR = 'F:/BFME-AgeoftheRing/aotr/data/'
OUT = os.path.join(HERE, '..', '..', '.temp', 'movies_review')
FPS = json.load(open(os.path.join(MS, 'fps.json')))
ES = json.load(open(os.path.join(HERE, '..', '..', '.temp', 'subtitles_es', 'es_reference.json'), encoding='utf-8'))['movies']


def video_file(v):
    cur, out = None, {}
    for l in open(AOR + 'ini/video.ini', encoding='latin-1'):
        m = re.match(r'^Video\s+(\S+)', l)
        if m:
            cur = m.group(1); continue
        m = re.match(r'^\s*Filename\s*=\s*(\S+)', l)
        if m and cur and cur not in out:
            out[cur] = m.group(1)
    return out[v]


def mp3(v):
    return AOR + 'audio/speech/' + ('CS01' if v == 'Overall_Game_Intro' else v.replace('_', '')) + '.mp3'


def cues(v):
    """[(start_sec, end_sec, en)] in time order"""
    fps = FPS.get(v, 24.0)
    out = [(c['start'] / fps, c['end'] / fps, t) for c, t in zip(ES.get(v, {}).get('subtitles', []), F.EN.get(v, []))]
    out += list(F.EXTRA.get(v, [])) + list(F.WHISPER.get(v, []))
    return sorted(out)


def rows(text):
    if '\n' in text or len(text) <= 44:
        return text
    words = text.split(); best = None
    for i in range(1, len(words)):
        a, b = ' '.join(words[:i]), ' '.join(words[i:])
        score = abs(len(a) - len(b)) - (8 if re.search(r'[,.;:!?]$', a) else 0)
        if best is None or score < best[0]:
            best = (score, a, b)
    return best[1] + '\n' + best[2]


def ts(sec):
    ms = round(sec * 1000); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def srt(path, items):
    with open(path, 'w', encoding='utf-8-sig', newline='\r\n') as o:
        o.write('\n'.join(f'{i}\n{ts(a)} --> {ts(b)}\n{rows(t)}\n' for i, (a, b, t) in enumerate(items, 1)))


def main():
    os.makedirs(OUT, exist_ok=True)
    final = {}
    for n, v in enumerate(F.ORDER):
        base = os.path.join(OUT, f'{n:03}_{v}')
        cs = cues(v); fps = FPS.get(v, 24.0)
        uk = getattr(U, 'UK', {}).get(v) if U else None
        final[v] = {'order': n, 'fps': fps, 'file': video_file(v), 'cues': [
            {'start': round(a, 3), 'end': round(b, 3), 'start_frame': int(round(a * fps)), 'end_frame': int(round(b * fps)), 'en': t,
             **({'uk': uk[i]} if uk and i < len(uk) else {})} for i, (a, b, t) in enumerate(cs)]}
        if cs:
            srt(base + '.en.srt', cs)
            if uk:
                srt(base + '.uk.srt', [(a, b, uk[i]) for i, (a, b, _) in enumerate(cs)])
        if '--subs-only' in sys.argv or os.path.exists(base + '.mp4'):
            continue
        with tempfile.TemporaryDirectory() as tmp:
            stripped = os.path.join(tmp, 'v.vp6')
            ea_vp6_tool.strip_audio(AOR + 'movies/' + video_file(v) + '.vp6', stripped)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', stripped, '-i', mp3(v), '-map', '0:v', '-map', '1:a',
                            '-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', '-b:a', '192k', base + '.mp4'], check=True)
        print(n, v, flush=True)
    json.dump(final, open(os.path.join(MS, 'final.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('done', len(final))


if __name__ == '__main__':
    main()
