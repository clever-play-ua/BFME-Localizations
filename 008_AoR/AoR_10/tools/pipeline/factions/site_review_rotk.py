# exec'd from make_site.py: site/review/rotk/ - minimal proofreading page for the RotK campaign (EN | UA editable | ✓),
# missions in order (AoR_UK_WIP/RoTK/NNN_*.json), saved in localStorage, «Export JSON» -> {var: {uk, reviewed}}.
import glob as _g, json as _j, html as _hh
_rows = []
for _fp in sorted(_g.glob('C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_UK_WIP/RoTK/*_AoR_RoTK_UA.json')):
    _d = _j.load(open(_fp, encoding='utf-8'))
    for _s in _d.get('strings', []):
        if (_s.get('en') or '').strip():
            _rows.append({'v': _s['var'], 'm': _s.get('mission', ''), 'en': _s['en'], 'uk': _s.get('uk') or _s.get('uk_ai') or ''})
_os.makedirs(_os.path.join(SITE, 'review', 'rotk'), exist_ok=True) if '_os' in globals() else os.makedirs(os.path.join(SITE, 'review', 'rotk'), exist_ok=True)
open(os.path.join(SITE, 'review', 'rotk', 'index.html'), 'w', encoding='utf-8').write('''<!DOCTYPE html><html lang="uk"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><title>Вичитка RotK</title>
<style>body{margin:0;background:#0b131b;color:#dfe6ec;font:14px/1.45 system-ui,sans-serif}.top{position:sticky;top:0;background:#122030;padding:8px 14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;border-bottom:1px solid #2f4a63;z-index:2}
h2{margin:22px 14px 6px;color:#8fb8d8;font-size:17px}.r{display:grid;grid-template-columns:minmax(0,560px) minmax(0,560px) 34px;justify-content:center;gap:16px;padding:6px 14px;border-bottom:1px solid #1d3246}h2{max-width:1190px;margin-left:auto!important;margin-right:auto!important}.cp{float:right;margin-left:8px;padding:2px 8px;font-size:12px}.r.ok{background:#12301f}
.en{white-space:pre-wrap;color:#b9c6d2}.v{font:11px monospace;color:#64768a}textarea{width:100%;box-sizing:border-box;background:#0f1a24;color:#fff;border:1px solid #2f4a63;border-radius:4px;font:inherit;padding:5px;resize:vertical}
input[type=checkbox]{width:22px;height:22px}button,select{background:#1d3246;color:#fff;border:1px solid #2f4a63;border-radius:4px;padding:6px 10px;cursor:pointer}@media(max-width:700px){.r{grid-template-columns:1fr 34px}.en{grid-column:1/-1}}</style></head><body>
<div class="top"><b>Вичитка «Повернення Короля»</b><span id="st"></span><select id="go"></select><button id="ex">Export JSON</button><label><input type="checkbox" id="hide"> сховати вичитані</label></div><div id="list"></div>
<script>const R=''' + _j.dumps(_rows, ensure_ascii=False) + r''';
const K='rotk-review-v1';let S={};try{S=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){}
const save=()=>{try{localStorage.setItem(K,JSON.stringify(S))}catch(e){}st()};
const st=()=>{const n=Object.values(S).filter(x=>x.r).length;document.getElementById('st').textContent=n+' / '+R.length+' вичитано'};
const L=document.getElementById('list'),G=document.getElementById('go');let m=null,mi=0;
R.forEach((x,i)=>{if(x.m!==m){m=x.m;mi++;const h=document.createElement('h2');h.id='m'+mi;h.textContent=m;L.appendChild(h);const o=document.createElement('option');o.value='m'+mi;o.textContent=m;G.appendChild(o)}
const s=S[x.v]||{},d=document.createElement('div');d.className='r'+(s.r?' ok':'');
d.innerHTML='<div><button class="cp" title="Копіювати EN">⧉</button><div class="en"></div></div><div><textarea rows="2"></textarea><div class="v"></div></div><input type="checkbox">';
d.querySelector('.en').textContent=x.en.replace(/\\n/g,'\n');d.querySelector('.v').textContent=x.v;
d.querySelector('.cp').onclick=e=>{navigator.clipboard.writeText(x.en.replace(/\\n/g,'\n'));e.target.textContent='✓';setTimeout(()=>e.target.textContent='⧉',900)};const t=d.querySelector('textarea'),c=d.querySelector('input');t.value=(s.uk!=null?s.uk:x.uk).replace(/\\n/g,'\n');c.checked=!!s.r;
t.oninput=()=>{S[x.v]=Object.assign(S[x.v]||{},{uk:t.value});save()};
c.onchange=()=>{S[x.v]=Object.assign(S[x.v]||{uk:t.value},{r:c.checked});d.classList.toggle('ok',c.checked);save()};L.appendChild(d)});
G.onchange=()=>document.getElementById(G.value).scrollIntoView();
document.getElementById('hide').onchange=e=>document.body.classList.toggle('h',e.target.checked);
document.head.insertAdjacentHTML('beforeend','<style>body.h .r.ok{display:none}</style>');
document.getElementById('ex').onclick=()=>{const out=R.filter(x=>S[x.v]).map(x=>({var:x.v,mission:x.m,en:x.en,uk:(S[x.v].uk!=null?S[x.v].uk:x.uk).replace(/\n/g,'\\n'),reviewed:!!S[x.v].r}));
const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify({exported:new Date().toISOString(),edits:out},null,1)],{type:'application/json'}));a.download='RotK_review_'+Date.now()+'.json';a.click()};st();
</script></body></html>''')
print('review rotk:', len(_rows), 'rows')
