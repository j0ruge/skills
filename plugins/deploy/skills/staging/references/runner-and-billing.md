# Runner and billing: will the target pipeline run? (Step 0b in full)

Read this when a `cd-*.yml` at the promoted commit has a hosted label, or when a run is red with zero steps. The `SKILL.md` keeps the rule; this file keeps the signature, the commands and the measured case.

### Step 0b — Will the target pipeline actually *run*? Read `runs-on` at the promoted commit

Knowing which branch triggers staging is not the same as knowing the job will start. Print the
runner of every job in the target workflow **as it exists in the commit you are promoting** —
GitHub runs the workflow file from the pushed commit, so the version on the target branch today
may not be the one that executes:

```bash
git show "origin/$SOURCE:.github/workflows/cd-staging.yml" | grep -n 'runs-on'
```

Hosted labels (`ubuntu-latest`, `windows-*`, `macos-*`) consume the org's Actions quota. When
the org is over its spending limit or a payment failed, a hosted job **never starts** — and
nothing tells you. The signature, measured on a real repo: job `conclusion: failure`, **zero
steps**, empty `runner_name`, ~3 s, and `gh run view --log-failed` answers `log not found`. It
reads as a broken build. The actual message lives only in the check-run annotations:

```bash
gh api /repos/<owner>/<repo>/check-runs/<job_id>/annotations -q '.[] | .message'
# "The job was not started because recent account payments have failed or your spending limit..."
```

Why this belongs in a *deploy* skill: in that repo the staging pipeline had silently not run
for two months — the last green deploy was the last one before the block — while PRs kept being
merged, one of them with zero CI. Self-hosted jobs bypass the quota entirely. So **a promotion is
only safe when the `cd-*.yml` at the promoted commit runs on runners that will pick the job up**;
if the promotion itself moves the jobs to self-hosted, that very push is the one that revives the
pipeline (see Step 4 on workflow changes). If it does not, say so before pushing anything: the
merge would land, the deploy would not, and the environment would keep serving the old image
while everything looks green.

**Default: self-hosted, and no hosted Actions.** Treat a hosted label in a `cd-*.yml`, or in a gate
the promotion depends on, as a finding rather than a fact of life. Propose one of two moves: put
the job on a self-hosted runner, or run the deploy as a script, Ansible or SSH from the operator's
machine. Never add a new hosted job, and that includes a "light" gate in front of the deploy. If
the pipeline has to start from a GitHub event, the workflow runs **entirely** on self-hosted.
Propose the migration; do not perform it inside the promotion.
