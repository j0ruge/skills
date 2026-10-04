<#
.SYNOPSIS
  Sabotage tests for the probes. Run once per machine/session before trusting their output.
.DESCRIPTION
  A probe earns trust only after it goes RED on a case built to fail and GREEN on a good one. This builds
  small fixtures in -WorkDir (nothing outside it is touched, nothing is deleted) and checks:
    scan        hidden files are counted (the .NET default skips them)
    dups        identical pair found; same-size file differing only in the MIDDLE excluded (partial hash
                ties, full hash must not); a hardlink is a path, not a physical copy (real waste = 1 copy)
    zipverify   good zip IDENTICAL; zip whose extracted file has one byte changed at the same size NOT-IDENTICAL
    room-check  tiny write OK; write larger than free space REFUSE
    refs-scan   control path finds hits (otherwise the probe is blind)
    delete-list dry-run refuses a path outside the allowed root
  Exit code 0 only if every check passes. Fixtures (a few MB) stay in -WorkDir for inspection.
  -WorkDir must be new or empty: a reused one is refused (exit 2).
#>
param([string]$WorkDir = (Join-Path $env:TEMP ("wdc-selftest-" + (Get-Date -Format 'yyyyMMddHHmmss'))))
$here = $PSScriptRoot
$fail = 0
# Fixtures left by an earlier run can make a check pass that should fail (a stale hardlink once did)
if ((Test-Path -LiteralPath $WorkDir) -and (Get-ChildItem -LiteralPath $WorkDir -Force | Select-Object -First 1)) {
    "REFUSE: WorkDir '$WorkDir' is not empty - pass a new folder"; exit 2
}
function Check([string]$name, [bool]$ok, [string]$detail) {
    if ($ok) { "PASS  $name  $detail" } else { "FAIL  $name  $detail"; $script:fail++ }
}
New-Item -ItemType Directory -Force -Path "$WorkDir\tree\sub", "$WorkDir\out", "$WorkDir\zip" | Out-Null

# scan: hidden file must be counted
Set-Content "$WorkDir\tree\visible.txt" 'abc' -NoNewline
Set-Content "$WorkDir\tree\sub\hidden.txt" 'defg' -NoNewline
(Get-Item "$WorkDir\tree\sub\hidden.txt").Attributes = 'Hidden'
$s = & "$here\scan.ps1" -Root "$WorkDir\tree" -OutDir "$WorkDir\out" -Tag T -DupMin 1
Check 'scan counts hidden files' ($s -match 'files=2\b') $s

# dups: identical pair + hardlink + near-duplicate
$dd = "$WorkDir\dups"; New-Item -ItemType Directory -Force $dd | Out-Null
$a = New-Object byte[] (3MB); (New-Object Random 7).NextBytes($a)
[IO.File]::WriteAllBytes("$dd\same1.bin", $a); [IO.File]::WriteAllBytes("$dd\same2.bin", $a)
$b = [byte[]]$a.Clone(); $b[1572864] = $b[1572864] -bxor 0xFF; [IO.File]::WriteAllBytes("$dd\middle-differs.bin", $b)
New-Item -ItemType HardLink -Path "$dd\same1-hardlink.bin" -Target "$dd\same1.bin" | Out-Null
$o2 = "$WorkDir\out2"; New-Item -ItemType Directory -Force $o2 | Out-Null
Get-ChildItem $dd -File | ForEach-Object { "$($_.Length)`t2026-01-01`t$($_.FullName)" } | Set-Content "$o2\D_dupcand.tsv"
$r = & "$here\dups.ps1" -InDir $o2 -MinBytes 1MB
$rows = Import-Csv "$o2\dups.csv"
Check 'dups finds the identical group' (($rows | Select-Object -ExpandProperty Group -Unique).Count -eq 1) $r
Check 'dups excludes the middle-byte near-duplicate' (-not ($rows.Path -match 'middle-differs')) ''
Check 'dups discounts the hardlink (3 paths, 2 physical, 1 copy wasted)' (($rows[0].Paths -eq '3') -and ($rows[0].PhysicalCopies -eq '2') -and ([long]$rows[0].RealWasteBytes -eq 3MB)) "paths=$($rows[0].Paths) physical=$($rows[0].PhysicalCopies)"

# zipverify: good and sabotaged
Set-Content "$WorkDir\zip\src-a.txt" 'content A' -NoNewline
Compress-Archive -Path "$WorkDir\zip\src-a.txt" -DestinationPath "$WorkDir\zip\good.zip" -Force
Compress-Archive -Path "$WorkDir\zip\src-a.txt" -DestinationPath "$WorkDir\zip\bad.zip" -Force
Expand-Archive "$WorkDir\zip\good.zip" "$WorkDir\zip\good" -Force
Expand-Archive "$WorkDir\zip\bad.zip" "$WorkDir\zip\bad" -Force
Set-Content "$WorkDir\zip\bad\src-a.txt" 'content X' -NoNewline
$zg = & "$here\zipverify.ps1" -Zips "$WorkDir\zip\good.zip"
$zb = & "$here\zipverify.ps1" -Zips "$WorkDir\zip\bad.zip"
Check 'zipverify good zip is IDENTICAL' ($zg -like 'IDENTICAL*') $zg
Check 'zipverify sabotaged zip is NOT-IDENTICAL' ($zb -like 'NOT-IDENTICAL*') $zb

# room-check
& "$here\room-check.ps1" -Bytes 1 -Destination $WorkDir | Out-Null; $okSmall = ($LASTEXITCODE -eq 0)
& "$here\room-check.ps1" -Bytes ([long]1e15) -Destination $WorkDir | Out-Null; $okBig = ($LASTEXITCODE -eq 1)
Check 'room-check accepts a tiny write and refuses a huge one' ($okSmall -and $okBig) ''

# refs-scan: the control must see something, the fresh fixture must be CLEAR
$rs = & "$here\refs-scan.ps1" -Path "$WorkDir\tree"
Check 'refs-scan control is not blind' (-not ($rs -match 'VERDICT: BLIND')) (($rs | Select-Object -First 2) -join ' / ')
Check 'refs-scan reports a fresh folder as CLEAR' ([bool]($rs -match 'VERDICT: CLEAR')) ''

# delete-from-list dry-run refuses outside the root.
# Use Git Bash explicitly: a bare "bash" from PowerShell is often C:\Windows\System32\bash.exe (WSL), where /c/... does not exist.
$bash = @("$env:ProgramFiles\Git\bin\bash.exe", "${env:ProgramFiles(x86)}\Git\bin\bash.exe", "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe") |
    Where-Object { Test-Path $_ } | Select-Object -First 1
if ($bash) {
    function ToGitBash([string]$p) { ($p -replace '^([A-Za-z]):', { '/' + $_.Groups[1].Value.ToLower() }) -replace '\\', '/' }
    Copy-Item "$here\delete-from-list.sh" "$WorkDir\delete-from-list.sh"   # a UNC script path (\\wsl...) has no Git Bash form
    $root = ToGitBash $WorkDir
    @("$root/tree/visible.txt", '/c/Windows/System32') | Set-Content -Encoding utf8NoBOM "$WorkDir\list.txt"
    $out = & $bash (ToGitBash "$WorkDir\delete-from-list.sh") --dry-run (ToGitBash "$WorkDir\list.txt") "$root/tree" 2>&1
    Check 'delete-from-list refuses a path outside the root (dry-run)' ([bool]($out -match 'would_delete=1 .*refused=1') -and (Test-Path "$WorkDir\tree\visible.txt")) (($out | Select-Object -Last 1))
} else { "SKIP  delete-from-list (Git Bash not found)" }

"fixtures: $WorkDir"
if ($fail) { "SELFTEST: $fail check(s) FAILED - do not trust the failing probe"; exit 1 }
"SELFTEST: all checks passed (fixtures are yours to remove: $WorkDir)"
exit 0   # explicit: otherwise the exit code of the last native command (the dry-run that refuses on purpose) leaks out
