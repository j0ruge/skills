# Safe deletion — executing an authorized round

Read this before deleting anything, even once the user has authorized it.

## The sequence, every time

1. **Fresh evidence.** Re-check each target on disk now — existence, size, and for duplicates a fresh full hash of
   both copies. The analysis may be hours old; files move.
2. **Manifest before destruction.** Write the list of what will go (paths, sizes, hashes where relevant) to a file
   outside temp folders — the user's plans/reports folder. It is the cheapest safety net and only works if written
   before.
3. **Reversible step first** where one exists: rename (`X` → `X.DELETE-<date>`), quit-and-rename for caches owned by
   a running client, move to a rescue folder. Use the system for a while (a week for a dead profile, minutes for a
   cache) and check what the plan says should still work.
4. **Delete from the saved list**, not from a fresh glob: `scripts/delete-from-list.sh <list> <allowed-root>` (Git Bash
   paths, `/c/...`). It refuses anything outside the root and treats "still exists after rm" as a failure. Use
   `--dry-run` first on a new list.
5. **Verify by artifact.** The path is gone; the kept copy still exists; the owning app still works (e.g. every
   `extensions.json` entry still has its folder; the Drive letter still lists files). Then `Get-Volume` and compare
   with the round's expected gain. Explain any gap.
6. **Record**: round, gain measured vs estimated, surprises — in the plan's Act section.

## Tooling quirks seen in Claude Code on Windows

- The Bash tool is Git Bash: paths are `/c/Users/...`. When telling the user to run something with the `!` prefix,
  give bash syntax — `Remove-Item` at a `!` prompt fails with "command not found".
- A bare `bash` invoked from PowerShell is often `C:\Windows\System32\bash.exe` — WSL, where `/c/...` does not exist.
  Call `%ProgramFiles%\Git\bin\bash.exe` explicitly, and never run a script from a `\\wsl.localhost\...` path
  through Git Bash.
- Some setups have a guard hook that blocks `Remove-Item` in PowerShell, even in scratch folders. That fits the
  default (the user deletes). After explicit authorization, `delete-from-list.sh` through the Bash tool is the
  controlled path; do not look for ways around a guard the user did not lift.
- `Clear-RecycleBin -DriveLetter X -Force` empties one drive's bin; show `recyclebin-list.ps1` first.
- Folders in `%TEMP%` created by elevated installers return "Permission denied" without admin; files held open by
  running apps (tray tools, editors) fail even as admin. Measure them (usually MB) and move on.

## After deleting a tool's folder

- PATH entries that pointed into it now dangle (e.g. `...\lm-studio\bin`): list with
  `[Environment]::GetEnvironmentVariable('Path','User') -split ';' | Where-Object { $_ -and -not (Test-Path $_) }`
  and offer to remove them.
- Shortcuts, scheduled tasks or services that pointed there: `refs-scan.ps1` again on the old path.

## Your own footprint

Analysis creates files too: inventories, copies, extracted archives. Before writing anything that could exceed 10% of the destination's free space (the rule
`scripts/room-check.ps1` enforces), run it; keep inventories on the drive with the most room; delete your own scratch copies as part of
the session (they are yours — but say what they were). Re-measure at the end of every session: one session (2026-10) found the
drive it was cleaning 4.3 GB fuller because of its own copy of a database.
