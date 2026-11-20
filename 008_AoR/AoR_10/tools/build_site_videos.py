"""Story videos for the site (Cloudflare Pages: max 25 MiB per file).
From the review pack 008_AoR/.temp/movies_review/NNN_<Video>.mp4 + .uk.srt/.en.srt (build_movie_review.py, proofread
subtitles) -> 008_AoR/.temp/site_video/<campaign>/NNN_<Video>.mp4 (h264 + aac, +faststart for streaming, < 24 MB)
+ .uk.vtt / .en.vtt + index.json [{n, video, file, duration, uk_lines, first_uk}].
make_site.py (site_overview.py) copies them to site/video/<campaign>/.
  + <base>/ HLS (master index.m3u8, v/, a_<lang>/) - what the site plays: Pages ignores Range, so a plain mp4 cannot seek.
usage: python build_site_videos.py fotr 1-15      (indices of the review pack, story order)"""
import json, os, re, subprocess, sys
B008 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(B008, '.temp', 'movies_review')
OUT_ROOT = os.path.join(B008, '.temp', 'site_video')
LIMIT = 24 * 1000 * 1000


def srt_to_vtt(path):
    t = open(path, encoding='utf-8-sig').read().replace('\r\n', '\n')
    t = re.sub(r'(\d\d:\d\d:\d\d),(\d\d\d)', r'\1.\2', t)
    t = re.sub(r'(?m)^\d+\n(?=\d\d:\d\d:\d\d\.)', '', t)  # cue numbers are optional in WebVTT
    return 'WEBVTT\n\n' + t.strip() + '\n'


def duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', path],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def encode(src, dst):
    for crf in (23, 25, 27, 29, 31):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf),
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', dst], check=True)
        if os.path.getsize(dst) < LIMIT:
            return crf
    raise SystemExit(f'{dst}: still over {LIMIT} bytes')


# Audio renditions of the HLS master playlist. The game's own voice-over is always there; a Ukrainian dub is added when
# 008_AoR/.temp/ua_voice/<NNN_Video>.(flac|wav|mp3) exists (re-encoded to aac 128k stereo, padded/trimmed to the video)
# and is then the default track. Dubs from the user: «AoR GO» folder (2026-11-20, FotR №4, №7, №11, №14).
UA_VOICE = os.path.join(B008, '.temp', 'ua_voice')
ORIGINAL = ('en', 'Оригінал (англійською)')
DUB = ('uk', 'Українська')


def ua_voice(base):
    for ext in ('flac', 'wav', 'mp3', 'm4a'):
        f = os.path.join(UA_VOICE, f'{base}.{ext}')
        if os.path.exists(f):
            return f
    return None


def hls(mp4, folder, dub=None):
    """mp4 (+ optional Ukrainian dub) -> HLS (Cloudflare Pages ignores HTTP Range, so seeking a plain mp4 does not work;
    HLS fetches small files): folder/index.m3u8 (master) + v/ (video) + a_<lang>/ per audio rendition, fMP4 segments.
    Video and the original audio are copied, only the dub is encoded. -> list of audio languages, default first."""
    import shutil
    shutil.rmtree(folder, ignore_errors=True); os.makedirs(folder)
    tracks = ([DUB] if dub else []) + [ORIGINAL]  # the dub (when there is one) is the default track
    vmap = 'v:0,agroup:aud,name:v ' + ' '.join(
        f'a:{i},agroup:aud,language:{lang},name:a_{lang}' + (',default:yes' if i == 0 else '') for i, (lang, _n) in enumerate(tracks))
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', os.path.abspath(mp4)]
    if dub:
        cmd += ['-i', os.path.abspath(dub), '-map', '0:v', '-map', '1:a', '-map', '0:a:0', '-c:v', 'copy',
                '-c:a:0', 'aac', '-b:a:0', '128k', '-ac:a:0', '2', '-ar:a:0', '48000', '-filter:a:0', 'apad',
                '-c:a:1', 'copy', '-t', str(duration(mp4))]
    else:
        cmd += ['-map', '0:v', '-map', '0:a:0', '-c', 'copy']
    # run INSIDE the folder with relative paths: ffmpeg writes the fMP4 init files (init_N.mp4) relative to the current
    # directory, not next to the variant playlists, when the paths are absolute (then the site served index.html instead)
    cmd += ['-f', 'hls', '-hls_time', '4', '-hls_playlist_type', 'vod', '-hls_segment_type', 'fmp4',
            '-hls_flags', 'independent_segments', '-hls_fmp4_init_filename', 'init.mp4', '-master_pl_name', 'index.m3u8',
            '-var_stream_map', vmap, '-hls_segment_filename', '%v/seg_%03d.m4s', '%v/stream.m3u8']
    subprocess.run(cmd, check=True, cwd=folder)
    for d in ['v'] + [f'a_{lang}' for lang, _n in tracks]:  # every variant playlist must find its init segment
        sub = os.path.join(folder, d)
        init = re.search(r'#EXT-X-MAP:URI="([^"]+)"', open(os.path.join(sub, 'stream.m3u8'), encoding='utf-8').read())[1]
        assert os.path.exists(os.path.join(sub, init)), f'{sub}: {init} missing'
    master = os.path.join(folder, 'index.m3u8')
    m = open(master, encoding='utf-8').read()
    for i, (_lang, name) in enumerate(tracks, 1):  # ffmpeg names the renditions audio_1, audio_2, ...
        m = m.replace(f'NAME="audio_{i}"', f'NAME="{name}"')
    open(master, 'w', encoding='utf-8', newline='\n').write(m.replace(chr(92), '/'))  # URIs must use / (ffmpeg on Windows writes \)
    return [lang for lang, _n in tracks]


def main():
    camp, rng = sys.argv[1], sys.argv[2]
    lo, hi = map(int, rng.split('-'))
    out = os.path.join(OUT_ROOT, camp)
    os.makedirs(out, exist_ok=True)
    index = []
    for name in sorted(os.listdir(SRC)):
        m = re.match(r'(\d{3})_(.+)\.mp4$', name)
        if not m or not lo <= int(m[1]) <= hi:
            continue
        base = name[:-4]
        dst = os.path.join(out, name)
        if not os.path.exists(dst):
            crf = encode(os.path.join(SRC, name), dst)
            print(name, 'crf', crf, os.path.getsize(dst) // 1000, 'KB', flush=True)
        dub = ua_voice(base)
        stamp = os.path.join(out, base, 'audio.json')  # which audio tracks this HLS folder was built with
        want = {'dub': os.path.basename(dub) if dub else None, 'dub_size': os.path.getsize(dub) if dub else 0}
        have = json.load(open(stamp, encoding='utf-8')) if os.path.exists(stamp) else None
        if not os.path.exists(os.path.join(out, base, 'index.m3u8')) or (have or {}).get('dub') != want['dub'] \
                or (have or {}).get('dub_size', 0) != want['dub_size']:
            want['audio'] = hls(dst, os.path.join(out, base), dub)
            json.dump(want, open(stamp, 'w', encoding='utf-8'))
            print(base, 'HLS audio:', want['audio'], flush=True)
        elif not os.path.exists(stamp):  # built before dubs existed: original audio only
            json.dump(dict(want, audio=['en']), open(stamp, 'w', encoding='utf-8'))
        audio = json.load(open(stamp, encoding='utf-8')).get('audio', ['en'])
        poster = os.path.join(out, base + '.jpg')  # preview frame at 30 % of the video, 320 px wide
        if not os.path.exists(poster):
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(round(duration(dst) * 0.3, 2)), '-i', dst, '-frames:v', '1',
                            '-vf', 'scale=320:-2', '-q:v', '4', poster], check=True)
        uk_lines, first = 0, ''
        for lang in ('uk', 'en'):
            srt = os.path.join(SRC, f'{base}.{lang}.srt')
            if os.path.exists(srt):
                vtt = srt_to_vtt(srt)
                open(os.path.join(out, f'{base}.{lang}.vtt'), 'w', encoding='utf-8', newline='\n').write(vtt)
                if lang == 'uk':
                    cues = re.findall(r'-->[^\n]*\n(.+?)(?:\n\n|\Z)', vtt, re.S)
                    uk_lines, first = len(cues), (cues[0].replace('\n', ' ') if cues else '')
        index.append({'n': int(m[1]), 'video': m[2], 'file': name, 'hls': base + '/index.m3u8', 'poster': base + '.jpg', 'audio': audio, 'duration': round(duration(dst), 1),
                      'uk_lines': uk_lines, 'first_uk': first, 'size': os.path.getsize(dst)})
    json.dump(index, open(os.path.join(out, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(index), 'videos ->', out)


if __name__ == '__main__':
    main()
