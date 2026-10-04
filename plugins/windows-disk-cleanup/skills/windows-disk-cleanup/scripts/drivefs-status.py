#!/usr/bin/env python3
"""Google Drive for desktop (DriveFS): is its cache safe to clear, and is it capped? Read-only, Windows.

Reports, per account: pending upload operations, items with local unsaved changes (dirty-handle) and
never-uploaded items (do-not-upload) BY NAME, offline-pinned folders, the content cache location and size,
the registry cap (ContentCacheMaxKbytes / MinFreeDiskSpaceKBytes, HKLM override and host-wide) and the last
cache-capacity lines from drive_fs.txt.

The metadata DB is opened IN PLACE with sqlite "mode=ro" - it works while Drive runs, and copying it
(several GB) can eat the very space being freed.

A dirty item that is an Office lock file (~$name, under 1 KB) does not block: it only records who opened a
document, and a stale one stays dirty forever (one run, 2026-10: a lock from 2025-05). Any other dirty item does.

Usage: python drivefs-status.py [--db <metadata_sqlite_db>]
Exit code: 0 = safe to clear for every account, 1 = not safe (or no DB), 2 = --db not found.
"""
import argparse, datetime, glob, os, re, sqlite3, sys

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

def is_office_lock(title, size):
    return bool(title) and title.startswith("~$") and isinstance(size, int) and size < 1024

def parent_path(con, sid):
    parts, cur = [], sid
    for _ in range(40):
        p = con.execute("select parent_stable_id from stable_parents where item_stable_id=?", (cur,)).fetchone()
        if not p:
            break
        cur = p[0]
        t = con.execute("select local_title from items where stable_id=?", (cur,)).fetchone()
        parts.append(t[0] if t and t[0] else "?")
    return "/".join(reversed(parts))

def items_with(con, key):
    """(title, size, date, folder) of every item carrying the property `key`."""
    out = []
    for (sid,) in con.execute("select item_stable_id from item_properties where key=?", (key,)).fetchall():
        props = dict(con.execute("select key, value from item_properties where item_stable_id=?", (sid,)).fetchall())
        row = con.execute("select local_title, file_size from items where stable_id=?", (sid,)).fetchone()
        title = (row[0] if row and row[0] else None) or props.get("local-title") or f"<item {sid}>"
        size = props.get("local-content-size", row[1] if row else None)
        ms = props.get("local-content-modified-date") or props.get("modified-date")
        when = datetime.datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d") if isinstance(ms, int) else "?"
        out.append((title, size, when, parent_path(con, sid)))
    return out

def main():
    # item names can be in any script and some stored values are not valid UTF-8: never crash on them
    sys.stdout.reconfigure(errors="replace")
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

    unsafe = 0
    for db in dbs:
        acct = os.path.basename(os.path.dirname(db))
        print(f"\n== account {acct}")
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10)
        con.text_factory = lambda b: b.decode("utf-8", "replace")
        ops = con.execute("select count(*) from operations").fetchone()[0]
        def count(key):
            return con.execute("select count(*) from item_properties where key=?", (key,)).fetchone()[0]
        dirty = items_with(con, "dirty-handle")
        locks = [d for d in dirty if is_office_lock(d[0], d[1])]
        real = [d for d in dirty if d not in locks]
        dnu = items_with(con, "do-not-upload")
        print(f"pending operations: {ops}   dirty-handle: {len(dirty)} (Office lock files: {len(locks)})   "
              f"do-not-upload: {len(dnu)}   trashed-locally: {count('trashed-locally')}")
        for t, s, w, p in dirty:
            tag = "Office lock file - holds no data, does not block" if is_office_lock(t, s) else "BLOCKS: unsaved local change"
            print(f"  dirty: {t} | {s} B | {w} | {p}  [{tag}]")
        others = [d for d in dnu if not is_office_lock(d[0], d[1])]
        print(f"  do-not-upload: {len(dnu) - len(others)} Office lock files" + (", others:" if others else ""))
        for t, s, w, p in others[:10]:
            print(f"    {t} | {s} B | {w} | {p}  <- exists only in this cache: copy it out before clearing")
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
        if ops == 0 and not real:
            note = " - close Office documents opened from Drive first" if locks else ""
            print(f"verdict: SAFE to clear (after quitting Drive from the tray){note}")
        else:
            unsafe += 1
            why = [f"{ops} pending operation(s)"] if ops else []
            why += [f"{len(real)} item(s) with unsaved local changes"] if real else []
            print("verdict: NOT safe: " + ", ".join(why) + " - wait for sync / close the files listed above")

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
    return 1 if unsafe else 0

if __name__ == "__main__":
    sys.exit(main())
