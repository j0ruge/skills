<#
.SYNOPSIS
  Extension versions VS Code (or a fork) already marked obsolete but never removed. Read-only unless -WriteList.
.DESCRIPTION
  VS Code removes folders listed in extensions\.obsolete only when it STARTS after a full close; people who
  never close it accumulate old versions. A folder is safe to delete when it is in .obsolete AND is not
  referenced by extensions.json (the registry of installed extensions) - and only with 0 editor processes.
  -WriteList writes those paths (Git Bash form) for delete-from-list.sh. After deleting, run with -Verify:
  every extensions.json entry must still have its folder.
.EXAMPLE
  pwsh -File vscode-obsolete.ps1                     # VS Code
  pwsh -File vscode-obsolete.ps1 -Editor .cursor     # Cursor; .windsurf for Windsurf
#>
param(
    [string]$Editor = '.vscode',
    [string]$WriteList,
    [switch]$Verify
)
$ext = Join-Path $env:USERPROFILE "$Editor\extensions"
if (-not (Test-Path (Join-Path $ext 'extensions.json'))) { "NOT FOUND: $ext\extensions.json - wrong -Editor, or this editor is not installed for this user"; exit 2 }
$proc = @{ '.vscode' = 'Code'; '.cursor' = 'Cursor'; '.windsurf' = 'Windsurf' }[$Editor]
$json = Get-Content (Join-Path $ext 'extensions.json') -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json
$registered = @($json | ForEach-Object { Split-Path $_.location.path -Leaf })
if ($Verify) {
    $missing = @($json | Where-Object { -not (Test-Path -LiteralPath ((($_.location.path) -replace '^/([a-zA-Z]):', '$1:') -replace '/', '\')) })
    "registered: $(@($json).Count)   with missing folder: $($missing.Count)"
    $missing | ForEach-Object { "  MISSING: $($_.identifier.id)" }
    return
}
$obs = Get-Content (Join-Path $ext '.obsolete') -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json
$marked = @($obs.PSObject.Properties | Where-Object Value -eq $true | ForEach-Object Name)
$present = $marked | Where-Object { (Test-Path (Join-Path $ext $_)) -and ($_ -notin $registered) }
$bytes = ($present | ForEach-Object { (Get-ChildItem (Join-Path $ext $_) -Recurse -File -Force | Measure-Object Length -Sum).Sum } | Measure-Object -Sum).Sum
$running = if ($proc) { @(Get-Process $proc -ErrorAction SilentlyContinue).Count } else { 0 }
"{0}: {1} obsolete folders still on disk, {2:N2} GB  |  {3} processes running: {4}" -f $Editor, @($present).Count, ($bytes / 1GB), $proc, $running
$present | ForEach-Object { "  $_" }
if ($WriteList) {
    if ($running -gt 0) { "Not writing the list: close every $proc window first (0 processes required)."; exit 1 }
    $present | ForEach-Object { ((Join-Path $ext $_) -replace '^([A-Za-z]):', { '/' + $_.Groups[1].Value.ToLower() }) -replace '\\', '/' } |
        Set-Content -Encoding utf8NoBOM $WriteList
    "list written: $WriteList"
}
