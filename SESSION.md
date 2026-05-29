# Session handoff log

## Origin
This project was bootstrapped from a general "Desktop" Claude Code session on
2026-05-29. From here on, **work on autotrip in this folder** so the Desktop
session stays for general work only. Open Claude Code in
`C:\Users\Abeelha\Documents\GitHub\autotrip` — `CLAUDE.md` loads the full
project context automatically.

## How the project came to be (intent)
User wanted an AI-assisted **auto photo editor** (real edits, not generation)
matching their personal dark/lo-fi/nightlife Snapseed aesthetic, plus:
- detect persons/faces vs environment, treat each differently
- auto-download/compose backdrops + procedural overlays (swirls, lines, color,
  hue, tone, vignette, blur)
- watch a folder, auto-edit new drops into multiple versions to compare
- a memory that tracks which versions get better/worse over time
- ship as a **public** GitHub repo with personal images excluded

## What was built (v0.1.0)
Full pipeline, tested end-to-end. See CLAUDE.md → Architecture / Current state.

## Continuing in this folder
- Resume: `claude` (or your launcher) inside this directory.
- Preference memory: `memory/MEMORY.md`.
- Backlog: CLAUDE.md → Next steps.

## Note
The originating Desktop session also covered unrelated topics (GPU undervolt,
work-account/RDP privacy). Those are NOT part of this project and were left in
the Desktop session on purpose.
