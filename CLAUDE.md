# AEP (auto-edit-pictures) — project context for Claude Code

> Open Claude Code **in this folder** to continue the project here (not the
> Desktop session). This file auto-loads as context. Caveman mode is the user's
> default communication style — terse, technical, no filler.

## What this is

Scene-aware automatic **photo editor**. Real pixel edits (numpy/Pillow),
**not** AI image generation. Drop a photo → detect person vs environment →
auto-produce N edited variants + a contact sheet → user rates them → a
preference memory learns which recipes trend better/worse.

(Originally prototyped under the name "autotrip"; renamed to AEP.)

## Architecture

```
aep/
  effects.py      17 pixel effects + named PRESETS (style recipes)
  detect.py       face detection (OpenCV Haar) + optional rembg subject matte
  generators.py   procedural backdrops (gradient/swirl/lines/hue) — math, license-free
  assets.py       backdrop download: Lorem Picsum (no key) / Pexels (optional key)
  compositor.py   mask-aware: blur/darken/replace background, overlay, vignette-to-subject
  pipeline.py     orchestrator: image -> analyze -> scene recipes -> variants + sheet
  memory.py       ratings.jsonl event log -> MEMORY.md digest (preference learning)
  watcher.py      watchdog folder watch -> auto-edit new drops
  cli.py          `python -m aep {once|watch|one|rate|memory}`
```

## Run

```bash
pip install -r requirements.txt          # core; optional: pip install rembg onnxruntime
python -m aep once                        # process ./input
python -m aep watch                       # live auto-edit on new drops
python -m aep one photo.jpg -n 5
python -m aep rate gabriel_night +1
python -m aep memory
```

## The user's edit style (drives the presets)

Distilled from 72 reference Snapseed edits: **dark lo-fi nightlife**. Measured
signature — brightness ~0.34 (low-key), ~15% crushed shadows, <1% blown
highlights (highlights always protected), warm accent (red/orange/skin) vs cool
azure-violet ambient, frequent vignette, grain + halftone/CRT texture, some full
B&W or heavy purple duotone. Presets `gabriel_night` / `gabriel_duotone` /
`gabriel_bw` encode this; `acid` / `vhs_dream` are wilder options.

## Conventions / decisions locked

- CPU-only, Windows-friendly. ML deps (rembg/mediapipe) are **optional** with
  graceful fallback to a radial face-centered mask.
- Default backdrop source = Lorem Picsum (free, no API key).
- **Public repo. `input/`, `output/`, `assets/cache/` are git-ignored — user's
  personal photos must NEVER be committed.** Safety net: bare `*.jpg/png/...`
  ignored except `samples/` and `docs/`.
- One recipe failing never kills the batch (per-recipe try/except).

## Current state (v0.1.0)

Working end-to-end and tested: detection, person + environment recipe sets (5
each), contact sheets, rating + memory digest. Known-good on test images.

## Next steps / backlog

- Retune `gabriel_duotone` palette (verify on more samples).
- Optional: enable `rembg` for true subject cutout (cleaner background replace).
- `samples/` currently empty — add a couple CC0/Picsum demo images (no faces)
  so the public repo has a runnable example without user photos.
- HALD-CLUT path: capture user's exact Snapseed "Look" as a `.cube` LUT and add
  it as a preset (needs the user to run an identity HALD image through Snapseed).
- Variant scoring could auto-bias future recipe selection from MEMORY.md.

## Memory continuity

Project preference memory lives in `memory/MEMORY.md` (regenerated from
`memory/ratings.jsonl`). For cross-session AI memory, keep notable decisions in
this CLAUDE.md and in `memory/MEMORY.md`. See `SESSION.md` for the handoff log
from the originating Desktop session.
