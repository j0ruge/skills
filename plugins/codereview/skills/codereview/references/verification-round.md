# Verification round — the orchestrator's side

Read this when a re-review range (`base=` from an earlier round) has prose files: Phase A step 9 printed `PROSE_SCOPE` with a `DOCS` or `DOC_ONLY` file. It decides which files go to a verifier, launches the verifiers and closes the earlier round's findings in Phase C. The verifier's own contract is `verify-agent.md`; only the verifier reads it.

## When it runs

All of these hold, or the re-review runs as a full round (SKILL.md, Phases B and C as written):

- `base=` names the head an earlier round reviewed, and the review is not in `worktree` mode (configuration.md): an uncommitted fix gives the script no range.
- The session holds that round's open findings (number, `file:line`, kind, claim), in the conversation or in a file it names; without that list, the re-review runs as a full round. The list stays with the session: no prompt carries it.
- The user passed no `verify=off`, and the session knows of no changed comment line inside a multi-line string or heredoc (*Which files*); when it knows of one, it falls back to a full round on its own.
- `prose_units.py` exited 0. A non-zero exit means no scope, never "no prose files", and the report says the round ran in full.
- An agent can be launched. The verifier is always an agent, never inline, whatever the file count: when no agent can be launched (runtime-routing.md, the inline fallback), there is no verification round.

## Which files

A file goes to a verifier only when `PROSE_SCOPE` gives it `kind` `DOCS` or `DOC_ONLY` and at least one unit, and Phase A did not classify it EXCLUDED or CONFIG: Phase A's classification wins over the script's `kind`. Every other file of the range follows today's flow: a deleted file (status `D`, whose entry has `units: []`), a `kind: CODE` file, any file with `units: []`, and an EXCLUDED or CONFIG one.

The script errs toward `CODE` — only line comments (`//`, `#`, `--`) count, so a changed block-comment line, a renamed, re-moded, new or deleted code file, a directive line, `.yml`/`.yaml`/`.toml`, `requirements*.txt`, `CMakeLists.txt` and a prose file whose changes land in no unit all take the full flow — with one declared limit: a `#`, `//` or `--` line inside a multi-line string or heredoc still counts as a comment. A session that sees such a line among a `DOC_ONLY` file's changes runs the round in full.

The sweep (Phase B2) is skipped only in a verification round that leaves no CODE or CONFIG file of the range outside the verifiers. A full round, `worktree` mode included, runs it as written.

## Launch

One verifier takes at most 400 unit lines (`unit_lines`) and 12 files. Above that, split by file across more verifiers in the same batch; a single file over 400 unit lines splits by unit ranges, each verifier given only its own ranges on its `Units:` line. `model: REVIEW_MODEL` on every call. Emit only the launch prompt below, placeholders filled — nothing added, nothing removed; exception: a refused `Read` under `{SKILL_DIR}` (runtime-routing.md, *Contrato ilegível*). Under `head=<sha>`, write that sha for `HEAD` in the diff and the `Range:` line (configuration.md, `head`).

```
Agent(model: REVIEW_MODEL, prompt: "
Start with ONE batch of parallel tool calls: Read {SKILL_DIR}/references/verify-agent.md and run
`git -P diff {MERGE_BASE}...HEAD -- {PROSE_FILES}`. Then follow verify-agent.md exactly.

- Repository: {REPO}
- Range: {MERGE_BASE}...HEAD
- Units: {one line per unit: path:start-end (changed: n, n)}
- Identifiers: {per file, from PROSE_SCOPE}
- Evidence: {path or none, per file}
- Skill dir: {SKILL_DIR}
- Hard rules: {CLAUDE.md prohibitions, verbatim, or none}
")
```

A verifier whose message does not end in `END_OF_VERIFICATION` is relaunched once, with the same files, base and head. When the sentinel is still missing, its files take the full flow in this round (a per-file agent each, and the sweep by the rule above), and their open findings stay open until that flow answers.

## Closing the earlier round's findings (Phase C, after step 1)

For each open finding of the earlier round:

- On a file a verifier held: read the range's diff over its lines. It closes only when its unit was read by a verifier whose message ended in `END_OF_VERIFICATION`, the diff touched that unit, and the verifier gave no `behavior` there. One whose lines the diff did not touch stays open and counts in the grade, unless a written verdict dismissed it.
- On a file that took today's flow (`kind: CODE`, or a verifier's files after its relaunch failed): it closes by today's rule, on what that flow's agent reports.

From a verifier's *Outside scope* list, a `behavior` on a line the branch wrote counts like any finding. The rest (a `form`, or a line older than the branch) does not count and is not dropped: list it in the report for the project's tracker.

Declared limit: older drift outside the edited units is not sought; it is the first round's job (configuration.md, *Re-review rounds*, first item).
