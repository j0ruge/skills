# Deck engine (template internals)

Read only when changing navigation, notes, the presenter window or print. The engine is ~120 lines of plain
JS at the bottom of `assets/deck-template.html`.

## Slide contract

```html
<section class="slide" data-section="Part name" data-title="Short title">
  …content with .enter on the blocks that animate in…
  <aside class="notes" data-t="45"><p>Speaker text…</p></aside>
</section>
```

- `data-section` is empty on the cover. The first slide of each section places a label on the footer
  progress line.
- `data-t` is the speaking time in seconds. It feeds the presenter window, the notes panel clock and
  `build.py`.
- `<body data-classification="Internal use">` goes into every PDF page.
- Optional, to reveal by clicks: `data-steps="N"` on the `<section>` and `data-step="1..N"` on its blocks.
- Optional, a hover tip: `data-tip="…"` (a translation; `data-tip-label` replaces the "Tradução" label) or
  `data-g="key"` on any inline element. A `data-g` shows `<p id="g-key">` from `<div id="glossario" hidden>`
  after the footer, so one entry serves every slide that names the term. `build.py` fails on a `data-g` with no
  entry and warns on an entry nothing uses.

## Behavior

| Feature | How |
|---|---|
| Fit | `translate(-50%,-50%) scale(min(w/1920, h/1080))` on an absolutely positioned stage |
| Navigation | Arrows, PageUp/Down, Space, Enter, Home/End, click on the stage (left third = back), swipe. A click within 400 ms of the window gaining focus, or outside the stage, does nothing. Enter and Space on a focused button belong to the button; a mouse click on a popup button drops its focus (`e.detail` is 0 only for a click from the keyboard), so Space still advances afterwards |
| Deep link | `#N` in the URL; it is kept in sync with `history.replaceState` |
| Notes panel | `N` toggles a bottom panel with elapsed time and the plan window for the slide |
| Presenter window | `P` opens `?apresentador#N` in a popup. Sync goes through `postMessage` to `opener`/popup, because BroadcastChannel does not cross `file://` windows. Messages carry `{deck, t0, gen}`. The popup sends `{hello}` every second, and a deck that lost it (F5) relinks and sends its slide back once. A `deck` that is not an integer is ignored: `NaN` passed `typeof … === 'number'` and left no active slide. Timer turns red 15 s past the plan |
| Timer | Starts when leaving the cover and is shared by both windows. `R` (either window) or the popup's button bumps `gen`, which wins everywhere; with the same `gen`, the oldest `t0` wins, so a reopened popup or a reloaded deck keeps the time already spoken |
| Key hint | Shown on mouse move (`body.hint`), hidden 2.5 s after the mouse stops. Never while the presenter window is open (`pwin` alive; a hello also clears it), in the popup or in print. Right after an F5 it can show until the first hello (≤ 1 s) |
| Steps | On a slide with `data-steps="N"`, arrows, click, swipe and the popup's buttons reveal the next step before changing slide, and going back lands on the slide fully revealed. A block not yet revealed gets `.later` (transparent, its space kept, so nothing jumps); `data-at` on the section carries the step for custom styling. Messages carry `{deck, step, t0, gen}`, and the popup shows "etapa s/N" and what the next click does. The hash stays `#N`, because `check-presenter` reads it; `#N.s` opens on step s, for screenshots |
| Print | One slide per page at 1920×1080 (`@page`). The footer is hidden, and `data-print` (classification · section · NN / TT) is drawn by `::after`. Every step prints revealed |
| Dark slide | A `<section class="slide dark">` (a close over a photo) puts `dark-mode` on the stage, which hides the footer as on the cover. Before 1.6.0 only the cover hid it, and the footer showed over the photo |
| Footer labels | One label per section on the progress line, the last one anchored right. Two labels closer than 24 px get `.tight`, and only the active one shows. Measured after the first `show()` (the page number narrows the line) and again on `document.fonts.ready` (a self-hosted font changes the widths) |
| Hover tip | `mouseover` on the stage finds the nearest `[data-tip],[data-g]`, fills `#tip` (inside the stage, so it scales with it) and places it below the term, or above when it would cross the bottom, clamped 64 px from the sides. Position is screen px ÷ the stage scale. It closes on `mouseout` to a non-term and on every slide change, and hides the key hint (in a call the hint would go out with the tip). Print hides it and the dotted underline |
| Motion | `.enter` fades 8 px in 450 ms without backwards fill; `prefers-reduced-motion` turns it off, and every transition with it, because `shoot.sh` captures that way |

## Export

```bash
google-chrome --headless=new --no-pdf-header-footer --virtual-time-budget=4000 \
  --print-to-pdf=dist/deck.pdf "file://$PWD/dist/deck.html"
```

`shoot.sh` does this and asserts page count == slide count.

## One part with its notes

When others re-present one part of the deck (a training whose part 1 each manager repeats to the team), hand them that
part as a PDF with each slide's notes below it, so the PDF is also the script. Measured on a training deck (10/11/2026),
where the names were `parte` and `roteiro`:

- Mark every slide `data-part="1"` or `"2"`.
- A script placed **before** the engine reads `?part=N&notes`. It removes the slides of the other parts, so the engine
  counts and numbers only what is left (`01 / 09`). In `notes` mode it adds, after each slide, a block with that slide's
  notes, a class on `<body>` and a `<style>` with a taller `@page`.
- In print, that mode turns `break-after` off on `.slide` and on for the block, which takes `min-height`, never
  `height`. A note too long for the page then becomes one more page, which the page count catches, instead of being cut.
  A page of 1920×1700 with a 620 px block fitted notes of up to 123 words at 27 px, with room to spare.
- **The class on `<body>` must not be the block's class.** With `.roteiro{display:none}` for the screen and `roteiro`
  also on `<body>`, the whole document vanished in print, and Chrome wrote a one-page blank PDF with exit 0. Debug print
  layout with Playwright, `page.emulateMedia({ media: 'print' })` plus `getBoundingClientRect()`: every box had height 0.
- Prove the PDF with three checks: the page count equals the part's slides (`pdfinfo`); no title (the slide's `h2`) of
  the other parts appears in `pdftotext` with whitespace normalized; the first ~60 characters of each note appear. Run
  the title detector on the full deck's PDF first and require it to find every title there: titles wrap across lines,
  and a negative check that cannot fail would pass blind.

```js
(() => {
  const q = new URLSearchParams(location.search), part = q.get('part');
  if (part) document.querySelectorAll('.slide').forEach(s => { if (s.dataset.part !== part) s.remove(); });
  if (!q.has('notes')) return;
  document.body.classList.add('notes-mode');  // not 'notes-block', or print hides everything
  document.querySelectorAll('.slide').forEach(s => {
    const b = document.createElement('div');
    b.className = 'notes-block';
    b.innerHTML = s.querySelector('.notes')?.innerHTML || '';
    s.after(b);
  });
  const pg = document.createElement('style');
  pg.textContent = '@page{size:1920px 1700px;margin:0}';
  document.head.append(pg);
})();
```

```css
.notes-block{display:none}
@media print{
  body.notes-mode .slide{break-after:auto}
  body.notes-mode .notes-block{display:block;width:1920px;min-height:620px;padding:44px 128px 40px;break-after:page;background:var(--bg)}
}
```

Print it with the Chrome line of *Export*, on `file://…/deck.html?part=1&notes`.

## Regression check

`node scripts/check-presenter.mjs dist/<name>.html` (Playwright, local or global) drives the deck and the
popup at 1366×657: `R` in each window, a reopened popup, F5 on the deck, the key hint, and clicks on the
band, after focus, mid-stage and on the left third. On a deck with `data-steps` it also checks that the
popup's arrow reveals the step on the deck, that the arrow changes slide only after the last step, and that
going back lands revealed (it prints "pulado" otherwise). On a deck with hover tips it hovers the first term and
checks that the tip opens with text inside the stage and closes when the mouse leaves. It waits 300 ms after
closing the popup before pressing `P` again: right after `close()` the key reached the window still closing and
no popup opened (Farel deck, 3 of 3 runs, 19/10/2026). A last tab with reduced motion, as `shoot.sh` opens the
deck, checks that no transition still runs and that the hidden footer labels are the colliding ones. It simulates the activation click with a window `focus`
event, because Playwright emulates focus on the pages it drives and the page never sees the real one. On
X11 the real activation click delivers `focus` 2–7 ms before `mousedown` (plain Chrome on Xvfb + openbox,
16/10/2026); on Windows it is still a human check. It also tabs to the popup's buttons, presses Enter and Space, clicks
with the mouse and presses Space, and posts a message with `deck: NaN`. A deck with an engine older than 1.5.0 fails
those four, and the script-error check with them, until the fix is ported.

## Layout check

`node scripts/check-fit.mjs dist/<name>.html` opens every slide fully revealed (`#N.s`) at 1920×1080, 1366×768,
1280×720 and 1366×657, and exits 1 when the stage leaves the window, an element leaves the slide, text is clipped,
something with text sits below `.src`, or anything that paints (text, a background, a border, an image, an SVG) goes
below the top of `#footer`. A slide that hides the footer, like the cover, is listed and not compared. It exits 2 when
it could not measure: no `section.slide`, no `#stage` or `#footer`, or a slide the navigation did not reach.
