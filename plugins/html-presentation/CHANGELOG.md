# Changelog — html-presentation

Versioned history of the plugin (mirrors `plugin.json`). The per-session record lives in
`skills/html-presentation/CHANGELOG.md`.

## [1.0.0] — 2026-09-30

### Added
- Skill `html-presentation`: workflow brief → source to Markdown → talk plan with a time budget per slide →
  design from the project's `DESIGN.md` → build → two inspection rounds → independent review → deliver
  (HTML, PDF, speaker script).
- `assets/deck-template.html`: 1920×1080 engine with the footer progress line by section, notes panel,
  presenter window with timer, print CSS with `classification · section · page`, and sample slides for
  each component.
- `scripts/build.py` (inline assets, generate the script from the notes, gates for offline, notes and time
  budget) and `scripts/shoot.sh` (screenshots with retry and reduced motion, laptop views, PDF page-count
  check, contact sheets).
- Agent `deck-reviewer`: a read-only independent review with a verdict and exact fixes.
- `evals/evals.json` + synthetic inputs: 2 cases (10-min training from a PDF, 8-min board report with a DESIGN.md). First iteration: with the skill 17/17 checks, without 12/17 (no speaker script in either run, no PDF in one).

### Why
Extracted from a real 15-minute training deck. Every gotcha in `SKILL.md` is a failure that happened while
building it: the stage clipped on laptops, faded headless captures, stale screenshots, presenter sync on
`file://`, footer collisions, and six material content losses that only the fresh reviewer caught.
