# PR Branch — Phase 1.1 in full

Read this at Phase 1.1, before touching any file: whether this run is the installed copy, where
the fixes are made, whether another writer is still active in the tree, and the sweep of leftover
checklists. SKILL.md keeps the decision; this file carries the commands and the why.

## Is this run the installed copy?

When the skill was loaded from a plugin cache (`~/.claude/plugins/cache/…`), the harness names the
directory it loaded ("Base directory for this skill"). A session opened before a plugin update
keeps loading the old directory until `/reload-plugins`, and nothing else says so:

```bash
python3 - "<base directory>" <<'EOF'
import json, os, sys
d = json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json')))
paths = [e['installPath'] for k, v in d['plugins'].items() if k.startswith('codereview@') for e in v]
print('current' if any(sys.argv[1].startswith(p + '/') for p in paths) else f'STALE, installed: {paths}')
EOF
```

`STALE` → stop and ask for `/reload-plugins`, then run the skill again. A skill loaded from a
symlink in `~/.claude/skills` or from a project is read from disk: nothing to check. Measured
2026-10-05 (sdd_agents PR #222): loaded from `…/codereview/2.9.4/` with `installPath`
`…/codereview/2.10.0`; the run missed the per-commit coverage rule added in between, and its report
never said that the four fix commits it pushed had been reviewed by no bot.

## Where the fixes are made

```bash
CUR=$(git branch --show-current)
HEAD_REF=$(gh pr view "$PR" --json headRefName -q .headRefName)
```

- **`CUR` == `HEAD_REF`** → work here.
- **The head mirrors another branch** (a review-only PR whose head the author keeps equal to
  `main`, against a base cut before the work) → fix on the source branch, as the author says,
  and mirror it with `git push origin <source>:<head>` before 5.0. A worktree on the mirror
  commits where nobody develops, and the next mirror push stops being a fast-forward. Measured
  2026-10-04 (projeto-final-vdr PR #3, `main` mirrored to `revisao-d75`): the fix went to `main`
  as `4b08c16`, the mirror push was `b1f1224..4b08c16`, and 5.0 compared the head after it.
- **They differ** → open a **worktree** on the PR branch and do the whole run there (fixes,
  checklists, tests), never `git checkout` in the user's checkout:

  ```bash
  git fetch origin "$HEAD_REF"
  WT="../$(basename "$(git rev-parse --show-toplevel)")-pr$PR"
  git worktree add "$WT" "$HEAD_REF"     # local branch exists: checks it out there
  # no local branch yet:  git worktree add -b "$HEAD_REF" "$WT" "origin/$HEAD_REF"
  cd "$WT"
  ```

  At the end (after Phase 6): `git worktree remove "$WT"` from the original checkout. If the branch
  is already checked out in another worktree, `git worktree add` refuses — work in that worktree.

**Why a worktree and not a checkout.** A clean tree is not an idle tree. Measured on 2026-10-02
(sdd_agents PR #195): the checkout was clean on a mission branch while a planner subagent was
writing that mission's artifacts into it. A `git checkout` of the PR branch would have carried
its files to the wrong branch, or pulled the tree out from under it. Another session, an
`sdd run` or an editor's autosave are the same story. The worktree leaves the user's checkout,
and whoever is writing in it, exactly as it was.

**Dirty tree with the PR branch checked out here** (`CUR` == `HEAD_REF`, uncommitted changes):
stop and report — those may be the user's edits in progress, and mixing review fixes into them
makes the commit unreviewable.

When the run ends, state the branch **and** the path where the edits landed.

## Same branch, another writer still active

`CUR` == `HEAD_REF` with a clean tree says nothing about who else is working in it. Before Phase 2
writes a checklist into the root and Phase 3 edits a file, look for a process still writing in or
measuring this tree — the project's pipeline runner, an agent session, a long test suite, a
stamp or health run. On Linux, list the processes whose working directory is inside it:

```bash
TOP=$(git rev-parse --show-toplevel)
for p in /proc/[0-9]*; do c=$(readlink "$p/cwd" 2>/dev/null) || continue
  case "$c" in "$TOP"|"$TOP"/*) printf '%s %s\n' "${p#/proc/}" "$(tr '\0' ' ' < "$p/cmdline" | cut -c1-100)";; esac
done 2>/dev/null
```

The list always carries noise — your own harness and shell, and long-lived daemons that merely
started there (a Codex `app-server daemon` up for 14 days showed up in the measured run). Judge by the
command, not by presence; `ps -o etime= -p <pid>` tells a daemon from a run started an hour ago.
Matching the path in the command line is not enough: runners started as `./bin/…` never name it.

**One is active** → do Phases 1–3.1 read-only, keep the checklists **outside** the tree (a scratch
directory), apply nothing, and tell the user what is running; resume at 3.2 once it exits, or when the
user stops it. A worktree does not help here: git refuses a second checkout of the same branch.

**Why.** Measured on 2026-10-02 (sdd_agents PR #196): the checkout sat clean on the PR branch while the
pipeline's PR-phase session and the mutation-catalogue run it had launched were still working in it.
Under the "work here" rule a fix to `bin/` would have changed the content the stamp was measuring,
and an untracked `coderabbit-review.md` in the root would have been charged by the runner's hat guard
to the running session — stopping the pipeline for a file it never wrote.

## Sweep leftover checklists

`*-review.md` files in the root of the tree you work in are this skill's scratch space from a
previous run. One whose header names a **different** PR is stale: delete it rather than read it as
if it described the current PR (Phase 3's cross-reviewer check consults these files).

```bash
grep -l "Review — PR #" *-review.md 2>/dev/null | while read -r f; do
  head -5 "$f" | grep -q "PR #${PR}\b" || { echo "stale, removing: $f"; rm -- "$f"; }
done
```
