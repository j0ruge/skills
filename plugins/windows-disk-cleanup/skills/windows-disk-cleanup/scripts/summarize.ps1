<#
.SYNOPSIS
  Human-readable digest of scan.ps1 output: coverage, biggest folders by depth, biggest files, bytes by year.
.EXAMPLE
  pwsh -File summarize.ps1 -InDir D:\inv              # every drive scanned into D:\inv
  pwsh -File summarize.ps1 -InDir D:\inv -Under $env:LOCALAPPDATA -Depth 5
#>
param(
    [Parameter(Mandatory)][string]$InDir,
    [string]$Under,
    [int]$Depth = 0,
    [int]$Top = 20
)
function Gb([long]$b) { [math]::Round($b / 1GB, 2) }
if (-not (Get-ChildItem $InDir -Filter '*_dirs.csv' -ErrorAction SilentlyContinue)) { "NOT FOUND: no scan.ps1 output (*_dirs.csv) in $InDir"; exit 2 }
Get-ChildItem $InDir -Filter '*_summary.txt' | ForEach-Object { Get-Content $_.FullName }
$dirs = Get-ChildItem $InDir -Filter '*_dirs.csv' | ForEach-Object { Import-Csv $_.FullName } |
    ForEach-Object { $_.Bytes = [long]$_.Bytes; $_.Depth = [int]$_.Depth; $_ }
if ($Under) {
    $d = if ($Depth) { $Depth } else { ($Under.TrimEnd('\').ToCharArray() | Where-Object { $_ -eq '\' }).Count + 1 }
    "`n--- under $Under (depth $d) ---"
    $dirs | Where-Object { $_.Depth -eq $d -and $_.Path -like "$($Under.TrimEnd('\'))\*" } | Sort-Object Bytes -Descending |
        Select-Object -First $Top @{n = 'GB'; e = { Gb $_.Bytes } }, Files, Path | Format-Table -AutoSize | Out-String -Width 250
    return
}
foreach ($lvl in 1, 2, 3) {
    "`n--- biggest folders, depth $lvl ---"
    $dirs | Where-Object Depth -eq $lvl | Sort-Object Bytes -Descending |
        Select-Object -First $Top @{n = 'GB'; e = { Gb $_.Bytes } }, Files, Path | Format-Table -AutoSize | Out-String -Width 250
}
"`n--- biggest files ---"
Get-ChildItem $InDir -Filter '*_big.csv' | ForEach-Object { Import-Csv $_.FullName } | ForEach-Object { $_.Bytes = [long]$_.Bytes; $_ } |
    Sort-Object Bytes -Descending | Select-Object -First ($Top * 2) @{n = 'GB'; e = { Gb $_.Bytes } }, LastWrite, Path |
    Format-Table -AutoSize | Out-String -Width 250
"`n--- GB by last-write year (old bytes are candidates, not verdicts) ---"
Get-ChildItem $InDir -Filter '*_years.csv' | ForEach-Object {
    $t = $_.BaseName -replace '_years$', ''
    "$t : " + ((Import-Csv $_.FullName | Where-Object { [long]$_.Bytes -gt 1GB } | ForEach-Object { "$($_.Year)=$(Gb $_.Bytes)" }) -join '  ')
}
