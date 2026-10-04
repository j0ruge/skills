# WSL and Docker virtual disks (.vhdx)

Read this when an `ext4.vhdx` / `docker_data.vhdx` is among the biggest files, or an old one turns up in a dead profile.

## Where they are

```powershell
Get-ChildItem "$env:LOCALAPPDATA\Packages","$env:LOCALAPPDATA\wsl","$env:LOCALAPPDATA\Docker" -Recurse -Filter *.vhdx -ErrorAction SilentlyContinue |
  Select-Object FullName, @{n='GB';e={[math]::Round($_.Length/1GB,1)}}, LastWriteTime
wsl -l -v      # distros and state (docker-desktop is Docker's backend, not a workspace)
```

## A live distro: measure inside before promising anything

The `.vhdx` grows and does not shrink on its own. Compacting frees only what is free **inside** it:

```powershell
wsl -d <distro> -- bash -lc "df -h /; du -xh --max-depth=2 ~ 2>/dev/null | sort -rh | head -20; du -xsh /var/cache/apt ~/.cache 2>/dev/null"
```

If `df` used ≈ the vhdx size, compacting gains nothing (one run, 2026-10: 32 GB used inside a 33.4 GB vhdx). Clean inside first
(`~/.cache`, `npm cache clean --force`, `yarn cache clean`, `pip cache purge`, `sudo apt clean`), then compact if the
gap is worth it. Starting a stopped distro just to measure is harmless but say that you did.

Compacting needs admin: `wsl --shutdown`, then `Optimize-VHD -Path <vhdx> -Mode Full` (Hyper-V module) or diskpart
(`select vdisk file=<vhdx>`, `attach vdisk readonly`, `compact vdisk`, `detach vdisk`).

## Docker Desktop

`docker system df` shows images, containers, volumes, build cache and RECLAIMABLE — use that number. Ask first whether
the machine's Docker holds production data. If it is test-only: `docker system prune -a --volumes`; otherwise
`docker system prune -a` without `--volumes`. Then compact `docker_data.vhdx` as above (Docker Desktop stopped).
If Docker is not used at all, uninstalling Docker Desktop removes the program and the vhdx.

## An old vhdx in a dead profile

Inspect without mounting and without admin — 7-Zip reads VHDX and ext4:

```powershell
& "$env:ProgramFiles\7-Zip\7z.exe" l <old>\ext4.vhdx | Select-String 'docker[\\/]volumes[\\/][^\\/]+[\\/]_data[\\/]' | Select-Object -First 20
```

Docker volumes live under `data\docker\volumes\<name>\_data\` inside Docker Desktop's data disk. Database markers:
`PG_VERSION` (PostgreSQL), `ibdata1` / `mysql` (MySQL/MariaDB), `WiredTiger` (MongoDB), `dump.rdb` (Redis).
One real old disk (2026-10) held a wiki (MariaDB) and a PostgreSQL volume, ~420 MB of a 19 GB file.

Ask whether that Docker was production or test **before** extracting anything. If data matters, extract just the volume
folders (`7z x <vhdx> -o<dest> "data\docker\volumes\<name>\*" -r`) and note the DB versions for a later restore;
the rest of the disk (images, layers) is rebuildable.
