# The gate on the promoted commit (Step 3 in full)

Read this when hosted CI is absent, queued or blocked, when a promotion PR shows `CONFLICTING`, or before publishing a `local/ci` status.

### Step 3 — Wait for CI green on the exact commit being promoted

Local checks and CI are not the same thing: CI runs integration suites,
containers and matrix jobs your laptop skips. Promoting while CI is still
running means finding out in the deploy what a cheap wait would have told you.

First make sure a run *can* exist. A PR with merge conflicts gets **no `pull_request` run at
all** — GitHub cannot build the merge ref, so it does not even queue the workflow. Waiting for
green there waits forever, and the last green run you find belongs to an older commit:

```bash
gh pr view <number> --json mergeable,mergeStateStatus -q '[.mergeable, .mergeStateStatus] | @tsv'
# CONFLICTING / DIRTY  → reconcile with the target first (Step 4), then come back
```

```bash
SOURCE=$(git rev-parse --abbrev-ref HEAD)
git fetch origin
gh run list --branch "$SOURCE" --limit 5 \
  --json databaseId,name,status,conclusion,headSha \
  --jq '.[] | "\(.databaseId) \(.name) \(.status)/\(.conclusion // "—") @\(.headSha[0:7])"'
```

Match the run's `headSha` against the commit you are promoting — a green run on
an older commit proves nothing about this one. If it is still running:

```bash
gh run watch <run-id> --exit-status --interval 20
```

Red CI stops the promotion.

A run that is red with **zero steps** is not red CI — it is the quota block from Step 0b, and the
same block will stop the target pipeline too. Do not read it as "the tests failed"; read the
annotations.

**The gate of record is local**, in line with the default in Step 0b. Hosted CI, when it exists,
is informational: its green does not replace the local gate, and its absence does not block it. It
also covers the cases where waiting gets you nowhere, such as a private repo under a billing block,
or PR jobs that sit `queued` with no runner assigned. Promoting with no gate at all is never an
option. Do this:

- Mirror the CI's own `run:` lines (the workflow, or the composite actions it calls such as
  `.github/actions/ci-gate-*`) on a tree identical to the promoted sha. Run one step at a time and
  record one exit code per step. Never pipe through `| tail`: it hides the exit code.
- Include the integration suite. It is the part your laptop usually skips and hosted CI used to
  cover.
- Publish the result through the Statuses API, which is not Actions and is not billed. Use
  `state=failure` when a step fails, and never `success` without having run the gate on that sha:

```bash
gh api -X POST repos/<o>/<r>/statuses/<sha> -f state=success -f context=local/ci \
  -f description="lint + typecheck + build + tests ok"
```

Measured on a release PR: all four `ci.yml` jobs stayed `queued` with no runner. The local gate
went 16/16, integration 279/279, and both statuses went on the sha before the merge.
