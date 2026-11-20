# The World in One Image — Friday, 20 November 2026

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/Tiannuryadins/makefun-news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/Tiannuryadins/makefun-news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

An entry for the make.fun bounty **"Sum up 20 November's world news in one image"**
(`news-image-20261120`): $250 in prizes shared by the top 50 entries — $50 for
1st, $30 for 2nd, $15 for 3rd, $5 for 4th–10th, $3 for 11th–50th. Entries close
Sunday 22 November 2026, 00:00 UTC (07:00 WIB). Entry is free.

## The idea

A newspaper front page for one day: the program writes a single poster that
lets anyone who missed Friday, 20 November 2026 catch up on it at a glance —
one lead story, a by-the-numbers strip, and twelve more stories in a grid, each
with a category tag and a hand-drawn icon. The image carries the news itself
(the judge has no news feed), so every story is named, dated and sourced on
the poster.

Run it and you get `world_news_20_nov_2026.png` written to `/output/entry.png`:

```bash
python3 main.py                                    # writes /output/entry.png
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py        # local testing override
```

`main.py` is standard library only and reads the poster PNG that ships in this
repo — no Pillow at run time (the grader runs `python3 -P -s`, where Pillow
does not exist), no network, and the same bytes on every run, so the two
grader runs write identical files. If `/output` is not writable it falls back
to `./output/entry.png`. The program checks the gate itself on every run with
a small stdlib PNG parser: the file must be a whole PNG of at most 1 MiB and
1024×1024 px. This poster is 1024×1024 px and under 1 MiB.

## The day in thirteen stories

All thirteen were reported on 20 November 2026 and cross-checked against at
least two independent sources (full list in BUILD-TRANSCRIPT.md):

| # | Story |
| --- | --- |
| 1 | **Cyclone Akvan hits Odisha at noon** — severe storm crosses near Gopalpur with 100 kmph winds; over 100,000 evacuated to 1,224 shelters; red alerts on the Odisha and Andhra coasts. *(IMD, JagranJosh, NewsXphere)* |
| 2 | **Anthropic's wild debut** — ANT opens at $111.50, tops a $2T valuation, then slides to ~$93; closes $97.17, up 17%. *(The Tech Portal, Reuters, FintechPro)* |
| 3 | **GTA VI: players get their say** — Metacritic user reviews open today; the critics' 99 from 150 reviews still stands. *(Factash, Polygon, qazinform)* |
| 4 | **Han ruling shakes Seoul** — top court overturns ex-PM Han Duck-soo's 15-year term; ruling party moves to impeach the chief justice. *(Reuters, Korea JoongAng Daily, Seoul Economic Daily)* |
| 5 | **Florida floods, Sierra buried** — 17 in of rain in 48 hours; NWS high flood risk into Friday; a system that may become Tropical Storm Kyle. *(NWS, America Report, Worldwide Screens)* |
| 6 | **Infantino faces a real race** — FIFA confirms Diallo and Tashima as challengers; first contested re-election since 2016. *(Reuters, CitiSports Online)* |
| 7 | **Crimean Bridge hit again** — third strike in a week; Neptune missiles damage the rail section; trains halted. *(Reuters, The Library Estate)* |
| 8 | **Missile scars Riyadh's tallest tower** — Houthi strike blows out PIF Tower windows on 7–8 floors; no injuries. *(Reuters, Sky News, The Curtain)* |
| 9 | **Pyongyang expands enrichment** — IAEA: new Yongbyon extension complete; weapons-grade output grows. *(Reuters, Asia Daily, The Library Estate)* |
| 10 | **Bangladesh lockdown turns violent** — Yunus home torched, 2 killed as Hasina's party shuts parts of the country. *(Reuters, Al Jazeera)* |
| 11 | **US, Venezuela sign military deal** — Hegseth hails Caracas as a "compliant security partner"; joint drills, intel sharing. *(CNN, AP, Latin America Reports)* |
| 12 | **Fiji, Tonga declare drought emergencies** — El Niño dries the Pacific; Fiji frees F$20M, Tonga orders a 27-day emergency. *(Reuters, Oceanographic Magazine)* |
| 13 | **Nicholls ton anchors NZ** — unbeaten 113 on day one of the Wellington Test; NZ 243 for 5 vs India. *(Education Times, JagranJosh)* |

Nothing here is invented. Stories 6–13 are flagged as borderline in
BUILD-TRANSCRIPT.md: their events fall on 18–19 November but they dominated
the 20 November reporting (20 Nov wires and briefs), the same rule the 17, 18
and 19 November entries used. Deliberately excluded on the date rule: the
ADNOC Hormuz tanker attack (17 Nov), the COP31 AI pledge (17 Nov) and the
Anthropic pricing itself (18 Nov — the debut trading is the 20 Nov story).

## Files in this repo

- `main.py` — the entry point: reads the poster and writes `/output/entry.png`
- `render_poster.py` — draws the poster with Pillow (build time only)
- `world_news_20_nov_2026.png` — the poster (1024×1024)
- `LICENSE` — MIT (OSI-approved)
- `BUILD-TRANSCRIPT.md` — research notes, test results, bundling notes

To change the poster, edit `render_poster.py` and re-run it:

```bash
pip install pillow        # only needed for rendering, not for the entry
python3 render_poster.py  # regenerates world_news_20_nov_2026.png
```

The renderer asserts that every headline and body fits its card, so a layout
overflow fails loudly at build time instead of shipping a broken poster.

## License

MIT — see `LICENSE`. Copyright (c) 2026 Januar.
