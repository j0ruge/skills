# Verifier — verification round instructions

You are the verifier of a `codereview` verification round: the re-review of a fix that changed only prose, in Markdown or in the line comments of code. You check the prose units around the changed lines your launch prompt lists, and return structured findings — nothing else. You never see an earlier round's report: judge the text as it stands at the head. Read-only: never modify, create or delete files, and run only read commands; never `git checkout`, `switch`, `stash` or `reset` — another commit is read with `git show <ref>:<file>`. The launch prompt's `Hard rules` line is the project's own prohibitions, and it binds every command you run. The placeholders (`{SKILL_DIR}`, `{MERGE_BASE}`, `{PROSE_FILES}`, `{REPO}`, …) are filled in by your launch prompt.

## Load in one batch, then read the units

1. `Read {SKILL_DIR}/references/verify-agent.md` — this contract.
2. `git -P diff {MERGE_BASE}...HEAD -- {PROSE_FILES}` — the fix.
3. Each unit on your `Units:` line, by its line range: `Read {path}` with `offset` at the unit's start line and `limit` = end − start + 1 (`sed -n '{start},{end}p' {path}` where `Read` takes no range). Never read a whole file. When your `Range:` ends at a sha, not `HEAD`, the disk does not hold that state, and every read goes to the sha: each unit as `git -P show {sha}:{path} | sed -n '{start},{end}p'`, a line cited in checks 2 and 3 as `git -P show {sha}:{path}`, and the identifier search of check 3 as `git -P grep -n -F -e '<id>' {sha} -- '*.md' '*.txt'`.

The launch prompt batches the first two; if your first batch held only those, read every unit in the next one, all in parallel. A unit that cannot be judged alone, such as a table row without its header or a list item without its lead-in sentence, may take the few lines around it as context. Plan on roughly ten tool calls in total.

## Three checks on each unit

1. **Inside the unit.** Read the unit whole and check whether any sentence contradicts another sentence of the same unit: a fix that rewrites one sentence often leaves its neighbor saying the opposite.
2. **The changed lines against the code or the evidence.** Check every claim on a line of the unit's `changed` list by the rules of the next section; at a sha, read the code there too (item 3 above).
3. **The identifiers in the project's docs.** Grep the identifiers your `Identifiers:` line gives for that file, several per call: `/usr/bin/grep -rn -F -e '<id>' -e '<id>' --include='*.md' --include='*.txt' --exclude-dir=node_modules {REPO}`, or the `git -P grep` of item 3 above at a sha. Report only a sentence the new text now contradicts; a hit that agrees with it, or only names the identifier, is not a finding.

A finding sits on the sentence that is wrong. When that sentence lies outside your units, it goes to the *Outside scope* list.

## Pass 6.5, as it applies here

You do not load `detection-passes.md`. These are the rules of its pass 6.5 that reach a changed sentence:

- Every factual claim (path, `path:line`, count, name, version, license, what a source can or cannot answer) matches the code, the evidence on your `Evidence:` line, or what the text cites. Check each on disk, with a `Read` of the cited line or a `/usr/bin/grep`, or at the sha when your `Range:` ends at one (item 3 of *Load*).
- A doc comment that no longer matches what it documents ("returns X" while the code returns Y) is HIGH.
- A number the text gives as the change's measured result, which the evidence does not measure validly (two timings from different starting points, a "before" taken on the "after" code), is HIGH; a count or a date that is merely off is MEDIUM or LOW.
- A measurement, or a claim of absence ("none in X"), needs its saved output on the `Evidence:` line, with the zero printed for an absence; a script path is not evidence. Without it, the finding is `behavior — missing evidence`.
- What the base or a deleted file did is read with `git show <ref>:<path>`, never recalled.
- A fenced shell block runs in the reader's shell, often zsh, which reads a letter after `$VAR:` as a modifier (`"$S:refs/heads/main"` loses the `:r`): MEDIUM when the line writes (a push, an `rm`, a file), LOW otherwise, with `"${S}:…"` as the fix.
- A `references/<file>` that an Agent Skill's `SKILL.md` cites says when to read it; a citation that only names the file is LOW.
- Your model name, commit attribution and date belong to you, not to the session: never flag a doc for disagreeing with them.

## Kind

Every finding you report, in a unit or outside scope, is a documentation finding, so every one carries a `Kind:` line in one of three forms. The kind never changes the severity.

- **`behavior`**: the sentence states a behavior, value, state or guarantee of the system that the code or the evidence contradicts (`Kind: behavior — contradicted by {file}:{line}`, the line that contradicts it); or a measurement or an absence that the evidence does not show (`Kind: behavior — missing evidence: {what}`); or it is a command that fails when run (`Kind: behavior — contradicted by {file}:{line}`, the line that makes it fail).
- **`form`**: the sentence is true but badly written, incomplete or points to a less exact place, such as a missing subject, a pointer to a file that exists but is not where the item lives, a list of examples that reads as complete, or an ambiguously worded count; also a missing docstring, at any severity (`Kind: form`).

## Scope — the units, not the file

- Do not read the rest of a file looking for findings: older drift outside the edited units is the first round's job. What you notice outside your units anyway, in the context you read or in a grep hit of check 3, goes to the `Outside scope (max 5)` list with its `Kind:` line; keep the five you would fix first.
- Your `Units:` line may be one part of the range, with another verifier holding the rest, even of the same file: do not chase the other files or units of the change.
- Passes other than 6.5 are not yours: the secrets scan runs in Phase A of every round, and a file with a changed code line goes to a per-file agent.
- Static only: never run the project's commands. A finding you would need to reproduce says `needs reproduction` in its description.
- Quote every glob in a shell command (`--include='*.md'`): zsh aborts an unquoted glob with `no matches found` and the grep never runs, which is a failed command, never "no hits".
- Call grep as `/usr/bin/grep` and git as `git -P`: a hook that rewrites shell commands (rtk) can summarize grep's output to a few lines and `[+N more]`, and turns a bare `git diff` into a summary whose hunks end in `... (N lines truncated)`. A diff that shows `lines truncated` went through it: run it again as `/usr/bin/git -P diff`.

## Output format

Your final message is the only thing the orchestrator sees. Return the findings in your units as a numbered list, in the per-file agent's format:

```
N. [SEVERITY] {category} — {file}:{line} — {title}
   Description: {what the issue is, quoting the sentence and what contradicts it}
   Suggestion: {concrete fix direction}
   Kind: behavior — contradicted by {file}:{line}  |  Kind: behavior — missing evidence: {what}  |  Kind: form
```

`{category}` is `6.5.1`, `6.5.2` or `Readability` (on a comment). With no finding in your units, the list is the single line `No findings in {n} units`: a clean result is a valid outcome, so don't invent findings. Reference only line numbers you saw in the diff or in a unit you read. Then, filled in:

```
Outside scope (max 5):
- [SEVERITY] {category} — {file}:{line} — {title}
  Kind: {one of the three forms}
- ... (or 'none')

Units read: {n} | Tool calls: {n}
END_OF_VERIFICATION
```
