#!/usr/bin/env bash
# Screenshot every slide + notebook viewport + PDF export, with the traps of headless Chrome handled.
#
# Usage: shoot.sh <dist/deck.html> [shots-dir] [pdf-path]
#
# Why each flag exists (each one was a real failure):
#   rm -f before capture      — a failed capture otherwise leaves the OLD png, and you review a stale slide
#   retry + [ -s file ]       — back-to-back headless runs sometimes exit without writing anything
#   --force-prefers-reduced-motion — without it the shot lands mid entrance animation (faded title)
#   1366×768 and 1280×720     — the stage must fit a laptop shared on a call, not only 1920×1080
#   fallbacks (WSL)           — no Chrome, pdfinfo or montage on PATH: Playwright's cached Chromium, a /Type /Page
#                               count, and Pillow grades; the contact sheets used to vanish without a word
#   taller window + crop      — --headless=new gives ~87 px of --window-size to the browser UI, so the stage came out
#                               at 0.92 with dark bands; the real viewport is measured once and the PNG cropped back
set -uo pipefail
[ -f "${1:-}" ] || { echo "uso: shoot.sh <deck.html> [shots] [pdf]"; exit 2; }
HTML=$(readlink -f "$1"); SHOTS=${2:-shots}; PDF=${3:-"${HTML%.html}.pdf"}
# Sem Chrome no PATH (WSL), serve o Chromium que o Playwright já baixou
CHROME=$(command -v google-chrome || command -v chromium || command -v chromium-browser \
  || ls -d "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux*/chrome 2>/dev/null | sort -V | tail -1)
[ -n "$CHROME" ] || { echo "Chrome/Chromium não encontrado"; exit 2; }
N=$(grep -o '<section class="slide' "$HTML" | wc -l)
mkdir -p "$SHOTS"; rm -f "$SHOTS"/*.png
fail=0
# Viewport real de uma janela 1920×1080: DH é a altura que a barra do navegador leva
printf '<p id=v></p><script>v.textContent="vh"+innerHeight</script>' > "$SHOTS/.viewport.html"
VH=$("$CHROME" --headless=new --disable-gpu --window-size=1920,1080 --dump-dom "file://$(readlink -f "$SHOTS")/.viewport.html" \
  2>/dev/null | grep -o 'vh[0-9]*' | tr -dc 0-9)
rm -f "$SHOTS/.viewport.html"; DH=$((1080 - ${VH:-1080})); [ "$DH" -gt 0 ] || DH=0
crop() { # file width height: tira as DH linhas a mais, com Pillow ou ImageMagick
  [ "$DH" -gt 0 ] || return 0
  if python3 -c 'import PIL' 2>/dev/null; then
    python3 -c 'import sys; from PIL import Image; f, w, h = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); Image.open(f).crop((0, 0, w, h)).save(f)' "$1" "$2" "$3"
  elif command -v convert >/dev/null; then convert "$1" -crop "${2}x${3}+0+0" +repage "$1"
  elif [ -z "${avisou:-}" ]; then echo "aviso: sem Pillow nem ImageMagick, as capturas ficam com $DH px a mais embaixo"; avisou=1; fi
}
shot() { # width height file slide
  for _ in 1 2 3; do
    "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-prefers-reduced-motion \
      --virtual-time-budget=3000 --window-size="$1,$(($2 + DH))" --screenshot="$3" "file://$HTML#$4" >/dev/null 2>&1
    [ -s "$3" ] && { crop "$3" "$1" "$2"; return 0; }
  done
  echo "FALHOU: $3"; fail=1
}
for n in $(seq 1 "$N"); do shot 1920 1080 "$SHOTS/s$(printf %02d "$n").png" "$n"; done
shot 1366 768 "$SHOTS/laptop-1366.png" 2
shot 1280 720 "$SHOTS/laptop-1280.png" 3
"$CHROME" --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=4000 \
  --print-to-pdf="$PDF" "file://$HTML" >/dev/null 2>&1
# Sem pdfinfo, conta os objetos /Type /Page: o PDF do Chrome não usa object streams (conferido contra pypdf, 19/10/2026)
if command -v pdfinfo >/dev/null; then PAGES=$(pdfinfo "$PDF" 2>/dev/null | awk '/^Pages/{print $2}')
else PAGES=$(python3 -c 'import re,sys;print(len(re.findall(rb"/Type\s*/Page(?![s\w])",open(sys.argv[1],"rb").read())))' "$PDF" 2>/dev/null); fi
echo "lâminas: $N · PDF: $PDF (${PAGES:-?} págs.)"
[ "${PAGES:-0}" = "$N" ] || { echo "PDF com $PAGES páginas para $N lâminas"; fail=1; }
# Contact sheets (4 per image) to review at legible scale — ImageMagick, or Pillow with the same geometry
if command -v montage >/dev/null; then
  ls "$SHOTS"/s*.png | xargs -n4 | nl -nln | while read -r k files; do
    montage $files -tile 2x2 -geometry 960x540+6+6 -background '#333' "$SHOTS/grade-$k.png"
  done
elif python3 -c 'import PIL' 2>/dev/null; then
  python3 - "$SHOTS" <<'PY'
import glob, sys
from PIL import Image
d = sys.argv[1]; fs = sorted(glob.glob(d + '/s*.png'))
for k in range(0, len(fs), 4):
    g = Image.new('RGB', (1944, 1104), '#333')
    for j, f in enumerate(fs[k:k + 4]):
        g.paste(Image.open(f).convert('RGB').resize((960, 540)), (6 + j % 2 * 972, 6 + j // 2 * 552))
    g.save(f'{d}/grade-{k // 4 + 1}.png')
PY
else
  echo "sem montage nem Pillow: grades não geradas; olhe cada sNN.png"
fi
exit $fail
