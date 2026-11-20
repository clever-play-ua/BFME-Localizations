"""English subtitles for AoR's 46 story videos with Whisper (faster-whisper large-v3, GPU).
Audio = DialogEvent mp3s in aotr/data/audio/speech (AOTRCampaign*.mp3, the video name without «_»).
Output: 008_AoR/AoR_10/movie_subtitles/en/<VideoName>.srt + en.json {video: [{start, end, start_frame, end_frame, text}]}.
Frames at 24 fps (the unit of the game's movie subtitle INIs). usage: python transcribe_movies.py [VideoName ...]"""
import glob, json, os, re, site, sys, time
for _d in glob.glob(os.path.join(site.getsitepackages()[-1], 'nvidia', '*', 'bin')):  # pip CUDA libs (cublas, cudnn)
    os.add_dll_directory(_d); os.environ['PATH'] = _d + os.pathsep + os.environ['PATH']
from faster_whisper import WhisperModel

AOR = 'F:/BFME-AgeoftheRing/aotr/data/'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'movie_subtitles', 'en')
FPS = 24
MAX_CHARS, MAX_SEC = 84, 6.5          # one subtitle = up to 2 rows of ~42 characters
PROMPT = ("Gandalf, Frodo, Samwise, Merry, Pippin, Aragorn, Legolas, Gimli, Boromir, Faramir, Denethor, Théoden, Éomer, Éowyn, "
          "Saruman, Sauron, Gollum, Sméagol, Elrond, Galadriel, Isildur, Elendil, Gil-galad, Nazgûl, Uruk-hai, Mordor, Isengard, "
          "Rohan, Gondor, Minas Tirith, Osgiliath, Helm's Deep, Rivendell, Moria, Lothlórien, Middle-earth, the One Ring.")


def videos():
    v, cur = {}, None
    for l in open(AOR + 'ini/video.ini', encoding='latin-1'):
        m = re.match(r'^Video\s+(\S+)', l)
        if m:
            cur = m.group(1); continue
        m = re.match(r'^\s*Filename\s*=\s*(\S+)', l)
        if m and cur and cur not in v:
            v[cur] = m.group(1)
    return [k for k in v if k.startswith('AOTRCampaign') and not k.endswith('_PH')]


def mp3(video):
    if video == 'Overall_Game_Intro':  # the intro shown at game start (CS01.vp6 + DialogEvent CS01)
        return AOR + 'audio/speech/CS01.mp3'
    return AOR + 'audio/speech/' + video.replace('_', '') + '.mp3'


def split(words):
    """words -> subtitle cues: break at sentence ends, pauses, or length/duration limits"""
    cues, cur = [], []
    for w in words:
        if cur:
            text = ''.join(x.word for x in cur).strip()
            gap = w.start - cur[-1].end
            if (len(text) + len(w.word) > MAX_CHARS or w.end - cur[0].start > MAX_SEC or gap > 0.8
                    or (re.search(r'[.!?…]$', text) and len(text) > 25)):
                cues.append(cur); cur = []
        cur.append(w)
    if cur:
        cues.append(cur)
    return cues


def rows(text):
    """two balanced rows when longer than ~42 characters"""
    if len(text) <= 44:
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


def main():
    os.makedirs(OUT, exist_ok=True)
    novad = '--novad' in sys.argv
    want = [a for a in sys.argv[1:] if not a.startswith('--')] or videos()
    model = WhisperModel('large-v3', device='cuda', compute_type='float16')
    jp = os.path.join(OUT, 'en.json')
    data = json.load(open(jp, encoding='utf-8')) if os.path.exists(jp) else {}
    wp = os.path.join(OUT, 'words.json')
    global WORDS
    WORDS = json.load(open(wp, encoding='utf-8')) if os.path.exists(wp) else {}
    for v in want:
        t0 = time.time()
        segs, info = model.transcribe(mp3(v), language='en', beam_size=5, word_timestamps=True, vad_filter=not novad,
                                      vad_parameters={'min_silence_duration_ms': 500}, initial_prompt=PROMPT,
                                      condition_on_previous_text=False)
        words = [w for s in segs for w in (s.words or [])]
        WORDS[v] = [[round(w.start, 2), round(w.end, 2), w.word] for w in words]
        cues = []
        for c in split(words):
            text = re.sub(r'\s+', ' ', ''.join(x.word for x in c)).strip()
            if text:
                cues.append({'start': round(c[0].start, 2), 'end': round(c[-1].end + 0.3, 2), 'text': rows(text)})
        for a, b in zip(cues, cues[1:]):          # no overlaps
            a['end'] = min(a['end'], b['start'] - 0.05)
        for c in cues:
            c['start_frame'], c['end_frame'] = int(c['start'] * FPS), int(c['end'] * FPS)
        data[v] = cues
        with open(os.path.join(OUT, v + '.srt'), 'w', encoding='utf-8-sig', newline='\r\n') as o:
            o.write('\n'.join(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}\n" for i, c in enumerate(cues, 1)))
        json.dump(data, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        json.dump(WORDS, open(wp, 'w', encoding='utf-8'), ensure_ascii=False)
        print(f'{v}: {len(cues)} cues, {info.duration:.0f}s audio, {time.time() - t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
