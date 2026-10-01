# Thread Resolution — Phase 5 commands in full

Read this at Phase 5, after all items are processed and tests pass. Run every command below
directly (never through a subagent): the closing count is the point, and a delegated batch that
silently skips a thread reports success just as convincingly as one that didn't.

`OWNER` and `REPO_NAME` are the two halves of `$REPO`; `PR_NUMBER` is the PR from the user input.

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
