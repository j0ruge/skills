#!/usr/bin/env python3
"""Google Drive for desktop (DriveFS): is its cache safe to clear, and is it capped? Read-only, Windows.

Reports, per account: pending upload operations, items with local unsaved changes (dirty-handle),
offline-pinned folders, the content cache location and size, the registry cap (ContentCacheMaxKbytes /
MinFreeDiskSpaceKBytes, HKLM override and host-wide) and the last cache-capacity lines from drive_fs.txt.

The metadata DB is opened IN PLACE with sqlite "mode=ro" - it works while Drive runs, and copying it
(several GB) can eat the very space being freed.

Usage: python drivefs-status.py [--db <metadata_sqlite_db>]
"""
import argparse, glob, os, re, sqlite3, sys

def reg_value(root, path, name):
    try:
        import winreg
        with winreg.OpenKey(root, path) as k:
            return winreg.QueryValueEx(k, name)[0]
    except OSError:
        return None

def dir_size(path):
    total = files = 0
    for r, _, names in os.walk(path):
        for n in names:
            try:
                total += os.path.getsize(os.path.join(r, n)); files += 1
            except OSError:
                pass
    return total, files

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", help="path to metadata_sqlite_db (default: every account under %%LOCALAPPDATA%%\\Google\\DriveFS)")
    a = ap.parse_args()
    base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "DriveFS")
    dbs = [a.db] if a.db else sorted(glob.glob(os.path.join(base, "*", "metadata_sqlite_db")))
    missing = [d for d in dbs if not os.path.isfile(d)]
    if missing:
        print("NOT FOUND:", ", ".join(missing)); return 2
    if not dbs:
        print("DriveFS metadata DB not found - Drive for desktop not installed for this user?"); return 1

    import winreg
    cache_root = reg_value(winreg.HKEY_CURRENT_USER, r"Software\Google\DriveFS", "ContentCachePath") or base
    print(f"cache root (HKCU ContentCachePath or default): {cache_root}")
    for label, path in (("override", r"Software\Policies\Google\DriveFS"), ("host-wide", r"Software\Google\DriveFS")):
        for name in ("ContentCacheMaxKbytes", "MinFreeDiskSpaceKBytes"):
            v = reg_value(winreg.HKEY_LOCAL_MACHINE, path, name)
            if v is not None:
                print(f"  HKLM {label} {name} = {v} KB ({v/2**20:.1f} GB)")
    print("  (no cap set = cache capacity unbounded; Drive refills a cleared cache on its own)"
          if not any(reg_value(winreg.HKEY_LOCAL_MACHINE, p, "ContentCacheMaxKbytes") for p in
                     (r"Software\Policies\Google\DriveFS", r"Software\Google\DriveFS")) else "")

    for db in dbs:
        acct = os.path.basename(os.path.dirname(db))
        print(f"\n== account {acct}")
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10)
        ops = con.execute("select count(*) from operations").fetchone()[0]
        def count(key):
            return con.execute("select count(*) from item_properties where key=?", (key,)).fetchone()[0]
        dirty = count("dirty-handle")
        print(f"pending operations: {ops}   dirty-handle: {dirty}   do-not-upload: {count('do-not-upload')}   trashed-locally: {count('trashed-locally')}")
        pinned = [r[0] for r in con.execute("""select distinct i.local_title from item_properties p join items i
                    on i.stable_id=p.item_stable_id where p.key in ('pinned','explicitly-pinned-folder') and i.is_folder=1
                    limit 15""")]
        print("offline-pinned folders (sample):", ", ".join(pinned) if pinned else "none")
        cc = os.path.join(cache_root, acct, "content_cache")
        if os.path.isdir(cc):
            b, f = dir_size(cc)
            print(f"content_cache: {cc}  {b/2**30:.2f} GB in {f} files")
        lf = os.path.join(cache_root, acct, "lost_and_found")
        if os.path.isdir(lf):
            b, f = dir_size(lf)
            print(f"lost_and_found: {f} files, {b/2**20:.1f} MB  <- look inside before clearing anything")
        verdict = "SAFE to clear (after quitting Drive from the tray)" if ops == 0 and dirty == 0 else "NOT safe: wait for sync / close open files"
        print("verdict:", verdict)

    # drive_fs.txt rotates (drive_fs_NNN.txt) on restart: read the three most recent files
    logs = sorted(glob.glob(os.path.join(base, "Logs", "drive_fs*.txt")), key=os.path.getmtime)[-3:]
    lines = []
    for log in logs:
        with open(log, encoding="utf-8", errors="replace") as fh:
            lines += [l.strip() for l in fh if re.search(r"Content cache capacity|UpdateContentCacheCapacity|capacity used", l)]
    if lines:
        print("\nlast capacity lines in drive_fs*.txt (2^62 bytes = unbounded):")
        for l in lines[-4:]:
            print("  " + l[:170])
    return 0

if __name__ == "__main__":
    sys.exit(main())
