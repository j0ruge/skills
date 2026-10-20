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
   A probe of something the fix both **sets and later clears** (a marker, a flag, a lock released on
   success) is green before the fix by construction: "gone at the end" also holds when it never
   existed. Assert the set state mid-test, then its absence. Step 4's "at least one goes red" does
   not catch it, because the other probes go red and hide the empty one. Measured 2026-10-14
   (digital_service_report_api PR #92, `01a7c87`): "a successful refresh clears the QUEBRADO marker"
   stayed green with the marker write sabotaged while three others went red; one assertion of the
   marker in the middle made that sabotage red too.
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
   loosened version, then restore the fix. Prove the sabotage actually changed the file before
   trusting a "still green" — a sabotage that did not apply proves nothing. Count the loosened text
   in the file itself (`grep -cF '<loosened text>' <file>`), not with `git diff | grep '^+'`: a shell
   hook can swap in `rtk git diff`, which indents every changed line (`  +…`), so the grep finds
   nothing on a file that did change. Measured 2026-10-19 (magic_tutor PR #8): on the same file,
   `git diff` and `rtk proxy git diff` piped to `grep '^+.*2027'` printed the line, `rtk git diff`
   printed nothing (rc 1), and `grep -c` counted 1. The other way round, a sabotage that breaks the syntax proves nothing
   either: the program dies at whatever runs first. Loosen into valid code, and read the red —
   it must be the probe of the rule you loosened. Measured 2026-10-05 (sdd_agents PR #222):
   `tbl = 1` → `:` is not awk, and the selftest went red at an unrelated probe; redone as
   `tbl = 0`, it went red at the probe of the rule.
   **An interrupted run leaves the sabotage in the file.** The restore runs after the probes, so a run
   killed in between skips it, and with the fix still uncommitted the tree already shows a diff:
   `git status` cannot tell the fix from the sabotage. After any interruption, count each loosened
   text again (`grep -cF`): every count must be 0 before the suite is trusted. Measured 2026-10-19
   (magic_tutor PR #21): the session ended during the last of a run of five sabotages, `"jogo": 0`
   stayed in `monitor/replays.py`, and the count found it.
   **A window no probe can stop in** is the one exit: the sabotage only reorders effects inside a
   gap no deterministic test reaches, such as two assignments in a row in one shell process, which
   only a signal lands between. Write the invariant down instead, in three places: a comment on the
   lines it protects, the commit message, and the closing report, each naming the sabotage that
   stayed green and why no test reaches it. "The test was hard to write" is not such a reason.
   Measured 2026-10-17 (jrc-libs PR #4, `release.sh`): 19 of 20 sabotages went red; the green one
   moved `publica=1` after `armado=0`, right after the push, a gap that only a Ctrl-C lands in. The
   comment sits in the exit trap that reads both flags, and commit `fc202d0` says "Não tem sensor".
5. **Fast suite** — the project's test command (the one detected for the 4.0 baseline) plus, when
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
