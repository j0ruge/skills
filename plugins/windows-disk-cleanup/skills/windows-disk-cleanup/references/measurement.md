# Measurement — knowing what fills the disk before deciding anything

Read this when running the inventory (step 2 of the workflow) or when a number "doesn't add up".

## Baseline first

Record free space per volume **before** touching anything and after every round:

```powershell
Get-Volume | Where-Object DriveLetter | Sort-Object DriveLetter |
  Select-Object DriveLetter, FileSystemLabel, @{n='SizeGB';e={[math]::Round($_.Size/1GB,1)}},
    @{n='FreeGB';e={[math]::Round($_.SizeRemaining/1GB,1)}},
    @{n='UsedPct';e={[math]::Round(100*($_.Size-$_.SizeRemaining)/$_.Size,1)}}
```

Also note: admin or not (`[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole('Administrators')`),
RAM (pagefile sizing), and which physical disk backs each letter (`Get-PhysicalDisk`).

## The scanner

`scripts/scan.ps1 -Root X:\ -OutDir <dir>` — read-only, C# core, one pass per drive. Run drives in parallel:

```powershell
$jobs = 'C:\','D:\','E:\' | ForEach-Object { Start-ThreadJob -ArgumentList $_ { param($r) & '<skill>\scripts\scan.ps1' -Root $r -OutDir '<dir>' } }
$jobs | Wait-Job | Receive-Job
```

In one real run (2026-10) this covered 2.5 million files on C: in ~3.5 minutes (each summary line prints `elapsed=`). A pure PowerShell loop is several
times slower. Then `scripts/summarize.ps1 -InDir <dir>` prints coverage, biggest folders per depth, biggest files and
bytes per year; `-Under <folder>` drills into one subtree.

Pick `-OutDir` on a drive with room (`scripts/room-check.ps1`), never inside the folder being scanned.

## Traps that make numbers lie

| Trap | Symptom | What to do |
|---|---|---|
| .NET `EnumerationOptions` skips Hidden+System by default | pagefile, `$Recycle.Bin`, `ProgramData` missing; totals far below "used" | `scan.ps1` sets `AttributesToSkip = ReparsePoint` only |
| Junctions/symlinks (`Documents and Settings`, `Application Data`) | folders counted twice | skipped as reparse points |
| Hardlinks (WinSxS, uv cache ↔ venvs, some installers) | folder sums and duplicate totals inflated | `dups.ps1` groups by NTFS physical ID; WinSxS is sized by `Dism /Online /Cleanup-Image /AnalyzeComponentStore` (admin) |
| Files at the drive root (`pagefile.sys`, `hiberfil.sys`, `swapfile.sys`) | absent from folder totals | listed in `<tag>_big.csv`; check `Get-CimInstance Win32_PageFileUsage` |
| No admin | `System Volume Information`, `WindowsApps`, other users unreadable | the summary prints **coverage = seen / used**; report it instead of guessing the rest. Admin can measure VSS with `vssadmin list shadowstorage` |
| Sparse / compressed files | logical size ≠ space on disk | rare outside cloud caches; treat cache numbers as upper bounds |
| A cache's size is not what clearing frees | uv showed 7.4 GB, `prune` freed 0.42 GB (one run, 2026-10) | use the tool's own estimate where one exists (`docker system df` RECLAIMABLE); where none exists (`uv cache prune` has no dry-run as of uv 0.11, 2026-07), say "frees only orphaned entries, likely far less than the folder" and measure before/after |

## Duplicates

`scripts/dups.ps1 -InDir <dir> -MinBytes 50MB` reads the scanner's `*_dupcand.tsv` (all drives at once, so
cross-drive copies show up): size → partial SHA256 → full SHA256 → physical ID. It prints apparent vs real waste.
In one real run (2026-10): apparent 22.7 GB, real 16.05 GB — 15 groups were pure hardlinks.

Most "real" duplicate bytes are usually inside whole environments (the same torch DLLs in three Python installs).
The lever is removing the environment, not individual files — say so instead of listing DLLs.

What hashing cannot see — the same content in another container. Look by base name for these pairs; each
appeared repeatedly in practice:
- `game.nsp` + `game.nsp.7z`, `game.nsp` + `game.nsz`
- `firmware.zip` + the extracted `.tar`
- `work.zip` + the extracted `work\` folder → prove with `scripts/zipverify.ps1` (CRC32 per entry, no extraction)

## Unexplained changes (Jidoka)

If free space moves without a reason during the session, stop and explain it before continuing. Usual causes:
1. **Your own files** — copies, scratch outputs, extracted archives. Check the session temp folder first.
2. **A sync client refilling** (Google Drive, OneDrive). Measure the rate (size every 90 s), then attribute it by
   per-process I/O, which needs no admin:

```powershell
function Snap { Get-CimInstance Win32_Process | Select-Object ProcessId, Name, ReadTransferCount, WriteTransferCount }
$a = Snap; Start-Sleep 30; $b = Snap; $ia = @{}; $a | ForEach-Object { $ia[$_.ProcessId] = $_ }
$b | ForEach-Object { $o = $ia[$_.ProcessId]; if ($o) { [pscustomobject]@{ Name=$_.Name;
  ReadMB=[math]::Round(($_.ReadTransferCount-$o.ReadTransferCount)/1MB,1);
  WriteMB=[math]::Round(($_.WriteTransferCount-$o.WriteTransferCount)/1MB,1) } } } | Sort-Object WriteMB -Descending | Select-Object -First 8
```

   A client that writes hundreds of MB while no other process reads much is refilling on its own.
3. **Windows**: pagefile growth (`Win32_PageFileUsage.AllocatedBaseSize`), updates (`C:\Windows\SoftwareDistribution`), restore points.

A log line at level E right after a change is not proof that the change caused it: compare with the same line's
history in older log files before blaming the change.
