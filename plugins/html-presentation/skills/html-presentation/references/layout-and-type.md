# Layout and type for projected decks

Read while composing slides. The template (`assets/deck-template.html`) has one sample slide per component.

## Scale (1920×1080 stage)

| Role | Size / weight | Notes |
|---|---|---|
| Cover title (`.t-hero`) | 132 / 700, tracking −0.035em | Two lines max |
| Slide title (`.t-title`) | 76 / 700 | A full claim, not a label. `max-width:30ch`; use `none` for one-liners |
| Lead (`.t-lead`) | 36 / 400 | One or two sentences that work without narration |
| Body / rule text | 29–31 / 400 | Never below 25 for anything the back row must read |
| Labels, chips, table headers, footer | ≥ 19 / 600, uppercase, 0.08em | 15–17 px disappears on a compressed video call |
| Numbers, dates, IDs, e-mail addresses | Mono, tabular | Mono is for disambiguation, not for looking "technical" |

The slide padding is 112 / 128 / 150. The bottom 150 px belong to the footer, so leave them empty.

## Components

- **Statement + items** (`.items`): 3–4 parallel things, separated by thin dividers, not by same-size
  cards.
- **Chart** (`.chart` + inline SVG): one series, one hue. Highlight only the bar that matters with
  `--brand-strong`, label values directly and skip the legend. For part-of-whole with severity, a stacked bar
  with direct labels beats a donut. Always cite the source (`.src`).
- **Record** (`.record`): a case or fact as an app "detail" card (label column + value column + status chip).
  It reads better than a bullet list and avoids the big-number hero template.
- **Flow** (`.flow`): 3–5 numbered steps; `.hot` marks the steps where damage happens.
- **Ranking table** (`.rank`): highlight the rows you will talk about with `tr.hl` and let the rest recede.
  When "consecutive years" and "total times" differ, show both.
- **Rules** (`.rule`): icon + short rule + one-line why. Two columns when there are 4.
- **Action block** (`.act`, brand-soft background): what to do. One per slide, near the end of the reading
  order. Only for actions: an objective or a claim goes in the lead, or on a line with a 2px brand bar. In
  the IACS deck (30/09/2026) the pink block on 8 of 21 slides read as wallpaper, and a design critique
  flagged it.
- **Mockups** (chat, email, AI prompt, auto-reply, "To:" autocomplete): build them in HTML in the
  project's visual grammar, with invented neutral names. They beat screenshots: translatable, sharp when
  projected, no real data. Put numbered pins on the *edges* of the mockup (position the card
  `relative`) so they never cover text, and mark the mockup illustrative in its `aria-label`.
- **Screenshot** (the real screen of the system the talk teaches): crop it to the part the slide talks about, so the
  screen's own text stays readable on the stage. In a training deck (10/11/2026) a 1563 px wide form section, shrunk
  into a 1040 px column, left its letters 10 to 12 px tall (ink from ascender to descender, measured on the capture
  and scaled by 0.665); a 560 px crop of the controls the slide pointed at, shown at 760 px, brought them to 20 to
  24 px. Crop with a script holding a table of boxes over the original capture, so a recapture is cropped the same
  way, and put the numbered pins on the crop's edges, as for mockups.
- **Hover tip** (`data-tip`, `data-g` + `#glossario`): text in another language (titles, a poem, a colophon) and
  terms the audience may not know. The questions the presenter asks after reading the deck are the list: in the
  Farel deck (19/10/2026) they became the glossary entries, and the slides stayed as clean as before. Write each
  entry in one or two sentences from a checked source; a long explanation belongs in the notes. Never put
  something essential only in a tip: the PDF does not show it. On a block of verse, drop the underline and
  highlight the line on hover instead (`--brand-soft` with a 2 px border), or the dotted lines compete with the
  text.
- **Generated diagram** (Archify, Mermaid): it enters as an image, unedited, in its own palette. A legend you
  write outside it restates the diagram's own semantics, so read its legend first. In the Portal deck
  (03/11/2026) the slide said "dashed = the future release", but Archify also draws the decline, which exists
  today, as a red dashed line; in the PDF the decline read as future. Name the stroke by its color too ("purple
  dashes"), and repeat outside the image, at deck scale, what its small text says.
- **Photo** (cover and close): it needs a license that allows reuse, and the credit goes on the slide. In the
  Portal deck (03/11/2026) Unsplash's search asked for a login, and Wikimedia Commons (Featured pictures) gave a
  CC BY photo with a named author. Record the author, license, URL, crop and sha256 in `material/`.
- **Close** (`.close`): 3 principles + a dark contact panel with the address in mono and the deadline.
- **Agenda** (`.agenda`, for talks of about 30 minutes or more): one row per `data-section`. Fill the minutes
  from the notes instead of typing them, or they drift after the first timing change. Inside the template's
  script, after `secs` exists:
  ```js
  document.querySelectorAll('.agenda [data-sec]').forEach(el => {
    const t = slides.reduce((a, s, k) => a + (s.dataset.section === el.dataset.sec ? secs[k] : 0), 0);
    el.textContent = '~' + Math.max(1, Math.round(t / 60)) + ' min';
  });
  ```
- **References appendix**: when the user asks for a citation standard (e.g. ABNT NBR 6023:2018), put the list
  after the close, as reading slides for the PDF. Their notes say they are not presented and carry
  `data-t="5"`; questions stay on the close. Before writing an "Acesso em", confirm the URL answers
  (`curl -s -o /dev/null -w '%{http_code}' -L <url>`). Cite a page that blocks bots by the archived copy you
  actually read.

## Refuse

- A kicker or eyebrow label above the title; the footer already says where you are.
- A grid of same-size icon cards as the page structure.
- The big-number hero template (giant number, small label, accent).
- Emoji or unicode glyphs as icons. Draw SVG icons with one stroke width.
- Brand color as a large surface. It is for marks, progress, alerts and the action.
- Pure black shadows. Tint them, keep them under 10%, and give them an offset.

## Pacing

A dense slide (table, chart) is followed by a lighter one. The cover and the close are the only dark or
full-width moments. If a slide needs more than ~60 s of talk, split it.
