# makefun-news-image-20261124

[![make.fun](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/jonsonbmth/makefun-news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/jonsonbmth/makefun-news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124)

A one-page newspaper front page summing up the world news of
**Tuesday 24 November 2026** — 39 verified stories across 7 regions,
drawn entirely in code. This is the afternoon rebuild (v2): it re-checks
every morning lead against the wires, corrects the numbers, and adds the
full day's news up to press time.

## What it is

`main.py` (Python 3.13, standard library only) renders a 1024x1024
newspaper front page and writes it to `/output/entry.png`
(`$MAKEFUN_OUTPUT_DIR` outside the grader). The program draws everything
itself: its own framebuffer, its own hand-typed bitmap fonts (a small
5x7 face for body text and a larger serif face for the masthead), its own
PNG encoder, hand-drawn illustrations for every story, and a dotted world
map with numbered pins. No network, no assets, no randomness, no clock —
two runs produce byte-identical output.

The front page carries a serif masthead, a red subhead with the three top
stories, a key-numbers strip, a region bar, a "The day in UTC" timeline,
three hero stories with illustrations, ten secondary stories, a world map
with pins, a numbered list of 26 more stories, and a DATE CHECK box that
lists the near-miss stories deliberately left out because they happened on
other days — plus the outcomes still open when the paper went to press.

## The news

Every story was verified against a real wire on 24 November 2026
(press time 09:00 UTC / 16:00 WIB): Reuters, KCNA, S&P Global, UEFA, AP,
WSJ, ING, the Bank of Canada, the US Treasury and the US State
Department. The three lead stories: Russian military jets entering the
Korea air defence zone near Ulleung island, where residents were told to
shelter for five minutes; Nvidia reinstating Jensen Huang as chief
executive, its shares jumping 31.5% on Monday and Asia's markets roaring
after it (Kospi +7.5%, Nikkei +4.5%, Taiwan +9.1%); and North Korea
saying it will consider shutting Switzerland's diplomatic office in
Pyongyang over sanctions on a children's camp.

Corrections to the morning edition: the Kospi, Nikkei and Taiex levels
are Tuesday's closes, not Monday's; US CPI was not due today (the next
print is 10 December); Dell and HP report after the US close, so their
results are not in yet; the Champions League games kick off in the
evening, so no scores are claimed; SoftBank's earnings were on 10
November, not today. Anything still undecided at press time — the CAS
ruling, the Ifo reading, the US data, the evening fixtures — is labelled
as due, not reported as fact. One-sided claims carry a CLAIM badge.

## How to run

```sh
mkdir -p out
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Writes `out/entry.png` (1024x1024, under 1 MiB, deterministic).

## Known limits

- Press time 09:00 UTC, so evening events (Champions League results,
  Dell/HP earnings, the CAS ruling, US data) are listed as due, not as
  results.
- All pictures are original illustrations drawn in code, not photographs.

## License

MIT — see `LICENSE`.
