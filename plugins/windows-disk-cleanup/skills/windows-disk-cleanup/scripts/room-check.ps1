<#
.SYNOPSIS
  Before writing anything big during a cleanup: will it eat the space you are trying to free? Read-only.
.DESCRIPTION
  Refuses (exit 1) when -Bytes exceeds -MaxFraction of the free space on the destination volume, and names
  the fixed drive with the most free space as the alternative. Exists because an analysis once copied a
  4.2 GB database into a temp folder on a drive with 7.8 GB free - the cleanup made the disk fuller.
  Prefer not copying at all: query in place (sqlite "file:...?mode=ro"), stream, or sample.
.EXAMPLE
  pwsh -File room-check.ps1 -Bytes (Get-Item $db).Length -Destination $env:TEMP
#>
param(
    [Parameter(Mandatory)][long]$Bytes,
    [Parameter(Mandatory)][string]$Destination,
    [double]$MaxFraction = 0.10
)
$letter = (Resolve-Path -LiteralPath $Destination -ErrorAction SilentlyContinue).Path
if (-not $letter) { $letter = $Destination }
$letter = $letter.Substring(0, 1)
$vol = Get-Volume -DriveLetter $letter -ErrorAction SilentlyContinue
if (-not $vol) { "NOT FOUND: no volume for '$Destination' (pass a path on a local drive letter)"; exit 2 }
$free = $vol.SizeRemaining
$best = Get-Volume | Where-Object { $_.DriveLetter -and $_.DriveType -eq 'Fixed' } | Sort-Object SizeRemaining -Descending | Select-Object -First 1
$msg = "{0:N2} GB into {1}: (free {2:N2} GB, limit {3:P0} = {4:N2} GB)" -f ($Bytes / 1GB), $letter, ($free / 1GB), $MaxFraction, ($free * $MaxFraction / 1GB)
if ($Bytes -le $free * $MaxFraction) { "OK  $msg"; exit 0 }
"REFUSE  $msg - use {0}: ({1:N2} GB free) or query in place instead of copying" -f $best.DriveLetter, ($best.SizeRemaining / 1GB)
exit 1
