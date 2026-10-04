# Google Drive for desktop (DriveFS) — reclaiming its cache without losing files or watching it refill

Read this when a `DriveFS\<account-id>\content_cache` folder is among the biggest items.

## Why it grows

Drive streams files on demand and keeps what it downloaded in `content_cache`. Out of the box the capacity is
effectively unbounded: the log prints `Initialize Content cache capacity (bytes): 4611686018427386880` (2^62),
and an internal heuristic can later set it to a large share of the disk (one run, 2026-10: 50,424 MB on a nearly full drive — the value appears in the log as `UpdateContentCacheCapacity`).
Clearing the cache without a cap is wasted effort: in one run (2026-10), right after a restart, Drive refilled it on its own at
~550–680 MB/min (0.5 → 8.7 GB in ~12 minutes), with no other process reading files.

## Where things are

| What | Where |
|---|---|
| Metadata DB, logs | `%LOCALAPPDATA%\Google\DriveFS\<account-id>\metadata_sqlite_db`, `%LOCALAPPDATA%\Google\DriveFS\Logs\drive_fs*.txt` (rotates on restart) |
| Cache root | `HKCU\Software\Google\DriveFS\ContentCachePath` (default: the DriveFS folder above); cache in `<root>\<account-id>\content_cache` |
| Cap (admin) | `ContentCacheMaxKbytes` (QWORD, KB) in `HKLM\Software\Policies\Google\DriveFS` (override) or `HKLM\Software\Google\DriveFS` (host-wide) |
| Floor (admin) | `MinFreeDiskSpaceKBytes` (QWORD, KB): Drive stops writing cache below this free space |

Per Google's admin documentation (fetched 2026-10): the cap is limited to 20% of available disk space, does not
apply to offline-pinned files or files being uploaded, and exists only as an admin setting.
Source: https://knowledge.workspace.google.com/admin/drive/advanced-drive-for-desktop-configuration
(old URL https://support.google.com/a/answer/7644837 redirects there).

## The order that works

1. **Status, read-only, in place**: `python scripts/drivefs-status.py`. It opens the DB with sqlite `mode=ro`
   while Drive runs; do not copy the DB — it grows with the number of items in the account (4.2 GB in one run, 2026-10) and copying it to the drive
   being cleaned made that drive fuller. Requirement to proceed: the verdict says SAFE (exit code 0), meaning no
   pending operations and no dirty item other than Office lock files (`~$name`, under 1 KB). Those only record who
   opened a document, and a stale one stays dirty forever: one run (2026-10) had a lock from 2025-05 that waiting
   would never clear. The script names every dirty and never-uploaded item. Copy out anything it marks as existing
   only in the cache, and look inside `lost_and_found` if it reports files there.
2. **Cap first** (admin terminal). Pick a value at or below 20% of the drive's free space (the documented ceiling); 10 GB = 10485760 KB:
   `reg add "HKLM\Software\Google\DriveFS" /v ContentCacheMaxKbytes /t REG_QWORD /d 10485760 /f`
3. **Restart Drive** — the user quits from the tray (gear › Quit) and reopens it. Drive reads the key only at
   start: a key written after the process started is ignored until the next restart.
4. **Confirm the cap by the log, not by the Initialize line**: about 2 minutes after start, `drive_fs*.txt` shows
   `UpdateContentCacheCapacity Changing content cache capacity to 10240 MBytes` (the Initialize line still says 2^62).
   Grep the most recent few log files: a `tail -f` monitor can miss the line when the log rotates.
5. **If the cache is still above the cap** (Drive stops growing but does not evict the excess — one run (2026-10)
   stayed at 25 GB for 40+ minutes with "capacity used: 451%"), clear it:
   1. user quits Drive from the tray (killing the process risks the DB); confirm a clean close: 0 `GoogleDriveFS`
      processes, `G:` unmounted, no `metadata_sqlite_db-wal`/`-shm` left;
   2. **rename** `content_cache` → `content_cache.OLD-<date>` (reversible);
   3. user reopens Drive; check: the log says `Created new content cache dir`, the Drive letter lists folders,
      offline-pinned files open (read a few), and one non-pinned file streams and lands in the new cache;
   4. only then delete the `.OLD` folder.
6. **Re-measure for ~10 minutes.** Growth should stop below the cap. If it does not, stop and attribute writes by
   process (`measurement.md`).

## Things that look alarming but are not

- `E` level lines such as `Syncing status response not found for account: no_user` right after start appear on
  every start (checked against months of logs); compare with older logs before blaming a change.
- Tray status "Up to date — checking for newer updates…" after a restart is normal.
- `do-not-upload` items are usually Office lock files (`~$name.docx`).
- `trashed-locally` items were deleted by the user; they live in Drive's online trash, not only in the cache.

## Old DriveFS caches

A second `DriveFS` folder inside an old profile or another drive (`<id>\content_cache`, `metadata_sqlite_db`) belongs
to a previous install. Check its `lost_and_found` (files that never uploaded); if empty or trivial, it is safe to
delete as part of that profile.
