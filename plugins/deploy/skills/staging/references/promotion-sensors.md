# Promotion sensors: what moves, and does it move the pipeline? (Step 4 in full)

Read this when any Step 4 sensor is non-empty, when the promotion PR conflicts with nothing to reconcile, when the backlog is long, or before pushing a promotion whose pipeline only publishes a mobile image tag.

### Step 4 — Sensors: what moves, and does it move the pipeline itself?

```bash
# Content this promotion carries (source → target) — count it, don't just skim it
git log --no-merges origin/$TARGET..origin/$SOURCE --oneline | wc -l
git log --no-merges origin/$TARGET..origin/$SOURCE --oneline

# Content that exists ONLY on the target — the one that bites
git log --no-merges origin/$SOURCE..origin/$TARGET --oneline

# Does the promotion modify the CD workflows themselves?
git diff origin/$TARGET origin/$SOURCE --name-only -- .github/workflows/
```

**Zero commits in the first count is not "done".** It means an earlier promotion already carried
everything — not that it reached the environment. Do not open an empty PR (Step 5 has nothing to
merge). Find the run that the target's current head produced, and go straight to Step 7's proof:

```bash
git rev-parse --short "origin/$TARGET"     # the merge commit of the last promotion
gh run list --branch "$TARGET" --limit 3 \
  --json databaseId,name,conclusion,headSha --jq '.[] | "\(.databaseId) \(.name) \(.conclusion // "—") @\(.headSha[0:7])"'
```

A red or missing run on that sha means the code is promoted and **not deployed**; a green one still
needs the container/migration/HTTP proof, because the run before it may have failed and left the
environment on an older image.

How to read the second one: environment branches accumulate **merge commits**
from previous promotions, and `--no-merges` filters those out. Empty output is
the healthy case — the target has no content of its own and the merge is clean.
Real commits there mean someone committed straight to the environment branch. Do
not force past it: merge the target **back** into the source first (a merge
commit, not a squash), then promote. Measure the conflicts before touching the
working tree — `git merge-tree --write-tree --name-only origin/$TARGET HEAD` lists
exactly the files that will conflict, so you know whether it is two adjacent
`import` lines or a real disagreement before you start.

**Empty output and a clean `merge-tree` still do not mean GitHub agrees.** A hotfix that went
straight to the production branch and was merged back into the source can leave source and
target with **two** merge bases (criss-cross). `merge-tree` resolves that through a virtual base
and reports nothing; GitHub marks the promotion PR `CONFLICTING / DIRTY` anyway. Measured: a target
whose tree equalled a source commit, zero commits of its own, two bases, and the PR stuck. The fix
is the same back-merge with nothing to reconcile: merge the target into the source (PR, merge
commit), check `git diff <old source> <new source>` is empty so the local gate still covers the
tree, and publish the status on the new sha. Count the bases before opening the PR:
`git merge-base --all origin/$TARGET origin/$SOURCE | wc -l` (more than 1 → back-merge first).

One more thing that reconciliation brings in: **the target's debt becomes your
gate.** CI checks the whole repository, not your diff. When the content merged
back was itself never gated (a PR merged during a quota block, say), its
formatting or lint failures now fail *your* promotion's CI — 17 files red on
prettier from the other PR is what it looked like. It is not your regression, but
it is yours to clear; do it in a separate commit so the merge commit stays a
pure reconciliation and the fix is easy to drop if upstream cleans it up. Squashing that reconciliation rewrites the
shared history and guarantees the same conflict returns on the next promotion.

The quota block is not the only way content arrives ungated. A PR whose files **all** match the
CI's `paths-ignore` (`**/*.md`, `docs/**`) gets **no run at all** — and "no run" is not green when
the linter checks those same files. Measured: a PR touching only `TODO.md` merged with zero checks,
while `prettier --check .` covers `.md`; the next promotion's CI went red on that one file and the
deploy was skipped. Compare `paths-ignore` with the linter's scope (`.prettierignore`), and run the
repo-wide lint on `SOURCE` before promoting.

Count the first one before you promote. A CD that has been failing for a while (Step 0b) turns
the next successful run into something that is **not incremental**: the backlog ships all at once.
Measured on one repo — the pipeline had been dead for six weeks, and the first green deploy carried
15 commits including an offline-storage feature, *and* replaced a hand-built image with a pipeline
one that had never run in that environment. Both halves are new at the same moment, so a failure
afterwards has two candidate causes and no way to separate them. Say the number out loud in the
promotion, and treat a long backlog as a reason to have the rollback target ready before you start,
not after.

**"Have the rollback target ready" is often impossible with what the pipeline leaves behind.** Many
staging pipelines publish only a **mobile tag** (`:staging`, `:latest`): every deploy re-points it,
so a minute after the promotion there is no name left for the image that was serving before. The
moment to fix that is *before* pushing, while the old image is still identifiable:

```bash
ssh <host> 'docker inspect <container> --format "{{.Image}}"'      # sha256:1b09...
ssh <host> 'docker tag sha256:1b09... <img>:pre-<version>'
```

That tag survives the pipeline's own cleanup — `docker image prune -f` without `-a` removes only
**dangling** images, and a tagged one is not dangling. Skip it and rollback degrades into "rebuild
the previous commit and hope", which is not a rollback.

The third command answers a question people forget to ask: if the promotion
changes `cd-*.yml`, which pipeline is about to run — the old one or the new one?
GitHub uses the workflow file **from the pushed commit**, so a change to the
staging workflow takes effect in this very run, while a change to the production
workflow only lands as a file and takes effect on the next promotion to
production. Say which case you are in, so nobody is surprised either way.
