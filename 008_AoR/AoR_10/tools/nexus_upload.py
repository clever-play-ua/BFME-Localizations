"""Upload a new version of an existing Nexus Mods file through the v3 Upload API (same flow as Nexus-Mods/upload-action):
multipart upload -> PUT parts -> complete -> finalise -> poll -> POST /mod-files/{id}/versions -> optional changelog.
The API key is read from C:/Users/UserM/Documents/NexusAPI.txt and never printed.
usage: python nexus_upload.py <zip> <file_id> <version> <display_name> [--mod-id N --changelog FILE] [--archive] [--dry]"""
import argparse, json, math, os, re, sys, time, urllib.request, urllib.error

API = 'https://api.nexusmods.com/v3'
UA = 'AoR-UA-localization-uploader'
ap = argparse.ArgumentParser()
ap.add_argument('zip'); ap.add_argument('file_id'); ap.add_argument('version'); ap.add_argument('name')
ap.add_argument('--mod-id'); ap.add_argument('--changelog'); ap.add_argument('--description')
ap.add_argument('--archive', action='store_true'); ap.add_argument('--dry', action='store_true')
a = ap.parse_args()
KEY = re.findall(r'[A-Za-z0-9+/=_\-\.]{40,}', open('C:/Users/UserM/Documents/NexusAPI.txt', encoding='utf-8').read())[0]


def api(method, path, body=None):
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={'apikey': KEY, 'User-Agent': UA, 'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode('utf-8') or '{}')
    except urllib.error.HTTPError as e:
        sys.exit(f'{method} {path} -> {e.code}: {e.read().decode("utf-8", "replace")[:500]}')


def raw(method, url, data, ctype):
    req = urllib.request.Request(url, data=data, method=method, headers={'Content-Type': ctype, 'Content-Length': str(len(data))})
    with urllib.request.urlopen(req, timeout=600) as r:
        return r.headers.get('ETag'), r.read()


GAME = 'lordoftheringsbattleformiddleearth2'
# the site/v1 numbers (file 625, mod 578) are game-scoped; the v3 write endpoints need the global ids
a.file_id = api('GET', f'/games/{GAME}/mod-file-versions/{a.file_id}')['data']['file']['id']
if a.mod_id:
    a.mod_id = api('GET', f'/games/{GAME}/mods/{a.mod_id}')['data']['id']
size = os.path.getsize(a.zip)
print(f'{os.path.basename(a.zip)}: {size} bytes -> file {a.file_id}, version {a.version}, name "{a.name}", archive old: {a.archive}')
if a.dry:
    sys.exit('dry run: nothing sent')
up = api('POST', '/uploads/multipart', {'filename': os.path.basename(a.zip), 'size_bytes': str(size)})['data']
uid, urls, psize = up['id'], up['part_presigned_urls'], up['part_size_bytes']
print('upload', uid, len(urls), 'parts')
parts = []
with open(a.zip, 'rb') as f:
    for i, u in enumerate(urls, 1):
        f.seek((i - 1) * psize); chunk = f.read(psize)
        etag, _ = raw('PUT', u, chunk, 'application/octet-stream')
        parts.append((i, etag.replace('"', '')))
xml = '<CompleteMultipartUpload>\n' + '\n'.join(f'  <Part>\n    <PartNumber>{n}</PartNumber>\n    <ETag>{e}</ETag>\n  </Part>' for n, e in parts) + '\n</CompleteMultipartUpload>'
raw('POST', up['complete_presigned_url'], xml.encode('utf-8'), 'application/xml')
print('finalise:', api('POST', f'/uploads/{uid}/finalise')['data'].get('state'))
for k in range(60):
    st = api('GET', f'/uploads/{uid}')['data']['state']
    print('state:', st)
    if st == 'available':
        break
    time.sleep(min(2 * 1.5 ** k, 30))
else:
    sys.exit('upload processing timed out')
body = {'upload_id': uid, 'name': a.name, 'version': a.version, 'file_category': 'main', 'archive_existing_file': a.archive,
        'update_mod_version': True}
if a.description:
    body['description'] = a.description
ver = api('POST', f'/mod-files/{a.file_id}/versions', body)['data']
print('created version:', json.dumps(ver, ensure_ascii=False)[:400])
if a.changelog and a.mod_id:
    text = open(a.changelog, encoding='utf-8').read().strip()
    print('changelog:', api('POST', f'/mods/{a.mod_id}/changelogs', {'version': a.version, 'changelog': text}))
