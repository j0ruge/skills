---
name: windows-disk-cleanup
description: "Frees Windows disk space without losing data: inventories drives, proves duplicates by hash (hardlinks discounted), deletes only in user-authorized rounds — manifest and reversible step first, re-measure after. Knows dev caches, Drive cache, old profiles, WSL/Docker disks. Triggers — disk full, free up space, C: full, clean disk, what can I delete."
metadata:
  version: 0.1.3
---

# Windows disk cleanup — measure, prove, delete in rounds, keep it from refilling

Turns "my disk is full, what can I delete?" into a measured plan and a sequence of small, verified deletions.
The method is PDCA: measure (Plan), delete one authorized round at a time (Do), verify by artifact and re-measure
(Check), then add a guard so the space does not fill again (Act).

## The contract with the user

- **Read-only until authorized.** Analysis, inventories and recommendations need no permission; deleting does.
  Many users say "I will delete it myself" — then deliver commands and a plan, and delete nothing.
- **Authorization is per round** ("I authorize round 2"). It does not carry over to the next round, to a resumed
  session, or to items added after the user said yes. Record it in the plan.
- **A broad go-ahead is not a round.** "Clean whatever is safe" or "I trust you" authorizes the analysis, not a list
  the user has not seen. Present round 1 (items, gain, evidence) and ask. The reversible step (rename, holding folder)
  belongs to its round and waits for the same yes. Evals in 2026-10 showed the need: without this line, the skill
  deleted two proven items and renamed an old profile on such a request.
- **The user owns personal data decisions** (media, games, work archives). Bring evidence (sizes, dates, "never
  played", "identical to X"), not verdicts.
- **Machine context changes the advice.** Read the machine's notes/memories/runbooks before recommending pagefile,
  hibernation or dump changes (an open BSOD investigation needs the pagefile), and ask whether Docker holds
  production data before treating its volumes as disposable.

## Workflow

### 1. Baseline
Before anything else, record free space per volume, admin status and RAM (`references/measurement.md` § Baseline first);
read that file before the inventory and whenever a number does not add up. Set the goal with the user — a common
target is ≥ 15% free per drive — and write it down: success is measured against it.

### 2. Inventory (Gemba)
- Run `scripts/selftest.ps1` once: the probes earn trust by going red on sabotaged cases. A FAIL means do not use
  that probe.
- `scripts/scan.ps1` per drive, in parallel (`Start-ThreadJob`), into a folder on the drive with most room
  (`scripts/room-check.ps1`). Then `scripts/summarize.ps1`.
- Report **coverage** (seen / used) next to every total. Without admin, a few % is unreadable — say so, do not guess.
- `scripts/dups.ps1` for cross-drive duplicates proven by content; it reports apparent vs real waste (hardlinks).
  `scripts/zipverify.ps1` proves a zip and its extracted folder equal by CRC32.
- Things the scan cannot see: Recycle Bins (`scripts/recyclebin-list.ps1`), WSL/Docker disks measured from inside
  (read `references/wsl-docker.md` when a `.vhdx` is among the biggest files), sync-client caches
  (`scripts/drivefs-status.py`), installed programs (`Uninstall` registry keys with `EstimatedSize`), Steam
  (`scripts/steam-games.ps1`), old editor extensions (`scripts/vscode-obsolete.ps1`).

### 3. Classify into rounds, safest first
Before classifying, read `references/catalog.md`: it lists, per kind of item, the evidence that makes it safe and
the reclaim method. Typical rounds:

| Round | Content | Risk |
|---|---|---|
| 1 | Regenerable caches via their own tools (pip, npm, Yarn, uv, Temp, old editor extensions, `.incomplete` downloads) | none — re-downloads at worst |
| 2 | Unused models/installers, duplicates proven by full hash | low |
| 3 | Sync-client caches (Google Drive) — **cap before clearing** (`references/google-drive.md`) | low if the order is right |
| 4 | Dead profiles / old installs — refs scan, rescue saves and keys, rename, wait, delete | medium, mitigated by rename |
| 5 | Personal data — the user decides item by item | user's call |
| 6 | Programs and environments (Docker, Unity, extra Pythons, SDKs) | uninstall properly |
| 7 | System (admin): hibernation, component store, restore points | measure first; often nothing to gain |

Before presenting the rounds, list what **not** to touch and why (`references/catalog.md` § Do not touch). Estimate each round's gain from the
tool's own numbers, and flag estimates the tools cannot confirm.

### 4. Write the plan where it survives the session
A Markdown plan in the user's plans/reports folder (not a temp folder): problem, target, baseline table with
coverage, rounds with gain, risk and exact commands, do-not-touch, Act checklist. Save the inventory files and
scripts' outputs next to it — they are the baseline for the next Check. Summarize it in chat; for a long plan, give
the path.

### 5. Execute an authorized round
Read `references/safe-deletion.md` before the first deletion of the session and follow it exactly: fresh evidence →
manifest → reversible step first → delete from the saved list (`scripts/delete-from-list.sh`, Git Bash) → verify by
artifact → `Get-Volume` → record measured vs estimated. For a Google Drive cache, read `references/google-drive.md`
first — the order there (cap, restart, then clear) is what keeps it from refilling.

### 6. Check after every round — and stop on surprises (Jidoka)
If free space moves without explanation, stop and explain before the next step (`references/measurement.md`
§ Unexplained changes). The first suspect is the analysis itself: copies, extracted archives, inventories. Then ask
the user what is installing or updating: a game launcher can stage an update on a different drive from the game.

### 7. Act — keep it from refilling
Prefer a mechanism over a reminder:
- sync-client cap (`ContentCacheMaxKbytes` for Google Drive);
- Storage Sense on a schedule. Its run frequency is value `2048` under
  `HKCU:\Software\Microsoft\Windows\CurrentVersion\StorageSense\Parameters\StoragePolicy` (0 = only when disk space is
  low); observed 2026-10: it left a 3-month-old item in a non-system drive's bin with the 30-day rule on — check the
  dates with `scripts/recyclebin-list.ps1`;
- model caches off the system drive (`HF_HOME`, `OLLAMA_MODELS`). Do not move uv's cache away from its venvs' drive:
  across volumes it copies instead of hardlinking;
- Visual Studio's automatic background download off, if `%TEMP%` keeps filling with installer copies;
- re-run `scan.ps1` in a month and compare with the saved baseline.

## Gotchas — the traps that cost the most

| Trap | Instead |
|---|---|
| Totals from tools that skip hidden/system files | `scripts/scan.ps1` (counts them, skips only reparse points) and report coverage |
| Counting hardlinks as duplicates | `scripts/dups.ps1` real waste by physical file ID |
| Promising a cache's folder size as the gain | the tool's own number; measure before/after |
| "Nothing references this folder" from a probe that may be blind | `scripts/refs-scan.ps1`: CLEAR only counts when its control path finds hits |
| Clearing Google Drive's cache without a cap | cap → restart → confirm in log → clear only if still above cap |
| Copying a big file (DB, archive) onto the drive being cleaned | query in place; `scripts/room-check.ps1` before any big write |
| Name + size as proof that two things are equal | full hash; zip vs folder by CRC32 (`scripts/zipverify.ps1`) |
| Deleting from a fresh glob or a remembered path | delete from the saved manifest; re-verify each item first |
| Trusting memory/notes about where things are | look on disk; notes go stale (repos reappear, dumps vanish) |
| Treating an `E` log line after a change as caused by it | compare with older logs first |
| Deleting what an uninstaller left behind as junk | it is what the program created (saves, replays, configs): show it, copy what the user keeps, verify by hash, then delete |

## Output

At the end of the analysis and after each round, report in plain language (match the user's language):
a table of drives (before → now, % used, target), what was done or is recommended with measured or estimated GB,
what was proven and how ("SHA256 equal", "CRC32 equal for all <n> entries"), surprises and their explanation,
and the next decision that is the user's. Keep jargon out of the summary; details stay in the plan file.

## Scope & verification

This skill describes third-party behavior observed on Windows 10/11 in 2026-10. Before asserting any of it — and
before saying a feature does **not** exist — check the source:

| Topic | Where to confirm |
|---|---|
| uv, pip, npm, Yarn cache commands | `uv cache prune --help`, `pip cache --help`, `npm cache --help`, `yarn cache --help` |
| Google Drive cache settings | https://knowledge.workspace.google.com/admin/drive/advanced-drive-for-desktop-configuration and `drive_fs*.txt` |
| VS Code obsolete extensions | `<editor>\extensions\.obsolete` and `extensions.json` on disk |
| Steam installs | `steamapps\appmanifest_*.acf` |
| WSL / Docker disks | `wsl --help`, `docker system df`, `Get-Help Optimize-VHD` |
| WinSxS, restore points | `Dism /Online /Cleanup-Image /AnalyzeComponentStore`, `vssadmin list shadowstorage` |

## Evaluating this skill

Trigger cases (should / should not fire, including near misses) are in `assets/trigger-evals.json`, in the
skill-creator eval-set format. The probes' own test is `scripts/selftest.ps1`.
