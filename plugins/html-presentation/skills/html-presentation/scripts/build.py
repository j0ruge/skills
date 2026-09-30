#!/usr/bin/env python3
"""Build a self-contained deck + speaker script from the source HTML.

Usage:
  python3 build.py <src/deck.html> [--out dist] [--duration MIN] [--name deck]

- Inlines every url(assets/...) and src="assets/..." as a data URI (deck works offline, one file).
- Writes <out>/<name>.html and <out>/roteiro-de-fala.md (generated from <aside class="notes" data-t>).
- Gates (exit 1): an asset left un-inlined, an external http(s) resource, a slide without notes/data-t,
  or a time budget above duration − 30 s (room for questions).
"""
import argparse, base64, html, pathlib, re, sys

MIME = {".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".svg": "image/svg+xml",
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("--out", default="dist")
ap.add_argument("--duration", type=float, help="talk length in minutes (checks the notes budget)")
ap.add_argument("--name", default=None, help="output basename (default: source basename)")
a = ap.parse_args()

src_path = pathlib.Path(a.src).resolve()
src = src_path.read_text(encoding="utf-8")
base = src_path.parent
errors = []

def inline(m):
    p = base / m.group(2)
    if not p.exists():
        errors.append(f"asset não encontrado: {m.group(2)}")
        return m.group(0)
    mime = MIME.get(p.suffix.lower(), "application/octet-stream")
    return f"{m.group(1)}data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}{m.group(3)}"

# Comments (CSS and HTML) carry example paths and the direction contract: never touch them.
COMMENT = r'/\*.*?\*/|<!--.*?-->'
ASSET = r'(url\(|src=")(assets/[^")]+)(\)|")'
parts = re.split(f'({COMMENT})', src, flags=re.S)
out = "".join(pt if re.fullmatch(COMMENT, pt, re.S) else re.sub(ASSET, inline, pt) for pt in parts)
live = re.sub(COMMENT, "", out, flags=re.S)
if re.search(r'(url\(|src=")assets/', live):
    errors.append("sobrou asset sem embutir")
ext = re.findall(r'(?:src|href)="(https?://[^"]+)"|url\((https?://[^)]+)\)|@import\s+url\(["\']?(https?://[^"\')]+)', live)
ext = [x for t in ext for x in t if x]
if ext:
    errors.append(f"recurso externo (o deck precisa funcionar offline): {ext[:3]}")

# Speaker script from the notes: the HTML is the single source of truth
slides = re.findall(r'<section class="slide[^"]*"[^>]*data-title="([^"]+)"[^>]*>(.*?)</section>', src, re.S)
lines = ["# Roteiro de fala", "",
         "Gerado por `build.py` a partir das notas do HTML. Edite as notas na fonte, não este arquivo.", "",
         "Teclas: ← → navegam · **N** notas · **P** janela do apresentador (notas + cronômetro) · **F** tela cheia · **R** zera o tempo.", ""]
acc = 0
for k, (title, body) in enumerate(slides, 1):
    m = re.search(r'<aside class="notes" data-t="(\d+)">(.*?)</aside>', body, re.S)
    if not m:
        errors.append(f"lâmina {k} ({title}) sem <aside class=\"notes\" data-t>")
        continue
    t = int(m.group(1))
    lines += [f"## {k:02d} · {html.unescape(title)} · {acc//60:02d}:{acc%60:02d} → {(acc+t)//60:02d}:{(acc+t)%60:02d} ({t}s)", ""]
    for para in re.findall(r"<p>(.*?)</p>", m.group(2), re.S):
        lines += [html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"\s+", " ", para)).strip()), ""]
    acc += t
lines.append(f"**Total planejado: {acc//60:02d}:{acc%60:02d}**")

if a.duration and acc > a.duration * 60 - 30:
    errors.append(f"notas somam {acc//60:02d}:{acc%60:02d}, acima de {a.duration:g} min − 30 s para perguntas")

if errors:
    print("BUILD REPROVADO:", *errors, sep="\n  - ")
    sys.exit(1)

outdir = pathlib.Path(a.out)
outdir.mkdir(parents=True, exist_ok=True)
name = a.name or src_path.stem
(outdir / f"{name}.html").write_text(out, encoding="utf-8")
(outdir / "roteiro-de-fala.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"ok: {outdir/name}.html ({len(out.encode())//1024} KB) · {len(slides)} lâminas · {acc//60:02d}:{acc%60:02d}")
