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
| `base` | — | Commit to diff against, replacing `git merge-base {BASE_BRANCH} HEAD` as `{MERGE_BASE}` in Phase A and in every agent prompt. Use it when the user names the base of a commit range, in prose too ("os commits de X a Y, sobre Z" → `base=Z`): the merge-base would review the whole branch. Also the way to re-review only the fixes after a report: `base=<the head the previous round reviewed>`. The range still ends at `HEAD`. |
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
- **Empty output under an explicit path scope is an error, not "No changes detected".** Re-check the pathspecs (`git diff --stat {MERGE_BASE}...HEAD -- <paths>` without exclusions, `git log --oneline -- <paths>`) before stopping. Measured: a 32-commit scope came back as 0 commits from the unquoted form.

## Runtime evidence

Read this in Phase C when the reviewed code already runs (a cron job, a deployed service, a scheduled script) — a diff review cannot see behavior that only shows up on real data.

- Look for the latest 2–3 run outputs: the scheduler's output dir (e.g. `cron/output/<job>/`), the service log, the job's last status. Read them, don't summarize them from memory.
- Compare each output with what the diff says should happen: a message that contradicts the code's intent, an event firing for the wrong records, a warning that repeats daily. File the mismatch as a finding with the output path and line as evidence.
- Measured: a review of a daily cron missed, in all per-file agents, an event that re-announced 9 records lost years earlier — it showed only in that morning's output.
- Never paste client data or credentials from the output into the report: cite the file and summarize.
