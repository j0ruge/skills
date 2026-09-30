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

## Behavior

| Feature | How |
|---|---|
| Fit | `translate(-50%,-50%) scale(min(w/1920, h/1080))` on an absolutely positioned stage |
| Navigation | Arrows, PageUp/Down, Space, Enter, Home/End, click (left third = back), swipe |
| Deep link | `#N` in the URL; it is kept in sync with `history.replaceState` |
| Notes panel | `N` toggles a bottom panel with elapsed time and the plan window for the slide |
| Presenter window | `P` opens `?apresentador#N` in a popup. Sync goes through `postMessage` to `opener`/popup, because BroadcastChannel does not cross `file://` windows. Timer turns red 15 s past the plan |
| Timer | Starts when leaving the cover; `R` resets |
| Print | One slide per page at 1920×1080 (`@page`). The footer is hidden, and `data-print` (classification · section · NN / TT) is drawn by `::after` |
| Motion | `.enter` fades 8 px in 450 ms without backwards fill; `prefers-reduced-motion` turns it off |

## Export

```bash
google-chrome --headless=new --no-pdf-header-footer --virtual-time-budget=4000 \
  --print-to-pdf=dist/deck.pdf "file://$PWD/dist/deck.html"
```

`shoot.sh` does this and asserts page count == slide count.
