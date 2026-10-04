<#
.SYNOPSIS
  Lists what is really in each drive's Recycle Bin (original path, size, deletion date). Read-only.
.DESCRIPTION
  Parses the $I* metadata files of the current user's bin on every fixed drive (format v2: size at offset 8,
  deletion FILETIME at 16, name length at 24, UTF-16 name at 28). Storage Sense only cleans the system
  drive's bin, so bins on other drives keep items indefinitely. Show the user the names before emptying -
  "7 GB in 3 files" is not something to empty blind.
#>
$sid = ([Security.Principal.WindowsIdentity]::GetCurrent()).User.Value
Get-Volume | Where-Object { $_.DriveLetter -and $_.DriveType -eq 'Fixed' } | Sort-Object DriveLetter | ForEach-Object {
    $bin = "$($_.DriveLetter):\`$Recycle.Bin\$sid"
    if (-not (Test-Path -LiteralPath $bin)) { return }
    Get-ChildItem -LiteralPath $bin -Force -Filter '$I*' -ErrorAction SilentlyContinue | ForEach-Object {
        $b = [IO.File]::ReadAllBytes($_.FullName)
        $ver = [BitConverter]::ToInt64($b, 0)
        $size = [BitConverter]::ToInt64($b, 8)
        $when = [DateTime]::FromFileTime([BitConverter]::ToInt64($b, 16))
        $name = if ($ver -ge 2) { [Text.Encoding]::Unicode.GetString($b, 28, ([BitConverter]::ToInt32($b, 24) - 1) * 2) }
                else { [Text.Encoding]::Unicode.GetString($b, 24, 520).TrimEnd([char]0) }
        [pscustomobject]@{ Drive = $_.FullName.Substring(0, 1); GB = [math]::Round($size / 1GB, 2); Deleted = $when.ToString('yyyy-MM-dd'); Original = $name }
    }
} | Sort-Object GB -Descending | Format-Table -AutoSize | Out-String -Width 220
