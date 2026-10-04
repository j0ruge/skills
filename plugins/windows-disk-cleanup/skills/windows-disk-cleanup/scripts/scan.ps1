<#
.SYNOPSIS
  Read-only disk inventory. Never modifies the scanned tree.
.DESCRIPTION
  Enumerates every file under -Root (hidden and system included; junctions/symlinks skipped so nothing
  is counted twice) and writes, into -OutDir, files prefixed with -Tag:
    <tag>_dirs.csv     folder totals up to -MaxDepth (folders >= -DirMin: 200 MB for a drive root, 1 MB for a folder)
    <tag>_big.csv      files >= -BigMin
    <tag>_ext.csv      bytes by extension (top 80)
    <tag>_years.csv    bytes by last-write year
    <tag>_dupcand.tsv  size<TAB>lastwrite<TAB>path for files >= -DupMin (input for dups.ps1)
    <tag>_summary.txt  file count, bytes seen, elapsed, and coverage (seen / used) when -Root is a drive root
  Run several drives in parallel with Start-ThreadJob; a C# core makes ~2.5M files take a few minutes.
.EXAMPLE
  pwsh -File scan.ps1 -Root C:\ -OutDir D:\inv
#>
param(
    [Parameter(Mandatory)][string]$Root,
    [Parameter(Mandatory)][string]$OutDir,
    [string]$Tag,
    [int]$MaxDepth = 6,
    [long]$BigMin = 100MB,
    [long]$DupMin = 5MB,
    [long]$DirMin = -1
)
$src = @'
using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections.Generic;
using System.Diagnostics;

public static class WdcScanV2 {  // V2: Run() gained dirMin; a new name avoids clashing with V1 already loaded in a session
    static string Csv(string s) { return "\"" + s.Replace("\"", "\"\"") + "\""; }

    public static string Run(string root, string outDir, string tag, int maxDepth, long bigMin, long dupMin, long dirMin) {
        var sw = Stopwatch.StartNew();
        root = root.TrimEnd('\\') + "\\";
        // Default EnumerationOptions skips Hidden|System: pagefile, $Recycle.Bin and ProgramData would vanish.
        // Skip only reparse points (junctions/symlinks), which would double-count.
        var opts = new EnumerationOptions {
            RecurseSubdirectories = true, IgnoreInaccessible = true,
            AttributesToSkip = FileAttributes.ReparsePoint, ReturnSpecialDirectories = false
        };
        var dirBytes = new Dictionary<string, long>(StringComparer.OrdinalIgnoreCase);
        var dirFiles = new Dictionary<string, long>(StringComparer.OrdinalIgnoreCase);
        var extBytes = new Dictionary<string, long>(StringComparer.OrdinalIgnoreCase);
        var extCount = new Dictionary<string, long>(StringComparer.OrdinalIgnoreCase);
        var yearBytes = new SortedDictionary<int, long>();
        long total = 0, count = 0;

        using (var big = new StreamWriter(Path.Combine(outDir, tag + "_big.csv"), false, new UTF8Encoding(true)))
        using (var dup = new StreamWriter(Path.Combine(outDir, tag + "_dupcand.tsv"), false, new UTF8Encoding(false))) {
            big.WriteLine("Path,Bytes,LastWrite");
            foreach (var f in new DirectoryInfo(root).EnumerateFiles("*", opts)) {
                long len; DateTime lw;
                try { len = f.Length; lw = f.LastWriteTime; } catch { continue; }
                var full = f.FullName;
                total += len; count++;
                var parts = full.Substring(root.Length).Split('\\');
                var acc = root.TrimEnd('\\');
                int n = Math.Min(parts.Length - 1, maxDepth);
                for (int i = 0; i < n; i++) {
                    acc = acc + "\\" + parts[i];
                    long v; dirBytes.TryGetValue(acc, out v); dirBytes[acc] = v + len;
                    dirFiles.TryGetValue(acc, out v); dirFiles[acc] = v + 1;
                }
                var ext = f.Extension.ToLowerInvariant(); if (ext.Length == 0) ext = "(none)";
                long e; extBytes.TryGetValue(ext, out e); extBytes[ext] = e + len;
                extCount.TryGetValue(ext, out e); extCount[ext] = e + 1;
                long y; yearBytes.TryGetValue(lw.Year, out y); yearBytes[lw.Year] = y + len;
                if (len >= bigMin) big.WriteLine(Csv(full) + "," + len + "," + lw.ToString("yyyy-MM-dd"));
                if (len >= dupMin) dup.WriteLine(len + "\t" + lw.ToString("yyyy-MM-dd") + "\t" + full);
            }
        }
        using (var w = new StreamWriter(Path.Combine(outDir, tag + "_dirs.csv"), false, new UTF8Encoding(true))) {
            w.WriteLine("Path,Depth,Bytes,Files");
            foreach (var kv in dirBytes.Where(k => k.Value >= dirMin).OrderByDescending(k => k.Value))
                w.WriteLine(Csv(kv.Key) + "," + kv.Key.Count(c => c == '\\') + "," + kv.Value + "," + dirFiles[kv.Key]);
        }
        using (var w = new StreamWriter(Path.Combine(outDir, tag + "_ext.csv"), false, new UTF8Encoding(true))) {
            w.WriteLine("Ext,Bytes,Count");
            foreach (var kv in extBytes.OrderByDescending(k => k.Value).Take(80))
                w.WriteLine(Csv(kv.Key) + "," + kv.Value + "," + extCount[kv.Key]);
        }
        using (var w = new StreamWriter(Path.Combine(outDir, tag + "_years.csv"), false, new UTF8Encoding(true))) {
            w.WriteLine("Year,Bytes");
            foreach (var kv in yearBytes) w.WriteLine(kv.Key + "," + kv.Value);
        }
        return string.Format("root={0} files={1} seenGB={2:F2} elapsed={3:F0}s", root, count, total / 1073741824.0, sw.Elapsed.TotalSeconds) + "|" + total;
    }
}
'@
if (-not (Test-Path -LiteralPath $Root -PathType Container)) { "NOT FOUND: root '$Root' is not a folder"; exit 2 }
if (-not ('WdcScanV2' -as [type])) { Add-Type -TypeDefinition $src -Language CSharp }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$isDriveRoot = $Root -match '^[A-Za-z]:\\?$'
if ($DirMin -lt 0) { $DirMin = if ($isDriveRoot) { 200MB } else { 1MB } }
if (-not $Tag) {
    $Tag = if ($Root -match '^[A-Za-z]:\\?$') { $Root.Substring(0,1).ToUpper() } else { (Split-Path $Root -Leaf) -replace '[^\w\-]', '_' }
}
$r = [WdcScanV2]::Run($Root, $OutDir, $Tag, $MaxDepth, $BigMin, $DupMin, $DirMin) -split '\|'
$line = $r[0]
if (-not $isDriveRoot) { $line += " coverage=n/a (folder, not a drive root)" }
if ($isDriveRoot) {
    $v = Get-Volume -DriveLetter $Root.Substring(0,1) -ErrorAction SilentlyContinue
    if ($v) {
        $used = $v.Size - $v.SizeRemaining
        # Coverage < 100% = areas you cannot read (VSS, WindowsApps, other users) or hardlink effects; report it, never guess it.
        $line += " usedGB={0:F2} coverage={1:P0}" -f ($used / 1GB), ([double]$r[1] / [math]::Max(1, $used))
    }
}
Set-Content -Path (Join-Path $OutDir "$($Tag)_summary.txt") -Value $line -Encoding utf8
$line
