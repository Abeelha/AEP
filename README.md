# autotrip

Scene-aware automatic **trippy photo editor**. Drop an image in a folder → it
detects whether the shot is a *person* or an *environment*, then auto-generates
several edited variants (real pixel edits — no AI image generation) so you can
pick the best. It learns which looks you prefer over time.

> Built for a dark lo-fi / nightlife aesthetic: crushed shadows, protected
> highlights, warm-neon-vs-cool-ambient split tone, grain, vignette, halftone.

## What it does

- **Detects faces / subject** (OpenCV Haar; optional `rembg` matting).
- **Person shots** → protect the subject, treat the background separately
  (blur, darken, or replace with a fetched/procedural backdrop), then grade.
- **Environment shots** → full-frame color grade + procedural overlays
  (swirls, lines, gradients, hue washes) + tone/hue shifts.
- **Multiple variants** per image + a contact sheet to compare at a glance.
- **Folder watch** — auto-edits new images as they land.
- **Preference memory** — rate variants; the digest tracks which recipes trend
  better/worse so the system improves.

## Effects & presets

17 effects (`hue, chroma, swirl, wave, kaleido, gradmap, posterize, solarize,
glitch, grain, bloom, vignette, crush, splittone, halftone, mono`) composed into
named presets: `gabriel_night`, `gabriel_duotone`, `gabriel_bw`, `acid`,
`vhs_dream`.

## Install

```bash
pip install -r requirements.txt
# optional better cutout:  pip install rembg onnxruntime
```

## Use

```bash
# process everything already in ./input
python -m autotrip once

# watch the folder and auto-edit new drops
python -m autotrip watch

# one file
python -m autotrip one path/to/photo.jpg -n 5

# rate a recipe so the memory learns your taste
python -m autotrip rate gabriel_night +1
python -m autotrip memory
```

Backdrop assets download from [Lorem Picsum](https://picsum.photos) (free, no
key). Set `PEXELS_API_KEY` + `assets.use_pexels: true` in `config.yaml` for
query-driven backgrounds (nature / buildings).

## Privacy

`input/`, `output/`, and `assets/cache/` are **git-ignored**. Your personal
photos are never committed to this public repo. Only code and license-free demo
material live here.

## License

MIT — see [LICENSE](LICENSE).
