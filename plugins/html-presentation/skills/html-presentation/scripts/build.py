#!/usr/bin/env python3
"""Build a self-contained deck + speaker script from the source HTML.

Usage:
  python3 build.py <src/deck.html> [--out dist] [--duration MIN] [--name deck]

- Inlines every url(assets/...) and src="assets/..." as a data URI (deck works offline, one file).
- Writes <out>/<name>.html and <out>/roteiro-de-fala.md (generated from <aside class="notes" data-t>).
- Gates (exit 1): an asset left un-inlined, an external http(s) resource, a slide without notes/data-t,
  or a time budget above duration − 30 s (room for questions).
- Warns (no failure) when a note, read at --wpm words per minute, needs 5 s or more beyond its data-t. A
  number counts as two words and a date (dd/mm) as three: said aloud they take more than written, and the
  time gate alone let a note at 157 written / ~187 spoken wpm through (Manutenção Proativa deck, 16/10/2026).
"""
import argparse, base64, html, pathlib, re, sys

MIME = {".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".svg": "image/svg+xml",
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("--out", default="dist")
ap.add_argument("--duration", type=float, help="talk length in minutes (checks the notes budget)")
ap.add_argument("--name", default=None, help="output basename (default: source basename)")
ap.add_argument("--wpm", type=int, default=150, help="speaking pace used for the note-length warning")
a = ap.parse_args()

src_path = pathlib.Path(a.src).resolve()
src = src_path.read_text(encoding="utf-8")
base = src_path.parent
errors, warnings = [], []

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
    text = [html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"\s+", " ", para)).strip())
            for para in re.findall(r"<p>(.*?)</p>", m.group(2), re.S)]
    for para in text:
        lines += [para, ""]
    spoken = sum(3 if re.fullmatch(r"\d{1,2}/\d{1,2}(/\d{2,4})?\W*", w) else 2 if re.search(r"\d", w) else 1
                 for w in " ".join(text).split())
    if spoken * 60 / a.wpm - t >= 5:
        warnings.append(f"lâmina {k} ({html.unescape(title)}): ~{spoken} palavras faladas pedem "
                        f"~{spoken * 60 / a.wpm:.0f} s a {a.wpm} ppm, e o data-t dá {t} s; corte a nota ou aumente o data-t")
    acc += t
lines.append(f"**Total planejado: {acc//60:02d}:{acc%60:02d}**")

if a.duration and acc > a.duration * 60 - 30:
    errors.append(f"notas somam {acc//60:02d}:{acc%60:02d}, acima de {a.duration:g} min − 30 s para perguntas")

for w in warnings:
    print("aviso de ritmo:", w)
if errors:
    print("BUILD REPROVADO:", *errors, sep="\n  - ")
    sys.exit(1)

outdir = pathlib.Path(a.out)
outdir.mkdir(parents=True, exist_ok=True)
name = a.name or src_path.stem
(outdir / f"{name}.html").write_text(out, encoding="utf-8")
(outdir / "roteiro-de-fala.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"ok: {outdir/name}.html ({len(out.encode())//1024} KB) · {len(slides)} lâminas · {acc//60:02d}:{acc%60:02d}")
