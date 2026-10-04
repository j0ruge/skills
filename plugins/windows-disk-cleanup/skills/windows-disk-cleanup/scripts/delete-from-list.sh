#!/usr/bin/env bash
# Deletes ONLY the paths listed in a manifest written beforehand, and only under an allowed root.
# Usage: delete-from-list.sh <list-file> <allowed-root>      (paths in Git Bash form: /c/Users/...)
#        delete-from-list.sh --dry-run <list-file> <allowed-root>
# - One path per line; CRLF and a UTF-8 BOM are tolerated.
# - A path outside <allowed-root> is refused and counted as a failure: the loop itself is the poka-yoke
#   against a malformed list or a variable that expanded to "/".
# - After each rm, the path must be gone; "rm said ok" is not the proof, the absence is.
# Run it only for a round the user explicitly authorized, after saving the list as the manifest.
set -u
dry=0; [ "${1:-}" = "--dry-run" ] && { dry=1; shift; }
list="${1:?list file}"; root="${2:?allowed root}"
[ -r "$list" ] || { echo "REFUSE: list '$list' not found or unreadable"; exit 2; }
root="${root%/}/"
case "$root" in /|/c/|/d/|/e/|/[a-z]/) echo "REFUSE: allowed root '$root' is a whole drive - pass a folder"; exit 2;; esac
ok=0; fail=0; gone=0; refused=0
while IFS= read -r p || [ -n "$p" ]; do
  p="${p%$'\r'}"; p="${p#$'\xef\xbb\xbf'}"; [ -z "$p" ] && continue
  case "$p" in "$root"?*) ;; *) echo "REFUSED (outside $root): $p"; refused=$((refused+1)); continue;; esac
  if [ ! -e "$p" ]; then gone=$((gone+1)); continue; fi
  if [ "$dry" = 1 ]; then echo "would delete: $p"; ok=$((ok+1)); continue; fi
  if rm -rf -- "$p" 2>/dev/null && [ ! -e "$p" ]; then ok=$((ok+1)); else echo "FAILED: $p"; fail=$((fail+1)); fi
done < "$list"
if [ "$dry" = 1 ]; then
  echo "would_delete=$ok already_gone=$gone refused=$refused dry_run=1"
else
  echo "deleted=$ok failed=$fail already_gone=$gone refused=$refused dry_run=0"
fi
[ "$fail" -eq 0 ] && [ "$refused" -eq 0 ]
