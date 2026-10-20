# Session log — html-presentation

Per-session lessons for this skill. The versioned history is `plugins/html-presentation/CHANGELOG.md`.

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
