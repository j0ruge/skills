# The Fix Loop — one logic finding at a time

Read this at Phase 3.2, before the first **logic** fix: a finding whose fix changes what the code
decides — a branch, a guard, a parser, a regex, a return value, an exit code. Prose, naming,
comments and pure formatting are **mechanical** and stay batched (SKILL.md 3.2).

## Why the loop exists

A review round that fixes everything and runs the suite once at the end finds the regressions the
fixes created **one round late**, when the bots review again. Measured on the sdd_agents kit:

- PR #46: the fix for a CodeRabbit r1 finding rotted the anchor of a mutation-catalogue mutant; the
  fast suite stayed green and the break surfaced only in the next full catalogue run.
- PR #45: three ~22-minute health runs for one branch, because each bot round's fixes touched code.
- `check-todo.sh`: five review rounds, and three times in a row the fix from one round **created**
  the defect the next round found (fail-open sensors, a `mawk` byte-split on multibyte input).

The trap: a probe that only reproduces the **finding** goes green after any fix that removes the
symptom — including one that opens a new fail-open next to it. The regression lives in the
**fix**, so the fix needs its own sensor.

## The loop, per logic finding

1. **Red — reproduce the finding.** Write the smallest test or probe that fails *because of the
   defect the reviewer named*. Run it and watch it fail. Check it is red **for the right reason**:
   if the exit code or message it reads is shared with another branch, assert the specific text of
   this branch *and* the absence of the other's marker. Cannot build a failing probe? Then the
   finding is unproven — go back to 3.1 and re-judge it before fixing anything.
2. **Fix** — the minimal change, with the editing tool, on the PR's head branch.
3. **Green** — the probe from step 1 passes. **Still red after the fix? Judge the probe before the
   fix.** A probe that went red at its first assertion (the missing key) never ran the others, so
   their expectations are unproven: check each against the fixture and the code that existed before
   the fix. Measured 2026-10-03 (ui24-agent PR #73): all three post-fix failures were the probe's —
   a field the output never had, a fixture value assumed instead of read, a label the existing code
   already produced right. Bending the fix to match them would have shipped the regression.
4. **Sabotage the fix.** Loosen or revert the line(s) the fix added — the guard becomes a no-op, the
   anchored regex becomes "anywhere", the strict comparison becomes lax — and run the probes again.
   At least one must go red. If none does, the fix has no sensor: write the probe that catches the
   loosened version, then restore the fix. Prove the sabotage actually changed the file
   (`git diff` shows the loosened line) before trusting a "still green" — a sabotage that did not
   apply proves nothing.
5. **Fast suite** — the project's test command (`references/regression-testing.md`, 4.1) plus, when
   the repo has one, the cheap half of its mutation catalogue (e.g. `tests/check-mutation.sh
   --anchors` in sdd-style kits): a fix that rots a mutant's anchor fails there in seconds. Compare
   against the 4.0 baseline; a new failure is this fix's regression, fixed before moving on.
6. Mark the checklist item and only then take the next logic finding.

Shell and `awk` tooling deserve the loop most: portability bugs (zsh not splitting `$var`, `mawk`
being byte-oriented, `pipefail` turning `grep -q` into exit 141 on large input) pass every probe
written with ASCII input on the author's shell.

## Stop rule

Two regressions created by fixes **in the same neighbourhood** (same function, same parser, same
sensor) mean stop patching. Ask which **state is missing** — e.g. "the parser does not know it is
inside a code block" — and fix that once; fixing each symptom individually produces the next
symptom. Record the decision in the checklist item.

## What stays out of the loop

- Mechanical/prose findings: batched, one suite run after the batch (Phase 4 as usual).
- Expensive owner-run gates (a full mutation catalogue, a health stamp): run **once**, after every
  reviewer has posted and all rounds are fixed — never per finding.
