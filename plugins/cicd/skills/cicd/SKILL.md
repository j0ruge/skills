---
name: cicd
metadata:
  version: 2.35.0
description: "GitHub Actions / Docker / GHCR pipeline troubleshooting and config, auto-routed by stack (Node/Prisma, Django/gunicorn, Vite). Self-hosted runner runbook — what breaks when you move a billed job onto one, which runner to trust for production — deploy-time proof (rollback with re-smoke, backup gates that check the dump), and Actions minute economics. Triggers — CI/CD, GitHub Actions, job never starts, Actions minutes/quota, GHCR auth, self-hosted runner, deploy queued, rollback/backup gate."
---

# CI/CD Skill — GitHub Actions, Docker & GHCR (Unified)

Skill for troubleshooting and configuring CI/CD pipelines. Detects the project type and routes to specific references.

## Default workflow

1. **Detect the stack** with the table below. Scenarios are tagged `[S]` shared, `[B]` backend-only, `[F]` frontend-only.
2. **When you have an error string or a concrete symptom**, read `references/symptom-index.md` first and grep it for the message. Each row gives the probable cause, the fix and the file/section with the detail.
3. **When you need the full diagnosis, recipe or checklist**, open the reference from the routing table, and only the section the index points to. Every reference over 300 lines opens with a `## Sumário`.
4. **When a file cites "lição N" / "lesson N"**, read that row in `references/lessons-learned.md`. Numbers are stable.
5. **Before calling anything fixed**, run through the Gotchas below. Most of them are a green signal that measured nothing.

---

## Project Detection

| Indicator                        | Project              |
| -------------------------------- | -------------------- |
| `prisma/schema.prisma`           | **Backend**          |
| `biome.jsonc` / `biome.json`     | **Backend (Biome)**  |
| `manage.py` / `requirements.txt` | **Backend (Django)** |
| `vite.config.ts`                 | **Frontend**         |

> **Linter detection:** If the project has `biome.jsonc` (or `biome.json`), it uses Biome for lint/format. Otherwise, it assumes ESLint+Prettier. Biome projects do NOT use ESLint or Prettier.

> **Backend Django:** `manage.py`/`requirements.txt` (sem Prisma/Biome) → backend Python servido por gunicorn, testes com pytest; read `references/django-backend.md` for it. Scenarios `[B]` Django são marcados como tal nas tabelas.

---

## Workflow Overview

Both projects use **3 separate workflows** with identical triggers:

| Workflow          | File                | Trigger                  | Runners                                     |
| ----------------- | ------------------- | ------------------------ | ------------------------------------------- |
| **CI**            | `ci.yml`            | PR → `develop` or `main` | `ubuntu-latest`                             |
| **CD Staging**    | `cd-staging.yml`    | Push → `develop`         | `ubuntu-latest` + `self-hosted, staging`    |
| **CD Production** | `cd-production.yml` | Tag `v*`                 | `ubuntu-latest` + `self-hosted, production` |

### CI Differences

```text
Backend (ESLint):  checkout → install → prisma generate → lint → prettier → migrate → test (Jest)
Backend (Biome):   checkout → install → [prisma generate] → biome check → [test if configured]
Frontend:          checkout → install → lint → typecheck → test (Vitest)
```

> **Note:** `[prisma generate]` and `[test]` are optional — they depend on whether the project has Prisma and a configured test framework, respectively. Projects without a test framework (e.g., `estimates_api`) skip the test step in CI and CD.

### Deploy Differences

| Aspect               | Backend                                             | Frontend                                     |
| -------------------- | --------------------------------------------------- | -------------------------------------------- |
| Build-args           | Does not need `environment:` in build job           | `environment:` required (VITE_* secrets)     |
| Image                | Generic (same for all envs)                         | Environment-specific (VITE_* embedded in JS) |
| Migration            | `prisma migrate deploy` before `up`                 | No migration                                 |
| `VIRTUAL_PORT`       | Required (`API_PORT` ≠ 80)                          | Not needed (nginx = port 80)                 |
| GHCR login on deploy | `docker/login-action@v3` before pull                | `docker/login-action@v3` before pull         |
| Prune                | `docker image prune -f`                             | `docker image prune -f --filter "label=..."` |
| Compose path         | Varies by project (e.g., `infra/nodejs/`, `infra/`) | Varies by project (e.g., `infra/<web>/`)     |

### Concurrency & Auth

- **CI:** `ci-${{ github.ref }}` with `cancel-in-progress: true`
- **CD:** `deploy-{staging|production}-<project>` with `cancel-in-progress: false`
- **GHCR:** `GITHUB_TOKEN` (automatic) via `docker/login-action@v3` — no PAT

---

## Routing Table — Detailed References

| Condition | Reference |
| --- | --- |
| When you have an error message or symptom and don't know the layer yet (all tags, 72 rows) | `references/symptom-index.md` |
| When another file cites a lesson by number, or you want every lesson on one theme (105 numbered lessons + theme index) | `references/lessons-learned.md` |
| When the failure is shared infra: GHCR `unauthorized` / TLS timeout, nginx-proxy network, SSL/ACME certificate (3a/3b/3c), runner via systemd offline, concurrency, monorepo npm (`exec`, ESLint v9, hoisting), deploy keys, `.env` whitespace, composite action, `actionlint` | `references/troubleshooting-shared.md` |
| When the runner is a container (`FROM myoung34/github-runner`, `infra/docker/runner/`): crashloop, `404 registration`, `registration has been deleted`, `version deprecated`, PAT 401, mute runner, silent `queued`, host paths, missing binaries | `references/self-hosted-runner-docker.md` |
| Before configuring a new environment's shared infra (runner, GHCR, DNS) | `references/checklist-shared.md` |
| When a Node/Prisma backend fails, by exit code or message (Zod, Prisma, Jest, Biome, stale migration image, monorepo `tsx` runtime, `--omit=dev`) | `references/troubleshooting-backend.md` |
| Before a backend deploy (secrets, tests, build) | `references/checklist-backend.md` |
| When Jest tests pass locally and fail in CI (fix patterns) | `references/test-fixes-backend.md` |
| When the frontend fails (blank page, VITE_*, React Router 404, Alpine healthcheck, Vitest/jsdom, vacuous typecheck, test-log noise) | `references/troubleshooting-frontend.md` |
| Before a frontend deploy (VITE_*, Dockerfile, CD) | `references/checklist-frontend.md` |
| When a cutover/hotfix shows layers disagreeing: build-time vs runtime, operator clone on the host, `--profile run` reconcile, `compose run` orphans poisoning the reverse-proxy pool (split 200/401), PID 1, `${{ }}` in comments, stale `build:` image, DB password in URL, OIDC redirect URIs | `references/cd-pipeline-pitfalls.md` |
| If the backend is Django/gunicorn (collectstatic/WhiteNoise, ALLOWED_HOSTS healthcheck-400, CSRF/proxy-SSL, migrate one-off, two-origin CORS) | `references/django-backend.md` |
| When the constraint is the Actions minute quota: measuring per job, self-hosted as lever, `paths-ignore`, cold cache, billing block, manual deploy while the block lasts | `references/ci-cost-minutes.md` |
| When moving a billed job to self-hosted, or a migrated job now fails: toolchain, service-container network, `container:` and runner version, which runner for the tag `cd-production`, repo debt revealed (root runner, test timeouts), `.env`/snapshot in CI, gate job turned tautological, build without `setup-buildx`/`gha` cache | `references/self-hosted-job-migration.md` |
| When designing or doubting the part of CD that proves the deploy: immutable rollback tag, re-smoke, gate order, backup proven by the artifact, proving the sensor, `cmd \| tail` dropping the exit code, `vars` repo vs environment, state gates, DB role, self-measuring gates | `references/cd-verification-and-rollback.md` |

The long references open with a "when to read" block that maps key symptoms to sections.

---

## Gotchas

One line each; read the numbered lesson in `references/lessons-learned.md` when you need the context and the full fix.

- **Jobs "failed" in ~3 s, no steps, empty `runner_name`, `log not found`:** the job never started. Check the run's `.name` first: if it is the workflow's file path, the workflow is invalid (lesson 83). Otherwise it is the billing/quota block, whose message lives only in `gh api /repos/<o>/<r>/check-runs/<job_id>/annotations` (lesson 74).
- **`${{ }}` inside a shell comment in `run:` invalidates the whole workflow**, which then does not fire on its own triggers (lesson 83). Gate with `actionlint`, which exits 0 without reading `run:` when `shellcheck` is missing from PATH (lesson 82).
- **`cmd | tail` returns `tail`'s status**, and `${PIPESTATUS[0]}` expands empty in zsh. Redirect to a file and read `$?`, or `set -o pipefail` (lesson 84).
- **A self-hosted deploy stuck in `queued` is silent:** `timeout-minutes` only starts after pickup (lesson 51). The log signature separates the modes (`404 registration` §7, `registration has been deleted` §9, `version deprecated` §8, PAT `401` §10a); they can stack (§10), and a mute runner shows none of them (§8b, `ls -d /actions-runner/bin.*`).
- **`DISABLE_AUTO_UPDATE` with any non-empty value, even `"0"`, disables auto-update** (lesson 48). In an ephemeral container that wipes state the update can never land; bump the `FROM` (lesson 87).
- **Roll back only to an immutable `sha-*` tag**, since the failing deploy just re-pointed `latest`, and re-smoke after `up -d`, whose exit 0 only means Docker accepted the request (lessons 59, 60).
- **`if: success()` skips exactly the deploy that failed.** Put secondary gates after the rollback step (lesson 61).
- **`healthy`, an empty log or an idempotent step's `reuse` is not proof.** Check the artifact (`gzip -t` + `COPY` count), fire a probe before trusting silence, and assert on the declared state (lessons 62, 67, 92).
- **Proving a sensor:** confirm the sabotage landed (`sed -i` and `str.replace` succeed on no match), assert on parsed structure rather than raw text that the explanatory comment also satisfies, and exclude your own connection when asserting absence (lessons 93, 98, 99).
- **Actions bills each job rounded up to the minute, on private repos only.** Self-hosted is free and outside the quota, and `/timing` `billable.total_ms` can read `0`; measure by `/jobs` + `runner_group_name` (lessons 68, 69, 74).
- **`paths-ignore` also skips a push that changes zero files** (a new environment branch, `--allow-empty`). Add `workflow_dispatch` before cutting the branch (lesson 81). A tag-triggered workflow runs the file from the tagged commit (lesson 76).
- **A job moved to self-hosted breaks on what the hosted image gave for free:** `cache: 'yarn'` invokes yarn, `127.0.0.1` is the containerized runner's own loopback, `container:` needs the runner's node24, the runner is root, test timeouts were calibrated on a dev machine. The job that watches a runner cannot run on it (lessons 71–73, 80, 101, 102).
- **Containerized runner:** bind mounts resolve on the host but CLI paths (`--env-file`, `-f`) resolve inside the container, the image must carry every binary the workflow calls, and the CD's `up -d` never recreates the runner (lessons 89, 90, 97).
- **VITE_* are baked at build time**, so changing the secret without rebuilding is a no-op, and a build-time image needs an environment suffix on its tag or a fast-forward promotion makes production overwrite staging (lessons 18, 64).
- **`docker run` does not pull and `compose run`/`up` does not rebuild when the tag exists locally**, so a stale image applies old migrations or declarations, green (lessons 29, 91).
- **`compose run` orphans inherit `VIRTUAL_HOST`** and poison the nginx-proxy upstream pool (~50% 401); pass `-e VIRTUAL_HOST= -e LETSENCRYPT_HOST=` (lesson 34).
- **GHCR paths must be lowercase** (`github.repository_owner` keeps the case), and GHCR packages are born private (lessons 55, 56).

---

## Useful Commands

```bash
# View workflow status
gh run list --limit 5

# View logs of a specific run
gh run view <run-id> --log-failed

# Re-run a failed workflow
gh run rerun <run-id>

# List secrets of an environment
gh secret list --env staging

# Check images on GHCR
gh api orgs/<ORG>/packages/container/<PACKAGE_NAME>/versions
```

### Validar os workflows antes de commitar

`actionlint` lê YAML **e** o shell dos `run:` — mas só a segunda metade se o
`shellcheck` estiver no PATH, e ele não avisa quando não está (lição 82).

```bash
# Instalar (binario Go unico, sem root) + a metade que importa
VER=$(gh api repos/rhysd/actionlint/releases/latest --jq .tag_name | tr -d v)
curl -sL "https://github.com/rhysd/actionlint/releases/download/v${VER}/actionlint_${VER}_linux_amd64.tar.gz" \
  | tar -xz -C /usr/local/bin actionlint
command -v shellcheck || sudo apt-get install -y shellcheck

# Provar que enxerga o shell ANTES de confiar no verde
actionlint -verbose 2>&1 | grep 'was disabled'   # nada impresso = regras ativas
actionlint                                        # exit 0 so vale depois da linha acima
```

### Backend

```bash
# Which tag is actually being served right now? (this is your rollback target)
# Accept ONLY immutable sha-* — `latest` was just re-pointed at the broken image (lesson 59).
docker inspect --format '{{.Config.Image}}' <container>

# Manual rollback (compose path varies by project)
export IMAGE_TAG=sha-<previous-short-sha>
docker compose -f <COMPOSE_PATH>/docker-compose.yml pull
docker compose -f <COMPOSE_PATH>/docker-compose.yml up -d --force-recreate

# NOT DONE YET — `up -d` exiting 0 only means Docker accepted the request (lesson 60).
# Wait for healthy, then re-run the same smoke you use for a forward deploy:
curl -fsS --max-time 10 https://<api-host>/health/ready | grep -q '"status":"ok"' \
  && echo "rollback re-smoked OK" \
  || echo "ROLLBACK DID NOT RESTORE SERVICE — production is down"
```

> Migrations are **not** reverted (`prisma migrate deploy` / `manage.py migrate` have no
> down step), so the previous image runs against the newer schema. Additive migrations
> survive that; destructive ones don't. See `cd-verification-and-rollback.md` §2.

### Frontend

```bash
# Same rule: immutable tag only. Note the environment suffix on build-time-baked
# images — without it a fast-forward merge makes prod overwrite staging (lesson 64).
export IMAGE_TAG=sha-<previous-short-sha>
docker compose -f <COMPOSE_PATH>/docker-compose.yml pull
docker compose -f <COMPOSE_PATH>/docker-compose.yml up -d --force-recreate
# ...then re-smoke, as above.

# Check VITE_* embedded in JS (inside the image)
docker exec <container> sh -c "grep -r '<your-domain>' /usr/share/nginx/html/assets/*.js | head -5"
```

> Stronger check: grep the bundle **as served over HTTPS** rather than the one inside the
> container — it proves what the user's browser actually receives, including any stale
> upstream in the reverse-proxy pool. Recipe in `cd-pipeline-pitfalls.md` §1 step 4.

---

## Pipeline Files

### Backend

| File                                  | Description                             |
| ------------------------------------- | --------------------------------------- |
| `.github/workflows/ci.yml`            | CI pipeline (lint + test) for PRs       |
| `.github/workflows/cd-staging.yml`    | CD pipeline for staging (push develop)  |
| `.github/workflows/cd-production.yml` | CD pipeline for production (tags v\*)   |
| `Dockerfile` or `infra/*/Dockerfile`  | Multi-stage build (path varies by project) |
| `infra/*/docker-compose.yml`          | Compose with GHCR image (path varies)   |
| `src/env.ts`                          | Zod validation of env vars              |

### Frontend

| File                                  | Description                             |
| ------------------------------------- | --------------------------------------- |
| `.github/workflows/ci.yml`            | CI pipeline (lint + typecheck + test)   |
| `.github/workflows/cd-staging.yml`    | CD pipeline for staging (push develop)  |
| `.github/workflows/cd-production.yml` | CD pipeline for production (tags v\*)   |
| `infra/<web>/Dockerfile`              | Multi-stage build (node + nginx; path varies by project) |
| `infra/<web>/docker-compose.yml`      | Compose with GHCR image                 |
| `infra/<web>/nginx.conf`              | nginx config (SPA try_files)            |
