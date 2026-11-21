# Session log — html-presentation

Per-session lessons for this skill. The versioned history is `plugins/html-presentation/CHANGELOG.md`.

## 2026-11-21 — the same TCC deck, version 2 with a real screen (v1.7.0)
- The user asked for the photo on slide 3 to grow under the mouse. Written by hand in the deck: `transform:scale`
  from `left center`, a dimming `box-shadow`, `z-index` above the content.
- The first scale, 1.7, put the enlarged image 41 px into the footer with `check-fit.mjs` green: it measures the
  resting slide. 1.55 stopped 1 px above the footer. The box was measured with Playwright, without opening the image.
- The image is private. The source references it by path, but `build.py` inlines it, so `dist/` HTML and PDF had to
  be ignored as well.
- Lesson added: component `.zoom` in the template and the entry *Zoom on hover* in `references/layout-and-type.md`.
- Not fixed here: a second deck built into the same `dist/` overwrites `roteiro-de-fala.md`.

## 2026-11-20 — the same TCC deck, second review round (v1.6.3)
- Two review fixes added sentences to the source line of slides 8 and 10. `.src` is anchored right and grows left on
  one line; it entered the left margin (x = 80 of a 128 px padding) with `check-fit.mjs` green in all four sizes.
- Lesson added: `check-fit.mjs` fails a `.src` that starts left of the slide's padding (gotcha *Source line under
  the content*). In the deck, the sentences moved into the slide body.

## 2026-11-20 — a TCC defence deck, re-skinned mid-build (v1.6.2)
- A 17-slide deck for a 15-minute defence, built on the employer's `DESIGN.md` because the user named that file.
  With the university's logo already in the footer, the user asked for the university's identity instead. The
  deck was re-skinned twice: first from the logo and CSS color counts, then again after a screenshot of the site.
- Lessons added: the brief asks whose identity governs (`SKILL.md`, step 1); *Identity without a DESIGN.md*
  (`layout-and-type.md`); the Playwright version comes from the build named in the launch error (`SKILL.md`,
  step 6); a color-field cover needs its own print rule (gotcha *Photo or dark slide lost in the PDF*).
- Not applied: the template's `'Minha Sans'` comment and the `.contact::before` bar, both flagged by the impeccable
  detector. They are false positives of that detector, and the template is better with them.

## 2026-11-18 — a business-plan deck, the user's review of a finished build (v1.6.1)
- A 40-slide deck redone from someone else's PowerPoint, with every gate green and an independent review done.
  The user then rejected the cover and the org chart, and found one redesigned slide weaker than its source.
- Lessons added, all in `layout-and-type.md`:
  - measure the cover photo: landscape, at least 1920 px wide, full-bleed, veil over the whole slide;
  - a diagram that comes as an image in the source is redrawn in HTML;
  - name the visual idea of a source slide before redrawing it, and keep it.
- The cover fix is proven by two earlier decks; the other two were planned in this session and not yet shot.

## 2026-11-10 — a training deck in two parts, part 1 as reading material (v1.6.0)
- A training deck whose part 1 each manager re-presents to the team, built on the 1.5.2 template with a sibling deck's
  look (photo cover and dark close).
- Lessons added:
  - the dark close showed the footer over the photo: the template now hides it on any `.dark` slide;
  - printing one part with its notes below each slide, with its three checks and the blank-PDF trap, in `engine.md`;
  - cropping screenshots so the screen's text is readable in the room, in `layout-and-type.md`.
- The independent reviewer still found 2 factual errors after every gate was green (a quotation confused with a cost,
  a quarter column read as a month), which the existing gotcha on the builder's review already covers.

## 2026-11-03 — Portal, the code review on the eve of the talk (v1.5.0)
- A code review of the finished deck and its tools, after a wording change that entered the footer with every gate
  green.
- Lessons added:
  - `check-fit.mjs`, ported from the deck with the holes the review reproduced closed;
  - the keys on the popup's buttons and the malformed message, in the template and in `check-presenter`;
  - two gotchas, and a "Layout check" section in `engine.md`.
- The prototype corrected the first fix: a guard with `:focus-visible` failed, because the key press turns it on.

## 2026-11-03 — Portal, the rest of the deck: polish, review, delivery (v1.4.3)
- The same 27-slide deck, finished: an impeccable critique and polish, then the `deck-reviewer` (SHIP WITH FIXES,
  5 material findings applied).
- Lessons added:
  - `shoot.sh` measures the browser bar by screenshot. The `--dump-dom` measure was wrong from Chrome 153, and the
    bar is now measured on Chrome 145, 153 and 156;
  - the chip rule for items, and the cover's classification;
  - the cover gotcha, generated diagrams and photos in `layout-and-type.md`, and a sentence on the reviewer
    gotcha.
- Not changed:
  - the cover layout itself (fixed `top`s), because a flow layout is a template change bigger than this lesson;
  - the description;
  - the presenter-window class names. A deck class `.plan` would have reached `#pview .plan`, but it was caught
    before the build, with no measured failure.

## 2026-11-03 — Portal, a 30-minute deck in English for the Direction (v1.4.2)
- The first deck in another language. The audience-visible engine strings (key hint, tip label) were translated;
  translating the N panel too crashed `check-presenter` (it matched the word "decorrido"), proved on the template.
- Lessons added: the checker reads the clock by position, and the gotcha for a deck in another language.
- Not changed: the template strings stay in Portuguese (one i18n object per `lang` is a bigger change than this
  lesson), and the description.

## 2026-10-19 — Guilherme Farel, questions after reading (v1.4.0)
- The presenter read the 12-slide deck and sent a list of questions (terms, people, a French poem). Answered from checked
  sources; the answers became hover tips (glossary + translations), notes and two reference slides; a fresh review
  gave SHIP WITH FIXES (7 material, all applied). The user asked for the tip feature in the skill.
- Lessons added: hover tips in the template (single-source glossary, inside the stage, gone in print), the build
  gate for a tip without entry (a check that read comments failed on the CSS example key), the tip check in
  `check-presenter`, and the cause of the reopened-popup timeout (a race in the check, not the deck).
- Not changed: the description (the feature does not change when the skill should trigger).

## 2026-10-19 — the 1.3.0 debt: footer labels and headless shots (v1.3.1)
- No new deck: the two items the 1.3.0 entry left open, reproduced on the template sample and checked on the Farel
  deck.
- Lessons added: reduced motion turns off transitions (the "overlap" was a fade caught mid-way), the footer measure
  after the first slide and on `fonts.ready`, the `--headless=new` viewport 87 px short (measured, compensated,
  cropped), the `chrome-linux64` glob, and two `check-presenter` checks.
- Not changed: the occasional timeout on the reopened popup in `check-presenter` (it predates this version).

## 2026-10-19 — Guilherme Farel, História Eclesiástica II (v1.3.0)
- A 12-slide, 8:25 seminar deck for a 10-minute slot over Zoom, in the project's IAP identity, following the
  professor's 7 required items; independent review SHIP WITH FIXES (3 material, all text, applied).
- Lessons added: reveal by clicks (template, engine reference, three `check-presenter` checks), a local
  Playwright through `NODE_PATH`, `shoot.sh` fallbacks for WSL, asking when a requirements file does not fit the
  subject, and the direction contract in impeccable's surface brief.
- Not changed: the user's explicit request for a numbered label above each title won over the "Refuse kicker"
  rule; it mapped each slide to a graded item.

## 2026-10-16 — Manutenção Proativa de Consumíveis, hint residue (v1.2.1)
- The 1.2.0 retest left one gap: the hint still flashed while the mouse crossed the deck. It is now hidden while
  the presenter window is open, the case where a shared window reaches an audience.

## 2026-10-16 — Manutenção Proativa de Consumíveis, QA round (v1.2.0)
- A 4-slide, 3:30 deck for a video call and a room, checked by a `/qa-execution` round (8 charters, 21
  scenarios) instead of by building a new deck.
- Lessons added (template, `build.py`, gotchas): shared timer and reset across windows, popup relink after
  an F5, key hint that fades, focus click that does not navigate, pace warning per note, and the port of
  engine fixes to existing decks. All six were reproduced on the template, not only on this deck.
- Instrument lesson: Playwright emulates focus on the pages it drives, so a window `focus` never reaches the
  page. The real activation click was measured with plain Chrome on Xvfb + openbox, read through raw CDP.
- Not changed: the deck ignores `hashchange` (a same-tab hash edit does not move it) and the template assumes
  a cover without a section. Neither hurt a presenter in this round.

## 2026-10-01 — Church cell group, "A esperança está voltando" (v1.1.1)
- Source was a 2-page study guide (PDF) for a 20-minute discussion at home, shown on a living-room TV;
  Bible verses quoted in full (NVI). 13 slides, 19:00 of notes, three discussion blocks of 3 min.
- Lesson added: print takes `.slide::after` for `data-print`, so an `::after` decoration needs a combined
  print rule (dark cover with a dawn glow).
- Confirmed, no change: the reviewer caught a quotation that differed from the chosen Bible translation
  (the source paraphrased Acts 1:11 inside quotes). Fidelity rule already covers it.

## 2026-09-30 — IACS E26/E27 training (v1.1.0)
- Source was a PPTX (15 slides) for a 30-minute technical training, presented by someone else from the
  delivered HTML; references in ABNT at the user's request. 25 slides, 25:15 of notes.
- Lessons added: PPTX two-pass extraction, missing glyphs in the font subset, photo/dark slides in print,
  one image inlined per `url()`, short section names, the `.src` line under growing content, the agenda
  minutes from `data-t`, the references appendix, and the action block only for actions.
- Confirmed, no change: a text fix overflowed its slide again after the independent review (full English
  labels pushed the source line over the cards). Step 7 already says to rerun steps 5–6 after the fixes.
- Not changed in the template: moving `.src` into the flow and a generic print rule for dark slides. Neither
  was verified beyond this deck, so both are gotchas for now.

## 2026-09-30 — origin
- Built from the 15x15 information-security training deck (15 min, 19 slides, room + video call, PDF for
  absentees).
- Testing the generic template surfaced two new cases, both fixed in the template: two sections starting near
  the end overlapped in the footer, and `build.py` tried to inline example paths inside CSS comments.
