# Deploy without Actions: an agent on the host watches the branch (Steps 0, 3, 4, 6 and 7)

Read this when no **enabled** workflow listens to a push and the repo documents another deploy
path — typically an agent container on the environment host that watches the environment branch,
runs the test gate on the server and deploys. The `SKILL.md` keeps the rule; this file keeps how
to recognise the topology, how each step changes, and the measured case.

### Recognise it (Step 0)

```bash
gh workflow list --all                     # `disabled_manually` = its `on:` block is dead text
gh api repos/<o>/<r>/commits/$(git rev-parse "origin/$TARGET")/statuses \
  --jq '.[] | [.created_at, .context, .state, .description] | @tsv'
```

- Statuses named per environment (`gate/staging`, `deploy/staging`, a request context such as
  `disparo/staging`) on the head of the environment branch are the agent's signature.
- The repo says so somewhere: a rules file (`.claude/rules/devops.md`), a runbook
  (`docs/deploy/`), an ADR, an `infra/<agent>/` directory. Read the runbook before promoting:
  it names the follow command and the request command.
- A disabled `cd-staging.yml` still in the tree is a record, not a pipeline. Reading its
  `on.push` builds the right map for a pipeline that no longer runs.

### What changes in each step

| Step | With Actions | With a host agent |
| --- | --- | --- |
| 3 — gate | CI run green on the exact sha | the local gate on the PR head (`local/ci` status) is evidence; the **agent** gates the merge commit itself, on the server, before deploying |
| 4 — sensors | workflow files in the diff move the pipeline in this very push | the agent's own directory in the diff (`git diff origin/$TARGET origin/$SOURCE --name-only -- <agent-dir>/`) moves **nothing** on merge: before merging, prove the host already runs that version (the file on the host, or the tool inside the agent container); if it does not, update and rebuild the agent first, by the runbook |
| 4 — disk | the build runs on the runner's disk; a self-hosted runner on the environment host needs the same check | the agent builds the images **on the environment host**, and the deploy's prune runs after the build: before merging, read `df -h /` and `docker system df` there. `docker rmi` of an image built on that host frees nothing while the BuildKit cache holds its layers; `docker builder prune -f --filter until=168h` does (`cicd` lesson 118) |
| 5 — promote | PR merge commit | the same: the merge on the environment branch **is** the trigger |
| 6 — watch | `gh run list --branch "$TARGET"` | the commit statuses of the merge commit, or the repo's follow script. Nothing in 2 minutes = the agent is down or cannot authenticate: read its logs on the host |
| 7 — red | `gh run rerun --failed` | one attempt per (sha, request): a red deploy is **not** retried on its own. Re-request through the repo's request command, and only for the **head** — the agent never reads an older sha |
| 7 — proof | the same | the same: `docker ps` image tags, the data, the hostname, then the e2e |

**A fix to the executor does not travel with the commit.** The gate and the deploy script come
from the tree of each sha; the agent's own image does not. When the failure is in the agent
(a missing tool in its image), the fix is a PR that lands in the source branch **plus** a rebuild
on the host, and then a new request for the **same** head. No new promotion: the head did not
change, and the environment branch would carry a commit that changes nothing deployed.

### Measured cases (`lighthouse_project`)

**2026-10-13, the fix after the failure.** The first deploy through the agent (`ea2e774`, promotion PR #19) passed the gate on the host in
~4 min and failed in the frontend build, before anything was brought up: the agent image lacked
`docker-buildx-plugin`, so `docker build` fell back to the legacy builder and rejected
`COPY --chmod` (`cicd` lesson 115). Staging kept serving the previous image. The fix went to
`develop` by PR (#20); the agent was rebuilt on the host; the same head was requested again
(`infra/staging/disparar.sh`): gate 16/16, deploy ~1.5 min, smoke and role proof green, then the
staging e2e 4/4. `gh run list` showed nothing throughout — the statuses were the only record.

**2026-10-14, the check before the merge.** The 0.3.0 promotion (PR #23) still carried that fix
from `develop` to `staging`: the Step 4 diff over `infra/deployer/` listed `Dockerfile`. Merging
it changes nothing on the host, so before the merge the host was probed:
`docker exec jrc-staging-lh-deployer docker buildx version` answered, the rebuild of the day before
was in place, and the promotion went ahead: gate 15/15 on the host, deploy, then the staging e2e.
