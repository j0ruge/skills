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

## Text color on every surface

A color that passes 4.5:1 against white can fail on the surfaces the slides actually use. In a TCC study guide built
on the same `DESIGN.md` as a deck (22/11/2026), the brand magenta `#e60073` measured 4.55:1 on white, 4.25:1 on
`#f7f7f7` and 3.85:1 on the pink callout `#fde6f1`. Measure every text token on each surface it sits on (`--bg`,
`--muted`, `--brand-soft`, a tinted callout), not only against white. If one fails, add a darker text token (there,
`#c80064`: 4.88–5.77:1) and keep the brand color for shapes, bars and borders.

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
- **Zoom on hover** (`class="zoom"` on an `<img>`): a real screen or a photo that the room cannot read at slide
  size grows while the mouse is over it, and the rest of the slide dims. Set the scale in `--zoom` (default 1.5) and
  the fixed point in `--zoom-origin` (default `left center`). Measure the enlarged box with Playwright
  (`getBoundingClientRect` after `mouse.move`): it must stay inside the stage and above the footer. In a TCC defence
  deck (21/11/2026) an 895 × 560 image at 1.7 went 41 px into the footer, and 1.55 stopped 1 px above it.
  `check-fit.mjs` and `shoot.sh` see only the resting state, so they pass either way. The PDF shows the small image:
  what the slide needs must be readable without the zoom. `build.py` inlines the image into `dist/` (HTML and PDF);
  an image kept out of the repository must have its `dist/` files ignored too, or it returns through them.
- **Zoom to the center** (a row of photos or figures): scaling in place from one origin pushes the side images off
  the stage, so here the photo leaves its place for the stage center. Wrap each `<img>` in a box that holds the
  resting size (`height` and `aspect-ratio:W/H`, `tabindex="0"`). On the box's `:hover` and `:focus-visible`, give
  the image `position:fixed;left:50%;top:50%;height:1000px;transform:translate(-50%,-50%);pointer-events:none`.
  Inside the scaled `#stage`, `fixed` resolves against the stage, so the photo lands on its center at any window
  size. The hover lives on the box, which does not move, and the enlarged photo takes no pointer: with the `:hover`
  on the image itself, the photo left the cursor and blinked (TCC defence deck, 26/11/2026: 4 to 6 of 11 samples,
  taken every 50 ms for 500 ms, came back small). Keep `.enter` off that block, because the entrance transform
  becomes the reference of `fixed` for 0.45 s. Measure with Playwright the center (within 20 px) and the height over
  those 500 ms, and prove the probe on two copies: one without the centering rule (637 px off center there) and one
  with the hover on the image.
- **Row of figures** (`figure` with a caption): in a grid of `repeat(3,auto)` columns, a line that spans the three
  (`grid-column:1/-1`) widens the `auto` columns to the container, and a `figure` in a flex column stretches the
  image box over its `aspect-ratio`. In the same deck the three images came out 9 to 20 % wider and touching, with
  `build.py` and `check-fit.mjs` green; only the shot showed it. Put the full-width line after the grid, give the
  figure `align-items:flex-start`, and give the caption `contain:inline-size;align-self:stretch`, or it wraps one
  word per line.
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
- **Source diagram** (an org chart or a flow that comes as an image inside the source deck): redraw it in HTML
  with the deck's tokens. It carries text, and shrunk to fit a column the text stops reading. In a business-plan
  deck (18/11/2026) an org chart of 1600×1062 px, shown at 1232 px wide, left the names unreadable on the stage,
  in the source's own colors, and the user rejected the slide. When one box per person does not fit at the
  label scale, group people under their role.
- **Photo** (cover and close): it needs a license that allows reuse, and the credit goes on the slide. In the
  Portal deck (03/11/2026) Unsplash's search asked for a login, and Wikimedia Commons (Featured pictures) gave a
  CC BY photo with a named author. Record the author, license, URL, crop and sha256 in `material/`. Measure the
  file before choosing it: a cover photo is landscape and at least as wide as the stage (1920 px), set full-bleed
  with the veil over the whole slide. In a business-plan deck (18/11/2026) a portrait photo of 426×945 px,
  stretched into a 680×1080 strip under a gradient that stopped at 48% of it, showed streaks in the fade, and
  the user rejected the cover. Two earlier decks with a 1920 px landscape photo and a full veil were the
  covers the user pointed to as good.
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

## Redesigning someone else's slide

The fidelity rule keeps the words and the numbers; the slide's visual idea needs the same care. Before
redrawing a source slide, name what its picture says (a trajectory, a comparison, a hierarchy) and keep that in
the new composition. In a business-plan deck (18/11/2026) the source showed eight systems on a rising curved
arrow, from a database to what comes next; the redesign kept every name on a straight line with dots, and the
user found it less interesting than the original.

## Identity without a DESIGN.md

When the organization of the talk has no `DESIGN.md`, derive one before falling back to the neutral palette.

- Measure the logo (its most frequent opaque pixels) and read the site's CSS: colors by frequency, `font-family`,
  radii, shadows. A skill that writes a `DESIGN.md` from a URL does this with a grounding rule; use one if installed.
- Look at a screenshot of the site before choosing surfaces. Frequencies give the palette, not how the site uses
  it. In the TCC deck (20/11/2026) a `DESIGN.md` made from the logo and the CSS counts gave a quiet blue-on-white
  deck; the screenshot showed a full yellow hero, uppercase titles and a short magenta rule, and the cover was redone.
- A licensed site font (Adobe Fonts) cannot be inlined. Pick an open font of the same model, self-host it, and
  record the swap (Futura PT became Jost in that deck).
- Measure every pair you take from the site: its white on yellow measured 1.47:1, and the deck put the brand blue
  on the yellow instead (6.27:1).
- Write in the `DESIGN.md` where each value came from and what was not found (no brand manual, in that deck).

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
