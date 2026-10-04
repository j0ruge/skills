<#
.SYNOPSIS
  Proves by CONTENT that a .zip and its extracted folder hold the same files. Read-only.
.DESCRIPTION
  For each zip, every entry's CRC32 (stored in the zip's central directory) is compared with the CRC32 of the
  file on disk - no extraction needed. The folder defaults to the zip's base name next to it; entries are also
  tried relative to the zip's own directory (zips that already contain the top folder).
  Name + size is not proof: two files can match both and differ in content.
  Output per zip: equal / missing / different, plus the first offending entry.
.EXAMPLE
  pwsh -File zipverify.ps1 -Zips (Get-ChildItem D:\work -Filter *.zip).FullName
#>
param(
    [Parameter(Mandatory)][string[]]$Zips,
    [string]$Folder
)
$src = @'
using System;
using System.IO;
using System.IO.Compression;
using System.Linq;

public static class WdcZipVerify {
    static readonly uint[] T = Enumerable.Range(0, 256).Select(n => {
        uint c = (uint)n; for (int k = 0; k < 8; k++) c = (c & 1) != 0 ? 0xEDB88320u ^ (c >> 1) : c >> 1; return c; }).ToArray();
    static uint Crc(string path) {
        uint c = 0xFFFFFFFFu; var buf = new byte[1 << 20];
        using (var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite, 1 << 20)) {
            int n; while ((n = fs.Read(buf, 0, buf.Length)) > 0) for (int i = 0; i < n; i++) c = T[(c ^ buf[i]) & 0xFF] ^ (c >> 8);
        }
        return c ^ 0xFFFFFFFFu;
    }
    public static string Run(string zipPath, string folder) {
        string baseDir = Path.GetDirectoryName(zipPath);
        if (string.IsNullOrEmpty(folder)) folder = Path.Combine(baseDir, Path.GetFileNameWithoutExtension(zipPath));
        int ok = 0, missing = 0, bad = 0; long bytes = 0; string first = "";
        using (var z = ZipFile.OpenRead(zipPath)) {
            foreach (var e in z.Entries.Where(x => x.Name.Length > 0)) {
                var rel = e.FullName.Replace('/', '\\');
                var hit = new[] { Path.Combine(folder, rel), Path.Combine(baseDir, rel) }.FirstOrDefault(File.Exists);
                if (hit == null) { missing++; if (first == "") first = "missing: " + rel; continue; }
                if (Crc(hit) == e.Crc32) { ok++; bytes += e.Length; } else { bad++; if (first == "") first = "CRC differs: " + rel; }
            }
        }
        string verdict = (missing == 0 && bad == 0 && ok > 0) ? "IDENTICAL" : "NOT-IDENTICAL";
        return string.Format("{0} | {1} | equal={2} missing={3} different={4} equalMB={5:F1} {6}",
            verdict, Path.GetFileName(zipPath), ok, missing, bad, bytes / 1048576.0, first);
    }
}
'@
if (-not ('WdcZipVerify' -as [type])) {
    Add-Type -TypeDefinition $src -Language CSharp -ReferencedAssemblies System.IO.Compression, System.IO.Compression.ZipFile, System.Linq, System.Runtime
}
# "pwsh -File zipverify.ps1 -Zips a.zip,b.zip" arrives as ONE string: split it, unless that string is itself a real path
$Zips = $Zips | ForEach-Object {
    if (Test-Path -LiteralPath $_) { $_ } else { $_ -split ',' | ForEach-Object { $_.Trim().Trim('"', "'") } | Where-Object { $_ } }
}
# rc=0 only when every zip is IDENTICAL: a missing zip or a mismatch must not look green to a caller
$allOk = $true
foreach ($z in $Zips) {
    if (-not (Test-Path -LiteralPath $z -PathType Leaf)) { "MISSING | $z"; $allOk = $false; continue }
    $line = [WdcZipVerify]::Run((Resolve-Path -LiteralPath $z).Path, $Folder)
    $line
    if ($line -notlike 'IDENTICAL*') { $allOk = $false }
}
if (-not $allOk) { exit 1 }
