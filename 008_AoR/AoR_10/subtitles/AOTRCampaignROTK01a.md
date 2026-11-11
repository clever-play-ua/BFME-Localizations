# AOTRCampaignROTK01a — intro of RotK mission 001 "The Lord of the Rings"

Video `aotr/data/movies/AOTRCampaignROTK01a.vp6` (156 s), voice `aotr/data/audio/speech/AOTRCampaignROTK01a.mp3`
(DialogEvent `AOTRCampaignROTK01a` in `data/ini/speech.ini`).

Transcribed with Whisper large-v3-turbo, then corrected by ear/context (`Mr. Lyle` → `he's alive`, `Pippi` → `Pippin`).
Speakers after 0:47 are from the film scene (Théoden's toast in Edoras, Gandalf/Aragorn, Merry/Pippin and the palantír);
the opening narration (0:00–0:47) speaker is not identified.

| Time | EN | UK (draft) |
|---|---|---|
| 0:00–0:10 | As Saruman's evil is washed away, we send a clear message to Mordor. | Зло Сарумана змито — і ми посилаємо Мордору ясний знак. |
| 0:11–0:17 | Men are not so weak yet that they are powerless to resist the Dark Lord's will entirely. | Люди ще не настільки слабкі, щоб зовсім не мати сили опиратися волі Темного Володаря. |
| 0:19–0:27 | The ruin of Isengard will prove to be a setback, but we would be fools to believe it a deterrent. | Падіння Ізенґарда стане для нього невдачею, та ми були б дурнями, якби вважали, що це його зупинить. |
| 0:30–0:37 | Sauron's power grows by the day. Soon he will be ready to strike. | Сила Саурона зростає з кожним днем. Невдовзі він буде готовий завдати удару. |
| 0:37–0:41 | Our only advantage now lies in his hubris. | Наша єдина перевага тепер — його пиха. |
| 0:41–0:47 | We must force his hand and make him believe that we will use the ring against him. | Ми мусимо змусити його діяти першим і повірити, що ми обернемо Перстень проти нього. |
| 0:47–1:00 | Théoden: Tonight we remember those who gave their blood to defend this country. | Теоден: Цього вечора ми згадуємо тих, хто пролив кров, захищаючи цю країну. |
| 1:02–1:05 | Théoden: Hail the victorious dead! — All: Hail! | Теоден: Слава звитяжним полеглим! — Усі: Слава! |
| 1:17–1:24 | Gandalf: No news of Frodo? — Aragorn: No word. Nothing. | Ґендальф: Жодних вістей про Фродо? — Араґорн: Ані слова. Нічого. |
| 1:27–1:38 | Gandalf: What does your heart tell you? — Aragorn: That Frodo is alive. | Ґендальф: А що каже тобі серце? — Араґорн: Що Фродо живий. |
| 1:42–1:47 | Gandalf: Yes. Yes, he's alive. | Ґендальф: Так. Так, він живий. |
| 2:02–2:11 | Merry: What are you doing? — Pippin: I just want to look at it. Just one more time. | Меррі: Що ти робиш? — Піпін: Я лише хочу на нього подивитися. Ще тільки раз. |
| 2:05–2:11 | Merry: Pippin, are you mad? … Put it back. | Меррі: Піпіне, ти з глузду з'їхав? … Поклади на місце. |
| 2:12–2:31 | Pippin! … Pippin! | Піпіне! … Піпіне! |

## In game (test)

The engine's automatic subtitle (stock `audiosettings.ini`: *If the string "DIALOGEVENT:<soundfilename>Subtitle"
is defined, a subtitle will …*) shows **one block per sound**, max 8 lines in a 640 px window, for
`AutomaticSubtitleDurationMS = 20000` (20 s) from the start of the sound. So only the opening narration fits;
it is shipped as `DIALOGEVENT:AOTRCampaignROTK01aSubtitle` (see `../tools/extra_uk.json`) to test whether the
mechanism works over a movie at all.
