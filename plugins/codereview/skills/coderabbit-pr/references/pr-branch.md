# PR Branch — Phase 1.1 in full

Read this at Phase 1.1, before touching any file: where the fixes are made, and the sweep of
leftover checklists. SKILL.md keeps the decision; this file carries the commands and the why.

## Where the fixes are made

```bash
CUR=$(git branch --show-current)
HEAD_REF=$(gh pr view "$PR" --json headRefName -q .headRefName)
```

- **`CUR` == `HEAD_REF`** → work here.
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

## Sweep leftover checklists

`*-review.md` files in the root of the tree you work in are this skill's scratch space from a
previous run. One whose header names a **different** PR is stale: delete it rather than read it as
if it described the current PR (Phase 3's cross-reviewer check consults these files).

```bash
grep -l "Review — PR #" *-review.md 2>/dev/null | while read -r f; do
  head -5 "$f" | grep -q "PR #${PR}\b" || { echo "stale, removing: $f"; rm -- "$f"; }
done
```
