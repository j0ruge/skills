---
name: zitadel-idp
metadata:
  version: 0.18.0
description: "Self-hosted Zitadel v4 OIDC field guide — a numbered quirk catalogue, working docker-compose and an idempotent TypeScript bootstrap. High-friction traps: FirstInstance env placement, JWT/JWKS over self-signed HTTPS, `--tlsMode external` and the console's mixed-content `Failed to fetch`, v2.66→v4, API v1→v2, silent-renew, 401 storms, UI language from the `locale` claim. Triggers — zitadel, oidc self-hosted, JWKS, masterkey, v2.66→v4, tlsMode external, pre-cutover check, locale claim."
---

# Zitadel IdP — Field Guide

This skill captures patterns and pitfalls discovered while integrating Zitadel `v4.x` self-hosted as the IdP for the JRC Brasil ERP. It exists to prevent every new project from re-discovering the same gotchas the hard way.

**Scope**: Zitadel `v4.x` (latest as of 2026-04) is the default target. v3 differs in a few places (notably no `OrganizationService.AddOrganization` v2 endpoint) — the references flag breaking changes when relevant. **v2.66.x** is also covered for one specific edge case (Quirk 24, masterkey via flag) because legacy stacks still run it; the rest of the skill remains v4-first.

**Out of scope**: Zitadel Cloud (managed), v3 setup, SAML flows, federation IdPs (login with Google/GitHub), Login UI v2 customization. The skill assumes self-hosted, OIDC-only, with the bundled Login UI v1.

## When to use this skill

Read this skill before you start any of the following:

- Drafting a `docker-compose.yml` that includes Zitadel
- Writing a script that programmatically creates Orgs, Projects, Roles, Apps via Management API
- Implementing JWT validation for Zitadel access tokens in any backend (Node/Go/Java/Python)
- Wiring an SPA or mobile app to Zitadel via Auth Code + PKCE
- Renaming or retiring a project role (the key is immutable — Quirk 48), or reconciling grants after the declarative config gains a role
- Diagnosing 401 / 403 / 404 / 400 against Zitadel — including: `Instance not found`, `User with state initial`, `Method Not Allowed`, `Organisation doesn't exist`, `Errors.Instance.Domain.AlreadyExists`, `404 {"code":5,"message":"Not Found"}` na hosted UI, 400 em `/oauth/v2/authorize?prompt=none`, 401 com JWT cujos `iss`/`aud`/`exp` parecem corretos (especialmente atrás de proxy TLS local com cert self-signed), ou 400 `COMMAND-1m88i "No changes"` em bootstrap idempotente
- Wiring an SPA hosted **fora de `localhost`/`127.0.0.1`** (acesso via LAN, IP `.sslip.io`, hostname custom) — exige HTTPS por causa do `crypto.subtle` (PKCE), e o consumer típico de `react-oidc-context` engole a rejeição do `signinRedirect`

If you are merely calling a pre-existing Zitadel deployment from your code, you probably only need `references/token-validation.md` and `references/api-cheatsheet.md`.

## Default workflow

1. **Error string or symptom in hand?** Scan the Gotchas index below; when a line matches, read its full entry in `references/quirks.md` (grep it by the error code, e.g. `grep -n 'COMMAND-1m88i' references/quirks.md`). If nothing matches, read `references/troubleshooting.md`, the symptom-first lookup.
2. **Building or changing something?** Open the one reference the task table below names. The references are designed to be readable in isolation — open the one you need without slogging through the rest.
3. **Fresh project?** Follow the implementation flow at the end of this file.

| When the task is… | Read |
|------|------|
| When bringing up Zitadel locally for the first time | `references/docker-compose-bootstrap.md` + use `assets/docker-compose.zitadel.yml` as starting point |
| When a local Zitadel is broken and must be reset | run `scripts/reset-zitadel.sh` |
| When creating Org/Project/Roles/App programmatically | `references/api-cheatsheet.md` + copy `assets/bootstrap-zitadel.ts` (the idempotent template) |
| When validating Zitadel JWT in Node | `references/token-validation.md` |
| When mapping domain `tenantId` to Zitadel `orgId` | `references/tenant-org-mapping.md` |
| When wiring an SPA (React + `react-oidc-context`) — boot-time silent renew, F5 retention, logout flow | `references/spa-recipes.md` |
| When applying org branding to the hosted Login UI v1 (logo, colors, custom texts) | `references/branding.md` |
| When planning a v2.66.x → v4.x upgrade (pre-flight, snapshot, login UI v2 container, validation, rollback) | `references/migration-v2-to-v4.md` |
| When refactoring callers from Management API v1 to v2 (Connect protocol, payload diffs, idempotence patterns) | `references/api-v1-to-v2-mapping.md` |
| When running prod + staging Zitadels side by side, or moving users between instances | `references/multi-instance-and-user-migration.md` |
| When running a role rename/migration across environments (declare-first, the grant tool, per-environment state) | `references/role-migration.md` |
| When a Gotchas line below matches and you need its symptom, cause, fix and evidence | `references/quirks.md` |
| When you hit a confusing error and want a quick lookup | `references/troubleshooting.md` |
| When proving a bootstrap actually wrote what the YAML declares (no PAT needed) | `references/troubleshooting.md` §"The bootstrap logs `reuse` for everything" |
| When one account loops back to the login screen while others log in fine | `references/troubleshooting.md` §"One account loops back…" |
| When creating a test/seed user and proving its password works, with no browser | `references/api-cheatsheet.md` §"Seed an admin user" + §"Prove a user's password without a browser" |
| When driving the SPA's UI language from the user's IdP language (`locale` claim) | `references/spa-recipes.md` §"Recipe — UI language from the IdP" |

## Gotchas — the quirk index

These bite first-time Zitadel integrators consistently. One line per quirk; the full text (symptom, cause, fix, measured evidence, and the file/section with the recipe) is in `references/quirks.md` under the same number — read it when a line here matches what you see. Numbers are stable: the references cite them as "Quirk N".

1. `ZITADEL_FIRSTINSTANCE_*` envs go on the `zitadel` service, not on `zitadel-init`.
2. The `/current-dir` volume must be writable by uid 1000, or setup loops on `permission denied`.
3. `ZITADEL_EXTERNALDOMAIN` is enforced via the `Host` header: calling `127.0.0.1:8080` answers `Instance not found`.
4. `/admin/v1/orgs/_setup` needs a human admin; create the org with v2 `AddOrganization`.
5. Human-user payload differs by API family: v1 `userName` + `firstName`/`lastName`, v2 `username` + `givenName`/`familyName`; v4 also rejects `clockSkew > 5s`.
6. A user created without `initialPassword` stays `initial`, and `_deactivate` fails with `COMMAND-ke0fw`.
7. Domain `tenantId` ≠ numeric `orgId`; Management calls need the number in `x-zitadel-orgid`.
8. Grants search is the global `/management/v1/users/grants/_search`; the per-user path answers `405`.
9. `loginV2.required=true` is the default from v3 on; without the Login UI v2 container the authorize flow hits `{"code":5,"message":"Not Found"}`.
10. `/silent-renew` must be in the app's `redirectUris`, or every `prompt=none` returns `400` and the SPA loops.
11. Access tokens carry no profile claims (`name`, `email`, org id); fall back to `sub`.
12. JWKS over self-signed HTTPS needs `NODE_EXTRA_CA_CERTS`; otherwise 100% of requests 401.
13. A Zitadel volume reset regenerates `projectId` and `clientId`; re-derive them from `bootstrap.json` on every boot.
14. `PUT …/oidc_config` with an unchanged body returns `400 COMMAND-1m88i "No changes"`; treat it as a no-op.
15. Behind a TLS-terminating proxy you need three settings: `ZITADEL_EXTERNALSECURE=true`, `ZITADEL_TLS_ENABLED=false` and `--tlsMode external`.
16. PKCE needs `crypto.subtle`, which only secure contexts expose; over HTTP on a LAN IP or `.sslip.io`, "Entrar" silently does nothing.
17. F5 with `InMemoryWebStorage` needs a boot-time `signinSilent`, guarded against re-mounting inside the `/silent-renew` iframe.
18. `post_logout_redirect_uri` is byte-matched like `redirect_uri` (`post_logout_redirect_uri invalid`).
19. Org branding does not paint the Login UI unless the project sets `privateLabelingSetting` to enforce the owner's policy.
20. The first label policy is a POST (a PUT answers `Org-0K9dq`), and a no-op re-run answers `Org-8nfSr`, not `COMMAND-1m88i`.
21. In v4 the asset path is `/assets/v1/org/policy/label/...`; the old `orgs/me` path answers `405`.
22. Login texts live at `/management/v1/text/login/{lang}` and accept short codes only (`pt-BR` → `LANG-lg4DP`).
23. After a single-app → multi-app YAML refactor, env from `dev.sh` must win over the YAML (`redirect_uri is missing in the client configuration`).
24. v2.66.x `start-from-init` does not reliably read `ZITADEL_MASTERKEY` (`panic: No master key provided`); pass `--masterkey`.
25. Login UI v2 in v4 is a separate container (`ghcr.io/zitadel/zitadel-login`): deploy it or turn `loginV2.required` off, and pick one.
26. v2 idempotence uses deterministic IDs and treats `ALREADY_EXISTS` as success.
27. v2 moves the contextual org id from the header into the body (`missing organization_id`).
28. Login UI v2 auto-provisioning is broken in v4.15.0 (`Awaiting file and reading token` or `Errors.Instance.Domain.AlreadyExists`).
29. The OIDC `client_id` is the numeric `clientId`, not your `applicationId` UUID (`Errors.App.NotFound`).
30. `ZITADEL_BOOTSTRAP_ENV` must be set explicitly in CD (it silently defaults to `dev`), and `bootstrap.json` refreshes only when the bootstrap runs.
31. `ZITADEL_DEFAULTINSTANCE_FEATURES_LOGINV2_REQUIRED=false` at FirstInstance breaks the Quirk 25 + 28 deadlock.
32. nginx-proxy: a sibling with `VIRTUAL_PATH` hides the container without one; declare `VIRTUAL_PATH=/` + `VIRTUAL_DEST=/`.
33. The Console "Add Human User" form truncates Username to the email's local part ("User could not be found").
34. `userLoginMustBeDomain=true` stamps loginNames on existing users, and turning it off does not undo it.
35. The Console leaves "Email verified" unchecked, so the first login waits for an SMTP code that may never arrive.
36. A JWT validator on the IdP's host needs `extra_hosts: idp.<domain>:host-gateway` (401 storm ~10 min after restart).
37. The 401 → silent-renew → refresh-token reuse → session-revoke cascade needs three layers: dedupe in `ApiClient`, no retry on 401, a guarded redirect listener.
38. CI bind-mount perms make `ZITADEL_FIRSTINSTANCE_PATPATH` fail with EACCES, which cascades into `unique_constraints_pkey` (not Quirk 28).
39. The default password policy needs four character classes; `openssl rand -hex` fails with `COMMAND-VoaRj`.
40. `zitadel-login` takes 90 s or more to go healthy on small CI runners; scope `up --wait`.
41. The bootstrap creates grants but never reconciles `roleKeys` when the YAML gains a role.
42. SPA → Express needs CORS ahead of auth, or the preflight `OPTIONS` 401s (looks like the 401-storm family).
43. Console `[unknown] Failed to fetch`: `environment.json` renders `api: http` against `issuer: https` under `--tlsMode disabled`; recreate the container, never `docker start`.
44. Prove `client_id` + `redirect_uri` with no credential: `/oauth/v2/authorize` must answer `302 …/ui/login/login`.
45. The OIDC config a deployed SPA uses is in its served JS bundle; grep that, not the workflow.
46. `ZITADEL_SEED_USER_ROLE` must list the roles of every app sharing the IdP; the create path writes it literally.
47. Prod + staging instances need per-environment audience and client id; a password hash can be imported but not exported.
48. A role key is immutable: the rename is four steps, with an alias at the claim boundary, and the old key is withdrawn only after the deploy.
49. `ListProjectRoles` has no Connect/v2 twin (`404`); use REST v1 `roles/_search`.
50. A config field the schema accepts and the bootstrap never reads is worse than a missing one; use `env > YAML > default`.
51. `reuse` for every resource can mean a stale input; prove it with the `creation_date` in `projections.project_roles4`.
52. Every role quirk ends in the same login loop; prove the running process has the code you are reading, and `403` is the honest status.
53. The user's language arrives as the `locale` claim (id_token only with `idTokenUserinfoAssertion: true`, `null` when unset).

## Migration v2.66 → v4 + API v2

When upgrading from v2.66.x to v4.x and refactoring callers from API v1 to v2:

- **Start with the runbook** in `references/migration-v2-to-v4.md` — pre-flight (Postgres required since v3, advisory A10015), upgrade path (direct v2.66 → v4 OK if Postgres in place — no v3 stop), schema migration runs automatically in the v4 image's `setup` phase, validation matrix, rollback.
- **Use the mapping table** in `references/api-v1-to-v2-mapping.md` when refactoring calls — covers all 15 v2 services (Organization, Project, Application, User, Authorization, Action, Feature, Settings, OIDC, IDP, Group, SAML, Session, WebKey, Instance), payload diffs (`firstName/lastName` → `givenName/familyName`, `userName` → `username`, `email.isEmailVerified` → `email.isVerified`, language `pt-BR` → `pt`), and idempotence patterns.
- **Login UI v2 is a separate container** — see Quirk 25. Reverse proxy must route `/ui/v2/login` to `zitadel-login:3000`, everything else (including OIDC discovery, OAuth, JWKS) to `zitadel:8080`. Path B (sticking with Login UI v1) is supported — Login UI v1 keeps working at `/ui/login/` indefinitely.
- **Bootstrap idempotence in v2 differs** (Quirk 26) — deterministic IDs in body replace `_search`-then-create round-trip. Existing v1-shaped bootstrap scripts keep working in v4; refactor only when there's a reason.
- **Connect protocol auth is unchanged**: same `Authorization: Bearer <PAT>` header. JSON variant uses `Content-Type: application/json`. Binary variant uses `application/connect+proto` (only if you have a generated client).

## Implementation flow (suggested order)

For a fresh project, this sequence avoids most reordering:

1. Copy `assets/docker-compose.zitadel.yml` and adjust ports / external domain. Read `docker-compose-bootstrap.md §1-3` first — the env layout is non-obvious.
2. `docker compose up -d`, wait for healthy, verify the PAT was written to `<volume>/admin.pat`. If not, see troubleshooting.
3. Copy `assets/bootstrap-zitadel.ts` and run it to create your Org/Project/Roles/App. The script is idempotent — re-runs are safe.
4. Capture the `projectId` and `clientId` from the output JSON. These become `OIDC_AUDIENCE` and the SPA's client_id respectively.
5. In your backend, wire JWT validation per `token-validation.md`. The audience must equal the `projectId`, NOT the `clientId`.
6. In your SPA, configure Auth Code + PKCE pointing at `http://<external-domain>/.well-known/openid-configuration`.
7. Test login end-to-end. If anything 4xx's, jump straight to `troubleshooting.md`.

## What this skill explicitly does NOT cover

- Production hardening (TLS, masterkey rotation, Postgres backup, SMTP) — these are real concerns but vary by environment. Quick pointer: terminate TLS at NGINX/Caddy/Traefik and set `ZITADEL_EXTERNALSECURE=true` + `ZITADEL_TLS_ENABLED=false` + start flag `--tlsMode external` (full triad — see `docker-compose-bootstrap.md §"TLS terminated by reverse proxy"`, quirk 15). Backup the Zitadel Postgres database like any other Postgres.
- v3 → v4 migration. Greenfield projects should start on v4. The skill covers v2.66 → v4 (the supported direct hop when Postgres is already in place — see `migration-v2-to-v4.md`), not v3 as an intermediate stop.
- Federation, SAML, SCIM, Actions, Webhooks. Add them when needed — they are mostly straight reads of the docs once Zitadel is bootstrapped correctly.

## Source of truth

- Bundled working references: `assets/bootstrap-zitadel.ts` (idempotent bootstrap) and `assets/docker-compose.zitadel.yml`.
- Upstream docs: <https://zitadel.com/docs> and the steps file at <https://github.com/zitadel/zitadel/blob/main/cmd/setup/steps.yaml>.

When the references in this skill diverge from upstream, trust the upstream docs but raise a note — Zitadel evolves quickly and these references will drift.
