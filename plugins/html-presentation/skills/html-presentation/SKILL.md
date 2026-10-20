---
name: html-presentation
description: "Build a polished, self-contained HTML slide deck (1920×1080) for a timed talk from source material — honoring the project's DESIGN.md, with presenter notes, a presenter window with timer, a PDF for absentees and a speaker script generated from the notes, checked by an independent reviewer agent. Triggers — presentation, slide deck, palestra, apresentação HTML, treinamento, 15x15, talk from a PDF, speaker notes."
license: MIT
metadata:
  author: JorUge
  version: "1.4.0"
---

# HTML Presentation

Turn source material (a PDF, a doc, notes, numbers) into a talk that looks designed, fits its time slot, and
still reads on its own as a PDF. The deck is one HTML file: no build step at presentation time, no network,
no framework. Open it in Chrome and present.

What makes this more than "slides in HTML":
- **The time slot is a budget.** Every slide carries its speaking time (`data-t`); the build fails when the
  notes don't fit the slot with room for questions.
- **One source of truth.** The slide HTML holds the speaker notes; the script (`roteiro-de-fala.md`) and the
  presenter window are generated from them, so they never drift.
- **The project's identity, not a theme.** Tokens come from the project's `DESIGN.md`, adapted to
  projection scale. No `DESIGN.md` → the template's neutral palette.
- **An independent reviewer.** The person who built the deck can't see what it lost from the source. A fresh
  reviewer with no build context compares slide by slide.

## Workflow

### 1. Brief (one round of questions)

Ask only what changes the work, in one batch: who presents; duration; how it is shown (room projector, video
call, both); whether the deck doubles as reading material for people who miss it (then every slide must
explain itself without narration); the closing call to action (contact, deadline); source language → talk
language. If the user already said it, don't ask again.

A requirements file that does not fit the subject (guidelines for another course, a second `DESIGN.md` in the
package) means the wrong file came along: ask which one governs before planning, even when the prompt says not
to ask. In the Farel deck (19/10/2026) the prompt patched "the guidelines talk about Church Fathers" over the
wrong course's guidelines, and the package's own `DESIGN.md` lost to the project's.

### 2. Read the whole source

Convert documents to Markdown before reading (MinerU for PDFs when available; `pdftotext -layout` otherwise,
and treat its tables with suspicion because it interleaves columns). Read all of it. Keep the originals
next to the project (`material/`) so the reviewer can check against them.

A PowerPoint source needs two passes: `python-pptx` for the text and the speaker notes, and
`soffice --headless --convert-to pdf` then MinerU for the layout and tables. The PDF export drops the notes,
and in the IACS E26/E27 deck (30/09/2026) the notes held a whole slide's talk.

### 3. Plan the talk before designing

- About one slide per minute; a 15-minute slot is 15–19 slides. Give each slide a `data-t` in seconds.
  The sum is the duration minus ~30 s for questions (`build.py --duration` enforces it).
- Group slides into 3–5 parts; `data-section` drives the progress line in the footer.
- **Fidelity rule:** when adapting someone else's material, nothing of substance is dropped, and every
  number, date and name matches the source exactly. Local examples replace foreign ones only where there is
  a real basis. Paraphrase is where errors enter ("passou de 100" when the source says 100).
- Every threat, risk or problem slide ends with what the audience should *do*: the `.act` block.

### 4. Design from the project's DESIGN.md

Copy `assets/deck-template.html` to `src/<name>.html` in the project. Then:
- Map the `DESIGN.md` tokens onto the template's role tokens (`--brand`, `--brand-strong`, `--brand-soft`/
  `--brand-deep`, surfaces, text). Respect its color rule: if the brand color fails contrast with white
  text, it never becomes a text background; `--brand-strong` does that job.
- Self-host its fonts in `src/assets/fonts/` and declare `@font-face`. `build.py` embeds them.
- App type scales are too small for a room. Keep the template's projection scale (title 76, lead 36, body
  29–31, labels ≥ 19 on the 1920 stage) and record it as a "deck scale exception" section in the
  project's `DESIGN.md`, the way a design system records a login-screen exception.
- Fill the direction-contract comment at the top of `<body>`. If the project also uses the `impeccable` skill,
  write the contract in its surface brief (`impeccable surface-brief write`) and drop the comment: impeccable
  forbids the contract in a served file, and `build.py` keeps comments in `dist/`.
- To reveal a slide by clicks, put `data-steps="N"` on the `<section>` and `data-step="1..N"` on its blocks
  (`references/engine.md`). Use it where the reveal is the content, not as decoration.
- For text in another language or a term the audience may not know, add a hover tip: `data-tip` (translation) or
  `data-g` (an entry in the hidden `#glossario`, one source for every slide). Read the "Hover tip" component in
  `references/layout-and-type.md` before writing the entries.

Read `references/layout-and-type.md` when composing slides: component catalog, what to avoid, mockups.

### 5. Build

```bash
python3 <skill>/scripts/build.py src/<name>.html --out dist --duration <minutes>
```

Output: `dist/<name>.html` (fonts and images inlined, works offline) and `dist/roteiro-de-fala.md`. The
build fails on an asset that was not inlined, any external `http(s)` resource, a slide without notes, or a
time budget over the limit, and on a hover tip `data-g` without its glossary entry. It also warns, without failing, when a note read at 150 words per minute needs 5 s
or more beyond its `data-t` (a number counts as two words, a date as three): the time budget alone let a 65 s
note that needs ~80 s through (Manutenção Proativa deck, 16/10/2026).

### 6. Inspect: two rounds at most

```bash
bash <skill>/scripts/shoot.sh dist/<name>.html shots
```

It captures every slide at 1920×1080, plus a 1366×768 and a 1280×720 laptop view, exports the PDF and
checks that it has one page per slide. It also writes 2×2 contact sheets (`shots/grade-*.png`). Look at every
sheet and both laptop shots. Fix everything in one batch, rebuild, and look again. Two rounds, then stop
polishing; the reviewer does the next pass better.

On WSL without Chrome, `pdfinfo` or ImageMagick on the PATH, `shoot.sh` uses Playwright's cached Chromium, counts
the PDF pages itself and draws the sheets with Pillow. A slide with `data-steps` is shot at step 0: capture each
step too with the same Chrome line and `deck.html#N.s` (window taller by the measured bar, PNG cropped back, as
in `shoot.sh`), and pass those shots to the reviewer.

With Playwright installed, also run `node <skill>/scripts/check-presenter.mjs dist/<name>.html`. It drives the
deck and the presenter window together and fails when the engine copy inside the deck regressed; a deck with
`data-steps` also gets the step checks. Without a global install, `npm i --prefix <dir> playwright@<version>`
(the one whose `chromium-NNNN` is already in `~/.cache/ms-playwright`, so nothing downloads) and run it with
`NODE_PATH=<dir>/node_modules`.

### 7. Independent review

Spawn the `deck-reviewer` agent (Claude Code). Elsewhere, spawn a general-purpose agent with the packet in
`references/review.md`. Never review in the build thread: the builder's framing hides exactly what the
review is for. Apply the material findings in one batch, then **rerun steps 5–6**. A text fix can overflow
its slide; one of the six fixes in the origin session did.

### 8. Deliver

- `dist/<name>.html`: present with it (keys below).
- `dist/<name>.pdf`: for absentees. The footer is hidden in print, so each page carries
  `classification · section · NN / TT` from `data-print`. Set `<body data-classification="…">`.
- `dist/roteiro-de-fala.md`: rehearsal script with a cumulative clock.
- Optional post-event kit: attendance, recording, minutes template, email to absentees with a reading
  deadline.

Presenter keys: `→ ←` navigate · `N` notes panel · `P` presenter window (notes, timer, next slide; put it on
the laptop while the projector shows the deck) · `F` fullscreen · `R` reset the timer in both windows.

## Gotchas (each one was a real failure)

- **Stage clipped on laptops.** `display:grid; place-items:center` plus `scale()` clips the 1920 stage in
  any window narrower than 1920, and `unsafe center` does not fix it. Center with
  `left:50%;top:50%;transform:translate(-50%,-50%) scale(s)`, as the template does.
- **Faded screenshots and PDFs.** An entrance animation with `fill-mode: both` makes headless captures
  catch the title at 30% opacity. Content must be visible by default, and capture with
  `--force-prefers-reduced-motion`. That flag only reaches what `prefers-reduced-motion` turns off, so the
  template turns off every transition there: a footer label still fading out was shot over its neighbor and
  read as a collision (template sample, 19/10/2026).
- **Stale screenshots.** Back-to-back headless runs sometimes write nothing, and the old PNG stays. You
  then review a slide that no longer exists. `shoot.sh` deletes first, retries and checks size.
- **Stage shrunk, with dark bands, in the shots.** In `--headless=new` (the full Chrome), `--window-size` is the
  outer window and 87 px go to the browser bar: a 1920×1080 window gave a 1920×993 viewport, and the stage
  came out at ~0.92 (Chromium 130 and 145, 19/10/2026). `shoot.sh` measures the real viewport, opens a taller
  window and crops the PNG back with Pillow or ImageMagick; without either, it warns.
- **Presenter window out of sync.** On `file://`, BroadcastChannel does not cross windows. Sync through
  `window.opener` / `postMessage`. The deck holds the popup only in memory: after an F5 the notes stayed on
  the old slide and the popup's arrows made the projector skip one. Each window also kept its own clock, so
  `R` reset only one and a reopened popup showed 00:00 minutes into the talk. The template now shares slide,
  start time and resets, and the popup's hello every second relinks a reloaded deck (Manutenção Proativa
  deck, 16/10/2026).
- **Sharing "a window" in a call still shows the key hint and the `N` panel.** Both belong to the deck page;
  only the popup stays private. The hint now fades 2.5 s after the mouse stops and never shows while the
  presenter window is open (a mouse crossing the deck flashed it); keep `N` closed while sharing.
- **A click to focus the deck changed the slide.** With the popup over the deck on one screen, every click
  navigated, even on the black band beside the stage. The template ignores a click within 400 ms of the
  window gaining focus and any click outside the stage.
- **Reopened popup timed out in `check-presenter`.** Pressing `P` right after closing the presenter window reached
  the window still closing, and no popup opened: the Farel deck failed 3 of 3 runs, and passed 18/18 with 300 ms
  of wait after `close()` (19/10/2026). The check now waits; if it times out again, suspect that race first.
- **A template fix does not reach existing decks.** Each deck carries its own copy of the engine, often
  customized. Port the fix by hand, keep the deck's changes, and run `check-presenter.mjs` on the rebuild.
- **Footer collisions.** The last section label runs into the page number, and two sections starting near
  the end overlap. The template anchors the last label to the right and hides colliding labels except the
  active one. Keep section names to about 12 characters: with five longer names in 22 slides, only the
  active label showed on every slide (IACS deck, 30/09/2026). The template measures after the first slide is
  shown and again when the fonts load: before that, the empty page number left the line 85 px wider and a
  self-hosted font was still loading (19/10/2026). `check-presenter.mjs` checks that the hidden labels collide.
- **Empty stage.** A narrow `max-width` on titles makes 3-line headings and leaves the bottom third blank. If
  a slide looks sparse, raise the type before adding content.
- **The builder's review misses content loss.** In the origin session the fresh reviewer found 6 material
  losses that the builder's two screenshot rounds passed: a dropped key instruction, a missing count ("7th
  time"), a wrong technical term, "job title" written where the source said "department", and a stage clipped
  on laptops.
- **Print loses context.** `@media print` hides the footer; without `data-print` the PDF has no page numbers,
  sections or classification.
- **Confidential source.** Material marked "Confidential" stays out of public places. Don't publish the
  deck as a public artifact; mark the PDF with the classification.
- **Glyph missing from the self-hosted font.** A latin subset (IBM Plex in the origin projects) has no `≠`,
  `→` or `←`. The browser swaps fonts for that one glyph and it renders misaligned ("=/"); `build.py` does
  not notice. Draw such symbols as inline SVG sized in `em`.
- **Photo or dark slide lost in the PDF.** The print rules repaint every `.slide` with `--bg` and reuse
  `.slide::before` as the 5px bar. A cover with a single-class selector loses its photo (white title on a
  light page), and a veil drawn with `::before` collapses to a 5px strip over a bright photo. Give such
  slides their own print rule (background again, veil with `inset:0`) and look at page 1 of the PDF.
  Print also takes `.slide::after` for the `data-print` footer, so a slide decorated with `::after` (a dawn
  glow on a dark cover) loses either the decoration or its page number. Put both in one print rule:
  `content:attr(data-print)` over the decoration's background, `inset:0`, text aligned bottom-right
  (cell-group deck, 01/10/2026).
- **Deck several times heavier than its assets.** `build.py` inlines every `url(assets/...)` separately:
  one photo used by four rules (screen and print, cover and close) made a 1.7 MB deck; declared once as
  `--photo:url(...)` it was 569 KB (IACS deck, 30/09/2026).
- **Source line under the content.** `.src` sits at a fixed spot above the footer (`position:absolute`), so
  content that grows runs under it: 3 slides of the IACS deck (30/09/2026), one of them after a review fix.
  Look for it in every shot.

## Files

| Path | When to read or run it |
|---|---|
| `assets/deck-template.html` | Starting point for every deck: engine, footer, notes, presenter window, print, sample slides per component |
| `scripts/build.py` | Run on every build: inlines assets, generates the script, enforces the gates |
| `scripts/shoot.sh` | Every inspection round: screenshots, laptop views, PDF, contact sheets |
| `scripts/check-presenter.mjs` | Step 6 when Playwright is installed, and after porting an engine fix: presenter window, shared timer, key hint, focus click, steps, hover tips, footer labels, reduced motion |
| `references/layout-and-type.md` | Read when composing slides (step 4): components, scale, mockups, what to refuse |
| `references/engine.md` | Read only when changing navigation, notes, presenter window or print behavior |
| `references/review.md` | Read before step 7, when spawning the reviewer: input packet and verdict format |
