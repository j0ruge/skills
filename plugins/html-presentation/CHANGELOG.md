# Changelog — html-presentation

Versioned history of the plugin (mirrors `plugin.json`). The per-session record lives in
`skills/html-presentation/CHANGELOG.md`.

## [1.1.0] — 2026-09-30

### Added
- PowerPoint sources (step 2): `python-pptx` for text and speaker notes, `soffice` → PDF → MinerU for the
  layout. The PDF export drops the notes, and in the IACS E26/E27 deck they held a whole slide's talk.
- `references/layout-and-type.md`: an **Agenda** component whose minutes come from the `data-t` of each
  section, and a **References appendix** (citation standard such as ABNT NBR 6023:2018, reading slides after
  the close, each URL checked with `curl` before its "Acesso em").
- Gotchas: glyph missing from the self-hosted font (`≠ → ←`), photo or dark slide lost in the PDF (print
  rules repaint `.slide` and reuse `.slide::before`), the same image inlined once per `url()` (1.7 MB →
  569 KB with one `--photo` variable), and the `.src` line running under content that grows.

### Changed
- "Footer collisions" now says to keep section names to about 12 characters.
- The action block is for actions only; objectives and claims go in the lead or on a line with a brand bar.

### Why
Second real deck built with the skill: a 30-minute technical training on IACS UR E26/E27 from a PPTX
(25 slides, room + Meet + PDF). Every item above failed or was fixed during that session. The print-CSS
failure was reproduced without the fix before it was written down.

## [1.0.1] — 2026-09-30

### Fixed
- `plugin.json` no longer declares `"agents": "./agents"`. With that field, `claude plugin install` failed
  with `Validation errors: agents: Invalid input`; the `agents/` directory is discovered automatically,
  as in the official plugins (e.g. `coderabbit`). The template in this repo's `CLAUDE.md` still shows the
  field, which is where the mistake came from.

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
