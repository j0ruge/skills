# Configuration

> **Defaults target TypeScript/React projects. Override any value to adapt the skill to a different stack (Vue, Angular, Python, Go, Node-only, etc.).**

## Contents

- [Default Values](#default-values) · [Override Syntax](#override-syntax) (presets per stack, the
  C# probe by type and by registration literal)
- [Base and batching](#base-and-batching) (a stale local base, a branch already merged, an isolated
  worktree) · [Stale copy](#stale-copy) · [Docs this session wrote](#docs-this-session-wrote)
- [Several repositories](#several-repositories) · [Folder without git](#folder-without-git) ·
  [Path-scoped reviews](#path-scoped-reviews) · [Code inside docs](#code-inside-docs)
- [Re-review rounds](#re-review-rounds) · [Runtime evidence](#runtime-evidence)

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

Where an import names a namespace and not a file (C#'s `using`, a Java or Kotlin `import` of a
package, Go), Phase A's probe misses most tests: `{Base}Tests.cs` finds only a test named after the
file, and "a changed test that imports it" never matches. Probe by the type instead: for each public
type the CODE file declares, `git grep -lw <Type> -- <test dirs>`; a hit in a test changed in the
range is `WITH_TESTS (indirect)`, a hit only in unchanged tests is `STALE_TESTS`. Measured
2026-10-18 (a .NET rules engine, 15 CODE files): `{Base}Tests.cs` found 6, the type name found a
test for 7 more, and the last 2 had none (one exercised only through another type's suite, one with
no test at all). The PR before it, on the same repo, had measured 27 of 41 files by type name and
almost none by file name.

A type the tests never name — registered under a string in a catalog, a container or a plugin
table — leaves that probe nothing to find. With no hit by type, probe the literal it registers
under (`Id => "first-strike"`, a `const string`), in quotes, over the changed tests: a hit is
`WITH_TESTS (indirect)`. In quotes, because the bare word matches prose and fixtures. A hit only in
a test that lists the registry proves the registration, not the behavior; Phase C says which.
Measured 2026-10-19 (the same engine, 14 `internal sealed` keyword classes, 37 changed test files):
no test named a type — the `-w` hits were card text in fixture XML, an unrelated `d.Defender` and
an invalid-id literal — and the quoted id hit 14 of 14, all in keyword tests; `reach` bare matched 6
test files, quoted 2. For 4 of the 14 the only hit was the registry listing, while their behavior
tests load fixture cards.

Overrides are applied on top of defaults — only the specified values change; unmentioned values keep their defaults.

## Base and batching

Read this in Phase A when step 2 lands on a local branch while `origin/<base>` exists, when a merge
base equals `HEAD`, or when the session runs isolated in a worktree.

- **Batching is the default.** Steps 1–3 run as one chain and steps 5–8 as parallel calls in one
  message, because every extra orchestrator turn is a main-model round-trip over the whole session
  context.
- **A local base can be stale.** Without `origin/HEAD`, step 2 stops at the local `main`, which may
  sit merged PRs behind. When `git rev-list --count main..origin/main` is above 0, the base is
  `origin/main`. Measured 2026-10-19 (magic_tutor): the local `main` was 24 commits behind, and its
  merge base gave a 22-commit range holding two PRs already merged.
- **A branch already merged diffs empty against `origin/<base>`** (its merge base is `HEAD`). When
  the user asks for that branch's code ("o código novo"), the range is what its PR brought:
  `git log --merges --ancestry-path --format=%h HEAD..origin/main` lists the merges after it, the last
  line is the one that brought it in, and `git merge-base <that merge>^1 HEAD` is `base=`. The header
  names both ends, and the fixes go on a new branch. Measured 2026-10-19: merge `2e14ab8`, base
  `2074fd5`, exactly the branch's 9 commits.
- **An isolated worktree session refuses the chain.** Its guard rejects any command it cannot prove
  stays in the worktree: a `$(git …) || …` chain ("names git in a form too complex to verify"), a
  `python3 - <<EOF` heredoc (the docstring probe), an argument computed at runtime
  (`python -X pycache_prefix=$S/pyc`). Run each git command plainly, as parallel calls in one
  message; call it as `/usr/bin/git` where a hook rewrites `git` (the rtk hook's `rtk git` is
  refused too); write scripts to the scratchpad and spell their paths out. Measured 2026-10-19
  (Claude Code, magic_tutor): the chain, the heredoc and the `$S` argument were refused, and the
  split calls ran.
- **The same hook can summarize `grep`.** Where its output decides a finding (a cross-file check,
  a reference count), call `/usr/bin/grep`: through the rtk hook,
  `grep -n "glob\|st_mtime" monitor/replays.py` printed the `def` lines and `[+32 more]`, while
  `/usr/bin/grep` showed the four lines the check needed (measured 2026-10-19).

## Stale copy

Read this when Phase A finds `{SKILL_DIR}` outside the `installPath` that
`~/.claude/plugins/installed_plugins.json` records. The copy outside can be older or newer, so
compare the two versions first, the one Phase A read and that record's `version`
(`printf '%s\n' <loaded> <installed> | sort -V | tail -1` prints the newer).

**Loaded copy older than the installPath:** the session loaded the skill before a
`claude plugin update`.

- Compare the two `SKILL.md`, not the folders:
  `/usr/bin/diff {SKILL_DIR}/SKILL.md <installPath>/skills/codereview/SKILL.md`. A `diff -rq` of the
  two skill folders differs on every release of this skill, because the `version:` line of
  `SKILL.md` moves with it, so it cannot tell a stale instruction from a newer reference.
- Call `diff` by its absolute path. A hook that rewrites shell commands can answer for it: measured
  2026-10-19, `diff` through the `rtk` hook printed `[ok] Files are identical`, rc 0, for the 2.21.2
  and 2.23.0 `SKILL.md`, four hunks apart, while `/usr/bin/diff -q` printed `differ`, rc 1. Read as
  identical, the review would have run the 2.21.2 instructions.
- Only the `version:` line differs: set `{SKILL_DIR}` to the installed skill folder and go on. The
  instructions in context are the installed ones, and the rest (the agents' contracts,
  `detection-passes.md`, `scan_secrets.sh`) is read by absolute path from `{SKILL_DIR}`. Take the
  Cost footprint's version from the installed `SKILL.md`, since Phase A read it before the switch,
  and say there which copy the session had loaded.
- Any other line differs: the instructions in context are not the installed ones. Read each hunk.
  None changes a step (a command, a phase, a gate, a threshold, an agent's contract or launch
  prompt) — they reword, re-date a figure in a rationale, or point at a file this review never
  reads: set `{SKILL_DIR}` to the installed folder, go on, and list the hunks in the Cost footprint.
  A hunk that changes a step: follow the installed text, not the loaded one. The hunk and every
  section it points to, read from the installed folder, are that text (the lines around it are
  equal); with hunks in several phases, Read the installed `SKILL.md` whole. Go on from there, list
  the hunks in the Cost footprint, and say in the closing report that `/reload-plugins` makes the
  next run load the installed copy.
- Measured 2026-10-18 (ui24_agent, rounds 4 to 10): the session had loaded 2.18.4 with 2.19.0
  installed, and the 2.18.4 folder carried an `.orphaned_at` file. The folders differed in the
  references and in `scan_secrets.py` (2.19.0 added `scanned`), the two `SKILL.md` only in the
  version line. With `{SKILL_DIR}` at the installed folder the agents read the 2.19.0 contracts and
  the pre-scan reported `scanned`; the old rule (any `diff -rq` difference means `/reload-plugins`)
  would have stopped round 4 in Phase A. A later update left the same session at 2.18.4 against
  2.20.0, again one line apart.
- Measured 2026-10-18 (a .NET rules engine, rounds 1 to 7): loaded 2.20.0 with 2.21.2 installed,
  the two `SKILL.md` four hunks apart besides the version — a pointer to `assets/trigger-evals.json`
  (read only when changing the description), the cost note's ratio, the read-only sentence
  reworded, and the stale-copy pointer now naming this section. No step among them: the review went
  on from the installed folder and closed at grade A; the version-only rule would have stopped it
  in round 1.
- Measured 2026-10-19 (the same engine, PR #10, round 2): loaded 2.20.0 with 2.22.0 installed,
  seven hunks apart besides the version, one of them a step (Phase B sends each DOCS file this
  session wrote to an agent). Applied from the installed `SKILL.md` hunk and *Docs this session
  wrote*, that step gave the round its only MEDIUM; the rule that stopped on a step hunk would have
  halted the round in Phase A and waited for the user.

**Loaded copy newer than the installPath:** `claude plugin marketplace update` caches the
marketplace's current version of every installed plugin, but only a `claude plugin update` that
names the plugin writes it in `installed_plugins.json`. `/reload-plugins` then loads the cached
version, while a session started fresh loads the `installPath`.

- Do not switch to the `installPath`. It is the older text, and the rules above would trade the
  instructions in context for it.
- Check that the loaded copy is the one the marketplace publishes, by the exit status:
  `/usr/bin/diff -rq -x .git -x .in_use -x .orphaned_at -x __pycache__ {SKILL_DIR}/../.. <installLocation>/plugins/codereview`,
  with the `installLocation` that `~/.claude/plugins/known_marketplaces.json` records for the
  marketplace named in the cache path. rc 0: go on with `{SKILL_DIR}`, put both versions in the
  Cost footprint (`loaded 2.25.2 = marketplace, installed 2.19.0`), and say in the closing report
  that `claude plugin update codereview@<marketplace>` aligns the record; running it is the user's
  call. An `.orphaned_at` in the loaded folder changes nothing: it says only that the record does
  not name that folder.
- rc 1: read the clone's `version:` line. Newer than the loaded copy: the marketplace moved past
  both, so go on with `{SKILL_DIR}`, the newer of the two on disk, and put the three versions in the
  Cost footprint. The same version with other files: the cached copy was edited, so list the files
  and ask the user before going on.
- Measured 2026-10-20 (lighthouse_project, a plan review): loaded 2.25.2 with 2.19.0 installed,
  recorded on 2026-10-18 by the last `claude plugin update codereview`. That afternoon another
  session ran `claude plugin marketplace update`, then `claude plugin update` for another plugin:
  2.25.2 entered the cache in the same second as new versions of three other plugins, and only the
  named one reached the record. Afterwards each of the 17 plugins installed from that marketplace
  had its current version cached, and three of them, this one included, were not in the record.
  `/reload-plugins` in the reviewing session loaded 2.25.2; a `claude` started 55 minutes later
  loaded 2.19.0 and wrote `.orphaned_at` in the 2.25.2 folder one second after it started. The
  2.25.2 folder matched the marketplace clone (rc 0); 2.19.0 differed from it in `SKILL.md` and five
  references the agents and Phase C read. Followed to the letter, the older-copy rule would have run
  the review on 2.19.0, twelve releases back.

## Docs this session wrote

Read this when a changed DOCS file was written by this session, by you or by a pipeline you run or
follow (a headless phase such as the `sdd run` DOCS phase, a writer agent you launched), and makes
factual claims (paths, counts, names, versions, licenses, what a source can or cannot answer).
Phase C step 7 is yours, so on your own file it is a self-review; on the pipeline's, nobody else
reads it: its own review ran before that phase, and step 7 checks the doc against the diff, not
against code the range leaves out.

- Send it to a Phase B agent in the same batch, launch prompt unchanged, with category
  `DOCS (written this session; evidence: <path or none>)` — also when Phase B otherwise runs inline
  (≤3 CODE files). The agent's contract says what a DOCS file gets.
- Rounds that keep finding the next claim in the same doc: recommend removing the claim, not adding
  evidence. In the series below every added word became the next round's finding (rounds 3 to 6),
  and it closed when the fixes took text out.
- Measured 2026-10-18 (a .NET rules engine, rounds 2 to 7): the orchestrator had written a
  knowledge doc and a handoff; the agent launched by hand for them found every MEDIUM of rounds 2
  to 6 (2, 2, 1, 1, 1), and round 7 closed at grade A.
- Measured 2026-10-19 (the same engine, PR #10, round 2 over the kit's REVIEW): the kit's DOCS
  phase had rewritten a table cell of a knowledge doc and added a pointer to it, after the kit's
  own review. Sent to an agent as written this session, the doc gave the round's only MEDIUM: the
  cell left out a form the parser accepts (`FE_NUM_COLOURS` with `OP_GREATER_THAN`) and ended by
  calling any other operator an error, against a code file the range did not touch.

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

- **Exclusions go quoted, in long form:** `':(exclude)docs/qa'`. The short `':!docs/qa'` is unsafe in zsh: unquoted, `!` is history expansion.
- **A path list never goes through an unquoted variable in zsh.** zsh does not word-split: stored
  in a variable (`P="a :!b"; git diff -- $P`), the list reaches git as one bogus pathspec and git
  prints nothing. Write the paths out, or split them with `${=P}`. Measured 2026-10-19 (four files
  named in the scope): `git diff HEAD --stat -- $F` printed nothing, and the same `$F` handed the
  secrets pre-scan an empty diff; only its `empty input` error said so.
- **A file the user names is CODE, whatever its extension.** The classification lists only
  `{fileExtensions}`, so a named `.tex`, `.ps1` or config file would get no agent and no line in
  the report. Measured 2026-10-05: `paper/preambulo.tex`, named in the scope of a Python review,
  had no preset; reviewed as CODE, its one finding was settled from the build output (see
  *Runtime evidence*).
- **Empty output under an explicit path scope is an error, not "No changes detected".** Re-check the pathspecs (`git diff --stat {MERGE_BASE}...HEAD -- <paths>` without exclusions, `git log --oneline -- <paths>`) before stopping. Measured: a 32-commit scope came back as 0 commits from the unquoted form.

## Code inside docs

Read this when the focus names code that lives inside a changed doc: a plan or spec whose fenced
`awk`/`bash`/regex blocks are what the PR promises to ship. Also with no focus, when the diff has
0 CODE and a doc carries commands a later step runs: the Checks of a plan, the recipes of a spec,
the conditions of a handoff. Classified by extension, a docs-only diff is all DOCS, Phase B
launches no agent, and the report grades code nobody read.

- **The doc that carries the code is CODE**, the same rule as a file the user names
  (*Path-scoped reviews*). The other docs in the diff stay DOCS.
- **A long doc goes to more than one agent**, each with a line range on its `File:` line
  (`docs/x/01-plano.md (category: CODE, lines 1–505)`); the rest of the launch prompt stays
  verbatim. The ≤3-file inline shortcut does not apply here: inline, the main model reads the
  whole doc.
- **The range names the sections that bind it** (`lines 354–645; also 105–106, § Contexto`). Past
  ~600 lines the agent reads only the changed regions (per-file-agent.md), so a rule written
  outside its range comes back as a gap. Measured 2026-10-20: the agent of lines 354–645 of a plan
  reported the docstring rule missing in I3 and I4, which § Contexto, lines 105–106, already set
  for every new file.
- Measured 2026-10-13 (`j0ruge/sdd_agents` PR #247, codereview 2.14.1): a 10-file docs-only diff
  classified 0 CODE; the 1184-line plan, split into two ranges (`1–505`, `506–632 + 973–1184`),
  gave two sonnet agents with findings, one of them a confirmed MEDIUM.
- Measured 2026-10-20 (lighthouse_project, the plan of a TypeScript library, no focus, 0 CODE):
  reviewed as CODE, the plan gave round 1 its two MEDIUMs, both in Checks a later step runs. The
  `*.tgz` sabotage a Check should catch read 34/0 instead of 33/1, and a Check's floor was already
  met at HEAD, green before the increment it gates.

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
  same job. Measured 2026-10-19 (Python, rounds 2 and 3 over uncommitted fixes): one `git stash
  create` taken before the fixes was the base of both rounds, and `git stash list` stayed empty.
- **Reproduce between rounds, not during one.** A mutant that confirms a `needs reproduction` finding
  (detection-passes.md, 6.12) edits a file: run it after every agent has returned, against the
  related test files, and restore the file before the next launch (`git status --short` empty).
  When the related tests need only a few files, mutate a copy instead: the module and its tests
  copied to the scratchpad take the mutants while agents still read the tree, which never changes.
  Measured 2026-10-19: 9 mutants of a Python module on such a copy, all killed, and `git status`
  as before.
  In Python, run each mutant with `-X pycache_prefix=<new empty dir>`: a mutant that
  only moves a block keeps the file size, and in the same second as the previous one the
  interpreter reuses that one's `.pyc` (it checks mtime in whole seconds and size). Measured
  2026-10-05: a mutant "passed" that way and failed once the cache was isolated. Not the
  `PYTHONPYCACHEPREFIX` variable: `-I` ignores every `PYTHON*` variable, so it is dropped in silence
  (measured 2026-10-17: `sys.pycache_prefix` was `None` and the `.pyc` landed next to the source).
- **A mutant that does not build is not a kill.** A broken build exits non-zero like a red test, but
  prints neither of the runner's summary lines (`Passed!|Failed!`), so a filter on them stays mute. Write the
  mutant as an exact text replacement that occurs once and must change the file, keep every symbol it leaves in use,
  and filter compiler errors too (`error CS`, `error TS`, `SyntaxError`, `IndentationError`). pytest
  sums up a module that fails to import as `1 error in 0.25s`, with no `failed`: that is a broken
  build, and a mutant that deletes a block's only statement leaves one (write `pass` in its place).
  Measured 2026-10-19: such a mutant was first counted killed. Measured 2026-10-17 (.NET,
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
- **A text finding in code converges when the sentence is true on every path, or leaves.** A
  warning, a comment or a docstring is a claim, as a doc sentence is: fix it by saying what holds on
  each path that reaches it, the silent one included, or delete it. A rewording that is true on the
  path the finding named comes back on the next path. Measured 2026-10-19 (magic_tutor, twelve
  rounds whose LOW count fell from 9 to 2): the doc tail closed when the sentence named the case
  with no warning (a log with no time leaves the file at its time of writing, silently), and the
  next doc round came back with no findings; a warning that said the files kept "the time of
  writing" was false on the path where the folder had stored another date (ext4 clamps the year 3000
  to 2446) until it said only that they did not get the end time.
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
- **Rename identifiers by syntax position, never by `sed`.** A naming finding is the fix that
  touches the most lines, and a text substitution also rewrites strings, comments, attributes
  (`x.name`) and keyword arguments (`f(name=…)`). Rename the `ast.Name` and `ast.arg` nodes of the
  function that binds the name (the `NAME` tokens, for a name unique in the module), and refuse a
  new name the function already uses. Read the source with `io.StringIO(src).readlines()`:
  `str.splitlines()` also breaks on `\x0c`, `\x85`, `\u2028` and other separators that are not line
  ends for Python, so its line numbers drift from the AST's and tokenize's. `col_offset` counts
  UTF-8 bytes: replace in the encoded line. Then prove the diff: the two token streams have the same
  length, and every token that differs is a `NAME` changed by a pair of the map, counted per pair.
  Measured 2026-10-18 (ui24_agent): a `cli.py` with one `\u2028` in a string literal gives 5633
  lines to `splitlines()` and 5632 to the AST, and round 4's tokenize renamer stopped with
  `StopIteration` until the lines came from `StringIO`; round 10 renamed 54 locals in 7 files this
  way (182 occurrences, every one a `NAME` of the map) and the suite stayed green.
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
- **The code a fix round wrote goes to an agent, as a doc does** (*Docs this session wrote*). With
  ≤3 CODE files the inline shortcut has the orchestrator grade its own fix: send those files to
  Phase B agents, launch prompt unchanged. Measured 2026-10-19 (magic_tutor, rounds 2–4 over a
  two-file Python fix): the agent found each round's only MEDIUM — a cached JSON body without `log`
  that crashed every later run, a `break` that left the older items unreachable — and a test written
  first went red on each.
- **The clean round covers the head it read, and nothing committed after it.** The fix for the last
  LOW, be it a docstring, a comment or one reworded message, is a new head: the series closes on a
  round over it, with the code agent and the sweep (the bullet above), not on the round before it.
  Measured 2026-10-19 (magic_tutor): the round over a two-line comment commit came back with a LOW
  in a comment the branch had written two rounds before (a 2 s resolution claimed for exFAT), which
  both earlier rounds had read without raising.
- **A line older than the branch is not the round's.** The per-file agent reads the whole file, so a
  round over a two-line fix also reports code the branch never touched. In Phase C, blame the
  finding's lines (`git blame -L <a>,<b> -- <file>`) and test that commit against the branch's base
  (`git merge-base --is-ancestor <sha> <branch base>`; rc 0 means it is older). Report it labeled
  `pre-existing (not introduced by this branch)`: it does not count against the stop rule, and the
  user decides whether it is fixed here or goes to the tracker. A line outside the round's diff that
  the branch wrote is the branch's own and counts. Measured 2026-10-19 (magic_tutor): the
  comment-commit round above also raised a mistyped `--log` that read as "nothing new" at
  `arquivar.py:229`, written by `5a941e7d`, an ancestor of the branch base (`--is-ancestor`: rc 0).
- **A doc that describes what the series changed belongs to every round.** Step 7 reads the docs in
  the round's CHANGED_FILES, and a re-review range holds only the last fix, so a doc whose clean
  round came before the series added a warning is never read again. In each round, grep the docs for
  every user-visible message or path the series added or changed since that doc's last clean round;
  a doc you then edit goes to an agent (*Docs this session wrote*). Measured 2026-10-19
  (magic_tutor): `docs/monitor.md` had its clean round before the date re-read and its warning
  existed, three rounds passed without it, and writing the missing sentence exposed the warning text
  that was false on one path (*A text finding in code converges*, above).
- **A fix to an amended decision greps every place that cites it.** A plan names a decision
  (`P10`) in each section that applies it, and a fix that rewrites it where the finding pointed
  leaves the other citations on the old text, for a later round to find. `grep -n` the decision's
  id over the doc before the fix is done, and fix every hit in the same commit. Measured 2026-10-20
  (the plan in *Code inside docs*): the fix to the amended P10 left three more places citing it.

## Runtime evidence

Read this in Phase C when the reviewed code already runs (a cron job, a deployed service, a scheduled script) — a diff review cannot see behavior that only shows up on real data.

- Look for the latest 2–3 run outputs: the scheduler's output dir (e.g. `cron/output/<job>/`), the service log, the job's last status. Read them, don't summarize them from memory.
- Read the data the code writes or reads too — an audit trail, a telemetry JSONL, a state file — not only its logs: count its events by origin and time window. Measured 2026-10-05: a per-file LOW ("a new client would be miscounted, if it ever wrote events") became MEDIUM when the audit trail showed 6 real events from that client, and the same trail showed two test runs writing to production where the handoff declared one.
- A build's own outputs count too. When a finding is marked `needs reproduction` and the build has
  already left its outputs (a PDF, a `.log`, a `.blg`, a bundle), read them before asking for a
  rebuild. Measured 2026-10-05: a per-file "`extradate` may be an unknown biblatex option" was
  settled without writing anything: no "Unknown option" in the build log, the style file
  declares the option, and `pdftotext` of the PDF shows "2006a"/"2006b" in the reference list.
- A file operation on a mounted destination (drvfs `/mnt/<x>`, a network or cloud-sync folder)
  does what that mount allows, not what the test's `tmp_path` does. When a finding rests on one
  (`utime`, `chmod`, a rename, a lock), run it on a throwaway file in the real destination folder,
  then delete the file. It is a write outside the scratchpad: do it between rounds, and name the
  folder in the report. Measured 2026-10-19 (magic_tutor): a LOW `needs reproduction` on `os.utime`
  in the Google Drive copy became HIGH. `/mnt/g` answered `PermissionError [Errno 1]` (drvfs files
  owned by root), while `/mnt/j` and ext4 accepted it, so every copy to the Drive had failed since
  the commit.
- Compare each output with what the diff says should happen: a message that contradicts the code's intent, an event firing for the wrong records, a warning that repeats daily. File the mismatch as a finding with the output path and line as evidence.
- Measured: a review of a daily cron missed, in all per-file agents, an event that re-announced 9 records lost years earlier — it showed only in that morning's output.
- Never paste client data or credentials from the output into the report: cite the file and summarize.
