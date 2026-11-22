#!/usr/bin/env bash
# Monta a bancada de teste numa pasta nova, fora do repositório e fora do /tmp (o /tmp some ao reiniciar):
# o Playwright 1.58.0 em <pasta>/pw, o Chromium, e a pasta <pasta>/capturas.
# Se o Chromium já está no cache do Playwright, a instalação o reaproveita.
# Uso: bash preparar.sh <pasta nova>
set -euo pipefail
DEST="${1:?informe a pasta de destino}"
mkdir -p "$DEST/pw" "$DEST/capturas"
npm i --prefix "$DEST/pw" playwright@1.58.0 --silent
# PLAYWRIGHT_SKIP_BROWSER_GC=1: sem isso, a instalação apaga do cache compartilhado os browsers que outros projetos usam.
(cd "$DEST/pw" && PLAYWRIGHT_SKIP_BROWSER_GC=1 npx --no-install playwright install chromium)
echo "pronto: $DEST"
