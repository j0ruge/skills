# Configuration

> **Defaults target TypeScript/React projects. Override any value to adapt the skill to a different stack (Vue, Angular, Python, Go, Node-only, etc.).**

## Default Values

| Variable | Default | Description |
|---|---|---|
| `baseDir` | `src/` | Root directory that contains application source files. |
| `fileExtensions` | `["ts", "tsx"]` | Extensions considered source code. Extend with `["js","jsx","vue","svelte","py","go"]` etc. |
| `testFilePatterns` | `["**/*.{test,spec}.{ts,tsx}", "**/test/**"]` | Globs that identify test files (resolved relative to `baseDir`). |
| `generatedDirs` | `["src/components/ui/**", "prisma/**", "**/generated/**"]` | Globs for auto-generated or UI-lib directories — classified as `UI_LIB` (reduced-rigor). |
| `uiLibReducedRigor` | `true` | When `true`, `UI_LIB` files receive only CRITICO/ALTO checks. Set to `false` to apply full analysis. |
| `frameworkPatterns` | `react` | Framework hint controlling which framework-specific rules are active. Options: `react` \| `vue` \| `angular` \| `node` \| `dotnet` \| `generic`. |
| `configFilePatterns` | `["*.config.*", "tsconfig*", ".env*", "package.json"]` | Globs matched as CONFIG files. |
| `styleFilePatterns` | `["**/*.css", "**/*.scss", "**/*.less"]` | Globs matched as STYLES files. |
| `base` | — | Commit to diff against, replacing `git merge-base {BASE_BRANCH} HEAD` as `{MERGE_BASE}` in Phase A and in every agent prompt. Use it when the user names the base of a commit range, in prose too ("os commits de X a Y, sobre Z" → `base=Z`): the merge-base would review the whole branch. Also the way to re-review only the fixes after a report: `base=<the head the previous round reviewed>`. The range ends at `HEAD` unless `head=` names another end. Such a round follows *Re-review rounds* below. |
| `head` | `HEAD` | Commit the range ends at, when the user names an end that is not `HEAD`, in prose too ("revise `A..B`", a range already merged with commits after `B`). It replaces `HEAD` in every Phase A command (steps 4–8), and in agent prompts the diff command is written out in full (`git diff {MERGE_BASE}..{head} -- {FILE_PATH}`), as in `worktree` mode. Without it, whatever was committed after the end enters the review unannounced. Measured 2026-10-05: a 15-commit range ended two commits before `HEAD`; the seven agents reviewed the right range only because each prompt carried the `A..B` diff written out. The report header names both ends. |
| `worktree` | auto | Review uncommitted work instead of `{MERGE_BASE}...HEAD`. Turns on by itself when the committed diff is empty but `git status --porcelain` is not — typically on the base branch itself, where `git merge-base` returns `HEAD` and the normal Phase A would stop with "No changes detected" over pending work. Changed files = `git diff HEAD --name-only` plus `git ls-files --others --exclude-standard`; per-file diff = `git diff HEAD -- <file>`, or `git diff --no-index /dev/null <file>` for an untracked file (rc 1 is normal there). **The secrets pre-scan needs both sources**: pipe `git diff HEAD --unified=0` and the `--no-index` diff of every untracked file into `scan_secrets.sh` — `git diff HEAD` alone never shows new files. Exclude runtime state the user did not author (`*.db`, caches) from CODE. Commit log: none. In agent prompts write the diff command out in full: `{MERGE_BASE}...HEAD` would be empty. The report header says `working tree vs HEAD {sha}`. |
| `sweep` | `pr` | Scope of the dead-code sweep (pass 6.9). `pr` = Bucket A only (symbols this PR introduced or orphaned); `full` = also run Bucket B (repo-wide tooling over code the PR did not touch, capped). Focus `dead-code` implies `full`. |

> **Note:** The array values in the table above are in JSON format for clarity only. When overriding, use comma-separated values without brackets (see Override Syntax below).

## Override Syntax

When `$ARGUMENTS` contains key-value overrides, apply them before classification.

**Format**: `key=value` pairs separated by spaces. Array values use commas.

**Examples**:

```text
# Python project
/codereview baseDir=app/ fileExtensions=py testFilePatterns=**/test_*.py frameworkPatterns=generic

# Vue project
/codereview baseDir=src/ fileExtensions=ts,vue frameworkPatterns=vue

# Node-only project (no UI framework)
/codereview fileExtensions=ts,js frameworkPatterns=node

# Shell/bash repo — `bin/tool` with no extension is CODE by its shebang (SKILL.md, Classify)
/codereview baseDir=. fileExtensions=sh,bash testFilePatterns=**/*.bats frameworkPatterns=generic

# Disable reduced rigor for generated files
/codereview uiLibReducedRigor=false

# C#/.NET WPF project
/codereview fileExtensions=cs,xaml testFilePatterns=**/*Tests.cs,**/*.Tests/**/*.cs frameworkPatterns=dotnet generatedDirs=**/obj/**,**/bin/**,**/*.Designer.cs configFilePatterns=*.csproj,*.sln,*.props,appsettings*.json

# C#/.NET Web API (ASP.NET Core)
/codereview fileExtensions=cs testFilePatterns=**/*Tests.cs frameworkPatterns=dotnet

# C#/.NET minimal — just set framework, use sensible auto-detection
/codereview fileExtensions=cs frameworkPatterns=dotnet
```

In a repo whose test scripts are its product — a kit whose `tests/*.sh` are the sensors the change
is about — a test change carries as much risk as the runner's. Keep them out of `testFilePatterns`
(the shell preset counts only `*.bats` as TESTS) so Phase B reviews them as CODE; classified as
TESTS they get no per-file agent at all.

Overrides are applied on top of defaults — only the specified values change; unmentioned values keep their defaults.

## Path-scoped reviews

Read this when the user limits the review to paths (`-- dir/ file`, "only the skill folder", "without docs/"). Pass the pathspecs to every Phase A command and to the agent prompts' diff commands.

- **Exclusions go quoted, in long form:** `':(exclude)docs/qa'`. The short `':!docs/qa'` is unsafe in zsh: unquoted, `!` is history expansion; stored in a variable (`P="a :!b"; git diff -- $P`), zsh does not word-split, git receives one bogus pathspec and prints nothing.
- **A file the user names is CODE, whatever its extension.** The classification lists only
  `{fileExtensions}`, so a named `.tex`, `.ps1` or config file would get no agent and no line in
  the report. Measured 2026-10-05: `paper/preambulo.tex`, named in the scope of a Python review,
  had no preset; reviewed as CODE, its one finding was settled from the build output (see
  *Runtime evidence*).
- **Empty output under an explicit path scope is an error, not "No changes detected".** Re-check the pathspecs (`git diff --stat {MERGE_BASE}...HEAD -- <paths>` without exclusions, `git log --oneline -- <paths>`) before stopping. Measured: a 32-commit scope came back as 0 commits from the unquoted form.

## Re-review rounds

Read this whenever `base=` names the head an earlier round reviewed (SKILL.md, *Re-review the fix*).
Five things decide whether the rounds converge:

- **The agents never see the earlier reports.** A finding a previous round dismissed with a written
  reason can come back with no new evidence — measured 2026-10-03: the same unreachable "partial
  batch" finding in rounds 2 and 3. Answer it by citing that verdict; it does not count against the
  stop rule. New evidence (a case the earlier reason did not cover) reopens it.
- **While agents or a background test run read the tree, it is theirs.** Compare with another ref by
  `git show <ref>:<file>` or `git diff <ref> -- <file>`, never `checkout` or `stash`: a one-second
  `git checkout main` mid-round (2026-10-03, to check whether a lint warning was pre-existing) voided
  a full suite run and forced every finding to be re-checked against the branch.
- **Reproduce between rounds, not during one.** A mutant that confirms a `needs reproduction` finding
  (detection-passes.md, 6.12) edits a file: run it after every agent has returned, against the
  related test files, and restore the file before the next launch (`git status --short` empty).
  In Python, run each mutant with `PYTHONPYCACHEPREFIX` set to a new empty directory: a mutant that
  only moves a block keeps the file size, and in the same second as the previous one the
  interpreter reuses that one's `.pyc` (it checks mtime in whole seconds and size). Measured
  2026-10-05: a mutant "passed" that way and failed once the cache was isolated.
- **Ask the fixer for the smallest change that closes the finding.** A new mechanism is new surface
  for the next round. Measured 2026-10-05, twelve rounds over ~670 lines: 8, 16, 13, 15, 9, 4, 5, 2,
  4, 4, 1, 0 findings; the atomic write one round asked for brought 4 of the next round's 15. With
  "a test, a docstring or one line before a new function" in the fixer's prompt, the curve fell
  15 → 9 → 4. Closing the finding is not applying the reviewer's suggestion: a suggestion that
  weakens the sensor is declined with a measurement (`[0-9]` in an id regex would have let a
  Unicode-digit id vanish silently instead of failing as unknown).
- **A count in CLAUDE.md that an agent calls stale is checked in the file.** The agents cite the
  value from the start of the session: measured 2026-10-05, four rounds flagged "CLAUDE.md says 1284
  tests" while the file, updated by each round's commit, already said 1336, 1352, 1362 and 1363.
  `grep` the current file before keeping a docs-drift finding.

## Runtime evidence

Read this in Phase C when the reviewed code already runs (a cron job, a deployed service, a scheduled script) — a diff review cannot see behavior that only shows up on real data.

- Look for the latest 2–3 run outputs: the scheduler's output dir (e.g. `cron/output/<job>/`), the service log, the job's last status. Read them, don't summarize them from memory.
- Read the data the code writes or reads too — an audit trail, a telemetry JSONL, a state file — not only its logs: count its events by origin and time window. Measured 2026-10-05: a per-file LOW ("a new client would be miscounted, if it ever wrote events") became MEDIUM when the audit trail showed 6 real events from that client, and the same trail showed two test runs writing to production where the handoff declared one.
- A build's own outputs count too. When a finding is marked `needs reproduction` and the build has
  already left its outputs (a PDF, a `.log`, a `.blg`, a bundle), read them before asking for a
  rebuild. Measured 2026-10-05: a per-file "`extradate` may be an unknown biblatex option" was
  settled without writing anything: no "Unknown option" in the build log, the style file
  declares the option, and `pdftotext` of the PDF shows "2006a"/"2006b" in the reference list.
- Compare each output with what the diff says should happen: a message that contradicts the code's intent, an event firing for the wrong records, a warning that repeats daily. File the mismatch as a finding with the output path and line as evidence.
- Measured: a review of a daily cron missed, in all per-file agents, an event that re-announced 9 records lost years earlier — it showed only in that morning's output.
- Never paste client data or credentials from the output into the report: cite the file and summarize.
