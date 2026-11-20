"""Export every AoR story video with its subtitles into 009_CINEMATICS/ (repo root).

    009_CINEMATICS/
      README.md
      video/NNN_<Video>.mp4                       review pack (vp6 picture + DialogEvent voice, h264/aac), story order
      subtitles/srt/{uk,en,es}/NNN_<Video>.srt    uk = proofread (the mod), en = final English, es = Spanish submod
      subtitles/cinematics_subtitles.json         every video: campaign, fps, duration, cues per language (sec + frames)
      subtitles/game/{uk,en,es}/data/english/movies/<Video>.ini   engine subtitle INIs (one row, Albertus MT 24)
      subtitles/game/{uk,en,es}/subtitles_<lang>.str               the SUBTITLE:<LL><Video>_NN strings (lotr.str format)
      subtitles/game/video.ini                    AoR 10.0.2 video.ini + HasSubtitles = Yes (whole-file override)

Sources: 008_AoR/.temp/movies_review (mp4 + .uk/.en.srt), AoR_10/movie_subtitles/edited.json (uk/en with frames),
008_AoR/.temp/subtitles_es/es_reference.json (Spanish, frames at each video's fps), AoR_10/movie_subtitles/fps.json.
The uk game files are the same as build_uk_submod.py ships (labels SUBTITLE:UA..., same frames).
usage: python export_cinematics.py [--no-video]"""
import json, os, re, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
AOR10 = os.path.dirname(HERE)
B008 = os.path.dirname(AOR10)
OUT = os.path.join(os.path.dirname(B008), '009_CINEMATICS')
REVIEW = os.path.join(B008, '.temp', 'movies_review')
ES = os.path.join(B008, '.temp', 'subtitles_es')
sys.path.insert(0, os.path.join(AOR10, 'movie_subtitles'))
import final_en  # noqa: E402  (ORDER = story order of the 47 videos)

CAMPAIGNS = [('intro', 'Вступ гри', 0, 0), ('fotr', '«Братство Персня»', 1, 15), ('ttt', '«Дві вежі»', 16, 26),
             ('rotk', '«Повернення Короля»', 27, 46)]
FONT, PITCH = 'Albertus MT', 24
LANG_NAME = {'uk': 'Ukrainian', 'en': 'English', 'es': 'Spanish'}


def campaign_of(n):
    for key, name, lo, hi in CAMPAIGNS:
        if lo <= n <= hi:
            return key, name, n - lo + 1
    raise ValueError(n)


def duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', path],
                       capture_output=True, text=True)
    return round(float(r.stdout.strip() or 0), 3)


GITHUB_LIMIT = 25 * 1000 * 1000  # GitHub web upload limit: bigger videos are re-encoded ...
TARGET = 19_500_000              # ... to about 19.5 MB (two-pass x264, size-targeted), audio aac 128k


def shrink(src, dst):
    """Two-pass x264 aimed at TARGET bytes (container overhead ~2 %); retries 8 % smaller if it still overshoots 19.99 MB."""
    import tempfile
    dur = duration(src)
    goal = TARGET
    total = int(goal * 8 / dur / 1000 * 0.98)
    small = total < 600  # very long videos (ROTK_14b: 9 min): 768x480 picture and 80k audio, or the bitrate gets too thin
    ak = 80 if small else 128
    scale = ['-vf', 'scale=768:480'] if small else []
    for _ in range(4):
        vk = max(120, int(goal * 8 / dur / 1000 * 0.98) - ak)
        with tempfile.TemporaryDirectory() as tmp:
            log = os.path.join(tmp, 'x264')
            base = ['ffmpeg', '-v', 'error', '-y', '-i', src] + scale + ['-c:v', 'libx264', '-preset', 'slow', '-b:v', f'{vk}k',
                    '-pix_fmt', 'yuv420p', '-passlogfile', log]
            subprocess.run(base + ['-pass', '1', '-an', '-f', 'mp4', os.devnull], check=True)
            subprocess.run(base + ['-pass', '2', '-c:a', 'aac', '-b:a', f'{ak}k', '-movflags', '+faststart', dst], check=True)
        if os.path.getsize(dst) < 19_990_000:
            return vk
        goal = int(goal * 0.92)
    raise SystemExit(f'{dst}: still {os.path.getsize(dst)} bytes')


def ts(sec):
    ms = int(round(sec * 1000))
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'


def write_srt(path, cues):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8-sig', newline='\r\n') as o:
        o.write('\n'.join(f'{i}\n{ts(c["start"])} --> {ts(c["end"])}\n{c["text"]}\n' for i, c in enumerate(cues, 1)))


def main():
    no_video = '--no-video' in sys.argv
    fps = json.load(open(os.path.join(AOR10, 'movie_subtitles', 'fps.json'), encoding='utf-8'))
    edited = json.load(open(os.path.join(AOR10, 'movie_subtitles', 'edited.json'), encoding='utf-8'))
    es_ref = json.load(open(os.path.join(ES, 'es_reference.json'), encoding='utf-8'))['movies']
    videos, game = [], {'uk': {}, 'en': {}, 'es': {}}
    for n, v in enumerate(final_en.ORDER):
        base = f'{n:03}_{v}'
        key, cname, k = campaign_of(n)
        mp4 = os.path.join(REVIEW, base + '.mp4')
        if not no_video:
            os.makedirs(os.path.join(OUT, 'video'), exist_ok=True)
            os.makedirs(os.path.join(OUT, 'audio'), exist_ok=True)
            dst = os.path.join(OUT, 'video', base + '.mp4')
            if os.path.getsize(mp4) > GITHUB_LIMIT:
                if not os.path.exists(dst) or os.path.getsize(dst) >= 19_990_000 or os.path.getsize(dst) == os.path.getsize(mp4):
                    kb = shrink(mp4, dst)
                    print(f'{base}: {os.path.getsize(mp4) / 1e6:.1f} MB -> {os.path.getsize(dst) / 1e6:.2f} MB ({kb} kbit/s video)', flush=True)
            elif not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(mp4):
                shutil.copyfile(mp4, dst)
            mp3 = os.path.join(REVIEW, base + '.mp3')  # the voice-over alone (DialogEvent mp3 of the game)
            if os.path.exists(mp3):
                shutil.copyfile(mp3, os.path.join(OUT, 'audio', base + '.mp3'))
        subs = {}
        for lang in ('uk', 'en'):
            subs[lang] = [{'start': c['start'], 'end': c['end'], 'start_frame': c['start_frame'], 'end_frame': c['end_frame'],
                           'text': c['text']} for c in (edited.get(v, {}).get(lang) or [])]
        es = es_ref.get(v)
        subs['es'] = [{'start': c['start_sec'], 'end': c['end_sec'], 'start_frame': c['start'], 'end_frame': c['end'],
                       'text': c['es']} for c in (es['subtitles'] if es else [])]
        for lang, cues in subs.items():
            if cues:
                write_srt(os.path.join(OUT, 'subtitles', 'srt', lang, base + '.srt'), cues)
                game[lang][v] = cues
        title = 'Вступний ролик гри' if key == 'intro' else f'{cname} · Ролик №{k}'
        videos.append({'n': n, 'video': v, 'file': f'video/{base}.mp4', 'campaign': key, 'campaign_ua': cname, 'number': k,
                       'title_ua': title, 'fps': fps.get(v), 'duration': duration(mp4), 'subtitles': subs})
    json.dump({'meta': {'what': 'Age of the Ring 10 story videos (cinematics) with subtitles, story order',
                        'languages': {'uk': 'Ukrainian, proofread (the Ukrainian mod since 0.19)',
                                      'en': 'English (Spanish timings + Whisper transcript, checked)',
                                      'es': 'Spanish, from the traduccion-es 1.2.2 submod'},
                        'times': 'start/end in seconds; start_frame/end_frame at the video\'s own fps (engine INI frames)',
                        'no_speech': [x['video'] for x in videos if not x['subtitles']['uk']]},
               'videos': videos},
              open(os.path.join(OUT, 'subtitles', 'cinematics_subtitles.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # engine format, same layout as the mod: one INI per video + the SUBTITLE strings (one row, like the mod)
    NL = '\r\n'
    for lang, movies in game.items():
        LL = {'uk': 'UA'}.get(lang, lang.upper())  # UA = the labels the mod ships
        root = os.path.join(OUT, 'subtitles', 'game', lang)
        os.makedirs(os.path.join(root, 'data', 'english', 'movies'), exist_ok=True)
        strs = [f'// {LANG_NAME[lang]} movie subtitles for Age of the Ring 10 - labels used by data/english/movies/*.ini']
        for v, cues in movies.items():
            vid = v.replace('_', '')
            lines = [f'    SubTitle = Label:{LL}{vid}_{i:02} Color R:255 G:255 B:255 Style:SOLID Align:CENTER '
                     f'Line:15 StartFrame:{c["start_frame"]} EndFrame:{c["end_frame"]}' for i, c in enumerate(cues, 1)]
            with open(os.path.join(root, 'data', 'english', 'movies', f'{v}.ini'), 'w', encoding='ascii', newline='') as o:
                o.write(f"; {LANG_NAME[lang]} movie subtitles - Video {v}. Label:X = SUBTITLE:X in lotr.csf; frames at the video's own fps{NL}"
                        f'SubTitles {v}{NL}    FontName = "{FONT}"{NL}    FontPitch = {PITCH}{NL}    SubTitleType = CINEMA{NL}'
                        + NL.join(lines) + f'{NL}End{NL}')
            for i, c in enumerate(cues, 1):
                text = ' '.join(c['text'].split()).replace('"', "''")
                strs += ['', f'SUBTITLE:{LL}{vid}_{i:02}', f'"{text}"', 'END']
        with open(os.path.join(root, f'subtitles_{lang}.str'), 'w', encoding='utf-8', newline='\r\n') as o:
            o.write('\n'.join(strs) + '\n')
    shutil.copyfile(os.path.join(B008, 'AoR_10_UK', 'data', 'ini', 'video.ini'), os.path.join(OUT, 'subtitles', 'game', 'video.ini'))
    print(len(videos), 'videos;', {l: len(m) for l, m in game.items()}, 'subtitled ->', OUT)


if __name__ == '__main__':
    main()
