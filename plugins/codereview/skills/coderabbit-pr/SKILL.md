---
name: coderabbit-pr
metadata:
  version: 4.0.1
description: Resolves AI review comments on a GitHub PR — auto-detects CodeRabbit, Copilot, Gemini, Codex; creates per-reviewer checklists, verifies findings against current code (with byte-exact inspection when reviewers cite invisible/control characters), applies fixes, runs regression tests, resolves GitHub conversations, then cleans up its own checklist files. Triggers — coderabbit, copilot review, gemini review, codex review, fix PR review.
---

## User Input

```text
$ARGUMENTS
```

Parse the user input before proceeding:

- **PR number** (required): integer, e.g. `49` or `#49`
- **Optional flags**:
  - `--skip-tests` — skip Phase 4 (regression testing)
  - `--dry-run` — verify only, do not apply fixes
  - `--reviewer <name>` — process only a specific reviewer (e.g., `--reviewer coderabbit`). Default: all detected reviewers.
  - `--keep-checklists` — keep the `{reviewer}-review.md` files after a successful run instead of deleting them (Phase 6). Use when you want the checklist as a durable audit artifact.

If `$ARGUMENTS` is empty or does not contain a PR number, ask: "What is the PR number?"

## Goal

Extract all review comments left by AI reviewers on a GitHub PR, create a structured checklist file **per reviewer** (e.g., `coderabbit-review.md`, `copilot-review.md`), verify each comment against the current code, fix valid issues, run regression tests, and resolve all GitHub conversations. Every item ends resolved with a justification.

This skill is **project-agnostic** and **reviewer-agnostic** — it works with any repo and any supported AI reviewer.

## References

Read each one at the step that needs it:

- `references/reviewer-registry.md` — read at Phase 1.2 when a login is not in the table below, and
  at 1.3 when structuring findings: comment structure, severity markers and metadata to discard per
  reviewer, plus the rule for unknown bots.
- `references/checklist-template.md` — read at Phase 2 before writing a checklist: file structure,
  resolved-item format, the zero-findings templates (a)/(b), severity mapping, the Final Result table
  and special cases (no file/line, deleted files, "Also applies to").
- `references/byte-exact-verification.md` — read at Phase 3.1 when a finding cites NUL bytes, BOM,
  zero-width or other invisible/control characters, before any verdict.
- `references/regression-testing.md` — read before the first fix of Phase 3.2 (the baseline is taken
  there) and at Phase 4: baseline format, test-command detection, comparison cases.
- `references/thread-resolution.md` — read when you reach Phase 5: the GraphQL commands that list, resolve and
  recount the review threads.

---

## Model Routing Strategy

| Phase | Task | Model |
|-------|------|-------|
| 1.1–1.3 | Repo/branch/PR context, reviewer detection, comment extraction (`--jq` projection) | **Run inline** |
| 1.3 | Structure findings (interpretation of prose) | **Cheaper model**, only past the size threshold |
| 2 | Create checklist files from structured data | Main model |
| 3 | Verdict on each comment — is the issue real, does the spec support it? | **Main model** |
| 3 | Apply code fixes decided by the main model | **Cheaper model** (only above 5 fixes) |
| 4 | Run tests | Main model |
| 5–6 | Resolve GitHub threads (mutations + a count that must reach zero), delete checklists | **Run inline** |

**How to delegate**: the `Agent` tool with `model` set to a cheaper tier than the one you run on,
e.g. `Agent({ model: "sonnet", prompt: "..." })`.

**Why most of this runs inline.** Fetching comments and resolving threads have one correct answer;
a subagent in the middle only adds variance, latency and silent omission, and a run that drops a
comment looks identical to a clean one. Determinism here is about trusting the result. Delegation stays where a model adds something: reading prose findings, judging
correctness (the strongest model in the session — the orchestrator), editing code. **Skip agent
routing entirely** when the PR has fewer than 5 comments across all reviewers.

---

## Operating Constraints

**Modifies code** on **the PR's head branch** (not necessarily the one checked out — Phase 1.1), and
never commits: the user decides when. The one tracking file per reviewer in the project root is
**ephemeral working state**, deleted in Phase 6.

**Scope discipline**: only fix issues raised by the reviewers — no unrelated refactors, improvements or style changes, even for issues you notice while reading code. Pre-existing test failures unmasked by your fixes are not yours to fix either (Phase 4).

**Error Handling**:

- **`gh` CLI not available or not authenticated**: Stop with: "The `gh` CLI is not installed or authenticated. Run `gh auth login` before using this skill."
- **PR not found**: Stop with: "PR #{n} not found or insufficient permissions."
- **No known reviewer bot posted anything at all** (nothing in `/comments` *and* nothing in `/reviews`): Stop with: "No AI review comments found on PR #{n}."
  This is **not** the same as a reviewer that posted but yielded zero actionable findings — an approval, a summary with no issues, or "unable to review". Those go through Phase 2's zero-findings path and must be reported, because case (b) there is a coverage gap the user needs to hear about. Stopping on them would swallow the most important thing the run learned.
- **File no longer exists**: Mark as `[x] File removed — not applicable`.
- **Line not locatable** (heavy modifications since review): Use context clues (function name, surrounding code) to locate. If truly unmappable: `[x] Not locatable in current code — requires manual review`.
- **Test command not detected**: Ask the user which command to use. Never skip tests silently.

---

## Execution Steps

### Phase 1: Detect Reviewers & Extract Comments

#### 1.1 Detect Repository, Branch, and Leftover State

```bash
gh auth status                                          # must be authenticated
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)   # owner/repo
PR=<the PR number from the user input>
git branch --show-current
gh pr view "$PR" --json headRefName -q .headRefName
```

**Confirm you are on the PR's branch.** The branch you start on is frequently *not* the PR's — the
user may have moved on since opening it, and fixes applied there never reach the PR, with nothing
failing loudly. If the two differ: **working tree clean** → `git checkout <headRefName>` and tell the
user you switched; **dirty** → stop and report (let the user stash or commit first). When the run
ends, state which branch the edits landed on.

**Sweep leftover checklists.** `*-review.md` files in the project root are this skill's scratch space
from a previous run. One whose header names a **different** PR is stale: delete it rather than read
it as if it described the current PR (Phase 3's cross-reviewer check consults these files).

```bash
grep -l "Review — PR #" *-review.md 2>/dev/null | while read -r f; do
  head -5 "$f" | grep -q "PR #${PR}\b" || { echo "stale, removing: $f"; rm -- "$f"; }
done
```

#### 1.2 Detect Which Reviewers Are Present

```bash
gh api "repos/$REPO/pulls/$PR/comments" --paginate --jq '[.[].user.login] | unique[]'
gh api "repos/$REPO/pulls/$PR/reviews"  --paginate --jq '[.[].user.login] | unique[]'
```

Query **both** endpoints and union the results: a reviewer can post only a review body (Gemini's
summary, a bot reporting it could not run) and another only inline comments — reading one endpoint
silently drops a reviewer. Match the logins against the known bots:

| Login | Reviewer |
|-------|----------|
| `coderabbitai[bot]` / `coderabbitai` | CodeRabbit |
| `copilot-pull-request-reviewer[bot]` (review object) / `Copilot` (its inline comments) | Copilot |
| `gemini-code-assist[bot]` | Gemini |
| `chatgpt-codex-connector[bot]` | Codex |

With `--reviewer`, filter to that reviewer. No known reviewer → stop with the "no comments" error.
Report: "Found reviews from: {list of reviewers}. Processing {N} reviewer(s)."

#### 1.3 Fetch & Parse Comments Per Reviewer

Separate **extraction** (mechanical, fixed) from **interpretation** (needs a model). **Extraction —
always run these directly:**

```bash
# Inline comments (attached to diff lines)
gh api "repos/$REPO/pulls/$PR/comments" --paginate --jq '.[] |
  "=====\nID: \(.id)\nAUTHOR: \(.user.login)\nPATH: \(.path)\nLINE: \(.line // .original_line)\nBODY:\n\(.body)\n"'

# Review bodies (where CodeRabbit and Gemini put most findings)
gh api "repos/$REPO/pulls/$PR/reviews" --paginate --jq '.[] | select(.body != "") |
  "=====\nID: \(.id)\nAUTHOR: \(.user.login)\nSTATE: \(.state)\nBODY:\n\(.body)\n"'
```

- `\(.line // .original_line)` — `line` comes back **null** once the diff around a comment goes stale
  (force-push, rebase, later commits); without the fallback those findings lose their anchor and get
  misfiled as "not locatable".
- `select(.body != "")` — approvals and review stubs carry an empty body; keeping them produces
  phantom findings.
- The projection drops the 30-50KB of `diff_hunk`, URLs, reactions and nested user objects **before**
  they reach any context — instead of a subagent absorbing them and hoping its summary is faithful.

**Interpretation — delegate only when the output is genuinely big** (roughly >1500 lines, or 3+
reviewers each with a long review body): hand *that text* to a cheaper-model agent per reviewer, in
parallel. Otherwise structure it yourself. Either way, produce a **numbered list** with, per finding:
sequential number; severity (CRITICAL/HIGH/MEDIUM/LOW; for the markers, `references/reviewer-registry.md`); file
path and line; title (bold text or first sentence); 1-2 sentence summary; whether a code suggestion is
included; source (inline/review-body/nitpick).

**Deduplication**: match by file path + line range + first 100 chars of title; a finding both inline
and in the review body keeps the inline version (more precise line); findings sharing a root cause
stay separate items with "Related to item #N". **Discard** pure metadata: walkthrough summaries,
paused review notices, "Actionable comments posted" headers, `<!-- fingerprinting:... -->` blocks.
A reviewer with 0 findings after filtering goes to Phase 2's zero-findings path.

---

### Phase 2: Create Checklist Files

For each reviewer with findings, write `{reviewer}-review.md` in the project root
(`coderabbit-review.md`, `copilot-review.md`, `gemini-review.md`, `codex-review.md`, or
`{bot-login}-review.md` for an unknown bot), following `references/checklist-template.md`: items by
severity (CRITICAL > HIGH > MEDIUM > LOW), each `- [ ]` with number, severity tag, file:line, title and
a 1-2 sentence summary; pre-addressed items noted; a "Final Result" table at the end, all Pending.

**Zero findings — first work out *why*.** The two causes look identical in the data and mean
opposite things, and the determination is mandatory: it is the difference between "this PR passed
review" and "nobody looked at this PR".

- **(a) It reviewed and found nothing** — a genuine pass.
- **(b) It never actually ran** — quota exhausted, bot error, review still pending. Bots announce it
  in the review body (e.g. *"Copilot was unable to review this pull request because the user who
  requested the review has reached their quota limit"*), and a check that sits `PENDING` forever is
  the same story. Recording it as "approved without issues" is false and buries a coverage gap. Do
  not count a (b) reviewer as coverage, and say so in the closing report.

Where it goes: **without `--keep-checklists`** (default), do **not** write a file — Phase 6 would
delete it seconds later — and carry the (a)/(b) determination into the **final report**. **With
`--keep-checklists`**, write the minimal file from the matching template (if so, in
`references/checklist-template.md`).

---

### Phase 3: Verify and Fix Each Comment

Process every checklist item across all reviewer files, grouped by file to minimize reads — one file
may have findings from several reviewers.

#### 3.1 Analysis (Main Model)

For each item (or group of items in the same file):

1. **Read the current code** at the referenced file and line (with ~30 lines of context).
   1.1. **Byte-exact verification** — if the reviewer cites NUL bytes, BOM, zero-width or other
   invisible/control characters, `Read` renders them as plain whitespace and misleads the verdict.
   Confirm against the bytes (`awk 'NR==<line>' <file> | od -c | head`) before calling it a false
   positive; the full procedure is in `references/byte-exact-verification.md`.
   1.5. **Verify referenced state** — a cited file path, line, runtime behavior or external artifact
   ("as documented in X", "see previous session", a cached plan, an old issue, "fixed in commit Y")
   is checked against the current state **before** accepting the diagnosis: the PR diff and live code
   are authoritative, and the comment may describe an obsolete snapshot (force-push, rebase, age).
   No longer matches → `[x]` — "Reviewer claim no longer applies: <what changed>".
2. **Check project specs/docs** if the comment questions a design decision. Many "issues" flagged by
   AI reviewers are by-design choices documented in specs, data models or CLAUDE.md — AI reviewers
   lack full project context. Verify the reviewer isn't wrong before marking "Fixed".
3. **Recalibrate severity** after reading the code — reviewers often default to MEDIUM or assign none
   (Copilot, Codex): **CRITICAL** data loss, security vulnerability, crash in production path;
   **HIGH** broken feature flow, silent data corruption, regression from a recent commit; **MEDIUM**
   incorrect edge-case behavior, inconsistency, missing validation; **LOW** style, naming, docs,
   nitpick. Update the tag in the checklist when it changes.
4. **Cross-reviewer check**: if another reviewer's checklist already resolved the same issue, mark
   `[x]` — "Already fixed — see {other-reviewer}-review.md #{item number}" (no duplicate work, and an
   audit trail across files).
5. **Evaluate**: does the issue still exist? Is the concern valid?
6. **Decide**:

   | Situation | Action | Checklist Status |
   |-----------|--------|-----------------|
   | Issue does not exist (already fixed or code rewritten) | None | `[x]` — "Already fixed" |
   | Issue fixed by another reviewer's round | None | `[x]` — "Already fixed — see {reviewer}-review.md #{N}" |
   | Issue exists, suggestion is valid | Prepare fix description | `[x]` — "Fixed" |
   | Issue exists, better fix available | Prepare alternative fix | `[x]` — "Fixed (alternative approach: {reason})" |
   | Issue exists but code is actually correct | None | `[x]` — "Not applicable: {reason}" |
   | Design decision documented in spec/docs | None | `[x]` — "Not applicable — by design per {spec reference}" |
   | `--dry-run` mode | None (verify only) | `[x]` — "Verified: {needs fix / already fixed / not applicable}" |

   Follow the reviewer's suggestion unless it is demonstrably wrong or contradicts project specs, and
   explain alternative approaches. Match the project's coding conventions.

#### 3.2 Fix Execution

**Before the first fix, capture the test baseline** (Phase 4.0, in `references/regression-testing.md`).
Then: **5 or fewer fixes** → apply them directly in the main model; **more than 5** → cheaper-model
agents in parallel, grouped by file, each receiving the file path, the fixes (exact
old_string → new_string or clear descriptions) and the instruction to change nothing beyond them.

#### 3.3 Update Checklists

After each item (or batch), mark the checkbox and add the status line in that reviewer's file. The
incremental save is what makes the run resumable: re-running an interrupted run verifies the checked
items without re-applying fixes.

---

### Phase 4: Regression Testing

**Skip** with `--skip-tests`, and **also when Phase 3 changed no files** — with no edits there is no
"after" to compare, and any failure would be pre-existing yet look like this run caused it. Say in
the report that tests were skipped and why.

If not skipped, follow `references/regression-testing.md`: detect the test command (npm, dotnet,
cargo, pytest, go, make — or ask), run it after the fixes and compare against the 4.0 baseline. Only
failures **not in the baseline** are regressions to fix in this PR; pre-existing ones are documented
in the checklists and go to a follow-up issue. **Never silence failing tests** (`it.skip`,
`if: false`, `continue-on-error: true`) to make CI green — document and defer. After each layer of
new-failure fixes, capture a fresh baseline: fail-fast cascades can run deeper than two levels.
Finally update each "Final Result" table with the counts by status and the test results.

---

### Phase 5: Resolve GitHub Conversations

After all items are processed and tests pass, resolve **all** review threads on the PR — from every
reviewer, not only those processed in Phase 3. Run the three steps directly (commands in
`references/thread-resolution.md`, to read when you reach this phase): a delegated batch that
silently skips a thread reports success just as convincingly as one that didn't.

1. **5.1** list the unresolved threads (GraphQL `reviewThreads`, `isResolved == false`);
2. **5.2** resolve each with the `resolveReviewThread` mutation, piping 5.1 into `while read` (a
   `for id in $ids` loop never splits in zsh) — every line must print `true`;
   anything else means the thread is still open, carry it into 5.3;
3. **5.3** count again: `unresolved: 0` is the success condition and the gate for Phase 6. Not zero →
   report which threads remain and why; never describe the run as complete. `reviewThreads(first: 100)`
   caps at 100 — on a PR that busy, page through and say so.

Update each checklist's `### Conversations` block (total threads, resolved in this run, previously resolved).

---

### Phase 6: Clean Up the Checklist Files

The checklists are scratch space: left behind, the next run's cross-reviewer check (3.1 step 4)
reads an old PR's file as current, and they clutter `git status`. Once 5.3 reports `unresolved: 0` and
the report is written, delete them by the header this skill writes — which covers an unknown
reviewer's `{bot-login}-review.md` and leaves unrelated docs like `security-review.md` alone:

```bash
grep -l "Review — PR #${PR}\b" *-review.md 2>/dev/null | while read -r f; do
  echo "removing: $f"; rm -- "$f"
done
```

A bare `rm -f *-review.md` is the tempting one-liner and the wrong answer: it deletes files this skill
never created. Skip this phase with `--keep-checklists` or in `--dry-run` (which never claims
completion).

Two rules only work as a pair — the fixed name `{reviewer}-review.md` and always deleting on success
(read `references/checklist-template.md §File naming` if tempted to rename a leftover). Cleanup runs
only on the success path, so an interrupted run leaves its checklists where a resume needs them.
If the project has no `.gitignore` entry for these, suggest `*-review.md` as defence in depth.

**The audit trail lives instead** in the resolved GitHub threads, the PR diff and the commit message;
the final report carries the findings table, since the file it came from is gone.

---

## Gotchas

- **Every comment ends `[x]` with a justification** — "Never skip" is checked by 5.3's
  `unresolved: 0`, not by memory.
- **Verify before trust**: reviewer claims are hypotheses until the live diff and code confirm them
  (3.1 step 1.5) — the anti-silencing principle of the 4.0 baseline, in another direction.
- **`Read` is not byte-faithful**: a control-character finding judged from `Read` output is a false
  "not applicable" waiting to happen (3.1 step 1.1).
- **Fixes on the wrong branch fail silently** — confirm `headRefName` first (1.1).
- **A reviewer that never ran is not a pass** (Phase 2, case b).
