# Regression Testing — Phase 4 in full

Read this before the first fix of Phase 3.2 (the baseline in 4.0 has to be captured before any
edit), and again at Phase 4 to compare. SKILL.md keeps the skip rules and the outline; this file
carries the baseline format, the test-command detection table and the comparison cases.

## Contents

- [When to skip](#when-to-skip)
- [4.0 Capture Pre-Fix Baseline](#40-capture-pre-fix-baseline)
- [4.1 Detect Test Command](#41-detect-test-command)
- [4.2 Run and Compare Against Baseline](#42-run-and-compare-against-baseline)
- [4.3 Update Final Status](#43-update-final-status)

## When to skip

Skip if `--skip-tests` was passed.

**Also skip if Phase 3 changed no files** — zero findings, or every item resolved as
already-fixed / not-applicable. This phase compares a before and an after; with no edits
there is no after, so a run proves nothing. Two concrete costs to running it anyway: on a
large suite it is minutes of pointless work, and any failure it surfaces is pre-existing
by construction yet arrives looking like this run caused it — the exact confusion the
4.0 baseline exists to prevent. Say in the report that tests were skipped and why.

## 4.0 Capture Pre-Fix Baseline

**Run the project's test command before applying any review fixes — in practice at the start of Phase 3.2, once the verdicts say something will change.** The step lives here because it pairs with the comparison in 4.2, not because it runs after Phase 3. Save the pass/fail counts and the list of failing test names. This is your **baseline** of pre-existing latent failures.

Why this matters: when CI is broken by an early-step failure (lint syntax error, missing config, broken `npm exec`), GitHub never reaches the test step — so failing tests in the test step are invisible until the early step is fixed. After your fixes unblock CI, those latent failures **appear as if they were caused by your edits**, but they were always there.

Without a baseline, Phase 4.2 cannot tell "regression caused by my fix" from "pre-existing latent unmasked by my fix" — and the skill ends up trying to fix unrelated bugs, expanding scope uncontrollably.

**A long suite does not have to block the fixes.** Run the baseline in a detached worktree of the
PR head (`git worktree add --detach <scratch> HEAD`, launched detached from the shell), and write
the 3.2 probes in the checkout meanwhile: the baseline still measures the head, never a tree being
edited. Only when the suite shares no state outside the tree (a port, a database, a fixed `/tmp`
path); remove the worktree after. Measured 2026-10-05 (sdd_agents PR #222): 1839 ok in ~8 min in
the worktree while the first red probe ran in the checkout.

**Save the baseline as:**

```
baseline_pass: <number>
baseline_fail: <number>
baseline_failing_tests:
  - <test 1 name>
  - <test 2 name>
  ...
```

If the baseline already shows N>0 failures, document them in each `{reviewer}-review.md` checklist (a "Pre-existing latent failures" subsection) BEFORE applying any fixes. They are out of scope for this run.

## 4.1 Detect Test Command

| Priority | Detection | Command |
|----------|-----------|---------|
| 0 | The project **declares** its gate: `TEST_CMD` in `.sdd/config.sh`, or a suite named in `CLAUDE.md` / `AGENTS.md` (e.g. `tests/run-all.sh`) | That command — the declared gate beats detection; a bash/markdown kit has none of the files below and would otherwise fall to "ask" |
| 1 | `package.json` has `scripts.test` | `npm test` |
| 2 | Monorepo with multiple `package.json` | `npm test` in each package with modified files |
| 3 | `*.sln` or `*.csproj` exists | `dotnet test` |
| 4 | `Cargo.toml` exists | `cargo test` |
| 5 | `pyproject.toml` or `setup.py` | `pytest` |
| 6 | `go.mod` exists | `go test ./...` |
| 7 | `Makefile` has `test` target | `make test` |
| 8 | None detected | Ask the user |

## 4.2 Run and Compare Against Baseline

Execute the test command after applying fixes. Compare against the Phase 4.0 baseline:

- **All pass and baseline was 0**: update all checklists with "All tests passed ({n} tests)."
- **Same failures as baseline (no new fails, no fewer fails)**: pre-existing latent — note in checklists, **do NOT attempt to fix in this PR**. Open a follow-up issue with the error signature and a link to this PR. Scope discipline is the priority.
- **New failures (failing tests not in baseline)**: caused by your fixes — diagnose and correct. These ARE regressions.
  **Rule out a flake first:** run the failing test alone a few times and its module once — from the
  directory and with the discovery flags the suite uses — and check whether it imports what you
  changed. Measured 2026-10-04 (projeto-final-vdr PR #3): one `tearDown` `PermissionError`
  (WinError 32, a lock file a helper process still held) in a full run, 30 of 30 green alone, in a
  module that does not import the fixed file; run from the repository root without `-s tests`, the
  same test "failed" 20 of 20 at import, which measures the command, not the test. A flake is not
  this PR's to fix: record it with that evidence, like a pre-existing failure, and run the full
  suite again before the Final Result.
- **Fewer failures than baseline**: your fixes accidentally fixed something. Note it but don't claim credit; the fix may be incidental and could regress later.
- **Mixed (some pre-existing + some new)**: separate the two lists. Fix only the new failures in this PR. Pre-existing go to the follow-up issue.

**Do not silence failing tests** (e.g., `it.skip`, `if: false` on the workflow step, `continue-on-error: true`) to make CI green. Document and defer.

**Cascade-aware rerun**: if your fixes uncovered new failures (the "new failures" branch above), rerun the baseline after addressing them — fail-fast cascades can have more than 2 levels (bug 1 masks bug 2 masks bug 3), and the second bug surfaced is not necessarily the last. After each layer of fixes, capture a fresh baseline before declaring victory.

## 4.3 Update Final Status

Update the "Final Result" table in each `{reviewer}-review.md` with:
- Count of items by status (Fixed, Already fixed, Not applicable, Pending)
- Test results
