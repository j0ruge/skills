# Byte-Exact Verification — Phase 3.1 step 1.1 in full

Read this when a reviewer's finding hinges on bytes you cannot see: NUL bytes (`\0`, `0x00`, `^@`),
BOM, zero-width characters, non-printable bytes, embedded escape sequences, or anything described
as an "invisible/control character".

## Why `Read` is not enough

The `Read` tool renders those bytes as plain whitespace and silently misleads the analysis. The
screen output of `\0create\0` is indistinguishable from ` create ` (regular spaces) — both look like
leading-space sentinels. The `Read` view is a normalized text rendering, not byte-faithful, and it
gives no warning when bytes were collapsed.

Before classifying such a finding as a false positive, confirm against the actual bytes. Trust
`od`/`xxd` over `Read` whenever the finding hinges on what specific bytes are present.

## Commands

| Need | Command |
|------|---------|
| Inspect a specific line | `awk 'NR==<line>' <file> \| od -c \| head` |
| Count NUL bytes in a whole file | `tr -cd '\000' < <file> \| wc -c` |
| Search for arbitrary byte patterns | `xxd <file> \| grep -i <pattern>` |
| Fallback when `od`/`xxd`/`tr` are unavailable | `python -c "print(repr(open('<file>').read()))"` — `repr()` produces a byte-faithful representation that escapes control characters |

## The principle

Same anti-trust principle as step 1.5 (verify referenced state) applied to a different surface:
don't outsource truth about bytes to a normalized view. Reviewers — especially deterministic
parsers like Copilot's — flag exactly these cases, and they are exactly the cases where `Read` is
unreliable. The cost of `od -c <file> | head` is essentially zero; the cost of a wrong "not
applicable" verdict is a public retraction.
