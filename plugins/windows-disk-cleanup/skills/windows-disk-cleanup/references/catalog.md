# Catalog — where Windows disk space usually goes, and how to reclaim each kind safely

Read this when classifying the inventory into rounds (step 3). Each entry: how to recognize it, the evidence that
makes it safe, the reclaim method, and the trap. Paths use `%LOCALAPPDATA%` etc.; confirm every path on the
real disk before citing it — layouts vary by version and by user.

## Contents
1. Regenerable caches (round 1)
2. Unused models, installers, proven duplicates (round 2)
3. Sync-client caches → `google-drive.md`
4. Dead profiles and old installs (round 4)
5. Personal data — the user's decision (round 5)
6. Programs and environments (round 6)
7. System files (round 7, admin)
8. Do not touch

## 1. Regenerable caches

Close the apps that own them first. Prefer each tool's own clean command: it knows what is in use.

| Cache | Default location | Reclaim | Trap |
|---|---|---|---|
| pip | `%LOCALAPPDATA%\pip\cache` (`pip cache dir`) | `pip cache purge` | several Pythons share one cache — fine |
| npm | `%LOCALAPPDATA%\npm-cache` (`npm config get cache`) | `npm cache clean --force` | `_npx` stays (packages `npx` runs, often MCP servers) — leave it |
| Yarn v1 | `%LOCALAPPDATA%\Yarn\Cache` | `yarn cache clean` | — |
| uv | `%LOCALAPPDATA%\uv\cache` (`uv cache dir`) | `uv cache prune` | venvs hardlink into it, so the folder size overstates the gain (7.4 GB folder → 0.42 GB freed in one run, 2026-10). No dry-run flag exists (checked with `uv cache prune --help`, uv 0.11.29): measure before/after. `uv cache clean` empties it but forces re-downloads |
| NuGet | `%USERPROFILE%\.nuget\packages` | `dotnet nuget locals all --clear` | next restore re-downloads everything |
| `%TEMP%` | `%LOCALAPPDATA%\Temp` | entries older than ~2 days via a saved list (`safe-deletion.md`); or Settings › System › Storage › Temporary files | skip the agent's own session folder; installer-created folders need admin |
| Visual Studio Installer leftovers | `%TEMP%\xxxxxxxx.xxx` folders (~142 MB each, observed 2026-10) + an update-payload folder | delete when no installer runs | the background download runs every few hours and leaves one copy per run (logs `%TEMP%\dd_BackgroundDownload_*`). Identify by `resources\app\ServiceHub\Services\Microsoft.VisualStudio.Setup.Service` inside. Root cause: VS › Tools › Options › Environment › Product Updates › automatic download |
| VS Code / Cursor / Windsurf old extension versions | `%USERPROFILE%\.vscode\extensions` (`.cursor`, `.windsurf`) | `scripts/vscode-obsolete.ps1`; restarting the editor after a full close also works | removed only at startup after a full close; never delete with the editor running; verify `extensions.json` afterwards |
| HuggingFace aborted downloads | `%USERPROFILE%\.cache\huggingface\hub\models--*\blobs\*.incomplete` | delete the `.incomplete` file | if the newer model is incomplete, the older version is probably the working one — keep it |
| Browser caches | profile `Cache`, `Code Cache`, `Service Worker` | the browser's own "clear browsing data" | never delete a live profile folder |
| Chrome on-device AI model | `...\Chrome\User Data\OptGuideOnDeviceModel` (~4 GB observed 2026-10; measure the folder) | Chrome › Settings › System › on-device AI toggle, if present in that version | deleting the folder alone: Chrome downloads it again |

## 2. Unused models, installers, proven duplicates

| Item | Evidence that makes it safe | Reclaim |
|---|---|---|
| LM Studio / GGUF models (`%USERPROFILE%\.cache\lm-studio\models`) | the app is not installed; the user uses another runtime; dates | delete the folder; remove its `bin` from PATH afterwards |
| HuggingFace models (`hub\models--org--name`) | last write date; no installed package uses it (search site-packages of the venvs) | delete the model folder (re-downloadable) |
| HF duplicate storage | on Windows without symlinks, `blobs\` and `snapshots\` both hold full copies | Developer Mode makes new downloads use symlinks; old models stay duplicated until re-downloaded |
| Ollama models (`%USERPROFILE%\.ollama\models`) | `ollama list`; the user's intent | `ollama rm <model>` — never delete blobs by hand |
| Duplicate files | **full SHA256** equal (`dups.ps1`), re-hash right before deleting | delete the extra copies, keep one; re-check the kept copy exists |
| Same content, two containers (`.nsp` + `.nsp.7z`, `.zip` + extracted folder) | `zipverify.ps1` IDENTICAL for zips; base-name match + the user's choice for other formats | keep one form |
| Old installers / firmware in Downloads | dates, the device/app no longer in use | user's call — list them with sizes |

## 3. Sync-client caches

Google Drive for desktop: read `google-drive.md` — the order (cap, restart, then clear) matters, or the cache
refills at hundreds of MB per minute. OneDrive: "Free up space" on the folder (files become online-only).

## 4. Dead profiles and old installs

A folder that looks like a user profile (`AppData`, `Desktop`, `Downloads`...) outside `C:\Users`, or a
`Windows.old`.

- **Recognize**: not in `HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList`; the whole tree shares one
  `LastWriteTime` (the date it was copied).
- **Prove nothing uses it**: `scripts/refs-scan.ps1 -Path <folder>` must say CLEAR (its control must not be BLIND).
- **Rescue what cannot come back** (copy with robocopy, verify by SHA256 file by file), usually small:
  - emulator saves and keys: `Roaming\Ryujinx\bis\*\save`, `Roaming\Ryujinx\sdcard\Nintendo\save`, `Roaming\Ryujinx\system\*.keys`,
    `...\yuzu\...\nand\*\save`, `...\yuzu\...\keys`
  - Unity games: `LocalLow\<studio>`; Unreal games: `Local\<game>\Saved\SaveGames`; `Roaming\.minecraft\saves`
  - anything the user names
- **Do not rescue**: Chromium-based app data (WhatsApp Desktop, Discord, Notion, Teams): it is `Cache`, `Service Worker`
  and encrypted `IndexedDB`, with no usable files in it; launcher logs (`Epic...\Saved`).
- **Old Docker/WSL disks inside it**: see `wsl-docker.md` — ask whether the machine's Docker held production data.
- **Reclaim**: rename (`AppData` → `AppData.DELETE-<date+7d>`), wait about a week, then delete. Large: often the biggest single win.

## 5. Personal data — the user's decision

Media, games, courses, ROM collections, project archives. Give evidence, never a verdict:
- Steam: `scripts/steam-games.ps1` (size + last played; "never" is common). Uninstall through Steam.
- Movies/series: size, date, whether a duplicate in another quality exists.
- Work folders (`*_aplicado`, project exports): only state facts (e.g. "zip IDENTICAL to the folder next to it").

## 6. Programs and environments

| Item | Check before |
|---|---|
| Docker Desktop + `docker_data.vhdx` | production or test? `docker system df`; uninstall if unused, else `docker system prune -a` (add `--volumes` only for test data) |
| Unity editors (`Program Files\Unity\Hub\Editor\<ver>`) | Unity Hub › Installs; projects registered |
| Several Python installs with heavy packages | which one is default (`py -0p`, `where python`); which projects use the others |
| SDKs (Windows SDK, Android SDK/NDK, .NET packs) | the user's current dev targets; remove through their installers |
| TeX Live, game launchers, trial software | usage; uninstall properly |
| Repos duplicated between Windows and WSL | which copy is live (`git log -1`, dates); never assume from memory |

## 7. System files (admin)

| Item | Measure | Reclaim | Do not |
|---|---|---|---|
| `hiberfil.sys` | size at root | `powercfg /h off` (disables hibernate + fast startup) or `/h /type reduced` | — |
| WinSxS | `Dism /Online /Cleanup-Image /AnalyzeComponentStore` | only if it says cleanup recommended: `/StartComponentCleanup` | delete anything by hand |
| Restore points / shadow copies | `vssadmin list shadowstorage` | System Protection settings | — |
| Windows Update leftovers, old dumps | Disk Cleanup › "Clean up system files" | same | — |
| Recycle Bin on non-system drives | `scripts/recyclebin-list.ps1` (original names) | `Clear-RecycleBin -DriveLetter X -Force` after showing the list | empty blind |

## 8. Do not touch

- `pagefile.sys` while a crash/BSOD investigation is open (full/automatic dumps need it). Check the machine's notes first.
- `C:\Windows\Installer`, `WinSxS`, `System32\DriverStore` by hand.
- A WSL distro's `ext4.vhdx` that is in use — measure inside instead (`wsl-docker.md`).
- App VMs (e.g. Claude Desktop `vm_bundles`), live browser profiles, password managers' data.
- Anything only "probably" duplicated.
