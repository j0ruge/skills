---
name: release
description: "Create a GitHub Release with categorized English notes from git history, on any stack. Follows the repo's tag series (`v1.2.0`, `<package>-v1.2.0`), covers a first release, and edits the notes of an already-published version instead of tagging it twice. Triggers — release, release notes, GitHub Release, gh release, changelog, semver, monorepo."
disable-model-invocation: true
compatibility: "Claude Code and Cursor read disable-model-invocation only at the top: the skill runs only as /release:release (/release in Cursor), never from context, because it publishes a GitHub Release. Requires git and an authenticated gh CLI."
metadata:
  version: 2.0.1
---

## User Input

```text
$ARGUMENTS
```

Interpret the input:

- **Semantic version** (e.g.: `3.0.0`, `2.1.0`): use as the new release version.
- **`--path <relative-dir>`** (e.g.: `--path LicenceManager/`): filter commits and diffs to only include changes in that directory. Can be combined with a version (e.g.: `1.0.0 --path src/api`).
- **Empty**: ask the user which version to use before proceeding.

---

## Objective

Create or update a **GitHub Release** with detailed release notes in **English**, covering the changes since the previous release of the same tag series (the whole history for a first release).

---

## Constraints

- The project stays as it is: no file edited, no commit pushed. The only write is the GitHub Release, created or with its notes edited.
- Everything in the note comes from git data.

---

## Execution — Step by Step

### 0. Parse arguments

Extract from `$ARGUMENTS`:
- `$NEW_VERSION` — the semantic version (if provided)
- `$PATH_FILTER` — the `--path` value (if provided). Step 3 appends it as `-- <path>`; step 5 prefixes the manifest paths with it.

If `$NEW_VERSION` is not provided, ask the user before proceeding.

### 1. Detect the project name

Detect the project name using ecosystem-specific files, in priority order:

```bash
# If --path filter is set, use directory/project name from that path
if [ -n "$PATH_FILTER" ]; then
  # Try to find a project file inside the path
  CSPROJ=$(ls "$PATH_FILTER"/*.csproj 2>/dev/null | head -1)
  if [ -n "$CSPROJ" ]; then
    PROJECT_NAME=$(basename "$CSPROJ" .csproj)
  else
    PROJECT_NAME=$(basename "$PATH_FILTER")
  fi
fi

# If no path filter or name not found yet, detect from root
if [ -z "$PROJECT_NAME" ]; then
  SLN=$(ls *.sln 2>/dev/null | head -1)
  if [ -n "$SLN" ]; then
    PROJECT_NAME=$(basename "$SLN" .sln)
  elif [ -f "package.json" ]; then
    PROJECT_NAME=$(node -p "require('./package.json').name" 2>/dev/null)
  elif [ -f "Cargo.toml" ]; then
    PROJECT_NAME=$(grep -m1 '^name' Cargo.toml | sed 's/name *= *"\(.*\)"/\1/')
  elif [ -f "go.mod" ]; then
    PROJECT_NAME=$(head -1 go.mod | awk '{print $2}' | awk -F/ '{print $NF}')
  fi
fi

PROJECT_NAME=${PROJECT_NAME:-$(basename "$(git rev-parse --show-toplevel)")}
```

### 2. Detect the tag series and the last release

```bash
git tag -l | sed -E 's/[0-9]+\.[0-9]+\.[0-9]+.*$//' | sort | uniq -c   # prefixes in use: v, <package>-v, …
gh release list --limit 5   # what is published; the "Latest" column (gh 2.85 has no isLatest in --json)
```

- **The new tag follows the repo's series, not a fixed `v`.** One prefix → `TAG_PREFIX` is it. Several
  (a monorepo with one series per package: `api-v0.2.0`, `web-v1.4.0`) → the one matching `--path`, or
  ask. No tags → `v`. A package series names the project too: `$PROJECT_NAME` comes from that
  package's manifest (e.g. `packages/<pkg>/package.json`), not the root's.
- **`$TAG` already exists** → another tool (a release script that attaches the artifact) published
  this version. Never create a second tag for it: the notes cover the range ending at `$TAG`, and
  step 7 edits that release.

```bash
TAG="$TAG_PREFIX$NEW_VERSION"
git rev-parse -q --verify "refs/tags/$TAG" >/dev/null && END="$TAG" || END=HEAD
LAST_TAG=$(git describe --tags --abbrev=0 --match "${TAG_PREFIX}[0-9]*" --exclude "$TAG" "$END" 2>/dev/null)
if [ -n "$LAST_TAG" ]; then LOG_RANGE="$LAST_TAG..$END"; DIFF_FROM="$LAST_TAG"
else LOG_RANGE="$END"; DIFF_FROM=$(git hash-object -t tree /dev/null); fi   # first release: whole history
git rev-list --count --no-merges "$LOG_RANGE"
```

Zero commits → nothing to release: say so and stop. When another tool already published the
version, `END` is its tag and the notes describe that release; with no earlier tag in the series, the
range is the whole history. `--match` keeps `v[0-9]*` apart from `api-v…`.

### 3. Collect git data

Execute **in parallel**. If `$PATH_FILTER` is set, append `-- $PATH_FILTER` to the git log and git diff commands below:

```bash
# Commits since the last release (excluding merges)
git log "$LOG_RANGE" --format="%h %s%n%b" --no-merges [-- $PATH_FILTER]

# Changed file statistics
git diff --stat "$DIFF_FROM" "$END" [-- $PATH_FILTER]

# Merged PRs (merge commits)
git log "$LOG_RANGE" --merges --oneline [-- $PATH_FILTER]

# Contributors — resolve GitHub usernames through the commits API
# Why this is complex: git author names often differ from GitHub usernames
# (e.g., "JorUge" in git vs "@j0ruge" on GitHub). Email search fails when
# emails are not public. The most reliable method is checking commit authorship
# via the GitHub API, which links commits to GitHub accounts regardless of
# git config names.

# Step 1: Get the repo owner and name
REPO_OWNER=$(gh repo view --json owner --jq '.owner.login' 2>/dev/null)
REPO_NAME=$(gh repo view --json name --jq '.name' 2>/dev/null)

# Step 2: For each commit in the range, resolve the GitHub username via the commits API
# The GitHub API returns the linked GitHub account for each commit, which is
# the authoritative source (it uses the email-to-account mapping GitHub maintains)
# Pipe into `while read`, not a `for` over a variable: zsh does not word-split an unquoted
# variable, so the loop would run once with every sha joined, and `2>/dev/null` would hide the
# error (0 contributors, rc 0).
git log "$LOG_RANGE" --format="%H" --no-merges [-- $PATH_FILTER] | while read -r sha; do
  gh api "/repos/$REPO_OWNER/$REPO_NAME/commits/$sha" --jq '.author.login // empty' 2>/dev/null
done | grep -v '^$' | sort | uniq | sed 's/^/@/'

# Total files and lines
git diff --shortstat "$DIFF_FROM" "$END" [-- $PATH_FILTER]
```

### 4. Analyze and categorize commits

Read the body and title of each commit to classify into categories:

| Prefix / Pattern           | Category             |
|----------------------------|----------------------|
| `feat:`                    | ✨ New Features      |
| `fix:`                     | 🐛 Bug Fixes        |
| `refactor:`                | 🏗️ Refactoring      |
| `docs:`                    | 📚 Documentation     |
| `test:`                    | 🧪 Tests             |
| `perf:`                    | ⚡ Performance       |
| `security` / `harden`     | 🔒 Security          |
| `chore:` / `ci:` / `build:` | 📦 Infrastructure  |
| No prefix                  | Analyze content and classify manually |

For each **feature** (`feat:`), group by source PR/branch when possible, creating a subsection with a descriptive title.

### 5. Identify added/removed dependencies

Auto-detect the package ecosystem and diff the appropriate files. With `$PATH_FILTER`, the
manifests are the ones inside it: prefix each path, never append a second `-- $PATH_FILTER`. Git
reads everything after the first `--` as pathspecs and adds them up, so the second one lists the
whole directory instead of filtering the manifest.

```bash
P=${PATH_FILTER:+${PATH_FILTER%/}/}   # "" without --path, "<dir>/" with it

# C#/.NET — PackageReference in .csproj files
git diff "$DIFF_FROM" "$END" -- "${P}*.csproj" "${P}Directory.Build.props" "${P}Directory.Packages.props"

# Node.js — package.json
git diff "$DIFF_FROM" "$END" -- "${P}package.json"

# Python — pyproject.toml, requirements.txt
git diff "$DIFF_FROM" "$END" -- "${P}pyproject.toml" "${P}requirements.txt" "${P}setup.py"

# Go — go.mod
git diff "$DIFF_FROM" "$END" -- "${P}go.mod"

# Rust — Cargo.toml
git diff "$DIFF_FROM" "$END" -- "${P}Cargo.toml"
```

Only run the command(s) matching the detected ecosystem. Analyze the diff to list added, removed, and updated dependencies.

For C#/.NET projects, look for `<PackageReference Include="..." Version="..." />` changes.

### 6. Compose the Release Note

Use **exactly** this format (adapt sections according to the collected data — omit empty sections):

````markdown
# 🚀 $PROJECT_NAME v$NEW_VERSION

**Release Date:** $TODAY_DATE
**Full Changelog:** $LAST_TAG...$TAG (first release: https://github.com/$REPO_OWNER/$REPO_NAME/commits/$TAG)
**$N files changed** — $INSERTIONS insertions(+), $DELETIONS deletions(-)

---

## ✨ New Features

### Descriptive feature title (#PR — `branch-name`)
- Bullet point describing the change with relevant technical details
- Mention endpoints, modules, integrations created
- Use **bold** for important technical terms

---

## 🏗️ Refactoring

- **Short title** — description of the refactoring with context

---

## 🔒 Security

- **Short title** — description of the security improvement

---

## 🐛 Bug Fixes

- **Identifier (if any)** — description of the fix

---

## ⚡ Performance

- **Short title** — description of the improvement

---

## 📚 Documentation

- List added or updated documentation
- Mention specific files when relevant

---

## 🧪 Tests

- **N test files** added/modified
- List test types: integration, unit, e2e
- Mention covered domains/modules

---

## 📦 Dependencies

- **Added:** list new packages
- **Removed:** list removed packages
- **Updated:** list packages with version changes
- Runtime/SDK version changes (e.g., .NET, Node.js, Go, Python)

---

## Included Pull Requests

- #N — short PR title/description

---

**Contributors:** @resolved-github-usernames (from the commits API in step 3, never git author names)
````

### 7. Create or edit the Release

**A new tag** — immediately after composing the release note, create the GitHub Release **without
asking for confirmation**:

```bash
gh release create $TAG --target $(git branch --show-current) --title "$TAG" --notes "$RELEASE_NOTES"
```

**`$TAG` already published** (step 2) — editing replaces the text of a release people already read:
read the current body first, carry what it holds (a checksum line the release script wrote, for
example) into the new note, show the note and ask. Then:

```bash
gh release view "$TAG" --json body -q .body          # before: what the new note must keep
NOTES_FILE=$(mktemp) && printf '%s\n' "$RELEASE_NOTES" > "$NOTES_FILE"   # outside the repo
gh release edit "$TAG" --notes-file "$NOTES_FILE"
gh release view "$TAG" --json body,assets            # after: body equal to the file (gh adds one final newline), assets unchanged
```

**The project reserves releases to a human** (its `CLAUDE.md` or `AGENTS.md` says so, e.g. "an
agent session runs only `--dry-run`") → that rule wins over "without asking": show the note and the
command, and run it on the user's go-ahead.

### 8. Display result

Display the full release note in the conversation along with the URL of the created or edited release.

---

## Quality Rules

1. **Do not fabricate** — each item in the release note must have a corresponding commit or PR.
2. **English** — all text must be in English.
3. **Technical details** — mention endpoints, modules, files, and specific technologies.
4. **Group by feature** — commits related to the same PR/feature should be grouped, not listed individually.
5. **Omit empty sections** — if there are no bug fixes, do not include the 🐛 section.
6. **Consistent format** — follow the template above exactly, including emojis in headers.
7. **Contributors must be verified GitHub usernames** — NEVER guess or fabricate usernames. NEVER use git author names as GitHub usernames (they are often different — e.g., git name `JorUge` vs GitHub `@j0ruge`). Resolve them with the commits API in step 3, which maps each commit's email to its GitHub account; a commit it does not resolve is left out rather than guessed. The same person may have multiple git author names but only ONE GitHub username. Never list the same person twice. Exclude bot accounts (e.g., `noreply@anthropic.com`).
8. **Path filter** — when `--path` is used, only include commits and file changes that touch that directory. The release title should reflect the component name, not the whole repo.
