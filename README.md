# makefun-news-image-20261124

[![make.fun](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/jonsonbmth/makefun-news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/jonsonbmth/makefun-news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124)

A one-page newspaper front page summing up the world news of
**Tuesday 24 November 2026** — 36 verified stories across 7 regions,
drawn entirely in code.

## What it is

`main.py` (Python 3.13, standard library only) renders a 1024x1024
newspaper front page and writes it to `/output/entry.png`
(`$MAKEFUN_OUTPUT_DIR` outside the grader). Everything is drawn by the
program itself: its own framebuffer rasterizer, its own hand-typed bitmap
fonts (including a serif masthead face), its own PNG encoder, and
hand-drawn illustrations and a dotted world map. No network, no assets,
no randomness — two runs produce byte-identical output.

The front page carries a serif masthead, a red subhead with the three top
stories, a key-numbers strip, a region bar, a "The day in UTC" timeline,
three hero stories with illustrations, ten secondary stories, a world map
with pins, a numbered list of 23 more stories, and a DATE CHECK box that
lists the near-miss stories deliberately left out because they happened on
other days.

## The news

Every story was verified against a real wire (Reuters, KCNA, S&P Global,
UEFA, Sportradar, Newsquawk, FXStreet) for Tuesday 24 November 2026.
Leads: South Korea's brief evacuation warning on Ulleung island after an
aircraft entered its airspace; Asia's sharp stock rally (Kospi +4.3%,
Nikkei +2.8%); and North Korea saying it may shut Switzerland's
diplomatic office in Pyongyang. Items still to happen at press time
(00:30 UTC) are marked FORECAST; one-sided claims are marked CLAIM.

## How to run

```sh
mkdir -p out
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Writes `out/entry.png` (1024x1024, under 1 MiB, deterministic).

## Known limits

- Press time 00:30 UTC, so the paper covers the day's early hours plus
  events scheduled later on Tuesday, marked as forecasts.
- All pictures are original illustrations drawn in code, not photographs.

## License

MIT — see `LICENSE`.
