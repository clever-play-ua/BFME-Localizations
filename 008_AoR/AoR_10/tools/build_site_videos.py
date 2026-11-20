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


# Audio renditions of the HLS master playlist: (stream index in the mp4, language, name shown in the player).
# A second voice-over later = add its track to the mp4 (or a separate input) and a line here.
AUDIO = [(0, 'en', 'Оригінал (англійською)')]


def hls(mp4, folder):
    """mp4 -> HLS (Cloudflare Pages ignores HTTP Range, so seeking a plain mp4 does not work; HLS fetches small files):
    folder/index.m3u8 (master) + v/ (video) + a_<lang>/ (one dir per audio rendition), fMP4 segments, no re-encode."""
    import shutil
    shutil.rmtree(folder, ignore_errors=True); os.makedirs(folder)
    vmap = 'v:0,agroup:aud,name:v ' + ' '.join(
        f'a:{i},agroup:aud,language:{lang},name:a_{lang}' + (',default:yes' if i == 0 else '') for i, (_, lang, _n) in enumerate(AUDIO))
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', os.path.abspath(mp4), '-map', '0:v']
    for idx, _lang, _n in AUDIO:
        cmd += ['-map', f'0:a:{idx}']
    # run INSIDE the folder with relative paths: ffmpeg writes the fMP4 init files (init_N.mp4) relative to the current
    # directory, not next to the variant playlists, when the paths are absolute (then the site served index.html instead)
    cmd += ['-c', 'copy', '-f', 'hls', '-hls_time', '4', '-hls_playlist_type', 'vod', '-hls_segment_type', 'fmp4',
            '-hls_flags', 'independent_segments', '-hls_fmp4_init_filename', 'init.mp4', '-master_pl_name', 'index.m3u8',
            '-var_stream_map', vmap, '-hls_segment_filename', '%v/seg_%03d.m4s', '%v/stream.m3u8']
    subprocess.run(cmd, check=True, cwd=folder)
    for d in ['v'] + [f'a_{lang}' for _i, lang, _n in AUDIO]:  # every variant playlist must find its init segment
        sub = os.path.join(folder, d)
        init = re.search(r'#EXT-X-MAP:URI="([^"]+)"', open(os.path.join(sub, 'stream.m3u8'), encoding='utf-8').read())[1]
        assert os.path.exists(os.path.join(sub, init)), f'{sub}: {init} missing'
    master = os.path.join(folder, 'index.m3u8')
    t = open(master, encoding='utf-8').read()
    for i, (_idx, _lang, name) in enumerate(AUDIO, 1):  # ffmpeg names the renditions audio_1, audio_2, ...
        t = t.replace(f'NAME="audio_{i}"', f'NAME="{name}"')
    open(master, 'w', encoding='utf-8', newline='\n').write(t.replace(chr(92), '/'))  # URIs must use / (ffmpeg on Windows writes \)


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
        if not os.path.exists(os.path.join(out, base, 'index.m3u8')):
            hls(dst, os.path.join(out, base))
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
        index.append({'n': int(m[1]), 'video': m[2], 'file': name, 'hls': base + '/index.m3u8', 'poster': base + '.jpg', 'duration': round(duration(dst), 1),
                      'uk_lines': uk_lines, 'first_uk': first, 'size': os.path.getsize(dst)})
    json.dump(index, open(os.path.join(out, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(index), 'videos ->', out)


if __name__ == '__main__':
    main()
