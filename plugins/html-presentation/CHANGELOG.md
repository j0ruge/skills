# Changelog — html-presentation

Versioned history of the plugin (mirrors `plugin.json`). The per-session record lives in
`skills/html-presentation/CHANGELOG.md`.

## [1.3.0] — 2026-10-19

### Added
- Reveal by clicks: `data-steps="N"` on a `<section>` and `data-step="1..N"` on its blocks. Arrows, click, swipe
  and the popup's buttons reveal the next step before changing slide; going back lands fully revealed. Messages
  carry `{deck, step, t0, gen}` and the popup shows "etapa s/N". Unrevealed blocks get `.later` (transparent,
  space kept); the PDF prints every step revealed. The hash stays `#N`, because `check-presenter.mjs` reads it;
  `#N.s` opens on a step, for screenshots.
- `check-presenter.mjs`: three step checks when the deck has `data-steps` ("pulado" otherwise). Red on the 1.2.1
  engine (3 failures), green on 1.3.0 (17 checks) on the template and on the Farel deck. Its error and header
  explain a local Playwright with `NODE_PATH`.
- `shoot.sh` on WSL without Chrome, `pdfinfo` or ImageMagick: Playwright's cached Chromium, a `/Type /Page`
  count, and Pillow contact sheets (or a warning). Before, the sheets the inspection step asks for vanished
  without a word. Checked with the default PATH: 8 slides, 8 pages, 2 sheets.
- `SKILL.md`: a requirements file that does not fit the subject (another course's guidelines, a second
  `DESIGN.md`) means ask which governs; with the `impeccable` skill, the direction contract goes in its surface
  brief, not in a comment that `build.py` ships to `dist/`.

### Why
A 10-minute HE II seminar deck on Guilherme Farel (19/10/2026), presented over Zoom. Its key moment, an acrostic
hidden in the 1535 Olivétan Bible colophon, needed a two-step reveal the template did not have. The prompt carried
the wrong course's guidelines and a package `DESIGN.md` the user overruled. Playwright was not installed globally,
and WSL had no Chrome, `pdfinfo` or `montage`.

### Known debt (not changed here)
- On the template's own sample, the footer labels "[PARTE 3]" and "[CONCLUSÃO]" still overlap: the `.tight`
  measure runs before the font loads. A project deck already re-measures on `document.fonts.ready`.
- Headless screenshots show the stage at ~0.93 with dark bands (the headless window reserves height). Not yet
  measured; the reviewer packet should say so.

## [1.2.1] — 2026-10-16

### Fixed
- The key hint never shows while the presenter window is open. On 1.2.0 it faded 2.5 s after the mouse
  stopped, but a mouse crossing the deck on its way to the popup still flashed it to the audience of a shared
  window. Without the popup (rehearsal) it behaves as before. `check-presenter.mjs` gained the check (red on
  1.2.0, green on 1.2.1) and now has 14.

### Why
The residue the 1.2.0 QA retest left open on the Manutenção Proativa deck (RS-929): the user chose "hide the hint
while the presenter window is open" over "only on the cover" and "accept".

## [1.2.0] — 2026-10-16

### Fixed
- Presenter window and deck share the clock. Messages carry `{deck, t0, gen}`: `R` in either window (or the
  popup's button) resets both, and a reopened popup or a reloaded deck keeps the time already spoken. Before,
  `R` reset only the window where it was pressed, and a reopened popup showed 00:00 minutes into the talk.
- A reloaded deck relinks the popup by itself. The popup sends a hello every second, and the deck answers
  once with its slide. Before, after an F5 the popup stopped following the deck, and the popup's arrows made
  the projector skip a slide.
- The key hint fades 2.5 s after the mouse stops, instead of staying while the mouse is over the page. In a
  call, the shared window showed it the whole time on a one-screen laptop.
- A click that only brings the deck window forward (within 400 ms of focus) and a click outside the stage
  no longer navigate; the left third is measured on the stage.

### Added
- `scripts/check-presenter.mjs`: Playwright regression check for the engine (13 checks). It failed 9 of
  them on the 1.1.1 engine and passes on 1.2.0, headless and headed.
- `build.py` warns, without failing, when a note read at 150 words per minute (`--wpm`) needs 5 s or more
  beyond its `data-t`; a number counts as two words and a date as three. On the four existing decks it flags
  only the slide that needed it.
- Gotchas: what a shared window shows in a call, the focus click, and engine fixes that must be ported by
  hand to each deck. `references/engine.md` documents the shared timer and the regression check.

### Why
A `/qa-execution` round on the Manutenção Proativa deck (RS-929, 16/10/2026) walked the presenter journeys in
persona and filed six findings against the template's engine and the build gate. Each fix was red before and
green after on the same check; the activation click was also measured with a real X11 click on plain Chrome,
since Playwright's focus emulation hides it.

## [1.1.1] — 2026-10-01

### Fixed
- Gotcha "Photo or dark slide lost in the PDF" now warns that print also takes `.slide::after` (the
  `data-print` footer). A cell-group deck drew its cover's dawn glow with `::after`; one combined print rule
  (`content:attr(data-print)` over the glow, `inset:0`) kept both, checked on page 1 of the PDF.

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
