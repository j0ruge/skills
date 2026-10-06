---
name: codereview
metadata:
  version: 2.13.0
description: Pre-PR review with severity grading and tiered model routing. Detects TOCTOU races, accessibility gaps, hardcoded secrets, silent-blinding sensors (swallowed errors, negative verdicts, gates aimed at the wrong file), docs drift, and dead code via a whole-repo sweep. Report carries an Overall Grade table + Recommended Actions. Stack-agnostic, TypeScript/React defaults. Triggers — code review, pre-PR, secrets scan, accessibility audit, dead code, silent failure, code health.
---

## User Input

```text
$ARGUMENTS
```

Read the user input before proceeding (if not empty). Valid inputs:

- Empty: full review of all changed files
- Focus area: `security`, `performance`, `types`, `bugs`, `tests`, `docs`, `a11y`, `race-conditions`, `dead-code`
- File path or glob: review only matching changed files
- Key-value overrides: `baseDir=app/ fileExtensions=ts,js`
- Focus in prose ("look at the separator") or a review handoff's risk list (Phase A): run `full`, prompts
  unchanged; answer each named point in Phase C and say where it was checked

Defaults are `baseDir=src/`, `fileExtensions=ts,tsx`, `frameworkPatterns=react`, tests `**/*.{test,spec}.{ts,tsx}` and `**/test/**`, UI_LIB `src/components/ui/**`, `prisma/**`, `**/generated/**`, CONFIG `*.config.*`, `tsconfig*`, `.env*`, `package.json`.

## Goal

Perform a comprehensive, automated code review of all changes in the current branch compared to the base branch. Produce a structured Markdown report with severity-rated findings, test coverage assessment, and a final grade.

This skill is **stack-agnostic**. Defaults target TypeScript/React but all values are configurable.

## References

The agents read their own contract by absolute path (`{SKILL_DIR}/references/…`); the orchestrator
reads a file only at the step that needs it:

- `references/configuration.md` — only when `$ARGUMENTS` carries `key=value` overrides or the stack
  is not TypeScript/React: override syntax and the presets (Python, Vue, Node, .NET, shell).
- `references/per-file-agent.md` — read it yourself only if Phase B runs inline (≤3 CODE files):
  the Phase B agent contract (batch loading, scope, focus mapping, return format).
- `references/sweep-agent.md` — read it yourself when the sweep runs inline or the agent under-reports
  and you redo the deepsearch: the Phase B2 contract (the two buckets, guardrails, return template).
- `references/detection-passes.md` — read it yourself when a phase runs inline, and in Phase C for the
  recalibration rules and the pass 6.10 remediation block (the agents load it on their own): every
  pass (Zen 5.x, 6.1–6.12) and its severity rules.
- `references/toctou-patterns.md` — the TOCTOU catalog with code examples. Agents load it only for
  check-then-act shapes; read it in Phase C when a race spans files (check in one, act in another).
- `references/report-template.md` — read at Phase C step 10, before writing the report.

---

## Model Routing Strategy

| Phase | Task | Runs in | Why |
|-------|------|---------|-----|
| A | Git context, file classification, test mapping, secrets pre-scan | **inline** (main session) | Fixed commands with one right answer |
| B | Per-file analysis (detection passes) | **sonnet** agents, in parallel | Pattern matching on code, no deep reasoning |
| C | Cross-file review, severity calibration, report | **Main model** (whatever the session runs) | Judgment, cross-references, a coherent report |

**≤3 CODE files** → skip routing and run Phase B inline too; the agent overhead isn't worth it.

**The `model` field makes the routing real.** An Agent call without it inherits the main model and bills the same per-file analysis at 2.5× to 5× Sonnet's rate. Pass `model: "sonnet"` on every Phase B and B2 call, and read the model back in the report's Cost footprint line.

---

## Operating Constraints

**Read-only.** This skill identifies issues and suggests fixes in the report; it does not apply them. Don't modify, create, or delete files, and don't run destructive commands — everything it runs (git, grep, the secrets script, dead-code tooling) is a pure read. The only output is the structured report in the conversation.

## Error Handling

- **Git command failures**: include the exact failing command and stop immediately.
- **File read failures**: skip the file and record it as `Could not analyze: {filename} ({reason})`.
- **Context / token exhaustion**: finish analyzing files already processed, note truncation, proceed to report.
- **Timeout**: prioritize CRITICAL/HIGH checks on remaining files, skip MEDIUM/LOW.

Regardless of failures, always produce a final report listing all files analyzed and all failures.

---

## Execution Phases

### Phase A: Git Context, File Classification & Secrets Pre-Scan (inline, main session)

Every step is a fixed command with one right answer, so it runs inline, not in an agent: an agent only adds variation, latency and the chance of a silently dropped field — and without the secrets pre-scan JSON the F-grade gate goes blind. Outputs are small.

Apply any `$ARGUMENTS` overrides before classifying, and keep the raw outputs. Three Bash turns cover steps 1–8 — (1) steps 1–3, base-branch detection as one fallback chain, plus this skill's version for the Cost footprint (`sed -n 's/^  version: //p' {SKILL_DIR}/SKILL.md`), `git ls-files '*handoff*'` and, from a plugin cache, the `installPath` in `~/.claude/plugins/installed_plugins.json`: a `{SKILL_DIR}` outside it is a stale copy if `diff -rq` differs (ask for `/reload-plugins`); (2) step 4; (3) steps 5–8 as parallel calls in one message — because every extra orchestrator turn is a main-model round-trip over the whole session context:

1. Verify git repo:  `git rev-parse --is-inside-work-tree`
2. Detect base branch (try: origin HEAD symbolic-ref, then main, then master)
3. Current branch: `git rev-parse --abbrev-ref HEAD`
4. Merge base:  `git merge-base {BASE_BRANCH} HEAD`, or the base commit the user names (`base=<sha>`, even in prose); an end other than `HEAD` is `head=<sha>` (configuration.md)
5. Changed files: `git diff {MERGE_BASE}...HEAD --name-only`
6. Diff stats:  `git diff {MERGE_BASE}...HEAD --stat`
7. Commit log:  `git log {MERGE_BASE}..HEAD --oneline --no-decorate`
8. Secrets pre-scan — runs on every review, whatever its size or focus:
   `git diff {MERGE_BASE}...HEAD --unified=0 | bash {SKILL_DIR}/scripts/scan_secrets.sh`
   (`{SKILL_DIR}` = absolute path of this SKILL.md's directory). It prints JSON `{findings:[...], scanners:[...], errors:[...]}`; keep it verbatim as `SECRETS_PRESCAN`, the authoritative source for Phase C's Secrets Detection table and F-grade gate. A crash or non-JSON output means the scan did not run: warn the user and re-run it — an absent payload is never "scan returned clean".

Classify each changed file:
- EXCLUDED: lock files, node_modules, dist, build, .next, min files, binaries, .claude/ (unless the user names the path)
- CODE: source files matching {fileExtensions} in {baseDir}, excluding tests and generated; an extensionless executable counts when its shebang runs one of those languages (`bin/tool`, `#!/usr/bin/env bash`)
- UI_LIB: files in {generatedDirs}
- TESTS: files matching {testFilePatterns}
- CONFIG: files matching {configFilePatterns}
- DOCS: *.md, *.txt
- STYLES: CSS/SCSS/LESS

For each CODE file, check test coverage by probing candidate test file paths — same dir (`{Base}.test.{ext}`, `{Base}.spec.{ext}`), a `__tests__` sibling, then the project test root, then a changed test that imports it — and record it as WITH_TESTS / STALE_TESTS / NO_TESTS. Probe all CODE files in one shell loop (one Bash call that prints `path|status` per file), not one call per file, in bash with `nullglob`: zsh aborts an unmatched glob.

Phase A hands Phases B and C: BASE_BRANCH, BRANCH_NAME, MERGE_BASE, DIFF_STAT, COMMIT_LOG, the FILES list (path, category, test_status), COUNTS per category, and SECRETS_PRESCAN.

If CHANGED_FILES empty, dirty `git status --porcelain` → `worktree` mode (`references/configuration.md`). Both empty → output "No changes detected between this branch and `{BASE_BRANCH}`." and stop — unless the user scoped paths: then empty is a pathspec error (read configuration.md §Path-scoped reviews).

If more than 15 CODE files, prioritize by change size (diff stat lines). Note deprioritized files.

### Phase B: Per-File Analysis (sonnet agents, parallel)

For each CODE file (or group of 2-3 small files sharing imports) — and each changed TESTS file on a test-quality focus (6.12) — **spawn a sonnet agent** to analyze it. Launch all agents **in parallel**, in one message.

Each agent reads its instructions itself, when it starts, from `{SKILL_DIR}/references/per-file-agent.md`, so every agent gets the same contract. Emit only the launch prompt below, placeholders filled — nothing added (no themes, framing or reproduction requests: those come back marked `needs reproduction`), nothing removed. `model: "sonnet"` on every call.

```
Agent(model: "sonnet", prompt: "
Start with ONE batch of parallel tool calls: Read {SKILL_DIR}/references/per-file-agent.md,
Read {SKILL_DIR}/references/detection-passes.md, run `git diff {MERGE_BASE}...HEAD -- {FILE_PATH}`,
and Read {FILE_PATH}. Then follow per-file-agent.md exactly — it carries your instructions,
scope and output format.

- Repository: {REPO}
- Branch: {BRANCH_NAME} → {BASE_BRANCH}
- Merge base: {MERGE_BASE}
- Framework: {frameworkPatterns}
- File: {FILE_PATH} (category: {CATEGORY})   — one line per file in the group
- Focus area: {FOCUS or 'full'}
- Skill dir: {SKILL_DIR}
- Hard rules: {CLAUDE.md prohibitions, verbatim, or none}
")
```

The agent returns a numbered findings list (`N. [SEVERITY] {category} — {file}:{line} — {title}`, with Description and Suggestion), or `No findings for {FILE_PATH}`, and ends with `Tool calls: … | Files read in full: …` and `END_OF_FILE_REVIEW`.

**Grouping**: files that import from each other share an agent when possible (max 3), which catches intra-group issues without the main model. A **TOCTOU** race spanning files (service reads, controller acts) is flagged single-file with "cross-file verification needed"; Phase C judges it.

### Phase B2: Dead Code Sweep (sonnet agent, parallel)

Spawn **one dedicated agent** for pass 6.9 (Dead Code & Unused Symbols), **in the same parallel batch** as the Phase B agents. It is separate because dead code is a **whole-repo reference-graph** question: a per-file agent sees one file and cannot tell whether an exported symbol is referenced elsewhere. This agent gets the changed-file list, the diff, and grep/tooling access to the whole repo.

**When to run it:**
- **Full review** (empty `$ARGUMENTS`) → run it, with Bucket A only — what this PR introduced or orphaned.
- **Bucket B is opt-in**: the repo-wide pass over pre-existing dead code (`knip`/`ts-prune`/`vulture`…, capped) runs only on focus `dead-code` or `sweep=full`. It was the expensive part of the sweep and none of it belongs to the PR; the report says in one line how to get it.
- Focus `dead-code` → run it and skip the per-file passes (the only analysis). Focus `bugs` → run it (dead code often masks or accompanies bugs).
- Narrow focuses (`security`, `a11y`, `types`, `performance`, `docs`, `tests`, `race-conditions`) → **skip it.** Unlike 6.10, dead code is hygiene, not a gate; in a focused security review it is noise.
- **≤3 CODE files** (routing skipped) → run the sweep **inline in the main model**.

**Output discipline**: the orchestrator sees only the agent's **final assistant message**, never its grep/tool outputs — so that message is the filled return template from `sweep-agent.md` (ending in `END_OF_DEAD_CODE_SWEEP`), not "done". Launch prompt, placeholders filled:

```
Agent(model: "sonnet", prompt: "
Start with ONE batch of parallel tool calls: Read {SKILL_DIR}/references/sweep-agent.md,
Read {SKILL_DIR}/references/detection-passes.md (pass 6.9), and run `git diff {MERGE_BASE}...HEAD`.
Then follow sweep-agent.md exactly — it carries the two buckets, the guardrails and the
return template.

- Repository root: {REPO}
- Branch: {BRANCH_NAME} → {BASE_BRANCH}
- Merge base: {MERGE_BASE}
- Framework: {frameworkPatterns}
- Changed CODE/CONFIG files: {LIST_OF_CHANGED_FILES}
- Focus area: {FOCUS or 'full'}
- Sweep: {full | pr}   — `full` only when `$ARGUMENTS` carries `sweep=full`
- Skill dir: {SKILL_DIR}
- Hard rules: {CLAUDE.md prohibitions, verbatim, or none}
")
```

Under-report (no `END_OF_DEAD_CODE_SWEEP`, or a bare status sentence) → re-run the grep deepsearch inline for the changed files; unlike the secrets gate, a missing dead-code result is **non-blocking** — note "dead-code sweep incomplete" and proceed.

### Phase C: Cross-File Review & Final Report (main model)

After all sonnet agents return, the main model:

1. **Collects all findings** from sonnet agents into a unified list. A per-file message without its `END_OF_FILE_REVIEW` line is partial: keep what it reports and mark the file `partially analyzed` in the report
2. **Merges the Phase A secrets pre-scan with pass-6.10 findings from the per-file agents.**
   - `secrets_prescan.findings` is **authoritative** — every entry is real (regex matched + exception filter applied) and goes straight into the Secrets Detection table.
   - Agent 6.10 findings are **supplemental** (context the regex missed, e.g. a custom DSL with a non-standard keyword). One NOT already in `secrets_prescan` (by `{file, line, kind}`) enters the table only if (a) it shows a concrete literal credential, not a category like "potential leak", AND (b) it matches a 6.10 category or a clear equivalent; otherwise drop it as low-signal speculation.
   - Dedup remaining entries by `{file, line, kind}`; on collision, keep the higher severity and prefer `source=ggshield` > `gitleaks` > `regex` > `sonnet` for provenance.
3. **Cross-file analysis** — only the main model has the whole picture: races spanning files (check in controller, act in service), schema consistency across related endpoints, import-chain coherence (producer and consumer types match). Code that already runs (cron, service): read its latest outputs (configuration.md §Runtime evidence). Add what you find to the list.
4. **Severity recalibration** — review each finding's severity:
   - Per-file agents may over-flag memoization issues (React.memo, useCallback) — downgrade per the rules in detection-passes.md
   - Ambiguous TOCTOU patterns in single-user contexts — downgrade to LOW
   - Patterns that are actually project conventions (check CLAUDE.md) — remove or downgrade
   - **Pass 6.11 (Silent-Blinding Sensors) findings never rise above HIGH and never touch the grade gate.** Downgrade to LOW, or drop, anything where the swallowed error has observable fallback behavior — the pass is about blind spots, not about `catch` syntax. A per-file claim that a future drift would blind a site was made without the tests: find the test that pins it before keeping the severity (detection-passes.md 6.11).
   - **Pass 6.10 (Secrets) findings are NEVER downgraded to MEDIUM/LOW and NEVER removed.** The only allowed recalibration is CRITICAL ↔ HIGH per the test-file nuance in detection-passes.md (inline test literals are HIGH; prod code is CRITICAL; env-var lookups are not flagged at all).
5. **Deduplication** — remove findings that overlap or repeat the same root cause (does not apply to pass 6.10 — each occurrence is reported, then aggregated if ≥3 in one file or ≥5 across PR).
6. **Test coverage summary** — compile from Phase A results
7. **Documentation sync check** — verify docs files in CHANGED_FILES per 6.5.2 rules
8. **Secrets gate** — if the merged Secrets Detection list has **≥1 entry from `secrets_prescan` OR ≥1 entry from sonnet that survived the supplemental filter in step 2**:
   - Set overall grade to **F** regardless of any other signal.
   - Prepend a BLOCKED banner to the report (see report template).
   - Add an entry under "Must Fix (CRITICAL)" per file with the remediation block from detection-passes.md pass 6.10.
   - If `secrets_prescan.errors` is non-empty (script crashed, ggshield timed out), also surface a warning to the user — the gate may have under-reported.
9. **Merge dead-code findings** from B2 (Bucket A = introduced/orphaned by this PR; Bucket B = pre-existing, capped, only on `dead-code` focus or `sweep=full`):
   - **MEDIUM/LOW only** — never HIGH/CRITICAL, never the secrets gate, never a forced F.
   - Honor the per-finding **Confidence**: drop or footnote Low-confidence items the guardrails couldn't clear (an unreferenced library export — external consumers are invisible to repo grep).
   - Bucket B stays a **capped summary** labeled "pre-existing (not introduced by this PR)", so it doesn't drown Bucket A; `BUCKET_B: skipped` → the template's one-line note instead of a table.
   - Sweep skipped (narrow focus) or under-reported → say so in the Dead Code section, don't omit it.
10. **Produce the final report** — before writing, read `references/report-template.md`; order:
   BLOCKED banner (only if step 8 triggered) · **Secrets Detection table** (always; "Status: PASS" with
   0 rows when clean) · findings table (CRITICAL > HIGH > MEDIUM > LOW, grouped by file) · Zen
   Principles summary · Bug/Security/Performance/Types summary · test coverage table · documentation
   sync table · **🧹 Dead Code & Cleanup** (when the sweep ran — Bucket A primary, Bucket B as a capped
   pre-existing summary when on; dead-code findings also feed Recommended Actions → Consider Fixing
   and the Code Quality rationale) · **Overall Grade table** · **Recommended Actions** (every bucket,
   `_None._` when empty) · **Cost footprint** line, last.

**The Overall Grade table, the Recommended Actions block and the Cost footprint close every report**,
in full even with little to say: the template's fallbacks, never prose in place of the table.

### Special Cases

- **Zero findings**: Output a congratulatory report. Grade A. Still show header, test coverage, and grade.
- **Focus area specified**: Only the matching detection passes were applied by sonnet agents. Mark non-analyzed sections as "Not analyzed (focused review on {area})".
- **File path/glob specified**: Only matching files were analyzed. Report shows only those files.
- **UI_LIB files**: Sonnet agents only flagged CRITICAL/HIGH. Note "(UI_LIB — reduced rigor)" in findings.
- **More than 50 findings**: Show all CRITICAL/HIGH/MEDIUM first, then LOW up to 50 total. Add overflow count.

---

## Operating Principles and Gotchas

- **Context efficiency**: agents hold file content and diffs, so the main model sees only findings;
  cap analysis at 15 full file reads across all agents.
- **Measure, don't guess** — the report's last line says which version of this skill ran, how many
  agents ran, on which model, how many tool calls each made and whether the sweep ran. Compare it with
  `/cost` (or the harness's per-session cost log) before and after any change to this skill; a change
  without that pair of numbers is a guess.
- **Re-review the fix, not the branch** — after fixing a report, the next round runs with
  `base=<head the last round reviewed>` and stops at the first round that finds nothing; a fix written
  as prose is the likeliest home of the next finding (measured 11 → 5 → 3 → 0).
- **Line numbers come from the diff or file actually read** — a line the reader can't find discredits
  the whole report.
- **A clean report is a valid outcome** — if the code is clean, say so rather than inventing findings.
- **Never whitelist a secret finding to reduce noise** — test-file passwords count like production
  ones; GitGuardian agrees. A false-positive re-read costs far less than a leaked credential.
- **Ground findings in evidence** — quote the problematic snippet when helpful; for secrets, mask the
  value with `***` (the report itself is copied into chat history).
