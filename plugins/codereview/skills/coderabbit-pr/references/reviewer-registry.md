# Reviewer Registry

Maps AI review bots to their GitHub login, comment structure, and output file name.

## Supported Reviewers

| Reviewer | GitHub Login(s) | Output File | Comment Style |
|----------|----------------|-------------|---------------|
| CodeRabbit | `coderabbitai[bot]`, `coderabbitai` | `coderabbit-review.md` | Inline + review body with `<details>` blocks |
| GitHub Copilot | `copilot-pull-request-reviewer[bot]` (review object), `Copilot` (its inline comments) | `copilot-review.md` | Review body + inline comments, under two logins |
| Gemini Code Assist | `gemini-code-assist[bot]` | `gemini-review.md` | Inline + review body summary |
| Codex | `chatgpt-codex-connector[bot]` | `codex-review.md` | Inline comments + boilerplate review body + status summary on the issue |

## Comment Structures by Reviewer

### CodeRabbit (`coderabbitai[bot]`)

Posts in **two places**:

1. **Inline review comments** — file-level, attached to diff lines (typically 2-12 per review)
2. **Review body** — contains the MAJORITY of findings:
   - "Actionable comments posted: N" header
   - `🧹 Nitpick comments` section with `<details>/<summary>` blocks per file
   - `⚠️ Outside diff range comments` section with same structure
   - Each finding: `` `LINES`: _CATEGORY_ | _SEVERITY_ `` followed by `**TITLE**`

**Severity markers**: `🔴` Critical, `🟠` Major/HIGH, `🟡` Medium, `🔵` Minor/LOW, `Refactor suggestion` = MEDIUM

**Metadata to discard**: walkthrough summaries, "Actionable comments posted" headers, paused review notices, `<!-- fingerprinting:... -->` blocks

### GitHub Copilot (`copilot-pull-request-reviewer[bot]` / `Copilot`)

Posts in **two places, under two logins**: the review object on `/reviews` is authored by `copilot-pull-request-reviewer[bot]` and may carry a body; the inline comments on `/comments` that belong to that review are authored by `Copilot`. Both logins are this reviewer — matching only one of them files half the findings under an unknown reviewer.

- Comments are plain text with markdown formatting
- Severity is typically not explicitly marked — default to MEDIUM
- Suggestions come in ````suggestion` code blocks
- No `<details>` blocks or structured sections

### Gemini Code Assist (`gemini-code-assist[bot]`)

Posts in **two places**:

1. **Review body** — contains a summary with severity-tagged findings
2. **Inline comments** — attached to specific lines

- Severity markers: `critical`, `high`, `medium`, `low` (text-based, case-insensitive)
- Suggestions in standard markdown code blocks

### Codex (`chatgpt-codex-connector[bot]`)

Posts in **three places** (measured on a `@codex review` request, 2026-10-01):

1. **Status summary** — an *issue* comment (`/issues/{PR}/comments`, which Phase 1 does not read)
   marked `<!-- codex-pull-request-review-summary -->`, with a table whose Status cell goes
   `🔄 **Running**` → `✅ **Completed**` (four minutes apart in that run). It appears **first**,
   before any finding exists.
2. **Review object** — state `COMMENTED`, body `### 💡 Codex Review` + a "Reviewed commit" line and
   an "About Codex in GitHub" `<details>` block. Pure metadata: discard it.
3. **Inline comments** — the findings. Title in bold, preceded by a priority badge
   (`![P1 Badge](https://img.shields.io/badge/P1-orange…)`); often an `AGENTS.md reference:` link.

- Severity marker: the `P<n>` badge. No fixed mapping — recalibrate in Phase 3 (Default: MEDIUM)
- May include code suggestions in fenced blocks

**While the summary says `Running`, Codex is pending — case (b), not a pass.** At that moment
`/pulls/{PR}/comments` holds zero Codex findings, and a wait loop that accepts *any* comment from
the bot exits on the summary itself. Wait for `Completed` before extracting:

```bash
gh api "repos/$REPO/issues/$PR/comments" --paginate \
  --jq '.[] | select(.body | contains("codex-pull-request-review-summary")) | .body' \
  | grep -oE 'Running|Completed' | tail -1
```

## Detection Strategy

To detect which reviewers are present on a PR, query both comment endpoints and collect unique `user.login` values that match any known bot login from the registry above.

```bash
# Collect all unique reviewer bot logins
gh api "repos/{REPO}/pulls/{PR}/comments" --paginate \
  --jq '[.[].user.login] | unique[]'

gh api "repos/{REPO}/pulls/{PR}/reviews" --paginate \
  --jq '[.[].user.login] | unique[]'
```

Match against the registry. Only process reviewers that have at least one comment.

## Extensibility

When a new reviewer bot appears that isn't in this registry:
1. Use the generic inline-comment parser (same as Copilot)
2. Default severity to MEDIUM
3. Name the output file `{bot-login}-review.md`
4. Log a note: "Unknown reviewer {login} — using generic parser"
