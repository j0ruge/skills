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
  order.
- **Mockups** (chat, email, AI prompt, auto-reply, "To:" autocomplete): build them in HTML in the
  project's visual grammar, with invented neutral names. They beat screenshots: translatable, sharp when
  projected, no real data. Put numbered pins on the *edges* of the mockup (position the card
  `relative`) so they never cover text, and mark the mockup illustrative in its `aria-label`.
- **Close** (`.close`): 3 principles + a dark contact panel with the address in mono and the deadline.

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
