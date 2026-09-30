# Independent review packet

The review runs in a **fresh agent** that never saw the build. In Claude Code, use the plugin's
`deck-reviewer` agent. Elsewhere, spawn a general-purpose agent with this packet as the prompt. It reads
and reports; it never edits.

## Inputs to pass (paths, not pasted content)

1. The request, in the user's words, plus the brief answers (duration, audience, how it is shown, whether it
   doubles as reading material, language).
2. Source HTML: `src/<name>.html` (notes are the `<aside class="notes" data-t>` blocks).
3. Screenshots: every `shots/sNN.png`, plus `shots/laptop-1366.png` and `shots/laptop-1280.png`. The
   reviewer has no browser, so a shot you don't pass is a check it can't run.
4. The source material as Markdown (and the original PDF path for tables).
5. The project's `DESIGN.md` (including its deck scale exception).

## What it checks

1. **Fidelity:** slide by slide against the source. Report omitted content, numbers or dates that differ,
   and claims not in the source that aren't clearly reasonable local examples, each with slide, text and
   source quote.
2. **Language:** errors, truncations, inconsistent terms.
3. **Visual (from screenshots):** overlap, clipping, footer collisions, laptop fit, text too small for a
   room, large empty areas, violations of `DESIGN.md`.
4. **Notes:** consistent with the slides; the sum of `data-t` against the slot; speaker text that
   misstates a number.
5. **Stand-alone reading:** any slide that only makes sense with narration.

## Verdict format (≤ ~600 words)

- **Verdict:** SHIP / SHIP WITH FIXES / REDO.
- **Material findings:** table # · slide · problem · exact fix (new text or CSS rule).
- **Minor findings:** short list.
- **What works:** 2–3 lines.

It must not pad the list; "correct" is a valid finding.

## After the verdict

Apply every material fix in one batch, then rebuild and reshoot. Re-send only if a fix was structural. Report
the verdict table to the user as it stands, open items included.
