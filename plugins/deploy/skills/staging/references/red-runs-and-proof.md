# Red runs, reruns and proof of deploy (Step 7 in full)

Read this when a run is red (before rerunning or re-promoting), when it is green and the deploy still has to be proved, or when an e2e suite fails after the deploy.

### Step 7 — Report the outcome honestly

On failure, show the failing step and say the deploy did not happen:

```bash
gh run view <run-id> --log-failed
```

#### Some red runs mean "run it again", not "start over"

Registry pushes fail transiently. Measured here: `ERROR: unknown blob` pushing to GHCR *after*
every layer had uploaded (76.7 s of pushing, then the manifest step failed). Nothing was wrong
with the build or the commit — `gh run rerun --failed` went green with no code change. Re-promoting
would have been the wrong reflex: there is nothing to fix, and a second merge commit on the
environment branch buys noise instead of a deploy. Same family: `TLS handshake timeout` or
`unauthorized` on `docker login`, `blob upload unknown`, `502`/`503` from the registry.

A self-hosted runner that shares its host with the environment adds one more: a **test timeout**
in a gate job. Measured: two repo-wide sweep tests (one takes ~0.2 s locally) hit 7.1 s and 6.2 s
against the 5 s default on a 4-core host at load ~4.5, and `gh run rerun --failed` went green.
Check the load (`uptime`) and that the failed step precedes the build, then rerun. The same
timeout recurring across promotions is the test's budget to fix, not luck to retry.

Before rerunning, answer one question: **did the failed run already change the environment?** Which
step failed decides it. A failure in build-and-push happens before anything is deployed; a failure
in a smoke or cleanup step happens *after* the new image is live, and there a rerun is not neutral —
it redeploys. Prove it instead of reasoning about it, with the verification command above:

```bash
ssh <host> 'docker inspect <container> --format "{{.Created}} {{.Config.Image}}"'
```

An unchanged `Created` means the environment is still on the old image and the rerun is safe. A
changed one means the deploy landed and the failure is downstream of it — read that step before
touching anything.

```bash
gh run rerun <run-id> --failed     # keeps the SAME run id
```

The reused run id is worth knowing because it saves a wrong turn: `gh run watch <run-id>` and every
verification command above keep working unchanged, and `gh run list` will not show a new run to
chase.

If the same step fails twice with the same error, stop calling it transient and read it as a real
fault.

On success, report the run URL and — this is the part worth stating explicitly —
**which environment is now serving the new code**. A pipeline that ends green
having skipped its smoke step is not the same as a verified deploy; check that
the smoke/health step actually ran rather than being skipped.

Green is the pipeline's opinion of itself. When the workflow has no smoke step — many
do not — prove the deploy with the data it should have changed, at the environment it
should have changed it in:

```bash
# 1. Migrations landed where the app reads from (Prisma shown; use the ORM's equivalent)
DATABASE_URL="<target env DB, read-only credentials>" npx prisma migrate status
# 2. The container running now was created by THIS run, not last month's
ssh <host> 'docker inspect <container> --format "{{.Created}} {{.Config.Image}}"'   # compare with the run's timestamps
#    Read BOTH fields. `Created` catches a stale container; `Config.Image` catches a stranger one:
#    an image name with no registry prefix (`dsr-web:latest`, not `ghcr.io/<org>/<img>:staging`)
#    means the container was built by hand on the host and the pipeline has never deployed here at
#    all. Compare it against the `image:` the compose file declares — measured once, they differed,
#    and "container up + hostname 200" had been reading as a working pipeline for weeks.
# 3. The public hostname answers with the new build
curl -s -o /dev/null -w '%{http_code}\n' https://<staging hostname>/
```

Measured on one deploy: four migrations stamped 18:49:18, container `Created` 18:49:18,
API answering `401 Access Token required` — that is a verified deploy. A green run whose
container is still `Up 5 days` is not.

#### A red e2e after the deploy is not yet a verdict on the deploy

A suite that runs against a shared environment carries its own debt: a test account with the wrong
role, a runner whose network drops (`net::ERR_NETWORK_CHANGED`). Triage before you call it a
regression or roll back:

- **Hard vs flaky.** A test is hard-failed only when *no* attempt passed. Comparing every ✘ line
  counts each flaky first attempt as a failure.
- **Compare the hard set with the last run on the previous image**, by test **title**, not
  `file:line`: a spec edited in this promotion shifts its line numbers, and the lookup reads "did not
  run last time".
- **Reproduce only what is new**, from the operator's machine against the same environment, with
  `--retries=0`. A cancelled run never reaches the reporter's summary, which is where the errors
  are printed; the previous run's summary or the isolated rerun is where you read them.

Measured on one promotion (2026-10-06): 11 hard failures; 8 were already there on the previous image
(one account still had an admin role, one runner network flake), and the 3 new ones passed in
isolation in 4–6 s. The deploy was fine; the suite was not.

The work is complete only when the pipeline finishes successfully **and** the proof
above holds. Do not exit silently on failure.
