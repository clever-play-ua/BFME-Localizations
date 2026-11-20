"""AI drafts for campaign-hero lines that had no Ukrainian at all -> AoR_UK_WIP/Factions/Heroes_AI_drafts.json
(lowest priority; in the build). Merges with what is already there. usage: python tr_heroes.py"""
import json, os, re
P = r'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_UK_WIP/Factions/Heroes_AI_drafts.json'
STR = {s['var'].lower(): s for s in json.load(open(r'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_10/strings.json', encoding='utf-8'))['strings']}

TR = {  # Frodo (2026-11-10)
    'CONTROLBAR:ExperiencedWalker': 'Досвідчений мандрівник (&W)',
    'CONTROLBAR:TooltipExperiencedWalker': 'Тип ефекту: Посилення\nФродо отримує бонус +50% до швидкості на 40 сек.\nКлікніть, щоб активувати',
    'CONTROLBAR:FrodoShoo': 'Прогнати голодних роззяв (&R)',
    'CONTROLBAR:ToolTipFrodoShoo': 'Фродо проганяє голодних роззяв\nКлікніть, щоб активувати',
    'CONTROLBAR:EvadeLobelia': 'Сховатися від Лобелії (&T)',
    'CONTROLBAR:ToolTipEvadeLobelia': 'Стає невидимим, коли стоїть на місці\nТакож постійно дає +10% броні всім героям-гобітам поблизу\nКлікніть, щоб активувати',
    'CONTROLBAR:HobbitRockLureAlep': 'Приманка (&C)',
    'CONTROLBAR:ToolTipHobbitRockLureAlep': 'Фродо кидає яблуко, щоб приманити цапа Філіпа у вказане місце\nКлікніть на іконку, потім оберіть ділянку',
    'CONTROLBAR:HobbitCloak': 'Ховайтеся тут, швидко! (&C)',
    'CONTROLBAR:ToolTipPhialofGaladrielMarshes': 'На 5 сек. оглушує невмерлі загони й завдає їм поступових пошкоджень\nКлікніть, щоб активувати',
    'CONTROLBAR:PhialofGaladrielFrodoToCU': 'Фіал Ґаладріель (&W)',
    'CONTROLBAR:ScouringFrodoLeadership': "Фродо Дев'ятипалий",
    'CONTROLBAR:ToolTipScouringFrodoLeadership': 'Потрібно: Рівень 5\nТип ефекту: Лідерство\nСоюзники поблизу отримують бонус +33% до пошкоджень, +33% броні\nй удвічі швидше набирають досвід\n\nПоєднується з посиленнями й заклинаннями\nПасивна здібність',
    'CONTROLBAR:FrodoRedBook': 'Червона книга Західної Межі (&V)',
    'CONTROLBAR:ToolTipFrodoRedBook': 'Фродо розповідає історію про падіння Володаря Перснів і Повернення Короля\nДає досвід обраним союзним загонам\nКлікніть на іконку, потім оберіть потрібні загони',
    # Aragorn (2026-11-10)
    'CONTROLBAR:AragornLeaderofMen': 'Лідер вільних людей (&T)',
    'CONTROLBAR:TooltipFellowshipStriderBlademaster': 'Потрібно: Рівень 5\nБродяжник отримує бонус +100% до пошкоджень, +100% броні, відкидає ворогів своїми ударами й бере смолоскип на 30 сек.\nДоступно лише з мечем\nКлікніть, щоб активувати',
    'CONTROLBAR:ToolTipFellowshipStriderLeaderofMen': 'Потрібно: Рівень 8\nТип ефекту: Заклинання\nСоюзні загони поблизу отримують бонус +33% броні\nПасивна здібність\n\nПісля активації загони поряд із Бродяжником на 20 сек. отримують бонус +50% до пошкоджень і імунітет до страху та жаху\nКлікніть, щоб активувати',
    'CONTROLBAR:ElessarEnvinyatar': 'Енвіньятар (&R)',
    'CONTROLBAR:ToolTipElessarEnvinyatar': 'Зцілює Араґорна й союзних героїв на всій мапі\nКлікніть, щоб активувати',
    'CONTROLBAR:CampaignElessarBladeMaster': "Андуріл, Полум'я Заходу (&W)",
    'CONTROLBAR:SpecialAbilityFellowshipElessarEstel': 'Естель (&T)',
    'CONTROLBAR:ToolTipSpecialAbilityFellowshipElessarEstel': 'Араґорн відкидає Тінь і не відступає від своєї мети\nКлікніть, щоб активувати',
    'CONTROLBAR:SpecialAbilityCommanderSword': 'Меч Еленділа (&T)',
    'CONTROLBAR:ToolTipCommanderSword': 'Тип ефекту: Активне ослаблення\nОбрані ворожі загони на 30 сек. отримують штраф -33% пошкоджень і броні\nСкасовує вороже лідерство\nКлікніть на іконку, потім оберіть потрібні загони',
    'CONTROLBAR:SpecialAbilityCommanderWords': 'Слова надії (&C)',
    'CONTROLBAR:ToolTipCommanderWords': 'Союзні загони в радіусі дії на 30 сек. отримують бонус +50% до пошкоджень і броні\nКлікніть на іконку, потім оберіть потрібний загін',
    'CONTROLBAR:ThreeHuntersLeadership': 'Троє мисливців',
    'CONTROLBAR:ToolTipHuntersLeadershipAragorn': 'Тип ефекту: Лідерство\nПоряд із Леґоласом чи Ґімлі Араґорн отримує бонус +25% броні й швидкості\nПасивна здібність',
    'CONTROLBAR:ToolTipAragornLeaderofMen': 'Тип ефекту: Заклинання\nСоюзні загони поблизу отримують бонус +33% броні\n\nПісля активації загони поряд з Араґорном на 20 сек. отримують бонус +50% до пошкоджень і імунітет до страху та жаху\nКлікніть, щоб активувати',
}

TR.update({  # campaign heroes batch 2 (2026-11-11): gaps on the hobbit / wizard / Fellowship / Faramir & Boromir pages
    'CONTROLBAR:ToolTipTheOneRing_Riddle': 'Робить невидимим\nКлікніть, щоб активувати',
    'CONTROLBAR:ToolTipRivendellGandalfGloriousCharge': 'Лучники поблизу на 30 сек. отримують бонус +20% дальності атаки й +15% до пошкоджень\nКлікніть, щоб активувати',
    'CONTROLBAR:ToolTipRivendellGandalfYouShallNotPass': 'На 10 сек. приголомшує ворожі загони в широкому радіусі навколо Ґендальфа\nКлікніть, щоб активувати',
    'CONTROLBAR:HarkenToMeLeadership': 'Слухайте мене!',
    'CONTROLBAR:ToolTipHarkenToMeLeadership': 'Тип ефекту: Лідерство\nЧас відновлення здібностей героїв поблизу скорочується на 25%\n~ ПАСИВНА ЗДІБНІСТЬ ~',
    'CONTROLBAR:GandalfFirstLight': "Перше світло п'ятого дня (&T)",
    'CONTROLBAR:ToolTipGandalfFirstLight': 'Спалах світла на 15 сек. приголомшує ворожі загони поблизу й завдає їм незначних пошкоджень\nКлікніть, щоб активувати',
    'CONTROLBAR:ToolTipHuntersLeadershipLegolas': 'Тип ефекту: Лідерство\nПоряд з Араґорном чи Ґімлі Леґолас отримує бонус +25% броні й швидкості\n~ ПАСИВНА ЗДІБНІСТЬ ~',
    'CONTROLBAR:HawkStrike_Summoned': 'Ельфійська вправність (&R)',
    'CONTROLBAR:ToolTipHawkStrikeStormcrow': 'Постріл двома стрілами, що завдає пошкоджень по площі\nДоступно лише пішки\nКлікніть на іконку, потім оберіть ціль',
    'CONTROLBAR:ToolTipHuntersLeadershipGimli': 'Тип ефекту: Лідерство\nПоряд з Араґорном чи Леґоласом Ґімлі отримує бонус +25% броні й швидкості\n~ ПАСИВНА ЗДІБНІСТЬ ~',
    'CONTROLBAR:Leap_Summoned': 'Дворфійські сокири! (&R)',
    'CONTROLBAR:ToolTipLeap_Summoned': 'Ґімлі стрибає в обране місце й завдає пошкоджень по площі\nКлікніть на іконку, потім оберіть ділянку',
    'CONTROLBAR:ToolTipHornofGondorIthilien': 'Звук рогу Ґондору лякає та приголомшує ворогів на 15 сек.\nКлікніть, щоб активувати',
    'CONTROLBAR:ToolTipWarCryIthilien': 'Тип ефекту: Заклинання\nСоюзні загони поблизу на 30 сек. отримують бонус +33% до пошкоджень, +20% швидкості та стійкість до страху й жаху\nКлікніть, щоб активувати',
    'CONTROLBAR:ToolTipCaptainofGondorBoromirIthilien': 'Миттєво наділяє обрані загони значною кількістю досвіду\nКлікніть на іконку, потім оберіть потрібні загони',
    # repeats of translated lines (same English, own hotkey) - hidden on the site, but the game needs them too
    'CONTROLBAR:ToolTipRivendellLightningSword': 'Меч Ґендальфа стріляє блискавками\nКлікніть на іконку, потім оберіть ціль',
    'CONTROLBAR:WizardBlastStormcrow': 'Глава істарі (&R)',
    'CONTROLBAR:GandalfNewMountStormcrow': 'Осідлати Тінегрива / Спішитися (&C)',
    'CONTROLBAR:ToolTipShadowfaxStormcrow': 'Клікніть, щоб перемкнутися між їздою\nна Тінегриві та пішим ходом',
    'CONTROLBAR:HornofGondorIthilien': 'Ріг Ґондору (&W)',
    'CONTROLBAR:WarCryIthilien': 'За Ґондор! (&R)',
    'CONTROLBAR:CaptainofGondorIthilien': 'Гордий, упертий та сильний (&T)',
    'CONTROLBAR:ToolTipSpecialAbilityRingwraithServantsOfSauronSummoned': 'Що більше назґулів збирається разом, то вони сильніші\nНазґули поблизу отримують бонус +10% до пошкоджень і броні\n~ ПАСИВНА ЗДІБНІСТЬ ~\n\nТип ефекту: Пасивне ослаблення\nВорожі загони поблизу отримують штраф -25% пошкоджень і -20% броні\n~ ПАСИВНА ЗДІБНІСТЬ ~',
})

TR.update({  # campaign heroes batch 3 (2026-11-12): Rohan, Gondor, Lothlórien, Woodland Realm, Dwarves, Dale & the East
    'OBJECT:CampaignDerufin': 'Деруфін',
    'OBJECT:CampaignDuilin': 'Дуїлін',
    'CONTROLBAR:ToolTipFerenCommander_BUTT': 'Необхідно: Рівень 3\nПрикликає загін сильванських слідопитів\nНа 5 рівні — ще й загін списоносців Зеленолісся\nНа 8 рівні — ще 1 загін сильванських слідопитів\nНа 10 рівні — по 2 загони кожного виду\nКлікніть, щоб активувати',
    'CONTROLBAR:ToolTipSummonBrandLeadership': 'Тип ефекту: Лідерство\nЛучники поряд із Королем Брандом отримують бонус +33% до пошкоджень, +33% дальності огляду й +15% дальності атаки\n~ ПАСИВНА ЗДІБНІСТЬ ~',
    'CONTROLBAR:ToolTipSummonBrandHuntersMark': 'Вороги в радіусі на 30 сек. отримують на 33% більше пошкоджень від атак на відстані\nКлікніть на іконку, потім оберіть ділянку',
    'CONTROLBAR:ToolTipTheodredLuckCampaign': 'Необхідно: Рівень 3\nТеодред вдягає шолом і отримує бонус +33% броні\nПісля активації Теодред на 30 сек. уникає всіх пошкоджень від атак на відстані\nКлікніть, щоб активувати',
})

TR.update({  # campaign heroes batch 4 (2026-11-13): Rivendell & the Dúnedain
    'OBJECT:Lindir': 'Ліндір',
    'CONTROLBAR:GamlingMount': 'Сісти верхи / Спішитися',
    'CONTROLBAR:ToolTipGlorfindelWrathArnor': 'Ґлорфіндел на 30 сек. отримує бонус +100% до пошкоджень\nКлікніть, щоб активувати\n\nТип ефекту: Заклинання\nҐлорфіндел наганяє страх на ворогів поблизу й назґулів\n~ ПАСИВНА ЗДІБНІСТЬ ~',
    'CONTROLBAR:GlorfindelSlayerArnor': 'Убивця демонів (&C)',
    'CONTROLBAR:ToolTipGlorfindelSlayerArnor': 'Відкидає загони в широкому радіусі навколо Ґлорфіндела, завдає їм пошкоджень і приголомшує їх на 15 сек.\nУдари Ґлорфіндела зблизька на 30 сек. знерухомлюють ворожих героїв\nКлікніть, щоб активувати',
    'CONTROLBAR:ShireGildorTelperion': 'Світло Тельперіона (&R)',
    'CONTROLBAR:ToolTipShireGildorTelperion': 'Ґілдор відкриває свій благословенний ліхтар, і ворожі загони тікають у жаху\nКлікніть, щоб активувати',
})

d = json.load(open(P, encoding='utf-8')) if os.path.exists(P) else {
    'meta': {'faction': 'Heroes', 'note': 'AI drafts for campaign-hero lines (heroes/campaign pages) that had no Ukrainian at all '
                                          '(lowest priority: any proofread text wins).'}, 'strings': []}
have = {r['var'].lower(): r for r in d['strings']}
bad = []
for var, ua in TR.items():
    k = var.lower(); en = STR[k]['en']
    hk_en = re.search(r'&(\w)', en); hk_ua = re.search(r'\(&(\w)\)$', ua)
    if bool(hk_en) != bool(hk_ua) or (hk_en and hk_en.group(1).lower() != hk_ua.group(1).lower()):
        bad.append((var, 'hotkey'))
    if 'ʼ' in ua or re.search('[ыэъё]', ua):
        bad.append((var, 'letters'))
    r = {'var': STR[k]['var'], 'en': en.replace('\n', '\\n'), 'uk_ai': ua.replace('\n', '\\n')}
    if k in have:
        have[k].update(r)
    else:
        d['strings'].append(r); have[k] = r
assert not bad, bad
json.dump(d, open(P, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(len(d['strings']), 'drafts in', P)
