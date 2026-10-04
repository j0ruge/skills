<#
.SYNOPSIS
  Duplicates proven by CONTENT, with hardlinks discounted. Read-only.
.DESCRIPTION
  Reads every *_dupcand.tsv that scan.ps1 wrote into -InDir, then: same size -> partial SHA256 (first+last MB)
  -> full SHA256. Each confirmed group also gets the NTFS physical file ID (volume serial + file index):
  paths sharing an ID are hardlinks of ONE file and waste nothing. WinSxS and uv (cache <-> venv) are full of
  them; counting paths instead of physical files inflated a real run from 16 GB to 22.7 GB.
  Writes <InDir>\dups.csv (one row per path) and prints apparent vs real waste.
  "Same format, different bytes" (game.nsp vs game.nsp.7z, zip vs extracted folder) is NOT found here:
  search by base name, and prove zip-vs-folder with zipverify.ps1.
.EXAMPLE
  pwsh -File dups.ps1 -InDir D:\inv -MinBytes 50MB
#>
param(
    [Parameter(Mandatory)][string]$InDir,
    [long]$MinBytes = 50MB,
    [string]$OutCsv
)
$src = @'
using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Security.Cryptography;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

public static class WdcDups {
    // FILETIMEs as uint pairs: declaring them as long adds padding and returns garbage serial/link counts.
    [StructLayout(LayoutKind.Sequential)]
    struct BY_HANDLE_FILE_INFORMATION { public uint Attr, CLo, CHi, ALo, AHi, WLo, WHi, VolSerial, SizeHigh, SizeLow, Links, IdxHigh, IdxLow; }
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool GetFileInformationByHandle(SafeFileHandle h, out BY_HANDLE_FILE_INFORMATION info);

    public static string PhysId(string path, out uint links) {
        links = 0;
        try {
            using (var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete)) {
                BY_HANDLE_FILE_INFORMATION i;
                if (!GetFileInformationByHandle(fs.SafeFileHandle, out i)) return "ERR";
                links = i.Links;
                return i.VolSerial.ToString("X8") + ":" + ((((ulong)i.IdxHigh) << 32) | i.IdxLow).ToString("X16");
            }
        } catch { return "ERR"; }
    }
    static string Partial(string path, long len) {
        const int B = 1 << 20;
        using (var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete, 1 << 16))
        using (var sha = SHA256.Create()) {
            var buf = new byte[B];
            int n = fs.Read(buf, 0, B); sha.TransformBlock(buf, 0, n, null, 0);
            if (len > 2L * B) { fs.Seek(-B, SeekOrigin.End); n = fs.Read(buf, 0, B); }
            sha.TransformFinalBlock(buf, 0, n);
            return Convert.ToHexString(sha.Hash);
        }
    }
    static string Full(string path) {
        using (var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete, 1 << 20))
        using (var sha = SHA256.Create()) return Convert.ToHexString(sha.ComputeHash(fs));
    }
    public static string Run(string[] inputs, string outPath, long minBytes) {
        var all = new List<Tuple<long, string, string>>();
        foreach (var inp in inputs)
            foreach (var line in File.ReadLines(inp)) {
                var p = line.Split('\t');
                if (p.Length < 3) continue;
                long len = long.Parse(p[0]);
                if (len >= minBytes) all.Add(Tuple.Create(len, p[1], p[2]));
            }
        int groups = 0, hardlinkOnly = 0; long apparent = 0, real = 0;
        using (var w = new StreamWriter(outPath, false, new UTF8Encoding(true))) {
            w.WriteLine("Group,SHA256,Bytes,Paths,PhysicalCopies,RealWasteBytes,PhysId,Links,LastWrite,Path");
            foreach (var bySize in all.GroupBy(t => t.Item1).Where(g => g.Count() > 1)) {
                var part = new Dictionary<string, List<Tuple<long, string, string>>>();
                foreach (var t in bySize) {
                    string h; try { h = Partial(t.Item3, t.Item1); } catch { continue; }
                    if (!part.ContainsKey(h)) part[h] = new List<Tuple<long, string, string>>();
                    part[h].Add(t);
                }
                foreach (var pg in part.Values.Where(v => v.Count > 1)) {
                    var full = new Dictionary<string, List<Tuple<long, string, string>>>();
                    foreach (var t in pg) {
                        string h; try { h = Full(t.Item3); } catch { continue; }
                        if (!full.ContainsKey(h)) full[h] = new List<Tuple<long, string, string>>();
                        full[h].Add(t);
                    }
                    foreach (var kv in full.Where(k => k.Value.Count > 1)) {
                        groups++;
                        long len = kv.Value[0].Item1;
                        var ids = kv.Value.Select(t => { uint l; var id = PhysId(t.Item3, out l); return Tuple.Create(t, id, l); }).ToList();
                        // unreadable IDs count as distinct physical files (conservative: never hides a real copy)
                        int phys = ids.Where(x => x.Item2 != "ERR").Select(x => x.Item2).Distinct().Count() + ids.Count(x => x.Item2 == "ERR");
                        long wasteApparent = len * (kv.Value.Count - 1), wasteReal = len * Math.Max(0, phys - 1);
                        apparent += wasteApparent; real += wasteReal; if (wasteReal == 0) hardlinkOnly++;
                        foreach (var x in ids)
                            w.WriteLine(groups + "," + kv.Key + "," + len + "," + kv.Value.Count + "," + phys + "," + wasteReal + "," + x.Item2 + "," + x.Item3 + "," + x.Item1.Item2 + ",\"" + x.Item1.Item3.Replace("\"", "\"\"") + "\"");
                    }
                }
            }
        }
        return string.Format("candidates={0} groups={1} hardlinkOnlyGroups={2} apparentWasteGB={3:F2} realWasteGB={4:F2}",
            all.Count, groups, hardlinkOnly, apparent / 1073741824.0, real / 1073741824.0);
    }
}
'@
if (-not ('WdcDups' -as [type])) { Add-Type -TypeDefinition $src -Language CSharp }
$inputs = @(Get-ChildItem $InDir -Filter '*_dupcand.tsv' | ForEach-Object FullName)
if (-not $inputs) { throw "No *_dupcand.tsv in $InDir - run scan.ps1 first." }
if (-not $OutCsv) { $OutCsv = Join-Path $InDir 'dups.csv' }
[WdcDups]::Run([string[]]$inputs, $OutCsv, $MinBytes)
