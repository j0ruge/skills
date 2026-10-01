# Session log — html-presentation

Per-session lessons for this skill. The versioned history is `plugins/html-presentation/CHANGELOG.md`.

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
