<#
.SYNOPSIS
  "Does anything on this system still point at <Path>?" - with a built-in positive control. Read-only.
.DESCRIPTION
  Searches running processes, user/machine environment variables (PATH included), registry Uninstall / Run /
  App Paths keys, services, scheduled tasks and .lnk shortcuts (Start Menu, Desktop, Quick Launch) for -Path.
  Then runs the SAME probe against -ControlPath, a folder you know is in use. A probe that also finds 0 there
  is blind, and its 0 for -Path proves nothing: the result is then BLIND, not CLEAR.
.EXAMPLE
  pwsh -File refs-scan.ps1 -Path 'E:\OldUser'
#>
param(
    [Parameter(Mandatory)][string]$Path,
    [string]$ControlPath = (Join-Path $env:LOCALAPPDATA 'Programs')
)
function Find-Refs([string]$target) {
    $pat = [regex]::Escape($target.TrimEnd('\'))
    $hits = [System.Collections.Generic.List[string]]::new()
    Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Path -match $pat } | ForEach-Object { $hits.Add("process: $($_.ProcessName) $($_.Path)") }
    foreach ($scope in 'User', 'Machine') {
        [Environment]::GetEnvironmentVariables($scope).GetEnumerator() | Where-Object { "$($_.Value)" -match $pat } |
            ForEach-Object { $hits.Add("env[$scope]: $($_.Key)") }
    }
    $keys = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall', 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall',
            'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall', 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run',
            'HKLM:\Software\Microsoft\Windows\CurrentVersion\Run', 'HKCU:\Software\Microsoft\Windows\CurrentVersion\App Paths',
            'HKLM:\Software\Microsoft\Windows\CurrentVersion\App Paths'
    foreach ($k in $keys) {
        $v = Get-ItemProperty $k -ErrorAction SilentlyContinue
        if ($v) { $v.PSObject.Properties | Where-Object { "$($_.Value)" -match $pat } | ForEach-Object { $hits.Add("reg: $k :: $($_.Name)") } }
        Get-ChildItem $k -ErrorAction SilentlyContinue | ForEach-Object {
            $p = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
            if ($p -and ($p.PSObject.Properties | Where-Object { "$($_.Value)" -match $pat })) { $hits.Add("reg: $($_.Name)") }
        }
    }
    Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | Where-Object { $_.PathName -match $pat } | ForEach-Object { $hits.Add("service: $($_.Name)") }
    Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { ($_.Actions | ForEach-Object { "$($_.Execute) $($_.Arguments) $($_.WorkingDirectory)" }) -match $pat } |
        ForEach-Object { $hits.Add("task: $($_.TaskPath)$($_.TaskName)") }
    $sh = New-Object -ComObject WScript.Shell
    $dirs = "$env:APPDATA\Microsoft\Windows\Start Menu", "$env:ProgramData\Microsoft\Windows\Start Menu", "$env:USERPROFILE\Desktop",
            "$env:PUBLIC\Desktop", "$env:APPDATA\Microsoft\Internet Explorer\Quick Launch"
    Get-ChildItem $dirs -Recurse -Filter *.lnk -ErrorAction SilentlyContinue | ForEach-Object {
        $t = $sh.CreateShortcut($_.FullName)
        if ("$($t.TargetPath) $($t.WorkingDirectory) $($t.Arguments)" -match $pat) { $hits.Add("shortcut: $($_.FullName)") }
    }
    , $hits
}
$target = Find-Refs $Path
$control = Find-Refs $ControlPath
"control ($ControlPath): $($control.Count) hits"
"target  ($Path): $($target.Count) hits"
$target | Select-Object -First 30 | ForEach-Object { "  $_" }
if ($control.Count -eq 0) { "VERDICT: BLIND - the probe found nothing even for a path in use; a 0 for the target proves nothing." }
elseif ($target.Count -eq 0) { "VERDICT: CLEAR - nothing on this system references the target (probe validated by the control)." }
else { "VERDICT: REFERENCED - resolve or accept each hit before renaming or deleting." }
