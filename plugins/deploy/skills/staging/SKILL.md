---
name: staging
description: "Promote code to staging (and on to production) through the repo's real CD pipeline. Reads each workflow's `on.push.branches` and `runs-on` instead of assuming — the wrong branch can deploy production, and a hosted job under a billing block never starts. Waits for CI green on the exact commit, promotes by PR merge commit, watches the run, then proves the deploy by the data. Triggers — deploy staging, promote to staging, subir para staging, CD pipeline, cd-staging, promover para produção."
metadata:
  version: 3.0.0
---

## Deploy to Staging

Promote the current work to the staging environment through whatever CD pipeline
the repository actually has.

**Read this before anything else.** A deploy command is one `git push` away from
shipping to production. Branch names carry no universal meaning: in one repo
`develop` triggers staging and `main` is just kept in sync; in another the chain
is `develop → staging → main`, where pushing `main` deploys to real users. An
earlier version of this skill hardcoded the first topology, so running it in a
repo of the second kind would have deployed **production** while reporting
"staging". That is the failure this workflow exists to prevent.

So the first step is never `git push` — it is reading the workflows to learn
which branch triggers what. Everything else follows from that map.

### Step 0 — Discover the topology (never assume it)

Print the trigger block of every workflow and build the branch → pipeline map:

```bash
for f in .github/workflows/*.y*ml; do
  echo "── $f"
  awk '/^on:/{flag=1} flag{print} /^permissions:|^env:|^jobs:/{if(flag) exit}' "$f" | head -12
  echo
done
```

Read the output and write down, explicitly:

| Branch | Workflow it triggers | Environment |
|---|---|---|
| e.g. `staging` | `cd-staging.yml` | staging |
| e.g. `main` | `cd-production.yml` | **production** |

Two things to settle before moving on:

- **Which branch is the staging trigger?** That is your `TARGET`. Your current
  branch (usually `develop`, sometimes a feature branch) is the `SOURCE`.
- **Which branch is a production trigger?** Mark it. You must not push it in
  this flow, and if `TARGET` turns out to equal it, stop and tell the user —
  what they asked for and what would happen have diverged.

If no workflow listens to a push at all (deploys are manual, or on tags), say so
and stop. Inventing a push target is how a repo gets deployed sideways.

A useful confirmation, since workflow headers usually state the intent in prose:

```bash
head -12 .github/workflows/cd-*.y*ml
```

### Step 0b — Will the target pipeline actually *run*? Read `runs-on` at the promoted commit

GitHub runs the workflow file from the pushed commit, so read the runners there, not on the target
branch today:

```bash
git show "origin/$SOURCE:.github/workflows/cd-staging.yml" | grep -n 'runs-on'
```

A hosted label (`ubuntu-latest`, `windows-*`, `macos-*`) under a billing block **never starts**, and
the red run reads as a broken build (zero steps, empty `runner_name`, `log not found`); the real
message lives only in the check-run annotations. Promote only when the `cd-*.yml` at the promoted
commit runs on runners that will pick the job up, and say so before pushing if it does not.
**Default: self-hosted, no hosted Actions**: a hosted label in a `cd-*.yml`, or in a gate the
promotion depends on, is a finding. Propose the migration; do not perform it inside the promotion.
When a runner is hosted or a run is red with zero steps, read `references/runner-and-billing.md`
(signature, annotations command, the measured case).

### Step 1 — Working tree must be clean

```bash
git status --short
```

Uncommitted changes mean the thing you are about to deploy is not the thing you
tested. Abort and tell the user what is dirty.

### Step 2 — Pre-flight, derived from the repo

The old version of this skill hardcoded `yarn test --watchAll=false` and
`npx eslint src/`, which silently did nothing in repos using npm, pnpm, a
different lint scope, or a monorepo. Detect instead:

```bash
ls package-lock.json yarn.lock pnpm-lock.yaml 2>/dev/null   # package manager
node -e "console.log(Object.keys(require('./package.json').scripts||{}).join(' '))"
```

Run the scripts that exist (`lint`, `typecheck`, `test`), with the matching
runner. Two traps worth knowing:

- **Monorepos**: the root script often fans out to workspaces
  (`npm run test --workspaces`), while `typecheck` may only exist per workspace
  (`npm run typecheck --workspace=packages/backend`). A root command that finds
  no script exits 0 and looks like a pass.
- **`tsc --noEmit` can be a no-op.** In a solution-style `tsconfig.json`
  (`"files": []` with project references) it type-checks nothing. Use
  `tsc -b --noEmit` there.

Pre-flight is a fast local filter, not the gate. The gate is Step 3.

### Step 2b — Does the promotion carry a version bump? Do it before the gate

Many repos bump the version *as part of* the promotion: it becomes the version the app displays,
the tracker's fixVersion and the tag that anchors the CHANGELOG. Look for the rule instead of
assuming there is none: a release script (`release:bump`, `npm version`, `cz bump`), a rule file
(`grep -rniE 'bump' .claude/rules/ docs/ CONTRIBUTING.md`), earlier release commits
(`git log --oneline --grep='release' -5 "origin/$SOURCE"`). If the rule exists, bump **first** and put
the commit where the precedent puts it (straight on `$SOURCE`, or by PR). Only then run Step 3. The
bump creates the commit you are about to promote, so a gate that ran before it publishes `local/ci`
on a sha that never ships.

### Step 3 — Wait for CI green on the exact commit being promoted

- **A conflicting PR gets no run at all.** Check before waiting:
  `gh pr view <n> --json mergeable,mergeStateStatus`. `CONFLICTING / DIRTY` → reconcile first (Step 4).
- **Match the run's `headSha`** against the commit you promote (`gh run list --branch "$SOURCE"`,
  then `gh run watch <run-id> --exit-status`). A green run on an older commit proves nothing. Red CI
  stops the promotion; red with **zero steps** is the Step 0b block, not failed tests.
- **The gate of record is local.** Mirror the CI's own `run:` lines (the workflow, or the composite
  actions it calls such as `.github/actions/ci-gate-*`) on a tree identical to the promoted sha: one
  exit code per step, never through `| tail`, integration suite included. Hosted CI is informational.
- **Publish it through the Statuses API**, which is not Actions and is not billed. `state=failure`
  when a step fails, and never `success` without having run the gate on that sha:

```bash
gh api -X POST repos/<o>/<r>/statuses/<sha> -f state=success -f context=local/ci \
  -f description="lint + typecheck + build + tests ok"
```

When hosted CI is absent or queued, or before publishing the status, read `references/local-gate.md`.

### Step 4 — Sensors: what moves, and does it move the pipeline itself?

```bash
git log --no-merges origin/$TARGET..origin/$SOURCE --oneline | wc -l     # what this promotion carries
git log --no-merges origin/$SOURCE..origin/$TARGET --oneline             # content ONLY on the target
git merge-base --all origin/$TARGET origin/$SOURCE | wc -l               # merge bases (want 1)
git diff origin/$TARGET origin/$SOURCE --name-only -- .github/workflows/ # does it move the pipeline?
```

| Reading | What it means | Do |
|---|---|---|
| 0 commits to carry | an earlier promotion carried everything, not that it reached the environment | no empty PR: find the run on the target's head and go to Step 7's proof |
| commits only on the target | someone committed straight to the environment branch | merge the target **back** into the source (merge commit, never squash); measure conflicts first with `git merge-tree --write-tree --name-only` |
| more than 1 merge base | criss-cross, typically a hotfix straight to production that was merged back; GitHub marks the PR `CONFLICTING` while `merge-tree` is clean | the same back-merge, even with nothing to reconcile; confirm the tree did not change |
| a long backlog | the next deploy is not incremental | say the number; have the rollback target ready **before** pushing (tag the serving image `pre-<version>` when the pipeline only publishes a mobile tag) |
| workflow files change | a staging change runs in this very push; a production change waits for the next production promotion | say which case you are in |

Reconciliation also makes **the target's debt your gate**, and a PR fully matched by `paths-ignore`
merged with no run at all: run the repo-wide lint on `SOURCE` before promoting. When any row above
applies, read `references/promotion-sensors.md` (commands and the measured incidents).

### Step 5 — Promote with a merge commit, via PR

For long-lived environment branches, promote with a **merge commit**, and prefer
a PR so the promotion leaves an artifact someone can read later:

```bash
gh pr create --base "$TARGET" --head "$SOURCE" \
  --title "Release: promote $SOURCE → $TARGET" --body-file <notes>
gh pr merge <number> --merge          # --merge, NOT --squash
```

Squash is wrong here specifically because environment branches are long-lived:
it creates a commit that shares no ancestry with the source, so the next
promotion sees the two branches as divergent and conflicts on content that is
actually identical.

If the repo's convention is a direct push instead of a PR, follow the
convention — check how previous promotions were made (`git log --merges
origin/$TARGET -5`) rather than imposing one.

Whatever the mechanism: **push only `$TARGET`.** Do not "sync" the production
branch as a side effect. If the user wants production, that is a separate,
explicit promotion (see below), not a step tucked inside a staging deploy.

### Step 6 — Watch the pipeline on the target branch

The run appears on the branch that received the push — `$TARGET`, not the source
branch. (The old version of this skill looked on `develop` unconditionally and
would have reported on the wrong pipeline.)

```bash
sleep 10
gh run list --branch "$TARGET" --limit 3 \
  --json databaseId,name,status,conclusion,headSha \
  --jq '.[] | "\(.databaseId) \(.name) \(.status)/\(.conclusion // "—") @\(.headSha[0:7])"'
gh run watch <run-id> --exit-status --interval 20
```

If no run appears, check the workflow's `paths-ignore` before assuming the worst: a push whose
files **all** match the ignore list (docs, `.claude/**`, specs) does not trigger the pipeline,
and that is the intended outcome — nothing to deploy. A promotion that carries code and still
produces no run is the Step 0b case.

### Step 7 — Report the outcome honestly

On failure, show the failing step (`gh run view <run-id> --log-failed`) and say the deploy did not
happen.

**Some red runs mean "run it again", not "start over".** Transient registry errors (`unknown blob`,
`TLS handshake timeout`, `unauthorized` on `docker login`, `502`/`503`) and test timeouts in a gate
on a self-hosted runner that shares its host with the environment are fixed by
`gh run rerun <run-id> --failed`, which keeps the same run id, never by re-promoting. Before
rerunning, prove the environment did not change: a failure after the deploy step makes the rerun a
redeploy. The same step failing twice with the same error is a real fault.

**Green is the pipeline's opinion of itself.** Report the run URL and which environment now serves
the new code, then prove it with the data, at that environment:

```bash
DATABASE_URL="<target env DB, read-only credentials>" npx prisma migrate status   # or the ORM's equivalent
ssh <host> 'docker inspect <container> --format "{{.Created}} {{.Config.Image}}"'  # BOTH fields, against the run
curl -s -o /dev/null -w '%{http_code}\n' https://<staging hostname>/
```

A red e2e after the deploy is triaged before it becomes a verdict: hard versus flaky, the hard set
compared with the last run on the previous image by test title, and only what is new reproduced
with `--retries=0`. When a run is red, or before calling a green one deployed, read
`references/red-runs-and-proof.md` (how to read each probe, the measured cases).

The work is complete only when the pipeline finishes successfully **and** the proof
above holds. Do not exit silently on failure.

### Promoting to production

Same procedure, one step further along the chain: `SOURCE` becomes the staging
branch, `TARGET` becomes the branch whose push triggers the production workflow.
Three differences that matter:

- **Ask first.** Staging is reversible in practice; production is visible to
  real users. Confirm explicitly, even if the user asked for "deploy" in general
  terms earlier in the conversation.
- **Workflow changes cross over here.** Edits to `cd-production.yml` that rode
  along in an earlier promotion are inert until this merge — the production
  pipeline that runs is the one in the commit you are pushing now.
- **Dump the production database before the merge, and verify it.** An image
  rollback target does not undo a migration. Take `pg_dump -Fc` (or the engine's
  equivalent) inside the production DB container, then confirm the expected
  tables are in it with `pg_restore --list`. Copy it off the host and check the
  sha256 matches on both copies. Put the path and hash in the PR body. If there
  is no verified dump, the merge does not happen. In one 0.9.0 promotion
  carrying 11 migrations, the user had to ask for this mid-flow, because the
  procedure only implied it.

### References: read them when a step sends you there

| File | Read it when |
|---|---|
| `references/runner-and-billing.md` | when a `cd-*.yml` has a hosted label, or a run is red with zero steps |
| `references/local-gate.md` | when hosted CI is absent, queued or blocked, or a promotion PR shows `CONFLICTING` |
| `references/promotion-sensors.md` | when a Step 4 sensor is non-empty, the PR conflicts with nothing to reconcile, or the backlog is long |
| `references/red-runs-and-proof.md` | when a run is red, or green and the deploy still has to be proved |

### Gotchas

- The image tag and the runner label come from the workflow, not from this
  skill — read them there if the user asks.
- `gh pr merge` sometimes merges successfully and then fails while updating the
  local checkout, which reads as "the merge failed". Confirm with
  `gh pr view <n> --json state,mergeCommit` before retrying, or you will try to
  merge something already merged.
- After a squash merge, `git branch -d` refuses with "not fully merged" even
  when every change is integrated — it tests ancestry, and squash breaks it. The
  sensor that actually settles it is content: `git diff <target> <branch>` empty
  means nothing was left behind.
