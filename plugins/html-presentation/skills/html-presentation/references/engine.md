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

## Behavior

| Feature | How |
|---|---|
| Fit | `translate(-50%,-50%) scale(min(w/1920, h/1080))` on an absolutely positioned stage |
| Navigation | Arrows, PageUp/Down, Space, Enter, Home/End, click on the stage (left third = back), swipe. A click within 400 ms of the window gaining focus, or outside the stage, does nothing |
| Deep link | `#N` in the URL; it is kept in sync with `history.replaceState` |
| Notes panel | `N` toggles a bottom panel with elapsed time and the plan window for the slide |
| Presenter window | `P` opens `?apresentador#N` in a popup. Sync goes through `postMessage` to `opener`/popup, because BroadcastChannel does not cross `file://` windows. Messages carry `{deck, t0, gen}`. The popup sends `{hello}` every second, and a deck that lost it (F5) relinks and sends its slide back once. Timer turns red 15 s past the plan |
| Timer | Starts when leaving the cover and is shared by both windows. `R` (either window) or the popup's button bumps `gen`, which wins everywhere; with the same `gen`, the oldest `t0` wins, so a reopened popup or a reloaded deck keeps the time already spoken |
| Key hint | Shown on mouse move (`body.hint`), hidden 2.5 s after the mouse stops. Never while the presenter window is open (`pwin` alive; a hello also clears it), in the popup or in print. Right after an F5 it can show until the first hello (≤ 1 s) |
| Steps | On a slide with `data-steps="N"`, arrows, click, swipe and the popup's buttons reveal the next step before changing slide, and going back lands on the slide fully revealed. A block not yet revealed gets `.later` (transparent, its space kept, so nothing jumps); `data-at` on the section carries the step for custom styling. Messages carry `{deck, step, t0, gen}`, and the popup shows "etapa s/N" and what the next click does. The hash stays `#N`, because `check-presenter` reads it; `#N.s` opens on step s, for screenshots |
| Print | One slide per page at 1920×1080 (`@page`). The footer is hidden, and `data-print` (classification · section · NN / TT) is drawn by `::after`. Every step prints revealed |
| Footer labels | One label per section on the progress line, the last one anchored right. Two labels closer than 24 px get `.tight`, and only the active one shows. Measured after the first `show()` (the page number narrows the line) and again on `document.fonts.ready` (a self-hosted font changes the widths) |
| Motion | `.enter` fades 8 px in 450 ms without backwards fill; `prefers-reduced-motion` turns it off, and every transition with it, because `shoot.sh` captures that way |

## Export

```bash
google-chrome --headless=new --no-pdf-header-footer --virtual-time-budget=4000 \
  --print-to-pdf=dist/deck.pdf "file://$PWD/dist/deck.html"
```

`shoot.sh` does this and asserts page count == slide count.

## Regression check

`node scripts/check-presenter.mjs dist/<name>.html` (Playwright, local or global) drives the deck and the
popup at 1366×657: `R` in each window, a reopened popup, F5 on the deck, the key hint, and clicks on the
band, after focus, mid-stage and on the left third. On a deck with `data-steps` it also checks that the
popup's arrow reveals the step on the deck, that the arrow changes slide only after the last step, and that
going back lands revealed (it prints "pulado" otherwise). A last tab with reduced motion, as `shoot.sh` opens the
deck, checks that no transition still runs and that the hidden footer labels are the colliding ones. It simulates the activation click with a window `focus`
event, because Playwright emulates focus on the pages it drives and the page never sees the real one. On
X11 the real activation click delivers `focus` 2–7 ms before `mousedown` (plain Chrome on Xvfb + openbox,
16/10/2026); on Windows it is still a human check.
