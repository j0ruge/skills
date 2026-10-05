<#
.SYNOPSIS
  Installed Steam games with size on disk and last played date, across every library. Read-only.
.DESCRIPTION
  Reads libraryfolders.vdf for the library paths and each appmanifest_*.acf for installdir and LastPlayed
  (Unix epoch; 0 = never launched). "Never played" and "not played in a year" are objective evidence for the
  user's uninstall decision - uninstall through Steam, never by deleting the folder.
  GB is the measured steamapps\common\<installdir> folder. The manifest's SizeOnDisk (ManifestGB) lags behind
  games that patch themselves: in 2026-10 MTG Arena had 11.51 GB in the manifest and 12.24 GB on disk.
  An empty GB means there is no folder to measure (manifest left behind, or no installdir in it).
  -Library replaces the discovered libraries (selftest uses it); -PassThru emits objects instead of the table.
#>
param([string[]]$Library, [switch]$PassThru)
if ($Library) { $libs = $Library } else {
    $steam = (Get-ItemProperty 'HKCU:\Software\Valve\Steam' -ErrorAction SilentlyContinue).SteamPath
    if (-not $steam) { $steam = "${env:ProgramFiles(x86)}\Steam" }
    $vdf = Join-Path $steam 'steamapps\libraryfolders.vdf'
    $libs = @($steam)
    if (Test-Path $vdf) { $libs += (Select-String -Path $vdf -Pattern '"path"\s+"([^"]+)"').Matches | ForEach-Object { $_.Groups[1].Value -replace '\\\\', '\' } }
}
function Get-AcfNumber([string]$text, [string]$key) {
    $m = [regex]::Match($text, '"' + $key + '"\s+"(\d+)"')
    if ($m.Success) { [long]$m.Groups[1].Value } else { 0L }
}
# HKCU stores "c:/program files (x86)/steam", the .vdf "C:\\Program Files (x86)\\Steam": normalize before de-duplicating
$libs = $libs | ForEach-Object { ($_ -replace '/', '\').TrimEnd('\').ToLowerInvariant() } | Sort-Object -Unique
$rows = $libs | ForEach-Object {
    $steamapps = Join-Path $_ 'steamapps'
    Get-ChildItem $steamapps -Filter 'appmanifest_*.acf' -ErrorAction SilentlyContinue | ForEach-Object {
        $t = Get-Content $_.FullName -Raw
        $lp = Get-AcfNumber $t 'LastPlayed'
        $manifest = Get-AcfNumber $t 'SizeOnDisk'
        # An empty installdir would make the path steamapps\common itself and count every game as this one
        $inst = [regex]::Match($t, '"installdir"\s+"([^"]+)"').Groups[1].Value
        $dir = Join-Path $steamapps "common\$inst"
        $bytes = if ($inst -and (Test-Path -LiteralPath $dir)) {
            [long](Get-ChildItem -LiteralPath $dir -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
        } else { $null }
        [pscustomobject]@{
            GB            = if ($null -ne $bytes) { [math]::Round($bytes / 1GB, 2) } else { $null }
            ManifestGB    = [math]::Round($manifest / 1GB, 2)
            Game          = [regex]::Match($t, '"name"\s+"([^"]+)"').Groups[1].Value
            LastPlayed    = if ($lp -gt 0) { [DateTimeOffset]::FromUnixTimeSeconds($lp).LocalDateTime.ToString('yyyy-MM-dd') } else { 'never' }
            Library       = Split-Path (Split-Path $_.FullName)
            Bytes         = $bytes
            ManifestBytes = $manifest
        }
    }
} | Sort-Object GB, ManifestGB -Descending
if ($PassThru) { $rows } else { $rows | Format-Table GB, ManifestGB, Game, LastPlayed, Library -AutoSize }
