# Thread Resolution — Phase 5 commands in full

Read this at Phase 5, after all items are processed and tests pass. Run every command below
directly (never through a subagent): the closing count is the point, and a delegated batch that
silently skips a thread reports success just as convincingly as one that didn't.

`OWNER` and `REPO_NAME` are the two halves of `$REPO`; `PR_NUMBER` is the PR from the user input.

## 5.0 The PR Head Carries the Fixes

Resolving a thread tells every reader "this is fixed in the PR". The skill never commits, so
right after Phase 4 the fixes exist only on disk. Check before 5.1:

```bash
git status --porcelain                                  # must not list the files you fixed
L=$(git rev-parse HEAD); P=$(gh pr view "$PR" --json headRefOid -q .headRefOid)
R=$(git ls-remote origin "refs/heads/$(gh pr view "$PR" --json headRefName -q .headRefName)" | cut -f1)
if [ "$P" = "$L" ]; then echo "head carries the fixes"
elif [ "$R" = "$L" ]; then echo "pushed: the API still answers ${P:-nothing}, read it again in a few seconds"
else echo "not pushed: the remote has ${R:-nothing}, local HEAD is $L"; fi
```

Anything uncommitted, or `not pushed` → stop, show the user the diff and ask them to commit and
push (or to authorise you to). Re-run the check after the push. With Phase 3 having changed no
files (every item already fixed / not applicable), the check passes trivially — resolve. A merged
PR has no head to carry them: check the follow-up PR's (pr-branch.md, *A PR already merged*).

**`pushed:` is the API behind your own push, not a push that failed.** Run the check again a few
seconds later; never push again, and never blame a hook for it. Right after a push, every API read
of the PR head can still answer the old one: `headRefOid` from `gh pr view`, and the `head.sha` of
REST `pulls/<n>`, even in the response to a `PATCH` sent after the push. `git ls-remote` reads the
branch itself. Measured on 2026-10-04 (sdd_agents PR #219): `headRefOid` still answered the
pre-push `b9e95ba` while `ls-remote` already had `d8da110`; the next query answered `d8da110`.
Measured on 2026-11-01 (sdd_agents PR #335), with the old two-way check and this paragraph at the
end of the section: a run that read only the section's top saw `f8b6938` against a local
`a25482f`, took it for a pre-push refusing the checklist and pushed again (`Everything
up-to-date`); the next read answered `a25482f`. Same day (sdd_agents PR #334): the `PATCH` of the
PR body, sent right after the push of `5d14540`, returned `head.sha` `0928490`; five seconds later
`ls-remote` and `headRefOid` both had `5d14540`.

**A pre-push that refuses a dirty tree refuses the checklist too.** The `{reviewer}-review.md`
files sit untracked in the root (`?? codex-review.md`), and a hook that rejects untracked files
stops the push this step asks for. Before that push, move them out of the tree to a scratch
directory and keep them there; Phase 6 deletes them there. Never `--no-verify`. The `.gitignore`
entry Phase 6 suggests would also clear it, but it is a commit to the user's repo, theirs to make.
Measured 2026-10-17 (acme-libs PR #4): the hook has a case "deve recusar, sem rodar o gate, o push
com arquivo não rastreado", and the push went through once the checklist left the root.

**Authorised to commit, one commit per finding?** Several findings usually share a file, so split
by hunk: classify every hunk of `git diff -U3` by finding **before** staging anything (one that
fits no finding stops the split), stage each group with `git apply --cached -`, and commit.
`git add -p` fed fixed answers (a here-doc of `n`/`y`) is the tempting shortcut, and it is blind:
each answer goes to whichever hunk git shows next, so a wrong guess stages the other finding's hunk
and the tree stays clean either way. Measured 2026-10-23 (magic_tutor PR #73): `n`, `y` on
`docs/monitor.md` staged the second finding's hunk (`4 +++-` in `git diff --cached --stat`) instead
of the first's (`2 +-`); the cached diff caught it before the commit. A
derived artifact the code shifts (line anchors in a doc) is recomputed per commit against the
index (`git diff --cached`), or the middle commits fail a check the last one passes. A tool that
rewrites only the index leaves the working tree on the old value: after the commit, `git diff`
shows the reversal as a pending edit, and the next `git add -A` undoes the recomputation. When
that reversal is the file's whole diff, `git checkout -- <file>` aligns the tree before the next
commit. Measured 2026-10-05 (sdd_agents PR #222, `69eeb4f`): an anchor rewritten 2122 → 2132 in
the index only; the checkout left the tree clean and the anchor check green. Then prove
the series: `git diff <base> HEAD` must be byte-identical (`cmp`) to the patch the suite passed on —
a misfiled or lost hunk still leaves a clean tree. Measured 2026-10-05 (sdd_agents PR #222): 14
hunks in 3 shared files, 4 commits, `cmp` equal.

Measured on 2026-10-02 (sdd_agents PR #195): followed literally, the run would have resolved the
CodeRabbit thread while the PR head (`3c739aa`) still carried the defect; the fix was pushed as
`96532c9` first, and only then resolved.

## 5.1 List Unresolved Threads

```bash
gh api graphql -f query='{
  repository(owner: "OWNER", name: "REPO_NAME") {
    pullRequest(number: PR_NUMBER) {
      reviewThreads(first: 100) {
        nodes { id isResolved comments(first: 1) { nodes { author { login } path } } }
      }
    }
  }
}' --jq '.data.repository.pullRequest.reviewThreads.nodes[]
         | select(.isResolved == false)
         | "\(.id)\t\(.comments.nodes[0].author.login)\t\(.comments.nodes[0].path)"'
```

## 5.2 Resolve Each Thread

Resolve threads from **all** reviewers (coderabbitai, copilot, gemini, codex, …), not only those processed in Phase 3.

**Reply first where you did not follow the suggestion.** For every item whose verdict was *Not
applicable* or *Fixed (alternative approach)*, post the reason on its thread before resolving it.
Resolved in silence, the thread — the audit trail Phase 6 points to — keeps the reviewer's claim
with no answer, and the bot raises the same finding on the next PR:

```bash
gh api -X POST "repos/$REPO/pulls/$PR/comments/<ID>/replies" \
  -f body='<the checklist Status line, in one or two sentences>'
```

`<ID>` is the inline comment's numeric `ID` from Phase 1.3, not the `PRRT_…` thread id. A finding
from a review body or outside the diff has no thread to reply to: its reason lives in the commit
message and the final report. Measured on 2026-10-04 (sdd_agents PR #219): CodeRabbit asked to
reopen a backlog record the project had decided; the reply with the reason drew *"Retiro a
recomendação"* and a recorded learning from the bot.

Feed 5.1's output straight into the loop, one thread per line:

```bash
<5.1 command> | while IFS=$'\t' read -r id _; do
  gh api graphql -f query="mutation { resolveReviewThread(input: {threadId: \"$id\"}) { thread { isResolved } } }" \
    --jq '.data.resolveReviewThread.thread.isResolved' | sed "s|^|$id -> |"
done
```

Do **not** capture the ids in a variable and loop with `for id in $ids`. zsh does not word-split an
unquoted variable, so the loop runs **once** with every id joined by newlines, and the API answers
`NOT_FOUND … global id of 'PRRT_…\nPRRT_…'`. Measured on 2026-10-01: zero threads resolved, caught
only by 5.3 reporting `unresolved: 2 of 2`. `while read` behaves the same in bash and zsh.

If you read more columns than the id — 5.1 prints the author and the file path too — never name the
path variable `path`. In zsh `path` is the array tied to `PATH`, so `read -r id who path` empties the
search path inside the loop and every `gh` and `sed` after it dies with `command not found`. Measured
on 2026-10-03: nothing resolved, every line an error, caught by 5.3. Use `_`, or a name like `file`.

Each line must print `true`. Anything else (an error, `false`) means that thread is still open — carry it into 5.3.
No line at all means 5.1 listed nothing, and that is not a failure: a bot can resolve its own
thread once the push reaches it, and 5.3 decides. Measured on 2026-11-01 (sdd_agents PR #335): the
fixed thread's `resolvedBy` was `coderabbitai[bot]`, the loop printed nothing and 5.3 answered
`total: 1  unresolved: 0`.

## 5.3 Verify Zero Remain

```bash
gh api graphql -f query='{
  repository(owner: "OWNER", name: "REPO_NAME") {
    pullRequest(number: PR_NUMBER) { reviewThreads(first: 100) { nodes { id isResolved } } }
  }
}' --jq '"total: \(.data.repository.pullRequest.reviewThreads.nodes | length)  unresolved: \([.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved==false)] | length)"'
```

`unresolved: 0` is the success condition and the gate for Phase 6. Not zero → report which threads
remain and why; never describe the run as complete. `reviewThreads(first: 100)` caps at 100: on a PR
that busy, page through and say so.

Then update each checklist with:

```markdown
### Conversations

- **Total threads**: {n}
- **Resolved in this run**: {n}
- **Previously resolved**: {n}
```

## 5.4 The Fix Commits Need a Review Too

The fixes 5.0 pushed are commits no bot has seen. Coverage is per commit (SKILL.md Phase 2, case
b), and a reviewer that runs only on request (Codex, `reviewer-registry.md`) never looks at them on
its own: the closing report would carry fix commits reviewed by nobody. Before the report and
Phase 6, offer to post `@codex review` on the PR (a comment on the user's PR is theirs to approve),
then wait, in the background, for `completed` on the new head with the registry's
`codex-review-state` command. `findings=false` is case (a) for the fix commits; a new finding is a
new round of this skill. With `findings=true`, read what was posted on the head before calling it a
finding (registry, *Codex*). CodeRabbit reviews the push on its own: read its allowance line before
asking (registry, *Coverage Per Commit*). Declined, the report names the fix commits as unreviewed.
Measured 2026-10-25 (magic_tutor PR #103): Codex's P2 was on `ee81a77`, the fix went out as
`693832e`, and the thread was resolved with `total: 1 unresolved: 0`. Only the user's
`@codex review` brought `completed 693832e… findings=false` and a 👍 on the PR.
