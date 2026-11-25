#!/usr/bin/env bash
# Close public self-registration on a Zitadel v4 instance: both keys, then prove it (Quirk 62).
#
#   1. The instance restriction disallowPublicOrgRegistration=true closes /ui/login/register/org.
#      That page reads only the restriction, never the login policy, so allowRegister alone leaves it open.
#   2. allowRegister=false in the instance's login policy closes /ui/login/register. The admin PUT copies
#      every field of the body into the command, so the body carries all 17 fields of the v4.15.0
#      UpdateLoginPolicyRequest as read from the GET, with only allowRegister changed.
#   3. Optional (--remove-orgs-prefix): delete the orgs a robot left behind, only when the name starts with
#      the prefix, every account is @example.com and the org owns no project.
#
# Without --apply it only reads and says what it would do. The proof re-reads everything: the restriction,
# the policy (only allowRegister may differ), each org's own policy (an org with its own policy and
# allowRegister=true keeps registration open there), and the anonymous org page, which must answer 404.
# The person page still answers 200 once closed, drawing an error: prove that one by the body.
#
# Usage: IDP=https://idp.example.com PAT_FILE=/path/to/pat ./close-public-registration.sh [--apply] [--remove-orgs-prefix PREFIX]
# The PAT must belong to an instance member (IAM_OWNER, Quirk 57). It goes to a 0600 header file in a temp
# dir, shredded on exit, and never into a command argument. Needs curl and python3.
# Exit: 0 done (or simulated), 1 stopped or proof failed, 2 usage.
set -euo pipefail

usage() { sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; }
APPLY=0
PREFIX=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --remove-orgs-prefix)
      if [ "$#" -lt 2 ] || [ -z "$2" ]; then echo "--remove-orgs-prefix needs a prefix" >&2; exit 2; fi
      PREFIX=$2; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1 (expected --apply, --remove-orgs-prefix PREFIX or --help)" >&2; exit 2 ;;
  esac
  shift
done
[ -n "${IDP:-}" ] || { echo "IDP is not set (expected the instance URL, e.g. https://idp.example.com)" >&2; exit 2; }
[ -r "${PAT_FILE:-}" ] || { echo "PAT_FILE is not a readable file: '${PAT_FILE:-}'" >&2; exit 2; }
IDP=${IDP%/}

D=$(mktemp -d)
trap 'shred -u "$D"/* 2>/dev/null || true; rmdir "$D" 2>/dev/null || true' EXIT
(umask 077; printf 'Authorization: Bearer %s\n' "$(tr -d '[:space:]' < "$PAT_FILE")" > "$D/auth.hdr")

# api METHOD PATH OUT [BODY] [ORG] -> prints the HTTP status; the response body goes to $D/OUT and $D/last
api() {
  local method=$1 path=$2 out=$3 body=${4:-} org=${5:-} code
  local args=(-sS -o "$D/$out" -w '%{http_code}' -X "$method" -H @"$D/auth.hdr" -H 'Content-Type: application/json')
  [ -n "$org" ] && args+=(-H "x-zitadel-orgid: $org")
  [ -n "$body" ] && args+=(--data-binary @"$D/$body")
  code=$(curl "${args[@]}" "$IDP$path")
  cp "$D/$out" "$D/last" 2>/dev/null || true
  echo "$code"
}

need() { # need GOT WANTED MESSAGE
  [ "$1" = "$2" ] || { echo "STOP: $3 (HTTP $1, expected $2): $(head -c 300 "$D/last" 2>/dev/null)" >&2; exit 1; }
}

anon_register_org() { curl -sS -o /dev/null -w '%{http_code}' "$IDP/ui/login/register/org"; }

# org_policies OUTFILE: each org's login policy, so the proof can see an org that overrides the instance
org_policies() {
  local org s
  for org in $(python3 -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))))' "$D/org-ids.json"); do
    s=$(api GET /management/v1/policies/login "pol-$1-$org.json" "" "$org")
    need "$s" 200 "the login policy of org $org"
  done
}

echo "== read"
s=$(api POST /admin/v1/orgs/_search orgs.json); need "$s" 200 "the PAT cannot list the orgs: it must belong to an instance member (Quirk 57)"
s=$(api GET /admin/v1/restrictions restrictions.json); need "$s" 200 "reading the instance restrictions"
s=$(api GET /admin/v1/policies/login policy-before.json); need "$s" 200 "reading the instance login policy"
python3 - "$D" "$PREFIX" <<'PY'
import json, sys
d, prefix = sys.argv[1], sys.argv[2]
orgs = json.load(open(f"{d}/orgs.json")).get("result", [])
r = json.load(open(f"{d}/restrictions.json"))
p = json.load(open(f"{d}/policy-before.json")).get("policy", {})
print("orgs:", ", ".join(f"{o['name']} ({o['id']})" for o in orgs))
print("restriction disallowPublicOrgRegistration:", r.get("disallowPublicOrgRegistration", False))
print("instance policy: allowRegister =", p.get("allowRegister", False), "| allowUsernamePassword =", p.get("allowUsernamePassword", False))
json.dump([o["id"] for o in orgs], open(f"{d}/org-ids.json", "w"))
json.dump([o["id"] for o in orgs if prefix and o["name"].startswith(prefix)], open(f"{d}/prefix-ids.json", "w"))
PY

echo "== each org's login policy (isDefault = inherits the instance's)"
org_policies before
python3 - "$D" before <<'PY'
import json, sys
d, tag = sys.argv[1], sys.argv[2]
for org in json.load(open(f"{d}/org-ids.json")):
    j = json.load(open(f"{d}/pol-{tag}-{org}.json")); p = j.get("policy", {})
    own = not j.get("isDefault", p.get("isDefault", True))
    print(org, "own policy" if own else "inherits", "| allowRegister =", p.get("allowRegister", False),
          "<- stays open: change this org's own policy too" if own and p.get("allowRegister") else "")
PY

: > "$D/remove.txt"
if [ -n "$PREFIX" ]; then
  echo "== orgs named $PREFIX*"
  for org in $(python3 -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))))' "$D/prefix-ids.json"); do
    printf '{"queries":[{"organizationIdQuery":{"organizationId":"%s"}}]}' "$org" > "$D/q-users.json"
    s=$(api POST /v2/users "users-$org.json" q-users.json); need "$s" 200 "the accounts of org $org"
    printf '{}' > "$D/q-proj.json"
    s=$(api POST /management/v1/projects/_search "proj-$org.json" q-proj.json "$org"); need "$s" 200 "the projects of org $org"
    python3 - "$D" "$org" <<'PY'
import json, sys
d, org = sys.argv[1], sys.argv[2]
names = [u.get("username", "") for u in json.load(open(f"{d}/users-{org}.json")).get("result", [])]
projs = json.load(open(f"{d}/proj-{org}.json")).get("result", [])
only_example = bool(names) and all(n.endswith("@example.com") for n in names)
go = only_example and not projs
print(f"{org}: accounts {names}, projects {len(projs)}", "-> remove" if go else "-> KEEP (not only @example.com, or owns a project)")
if go:
    open(f"{d}/remove.txt", "a").write(org + "\n")
PY
  done
fi

echo "== anonymous: GET /ui/login/register/org -> $(anon_register_org)"

if [ "$APPLY" -ne 1 ]; then
  echo "SIMULATION: nothing was written. Run with --apply to write."
  exit 0
fi

echo "== write"
if python3 -c 'import json,sys; sys.exit(0 if json.load(open(sys.argv[1])).get("disallowPublicOrgRegistration") else 1)' "$D/restrictions.json"; then
  echo "restriction: already on"
else
  printf '{"disallowPublicOrgRegistration":true}' > "$D/body-restriction.json"
  s=$(api PUT /admin/v1/restrictions resp-restriction.json body-restriction.json); need "$s" 200 "writing the restriction"
  echo "restriction: written (HTTP $s)"
fi

python3 - "$D" <<'PY'
import json, sys
d = sys.argv[1]
p = json.load(open(f"{d}/policy-before.json")).get("policy", {})
# The 17 fields of UpdateLoginPolicyRequest in v4.15.0 (proto/zitadel/admin.proto). A field absent from the
# GET is the zero of its type, and sending it absent writes the same zero.
fields = ["allowUsernamePassword", "allowRegister", "allowExternalIdp", "forceMfa", "passwordlessType",
          "hidePasswordReset", "ignoreUnknownUsernames", "defaultRedirectUri", "passwordCheckLifetime",
          "externalLoginCheckLifetime", "mfaInitSkipLifetime", "secondFactorCheckLifetime",
          "multiFactorCheckLifetime", "allowDomainDiscovery", "disableLoginWithEmail",
          "disableLoginWithPhone", "forceMfaLocalOnly"]
body = {f: p[f] for f in fields if f in p}
body["allowRegister"] = False
json.dump(body, open(f"{d}/body-policy.json", "w"))
json.dump(fields, open(f"{d}/fields.json", "w"))
print("policy: the body carries", len(body), "field(s) read from the GET, with allowRegister=false")
PY
if python3 -c 'import json,sys; sys.exit(0 if json.load(open(sys.argv[1])).get("policy",{}).get("allowRegister") else 1)' "$D/policy-before.json"; then
  s=$(api PUT /admin/v1/policies/login resp-policy.json body-policy.json); need "$s" 200 "writing the login policy"
  echo "policy: written (HTTP $s)"
else
  echo "policy: allowRegister already off"
fi

while read -r org; do
  [ -n "$org" ] || continue
  s=$(api DELETE "/v2/organizations/$org" "del-$org.json"); need "$s" 200 "removing org $org"
  echo "org $org: removed (HTTP $s)"
done < "$D/remove.txt"

echo "== proof"
s=$(api GET /admin/v1/restrictions restrictions-after.json); need "$s" 200 "re-reading the restrictions"
s=$(api GET /admin/v1/policies/login policy-after.json); need "$s" 200 "re-reading the policy"
s=$(api POST /admin/v1/orgs/_search orgs-after.json); need "$s" 200 "re-reading the orgs"
python3 -c 'import json,sys; json.dump([o["id"] for o in json.load(open(sys.argv[1])).get("result", [])], open(sys.argv[2], "w"))' \
  "$D/orgs-after.json" "$D/org-ids.json"
org_policies after
python3 - "$D" <<'PY'
import json, sys
d = sys.argv[1]
r = json.load(open(f"{d}/restrictions-after.json"))
a = json.load(open(f"{d}/policy-before.json")).get("policy", {})
b = json.load(open(f"{d}/policy-after.json")).get("policy", {})
fields = json.load(open(f"{d}/fields.json"))
changed = [f for f in fields if a.get(f) != b.get(f)]
expected = ["allowRegister"] if a.get("allowRegister") else []   # a re-run writes nothing and changes nothing
ids = json.load(open(f"{d}/org-ids.json"))
removed = [l.strip() for l in open(f"{d}/remove.txt") if l.strip()]
open_orgs = []
for org in ids:
    j = json.load(open(f"{d}/pol-after-{org}.json")); p = j.get("policy", {})
    if not j.get("isDefault", p.get("isDefault", True)) and p.get("allowRegister"):
        open_orgs.append(org)
checks = {
    "restriction on": r.get("disallowPublicOrgRegistration") is True,
    "allowRegister off": b.get("allowRegister", False) is False,
    "only allowRegister changed": changed == expected,
    "no org overrides with allowRegister=true": not open_orgs,
    "removed orgs are gone": not set(removed) & set(ids),
}
for k, v in checks.items():
    print(("ok   " if v else "FAIL ") + k)
print("changed fields:", changed, "| orgs with their own open policy:", open_orgs)
sys.exit(0 if all(checks.values()) else 1)
PY
c=""
for _ in 1 2 3 4 5 6; do
  c=$(anon_register_org); [ "$c" = 404 ] && break
  python3 -c 'import time; time.sleep(5)'
done
echo "anonymous: GET /ui/login/register/org -> $c (expected 404)"
[ "$c" = 404 ] || { echo "STOP: the org page still answers $c" >&2; exit 1; }
echo "public registration closed: ok (the person page answers 200 with an error; prove it by the body, Quirk 62)"
