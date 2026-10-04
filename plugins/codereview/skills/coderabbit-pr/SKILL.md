---
name: coderabbit-pr
metadata:
  version: 4.3.7
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

It is **project-agnostic** and **reviewer-agnostic**: any repo, any supported AI reviewer.

## References

Read each one at the step that needs it:

- `references/pr-branch.md` — read at Phase 1.1, before its worktree, active-writer check and sweep.
- `references/reviewer-registry.md` — read at Phase 1.2 when a login is not in the table below, and
  at 1.3 when structuring findings: comment structure, severity markers and metadata to discard per
  reviewer, the rule for unknown bots; Phase 2: coverage per commit.
- `references/checklist-template.md` — read at Phase 2 before writing a checklist: file structure,
  resolved-item format, the zero-findings templates (a)/(b), severity mapping, the Final Result table
  and special cases (no file/line, deleted files, "Also applies to").
- `references/byte-exact-verification.md` — read at Phase 3.1 when a finding cites NUL bytes, BOM,
  zero-width or other invisible/control characters, before any verdict.
- `references/regression-testing.md` — read before the first fix of Phase 3.2 (the baseline is taken
  there) and at Phase 4: baseline format, test-command detection, comparison cases.
- `references/fix-loop.md` — read at Phase 3.2 before the first logic fix.
- `references/thread-resolution.md` — read when you reach Phase 5: the GraphQL commands that list, resolve and
  recount the review threads.
- `assets/trigger-evals.json` — read before changing the `description`: should/should-not trigger cases.

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

**How to delegate**: `Agent({ model: "sonnet", prompt: "..." })` — a tier cheaper than yours.

**Why most of this runs inline.** Fetching comments and resolving threads have one correct answer;
a subagent in the middle only adds variance and silent omission, and a run that drops a comment
looks identical to a clean one. Delegate where a model adds something: reading prose findings,
editing code; the verdict stays with the orchestrator. **Skip agent routing entirely** when the PR
has fewer than 5 comments across all reviewers.

---

## Operating Constraints

**Modifies code** on **the PR's head branch** (not necessarily the one checked out — Phase 1.1), and
never commits: the user decides when. The one tracking file per reviewer in the project root is
**ephemeral working state**, deleted in Phase 6.

**Scope discipline**: only fix issues raised by the reviewers — no unrelated refactors, improvements or style changes, even for issues you notice while reading code. Pre-existing test failures unmasked by your fixes are not yours to fix either (Phase 4).

**Error Handling**:

- **`gh` CLI not available or not authenticated**: Stop with: "The `gh` CLI is not installed or authenticated. Run `gh auth login` before using this skill."
- **PR not found**: Stop with: "PR #{n} not found or insufficient permissions."
- **No known reviewer bot posted anything at all** (on none of the three endpoints of 1.2): Stop with: "No AI review comments found on PR #{n}."
  A reviewer that posted but yielded zero actionable findings (an approval, an empty summary, "unable to review") is **not** this case: it goes through Phase 2's zero-findings path and is reported.
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

**Work on the PR's branch, without moving the user's checkout.** The branch you start on is often
*not* the PR's, and fixes made there never reach the PR. If they differ, open a **git worktree** on
`headRefName` and run everything there — never `git checkout` here: a clean tree is not an idle one
(a subagent or another session may be writing in it). Same branch, but a writer still active (a
pipeline session, a suite, a stamp)? Read-only until it exits. Then sweep stale `*-review.md` checklists.
Commands and the why: `references/pr-branch.md`.

#### 1.2 Detect Which Reviewers Are Present

```bash
for e in pulls/$PR/comments pulls/$PR/reviews issues/$PR/comments; do
  gh api "repos/$REPO/$e" --paginate --jq '[.[].user.login] | unique[]'; done
```

Union all three: a reviewer may post only a review body (Gemini's summary, a quota notice), only
inline comments, or only an issue comment (CodeRabbit on the Free plan: a walkthrough, no review —
case (b), registry). Skip one and a reviewer silently vanishes. Match the logins against the
known bots:

| Login | Reviewer |
|-------|----------|
| `coderabbitai[bot]` / `coderabbitai` | CodeRabbit |
| `copilot-pull-request-reviewer[bot]` (review object) / `Copilot` (its inline comments) | Copilot |
| `gemini-code-assist[bot]` | Gemini |
| `chatgpt-codex-connector[bot]` | Codex |

With `--reviewer`, filter to that reviewer.
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
- The projection drops `diff_hunk`, URLs, reactions and nested user objects (most bytes, per `wc -c`)
  **before** they reach any context.

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
  in the review body (Copilot: *"unable to review … reached their quota limit"*); a check stuck
  `PENDING`, or a Codex summary comment still `Running` (registry), is the same story. Recording it
  as "approved without issues" buries a coverage gap: do not count it as coverage, and say so in
  the closing report. **Coverage is per commit**, findings or not: commits after a reviewer's last
  review are (b) for it (registry).

Where it goes: **without `--keep-checklists`** (default), do **not** write a file — Phase 6 would
delete it seconds later — and carry the (a)/(b) determination into the **final report**. **With
`--keep-checklists`**, write the minimal file from the matching template.

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
   No longer matches → `[x]` — "Reviewer claim no longer applies: <what changed>". A doc-anchored
   finding about what the program does is a claim about the code that produces it: fix it there.
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

**Before the first fix, capture the test baseline** (Phase 4.0). Then **logic fixes** (guard,
branch, parser, regex, exit code): one at a time, main model, via `references/fix-loop.md`.
**Mechanical** (prose, naming): ≤5 → main model; more → cheaper-model agents in parallel by
file, given exact old → new, changing nothing else.

#### 3.3 Update Checklists

After each item (or batch), mark the checkbox and add the status line in that reviewer's file. The
incremental save is what makes the run resumable: re-running an interrupted run verifies the checked
items without re-applying fixes.

---

### Phase 4: Regression Testing

**Skip** with `--skip-tests`, and **also when Phase 3 changed no files** — with no edits there is no
"after" to compare, and any failure would be pre-existing yet look like this run caused it. Say in
the report that tests were skipped and why.

If not skipped, follow `references/regression-testing.md`: detect the test command, run it after the
fixes and compare against the 4.0 baseline. Only failures **not in the baseline** are regressions to
fix in this PR; pre-existing ones are documented in the checklists and go to a follow-up issue.
**Never silence failing tests** (`it.skip`, `if: false`, `continue-on-error: true`) to make CI green
— document and defer. After each layer of new-failure fixes, capture a fresh baseline: fail-fast
cascades can run deeper than two levels. Finally update each "Final Result" table with the counts by
status and the test results.

---

### Phase 5: Resolve GitHub Conversations

After all items are processed and tests pass, resolve **all** review threads on the PR — from every
reviewer, not only those processed in Phase 3. Run the steps directly, never delegated (commands in
`references/thread-resolution.md`).

0. **5.0** the PR head must carry the fixes (`headRefOid` == `HEAD`, nothing uncommitted); if
   not, ask the user to commit and push first;
1. **5.1** list the unresolved threads (GraphQL `reviewThreads`, `isResolved == false`);
2. **5.2** resolve each with the `resolveReviewThread` mutation, piping 5.1 into `while read` — every
   line must print `true`; anything else means the thread is still open, carry it into 5.3;
3. **5.3** count again: `unresolved: 0` is the success condition and the gate for Phase 6. Not zero →
   report which threads remain and why; never describe the run as complete.

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
never created. A project rule against deleting files (CLAUDE.md) makes the `rm` a `mv` to a
scratch directory. Skip this phase with `--keep-checklists` or in `--dry-run` (which never claims
completion).

Two rules only work as a pair — the fixed name `{reviewer}-review.md` and always deleting on success
(read `references/checklist-template.md §File naming` if tempted to rename a leftover).
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
- **Fixes on the wrong branch fail silently** — worktree on `headRefName`, never a checkout (1.1).
- **Resolve only what the PR head carries** — unpushed fix, open thread (5.0).
- **A reviewer that never ran is not a pass**, nor one behind the head (Phase 2, case b).
- **A probe of the finding does not test the fix** — sabotage it until one goes red (3.2).
- **A clean tree on the PR branch can still be busy** — another writer: read-only until it exits (1.1).
- **A doc-anchored finding may be a code defect** — a prose-only fix leaves the program lying (3.1).
- **A suggested wrapper can disarm a timeout** — under `timeout --foreground` only the `bash -c`
  wrapper dies, and the real step outlives the deadline (3.1 step 6: demonstrably wrong).
- **zsh breaks the 5.2 loop two ways** — `for id in $ids` never splits; `read … path` empties `PATH` (5.2).
