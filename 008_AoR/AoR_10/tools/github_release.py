"""Keep ONE GitHub release up to date instead of creating a new one each time.

Each run, for the release with tag TAG in clever-play-ua/BFME-Localizations:
  * creates it on the first run (a release still on an old tag from OLD_TAGS is moved to TAG, the old tag deleted);
  * moves the tag to the current commit of the branch (default main);
  * title «Age Of The Ring Українською v.0.13 [Від 11 листопада 2026]» (date = today, or --date YYYY-MM-DD);
  * description «Українізатор постійно оновлюється»;
  * replaces the asset: the old ukrainian-localization*.zip is deleted, the new one uploaded as
    ukrainian-localization_<version>.zip. The release page link stays the same:
    https://github.com/clever-play-ua/BFME-Localizations/releases/latest

Token: a fine-grained personal access token for this repository with "Contents: Read and write", saved in
C:/Users/UserM/Documents/GitHubAPI.txt (outside the repo; never printed).

usage: python github_release.py <zip> <version> [--date 2026-11-11] [--branch main] [--dry]
"""
import argparse, datetime, json, os, sys, time, urllib.request, urllib.error

OWNER, REPO = 'clever-play-ua', 'BFME-Localizations'
TAG = 'AoR-UK-Latest'
OLD_TAGS = ['latest-build']
BODY = 'Українізатор постійно оновлюється'
TOKEN_FILE = 'C:/Users/UserM/Documents/GitHubAPI.txt'
MONTHS = ['січня', 'лютого', 'березня', 'квітня', 'травня', 'червня', 'липня', 'серпня', 'вересня', 'жовтня', 'листопада', 'грудня']

ap = argparse.ArgumentParser()
ap.add_argument('zip'); ap.add_argument('version')
ap.add_argument('--date'); ap.add_argument('--branch', default='main'); ap.add_argument('--dry', action='store_true')
ap.add_argument('--notes', help='what changed in this version (added under the description)')
a = ap.parse_args()
if a.notes:
    BODY = f'{BODY}\n\n**v{a.version}**\n{a.notes}'
day = datetime.date.fromisoformat(a.date) if a.date else datetime.date.today()
TITLE = f'Age Of The Ring Українською v.{a.version} [Від {day.day} {MONTHS[day.month - 1]} {day.year}]'
ASSET = f'ukrainian-localization_{a.version}.zip'
TOKEN = None if a.dry else open(TOKEN_FILE, encoding='utf-8').read().split()[0]  # first token = this repository's; others below belong to other projects


def api(method, url, body=None, data=None, ctype='application/json'):
    if not url.startswith('http'):
        url = f'https://api.github.com/repos/{OWNER}/{REPO}' + url
    payload = data if data is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(url, data=payload, method=method, headers={
        'Authorization': f'Bearer {TOKEN}', 'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'aor-ua-release', 'Content-Type': ctype})
    for attempt in range(4):  # occasional TLS/network hiccups on this machine: retry
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                raw = r.read()
                return r.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8', 'replace')[:400]
        except urllib.error.URLError as e:
            if attempt == 3:
                raise
            print('network error, retrying:', e.reason)
            time.sleep(3 * (attempt + 1))


print(f'release {TAG}: "{TITLE}", asset {ASSET} <- {os.path.basename(a.zip)} ({os.path.getsize(a.zip)} bytes)')
if a.dry:
    sys.exit('dry run: nothing sent')

st, ref = api('GET', f'/git/ref/heads/{a.branch}')
if st != 200:
    sys.exit(f'branch {a.branch}: {st} {ref}')
sha = ref['object']['sha']
st, r = api('PATCH', f'/git/refs/tags/{TAG}', {'sha': sha, 'force': True})  # the tag follows the latest commit
if st in (404, 422):
    st, r = api('POST', '/git/refs', {'ref': f'refs/tags/{TAG}', 'sha': sha})
print('tag', TAG, '->', sha[:7], st)

fields = {'tag_name': TAG, 'name': TITLE, 'body': BODY, 'draft': False, 'prerelease': False, 'make_latest': 'true'}
st, rel = api('GET', f'/releases/tags/{TAG}')
old = None
if st != 200:
    for t in OLD_TAGS:  # migrate the release from an earlier tag name
        st, rel = api('GET', f'/releases/tags/{t}')
        if st == 200:
            old = t
            break
if st == 200:
    st, rel = api('PATCH', f'/releases/{rel["id"]}', fields)
else:
    st, rel = api('POST', '/releases', fields)
if st not in (200, 201):
    sys.exit(f'release: {st} {rel}')
print('release', rel['id'], rel['html_url'])
for t in OLD_TAGS:
    st, _ = api('DELETE', f'/git/refs/tags/{t}')
    if st == 204:
        print('deleted old tag', t)

for asset in rel.get('assets', []):
    if asset['name'].startswith('ukrainian-localization'):
        print('delete old asset', asset['name'], api('DELETE', f'/releases/assets/{asset["id"]}')[0])
up = rel['upload_url'].split('{')[0] + f'?name={ASSET}'
st, asset = api('POST', up, data=open(a.zip, 'rb').read(), ctype='application/zip')
if st != 201:
    sys.exit(f'upload: {st} {asset}')
print('uploaded', asset['browser_download_url'])
