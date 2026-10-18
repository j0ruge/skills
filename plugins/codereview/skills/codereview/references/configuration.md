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
| `worktree` | auto | Review uncommitted work instead of `{MERGE_BASE}...HEAD`. Turns on by itself when the committed diff is empty but `git status --porcelain` is not — typically on the base branch itself, where `git merge-base` returns `HEAD` and the normal Phase A would stop with "No changes detected" over pending work. Changed files = `git diff HEAD --name-only` plus `git ls-files --others --exclude-standard`; per-file diff = `git diff HEAD -- <file>`, or `git diff --no-index /dev/null <file>` for an untracked file (rc 1 is normal there). **The secrets pre-scan needs both sources**: pipe `git diff HEAD --unified=0` and the `--no-index` diff of every untracked file into `scan_secrets.sh` — `git diff HEAD` alone never shows new files. Exclude runtime state the user did not author (`*.db`, caches) from CODE. Commit log: none. In agent prompts write the diff command out in full: `{MERGE_BASE}...HEAD` would be empty. The report header says `working tree vs HEAD {sha}`. A repo whose whole history is one commit, asked for as a whole ("o projeto todo", "all of it"), is not this mode: worktree reviews only what is pending. Use `base=4b825dc642cb6eb9a060e54bf8d69288fbee4904`, git's empty tree, with the two-dot `git diff <tree> HEAD` written out in every prompt: three-dot needs a commit on both sides (`fatal: Invalid symmetric difference expression`). Measured 2026-10-18: worktree mode would have graded a `TODO.md` and 60 transcripts; the empty-tree range sent the 12 non-empty CODE files to 5 agents. |
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

## Several repositories

Read this when `$ARGUMENTS` names more than one repository ("nos repos", "both repos"), or when the
handoff the review answers to lists them. The session's working directory is only one of them, and its
branch can be the smaller part. Measured 2026-10-16 (RS-929): the session ran in the API repo, whose
branch held 5 `.md` files; the code under review (a shell sensor and its test, a measurement script, an
HTML deck engine) sat on a same-named branch in a sibling repo. Reviewed from the cwd alone, the report
grades "A, no CODE files" and never reads the one HIGH.

- **Phase A once per repo**, each with its own base branch (here `origin/develop` and `origin/main`) and
  its own secrets pre-scan: a clean scan of one repo says nothing about the other.
- **One Phase B batch** for the CODE files of every repo. Each launch prompt names its repo and writes the
  diff command out (`git -C <repo> diff <merge-base>...HEAD -- <file>`), since `{REPO}` differs per agent.
- **One report**: the header lists each repo with branch → base, the head reviewed and its counts; the
  Overall Grade table gets one grade column per repo. A re-review names, per repo, the head it starts from.

## Folder without git

Read this when Phase A step 1 fails with `not a git repository` on the folder the user asked to
review: scripts that never had a repo. Stopping there reviews nothing, and `git init` inside the
folder writes a `.git` the user did not ask for. Build the range in the scratchpad instead. It is the
review's one write, and it stays outside the folder.

- **The git dir in the scratchpad, the folder as work tree:** `export GIT_DIR=<scratchpad>/review.git
  GIT_WORK_TREE=<folder>`, then `git init -q -b main` and a local `git config`: `core.fileMode false`
  (`/mnt/c` reports every file as 0777), `core.autocrlf false`, `user.name` and `user.email`. An empty
  root commit (`git commit --allow-empty`) is `{MERGE_BASE}`; a commit of the authored files, added by
  name so build outputs and downloaded material stay out, is `HEAD`.
- **Every git command carries the prefix:** Phase A, the secrets pre-scan, the docstring probe. The
  agents' shells do not inherit the orchestrator's exports, so the launch prompt's `Repository:` line
  says the folder has no `.git` and gives the prefix, and the diff command is written out with it, as
  in `worktree` mode.
- **A re-review round commits the fixes** to the same git dir and runs with `base=<previous head>`.
- Measured 2026-10-17 (codereview 2.17.0, Python and shell scripts plus an HTML deck in a Windows
  folder under WSL): three rounds of 6, 6 and 5 sonnet agents, each running its prefixed diff, and
  nothing written inside the folder.

## Path-scoped reviews

Read this when the user limits the review to paths (`-- dir/ file`, "only the skill folder", "without docs/"). Pass the pathspecs to every Phase A command and to the agent prompts' diff commands.

- **Exclusions go quoted, in long form:** `':(exclude)docs/qa'`. The short `':!docs/qa'` is unsafe in zsh: unquoted, `!` is history expansion; stored in a variable (`P="a :!b"; git diff -- $P`), zsh does not word-split, git receives one bogus pathspec and prints nothing.
- **A file the user names is CODE, whatever its extension.** The classification lists only
  `{fileExtensions}`, so a named `.tex`, `.ps1` or config file would get no agent and no line in
  the report. Measured 2026-10-05: `paper/preambulo.tex`, named in the scope of a Python review,
  had no preset; reviewed as CODE, its one finding was settled from the build output (see
  *Runtime evidence*).
- **Empty output under an explicit path scope is an error, not "No changes detected".** Re-check the pathspecs (`git diff --stat {MERGE_BASE}...HEAD -- <paths>` without exclusions, `git log --oneline -- <paths>`) before stopping. Measured: a 32-commit scope came back as 0 commits from the unquoted form.

## Code inside docs

Read this when the focus names code that lives inside a changed doc: a plan or spec whose fenced
`awk`/`bash`/regex blocks are what the PR promises to ship. Classified by extension, a docs-only
diff is all DOCS, Phase B launches no agent, and the report grades code nobody read.

- **The doc that carries the named code is CODE**, the same rule as a file the user names
  (*Path-scoped reviews*). The other docs in the diff stay DOCS.
- **A long doc goes to more than one agent**, each with a line range on its `File:` line
  (`docs/x/01-plano.md (category: CODE, lines 1–505)`); the rest of the launch prompt stays
  verbatim. The ≤3-file inline shortcut does not apply here: inline, the main model reads the
  whole doc.
- Measured 2026-10-13 (`j0ruge/sdd_agents` PR #247, codereview 2.14.1): a 10-file docs-only diff
  classified 0 CODE; the 1184-line plan, split into two ranges (`1–505`, `506–632 + 973–1184`),
  gave two sonnet agents with findings, one of them a confirmed MEDIUM.

## Re-review rounds

Read this whenever `base=` names the head an earlier round reviewed (SKILL.md, *Re-review the fix*).
These decide whether the rounds converge:

- **The agents never see the earlier reports.** A finding a previous round dismissed with a written
  reason can come back with no new evidence — measured 2026-10-03: the same unreachable "partial
  batch" finding in rounds 2 and 3. Answer it by citing that verdict; it does not count against the
  stop rule. New evidence (a case the earlier reason did not cover) reopens it. Only a verdict written
  per part can be cited: a part of a multi-part finding dropped without one comes back as new
  (report-template.md, *Findings Table*).
- **While agents or a background test run read the tree, it is theirs.** Compare with another ref by
  `git show <ref>:<file>` or `git diff <ref> -- <file>`, never `checkout` or `stash`: a one-second
  `git checkout main` mid-round (2026-10-03, to check whether a lint warning was pre-existing) voided
  a full suite run and forced every finding to be re-checked against the branch.
- **Rounds over uncommitted fixes need a snapshot of what each round reviewed.** `base=<head>`
  assumes a commit per round; when nobody asked for commits there is no such ref, and `git diff HEAD`
  hands every round all the earlier rounds' fixes again. When a round launches, take
  `S=$(git stash create)` (empty output = clean tree: use `HEAD`): a commit object of the working
  tree that leaves the tree, the index and the stash list untouched. The next round writes
  `git diff $S -- <file>` out in each prompt, the sweep's too. Untracked files stay out of it, so a
  file new since `HEAD` diffs whole. Measured 2026-10-18 (Python, rounds 3 and 4 over uncommitted
  fixes): scratchpad copies of the reviewed files and `diff -u <copy> <file>` in the prompts did the
  same job; `git stash create` was checked afterwards in a scratch repo.
- **Reproduce between rounds, not during one.** A mutant that confirms a `needs reproduction` finding
  (detection-passes.md, 6.12) edits a file: run it after every agent has returned, against the
  related test files, and restore the file before the next launch (`git status --short` empty).
  In Python, run each mutant with `-X pycache_prefix=<new empty dir>`: a mutant that
  only moves a block keeps the file size, and in the same second as the previous one the
  interpreter reuses that one's `.pyc` (it checks mtime in whole seconds and size). Measured
  2026-10-05: a mutant "passed" that way and failed once the cache was isolated. Not the
  `PYTHONPYCACHEPREFIX` variable: `-I` ignores every `PYTHON*` variable, so it is dropped in silence
  (measured 2026-10-17: `sys.pycache_prefix` was `None` and the `.pyc` landed next to the source).
- **A mutant that does not build is not a kill.** A broken build exits non-zero like a red test, but
  prints neither of the runner's summary lines (`Passed!|Failed!`), so a filter on them stays mute. Write the
  mutant as an exact text replacement that occurs once and must change the file, keep every symbol it leaves in use,
  and filter compiler errors too (`error CS`, `error TS`, `SyntaxError`). Measured 2026-10-17 (.NET,
  warnings as errors): a regex over a C# line split an interpolated string at its `;` (CS1002), and
  `throw;` left `catch (… e)` unused (CS0168); the filter printed nothing for the three mutants.
  Rewritten (`throw new InvalidDataException(e.Message, e)` for the last), they turned 1, 2 and 1
  tests red. Assert "once" and "changes" before writing: a later round's fix moves or repeats the
  anchor (measured 2026-10-18: `except FileNotFoundError:` appeared twice after one, and the assert
  stopped the run before any file was touched).
- **Ask the fixer for the smallest change that closes the finding.** A new mechanism is new surface
  for the next round. Measured 2026-10-05, twelve rounds over ~670 lines: 8, 16, 13, 15, 9, 4, 5, 2,
  4, 4, 1, 0 findings; the atomic write one round asked for brought 4 of the next round's 15. With
  "a test, a docstring or one line before a new function" in the fixer's prompt, the curve fell
  15 → 9 → 4. Closing the finding is not applying the reviewer's suggestion: a suggestion that
  weakens the sensor is declined with a measurement (`[0-9]` in an id regex would have let a
  Unicode-digit id vanish silently instead of failing as unknown).
- **The fix list the orchestrator writes is prose too.** A user-facing message or a state guarantee
  spelled out in it is implemented literally and becomes the next round's top finding. Measured
  2026-10-14, a bash refresh tool over four rounds (1 HIGH/11 MEDIUM → 1/2 → 0/1 → 0/0): "staging
  nao foi tocado", prescribed for any client exit code above 3, came back HIGH, because ssh also
  returns 255 when the connection drops after the remote command started; "the previous pointer
  survives a failed write" came back MEDIUM, because `rollback` then trusted the stale pointer. Name
  the property ("say only what is known"), not the wording, and ask the fixer what the user does next
  on the path it changed. The round after that came back 0 HIGH / 0 MEDIUM once its two MEDIUM
  claims were reproduced and refuted.
- **A fix that writes "measured" measures the exact line it writes.** A claim measured on half of a
  recipe vouches for the other half by proximity, and the next round reads the half nobody ran.
  Measured 2026-10-16, rounds over a plan reviewed as CODE: round 2 timed the wait
  (`timeout 590 tail --pid`) and wrote "measured" next to the one-liner the plan prescribed,
  `l=$(mktemp) && nohup … &`; round 3 came back HIGH on that line, because `&` sends the whole `&&`
  list to the background, `l` is set only in that subshell, and the log read `log=[]`
  (`bash -c 'l=$(mktemp) && true & wait; echo "l=[$l]"'` prints `l=[]`). Paste the line as it stands
  in the text, run it, and quote its output next to the claim.
- **Reflow prose by script, never by hand.** A fix that grows a wrapped paragraph invites a hand
  reflow, and a hand reflow joins two lines or drops a word that the next round reports. Measured
  2026-10-16: three hand reflows between rounds each left joined lines, and each came back as a LOW;
  the script below closed it, and was reused on 2026-10-17 for a shell header past 100 columns. It
  keeps every backtick span whole and fails unless the words before and after match:

  ```python
  import re, textwrap
  def reflow(par: str, first: str = "- ", rest: str = "  ", width: int = 100) -> str:
      glued = re.sub(r"`[^`]*`", lambda m: m[0].replace(" ", "\u00a0"), " ".join(par.split()))
      out = textwrap.fill(glued, width, initial_indent=first, subsequent_indent=rest,
                          break_long_words=False, break_on_hyphens=False).replace("\u00a0", " ")
      assert out.split() == first.split() + par.split(), "the reflow changed the words"
      return out
  ```
- **A count in CLAUDE.md that an agent calls stale is checked in the file.** The agents cite the
  value from the start of the session: measured 2026-10-05, four rounds flagged "CLAUDE.md says 1284
  tests" while the file, updated by each round's commit, already said 1336, 1352, 1362 and 1363.
  `grep` the current file before keeping a docs-drift finding.
- **The tests a fix adds get no agent.** On a full review Phase B sends TESTS only on a test-quality
  focus, so the round after a fix grades Test Coverage on test files nobody read. Back that grade with
  one mutant per guard the fix added, run against its tests (*Reproduce between rounds*; 6.12, *One
  case for two guards*), and give the mutant count in the Test Coverage row. Measured 2026-10-17: round
  2 diffed 14 new test files (788 lines) and launched no agent for them; the 24 mutants run after round
  1's fixes and the 12 after round 2's, all killed, were what the two A grades stood on.

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
