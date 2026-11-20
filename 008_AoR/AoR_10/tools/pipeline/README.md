# Пайплайн перекладу AoR 10 (фракції, герої, правила, сайт)

Робочі скрипти, перенесені зі scratchpad (2026-11-19). Шляхи до репо та гри (`F:/BFME-AgeoftheRing`) абсолютні,
структура тек `factions/ terms9/ heroes/` має лишатися як є (скрипти посилаються на `HERE/..`).
Згенеровані файли (site/, ini_idx.pkl, todo.json, логи, bak) — у `.gitignore`.

## 1. Фракція: чернетка → сторінка для громади
```
cd factions
python make_faction.py Wild        # дерево фракції з INI гри -> AoR_UK_WIP/Factions/Wild_AoR_UA.json
python todo_dump.py Wild           # неперекладені рядки -> todo.json / todo.txt (+ що знає пам'ять перекладів tm.py)
#   переклад чернеток пишемо в tr_wild.py (словник T = {var: ua})
python apply_drafts.py Wild        # перевірка tr_wild.py -> Factions/Wild_AI_drafts.json
python make_faction.py Wild        # перезбірка з урахуванням чернеток
python make_web.py Wild            # -> Factions/Wild_AoR_UA.html (сторінка для вичитки)
python make_site.py                # factions/site/: усі фракції + герої кампанії + дерево технологій
npx wrangler@4 pages deploy site --project-name aor-uk-localization --branch main --commit-dirty=true
```
Ключі фракцій: Isengard, Men (Gondor), Rohan, Mordor, Guldur, Dwarves (Erebor), Wild (Misty Mountains), Heroes.
Пріоритет джерел у make_faction: `*_reviewed.json` (вичитка FoLD) > `*_serhii.json` > гра (CSF) > `*_AI_drafts.json`.

## 2. Імпорт вичитки FoLD (експорт зі сторінки сайту)
`review_fold8.py` / `review_fold8_dump.py` — зразок останнього імпорту: скопіювати як `review_fold9.py`,
змінити `SRC` (json експорту) і рішення-відповіді, запустити `*_dump.py` → таблиця різниць на затвердження,
потім `review_fold9.py` → `Factions/<F>_reviewed.json`. `review_dump.py <file.json>` — до/після по словах.

## 3. Правила термінології (глобальні заміни по всіх джерелах)
```
python terms9/round28.py --dry     # показати зміни (лог terms9/round28_log.txt), без --dry — застосувати (бекап у terms9/bak/)
```
`apply9.py` містить «ходок» по всіх джерелах: героїв/Skirmish/RoTK JSON, Serhii/Menu_tooltips/RingPowers/Fellowship/FotR/TTT,
menu_strings, Factions (*_serhii, *_AI_drafts, *_reviewed) і колонки UK / UK AI у RotK_campaign_strings.xlsx.
Новий раунд = новий `roundNN.py` за зразком round28 (функція `fix(var, en, ua)`).
Перевірка стабільності — усі раунди з `--dry` мають дати `changed 0`:
```
for f in terms9/apply9.py terms9/apply10.py terms9/round*.py heroes/rules.py; do python $f --dry | grep changed; done
```
`heroes/rules.py` — правила для описів здібностей героїв (точні заміни + regex).

## 4. Допоміжні
- `peek.py var|en <regex>` — EN | UA для міток; `same_en.py` — UA для того самого EN в інших мітках;
  `terms_check.py`, `wordcount.py <regex>` — як термін перекладено по проєкту.
- `hero_lint.py` — неперекладене / порушення стандартів на сторінках героїв → `hero_lint.txt`.
- `make_hero.py`, `site_heroes.py`, `site_tree.py` — сторінки героїв кампанії та дерево (викликаються з make_site).
- `site_overview.py` (викликається з make_site) — головна `/` (версія й дата з першого заголовка `## версія · дата`
  у 008_AoR/CHANGELOG.md, кнопки Nexus / GitHub, загальний статус, останні 3 версії) і `/changelog/` (усі версії).
  Список фракцій тепер на `/factions/`. Статус рахує `site_status.py` (той самий пріоритет джерел, що й build_uk_submod:
  вичитано / переклад / чернетка ШІ / англійською; кампанії — за аркушами xlsx, «Війна Кольця» — мітки LW*/WOTR*/STRATEGICHUD).
  Після кожного релізу: додати розділ у CHANGELOG.md, `python make_site.py`, задеплоїти.
- `iniparse.py` (кеш `ini_idx.pkl`), `icons.py` (іконки з атласів гри), `biglist.py` (вміст .big).

## 5. Реліз (скрипти рівнем вище, у `tools/`)
`build_uk_submod.py` (VERSION) → `nexus_upload.py` → `github_release.py`; субтитри відео — `transcribe_movies.py`,
`build_movie_review.py`, `import_movie_srt.py`, `fix_movie_srt.py` (методологія: `AoR_10/movie_subtitles.json`).
