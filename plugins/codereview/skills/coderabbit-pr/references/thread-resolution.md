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
[ "$(gh pr view "$PR" --json headRefOid -q .headRefOid)" = "$(git rev-parse HEAD)" ] \
  && echo "head carries the fixes" || echo "PR head differs from local HEAD"
```

Anything uncommitted, or a different head → stop, show the user the diff and ask them to commit
and push (or to authorise you to). Re-run the check after the push. With Phase 3 having changed
no files (every item already fixed / not applicable), the check passes trivially — resolve.

**Authorised to commit, one commit per finding?** Several findings usually share a file, so split
by hunk: classify every hunk of `git diff -U3` by finding **before** staging anything (one that
fits no finding stops the split), stage each group with `git apply --cached -`, and commit. A
derived artifact the code shifts (line anchors in a doc) is recomputed per commit against the
index (`git diff --cached`), or the middle commits fail a check the last one passes. Then prove
the series: `git diff <base> HEAD` must be byte-identical (`cmp`) to the patch the suite passed on —
a misfiled or lost hunk still leaves a clean tree. Measured 2026-10-05 (sdd_agents PR #222): 14
hunks in 3 shared files, 4 commits, `cmp` equal.

Measured on 2026-10-02 (sdd_agents PR #195): followed literally, the run would have resolved the
CodeRabbit thread while the PR head (`3c739aa`) still carried the defect; the fix was pushed as
`96532c9` first, and only then resolved.

A different head right after **your own** push can be the API lagging, not the push failing. Read
the remote ref itself before you stop:

```bash
git ls-remote origin "refs/heads/$(gh pr view "$PR" --json headRefName -q .headRefName)"
```

If it equals `git rev-parse HEAD`, the push landed: re-run the check a few seconds later instead of
asking the user to push again. Measured on 2026-10-04 (sdd_agents PR #219): right after `git push`,
`headRefOid` still answered the pre-push `b9e95ba` while `ls-remote` already had `d8da110`; the next
query answered `d8da110`.

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
