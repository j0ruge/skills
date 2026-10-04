<#
.SYNOPSIS
  Installed Steam games with size on disk and last played date, across every library. Read-only.
.DESCRIPTION
  Reads libraryfolders.vdf for the library paths and each appmanifest_*.acf for SizeOnDisk and LastPlayed
  (Unix epoch; 0 = never launched). "Never played" and "not played in a year" are objective evidence for the
  user's uninstall decision - uninstall through Steam, never by deleting the folder.
#>
$steam = (Get-ItemProperty 'HKCU:\Software\Valve\Steam' -ErrorAction SilentlyContinue).SteamPath
if (-not $steam) { $steam = "${env:ProgramFiles(x86)}\Steam" }
$vdf = Join-Path $steam 'steamapps\libraryfolders.vdf'
$libs = @($steam)
if (Test-Path $vdf) { $libs += (Select-String -Path $vdf -Pattern '"path"\s+"([^"]+)"').Matches | ForEach-Object { $_.Groups[1].Value -replace '\\\\', '\' } }
function Get-AcfNumber([string]$text, [string]$key) {
    $m = [regex]::Match($text, '"' + $key + '"\s+"(\d+)"')
    if ($m.Success) { [long]$m.Groups[1].Value } else { 0L }
}
# HKCU stores "c:/program files (x86)/steam", the .vdf "C:\\Program Files (x86)\\Steam": normalize before de-duplicating
$libs = $libs | ForEach-Object { ($_ -replace '/', '\').TrimEnd('\').ToLowerInvariant() } | Sort-Object -Unique
$libs | ForEach-Object {
    Get-ChildItem (Join-Path $_ 'steamapps') -Filter 'appmanifest_*.acf' -ErrorAction SilentlyContinue | ForEach-Object {
        $t = Get-Content $_.FullName -Raw
        $lp = Get-AcfNumber $t 'LastPlayed'
        [pscustomobject]@{
            GB         = [math]::Round((Get-AcfNumber $t 'SizeOnDisk') / 1GB, 1)
            Game       = [regex]::Match($t, '"name"\s+"([^"]+)"').Groups[1].Value
            LastPlayed = if ($lp -gt 0) { [DateTimeOffset]::FromUnixTimeSeconds($lp).LocalDateTime.ToString('yyyy-MM-dd') } else { 'never' }
            Library    = Split-Path (Split-Path $_.FullName)
        }
    }
} | Sort-Object GB -Descending | Format-Table -AutoSize
