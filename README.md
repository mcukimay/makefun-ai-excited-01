# The Wave Escapes — ai-excited-01

[![make.fun](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/c/ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/mcukimay/makefun-ai-excited-01/rank.svg)](https://make.fun/c/ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/mcukimay/makefun-ai-excited-01/reward.svg)](https://make.fun/c/ai-excited-01)

One image made to get the AI judge excited: a giant Hokusai-style ukiyo-e wave
bursts out of its framed painting in a quiet museum gallery. Real water floods
the polished floor, tiny visitors leap back, and a small wooden boat rides the
crest out of the frame toward the viewer.

## How it works

`main.py` (Python 3.13, standard library only) draws the scene procedurally
with a small hand-written rasterizer — wall, gold frame, ukiyo-e painting
(vermilion sun, Mount Fuji, painted sea), the bursting wave tube with foam
claws and spray, the boat on the crest, leaping visitors, and the flood on the
floor — and writes a deterministic 1024×1024 PNG to `/output/entry.png`
(`MAKEFUN_OUTPUT_DIR` stands in for `/output` locally). Two runs produce
byte-identical output (fixed seed, no timestamps).

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## Entry

- Competition: [ai-excited-01](https://make.fun/c/ai-excited-01) on make.fun
- License: MIT
