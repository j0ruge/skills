#!/usr/bin/env bash
# diagnose.sh — retrato somente leitura de um jogo Windows instalado pelo Lutris.
# Uso: diagnose.sh <parte-do-slug-ou-nome-do-yml>     ex.: diagnose.sh magic
# Não altera nada: lê config, prefixo, logs e pacotes. Pode rodar com o jogo aberto.
set -u

needle="${1:-}"
if [ -z "$needle" ]; then
  echo "uso: $0 <parte-do-slug>   (ex.: $0 magic)" >&2
  exit 2
fi

DATA="${XDG_DATA_HOME:-$HOME/.local/share}/lutris"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}/lutris"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/lutris"

section() { printf '\n=== %s\n' "$1"; }

section "Lutris"
lutris --version 2>/dev/null | tail -1 || echo "lutris não encontrado"
python3 -I - "$DATA/pga.db" "$needle" <<'PY'
import sqlite3, sys
db, needle = sys.argv[1], sys.argv[2].lower()
try:
    rows = sqlite3.connect(db).execute(
        "select id, slug, runner, configpath, installed from games").fetchall()
except Exception as exc:
    print("pga.db ilegível:", exc); sys.exit(0)
for r in rows:
    if needle in (r[1] or "").lower() or needle in (r[3] or "").lower():
        print(f"id={r[0]} slug={r[1]} runner={r[2]} configpath={r[3]} installed={r[4]}"
              f"   → lançar: lutris lutris:rungameid/{r[0]}")
PY

section "Config do jogo"
yml=""
for d in "$DATA/games" "$CFG/games"; do
  for f in "$d"/*"$needle"*.yml; do
    [ -f "$f" ] && { yml="$f"; break 2; }
  done
done
if [ -z "$yml" ]; then
  echo "nenhum yml com '$needle' em $DATA/games ou $CFG/games"; exit 1
fi
echo "$yml"
# Só as seções de nível raiz que importam (game, wine, system); 'script:' é o instalador.
awk '/^[a-z_]+:/{show=($1=="game:"||$1=="wine:"||$1=="system:")} show' "$yml"

prefix=$(awk '/^game:/{g=1;next} /^[a-z_]+:/{g=0} g && /^  prefix:/{sub(/^  prefix: */,""); print; exit}' "$yml")
prefix="${prefix/#\~/$HOME}"
echo "prefixo: ${prefix:-<não definido>}"

section "Runner efetivo"
ver=$(awk '/^wine:/{w=1;next} /^[a-z_]+:/{w=0} w && /^  version:/{sub(/^  version: */,""); print; exit}' "$yml")
[ -z "$ver" ] && [ -f "$CFG/runners/wine.yml" ] && \
  ver=$(awk '/^wine:/{w=1;next} /^[a-z_]+:/{w=0} w && /^  version:/{sub(/^  version: */,""); print; exit}' "$CFG/runners/wine.yml")
echo "versão configurada: ${ver:-<padrão: GE-Proton (Latest) → umu-run>}"
python3 -I -c "
import sys; sys.path.insert(0,'/usr/lib/python3/dist-packages')
from lutris.util.wine import proton
u = proton.get_umu_path()
print('umu-run:', u, '| is_proton_path(umu-run) =', proton.is_proton_path(u),
      '(False = managers DXVK/VKD3D/NVAPI do Lutris atuam no prefixo Proton; ver references/lutris-umu-dll-managers.md)')
" 2>/dev/null | grep -v -i protobuf
ls -1d "$HOME"/.local/share/Steam/compatibilitytools.d/*/ "$DATA"/runners/wine/*/ 2>/dev/null | sed "s|$HOME|~|"

[ -n "$prefix" ] && [ -d "$prefix" ] || { echo "prefixo inexistente"; exit 1; }

section "Estado do Proton no prefixo"
[ -f "$prefix/version" ] && echo "version: $(cat "$prefix/version")"
# Ordem do prefix_info no script 'proton' do GE-Proton11 (confira em outra versão:
# grep -n 'prefix_info' <PROTONPATH>/proton): linha 10=use_wined3d 11=use_dxvk_dxgi 13=use_nvapi 14=use_dxvk_d3d8.
if [ -f "$prefix/config_info" ]; then
  echo "config_info (o que o Proton aplicou; ordem do GE-Proton11):"
  awk 'NR==10{print "  use_wined3d    =",$0} NR==11{print "  use_dxvk_dxgi  =",$0} NR==13{print "  use_nvapi      =",$0} NR==14{print "  use_dxvk_d3d8  =",$0}' "$prefix/config_info"
fi

section "DLLs gráficas em system32"
s32="$prefix/drive_c/windows/system32"
for dll in d3d9 d3d11 d3d12 d3d12core dxgi nvapi64; do
  f="$s32/$dll.dll"
  if [ -L "$f" ]; then
    echo "$dll.dll → SYMLINK $(readlink "$f" | sed "s|$HOME|~|")"
  elif [ -f "$f" ]; then
    printf '%s.dll  arquivo %s bytes  sha=%s  mtime=%s\n' "$dll" "$(stat -c %s "$f")" \
      "$(sha256sum "$f" | cut -c1-12)" "$(stat -c %y "$f" | cut -d. -f1)"
  else
    echo "$dll.dll ausente"
  fi
done
for dll in d3d9 d3d11 d3d12 d3d12core dxgi nvapi64; do
  [ -e "$s32/$dll.dll.orig" ] && echo ".orig presente: $dll.dll.orig (o Lutris trocou essa DLL em algum momento)"
done
extras=0
for f in "$s32"/d3dx*.dll.orig "$s32"/d3dcompiler_*.dll.orig; do [ -e "$f" ] && extras=$((extras + 1)); done
[ "$extras" -gt 0 ] && echo ".orig de d3dx*/d3dcompiler_*: $extras (manager D3D Extras do Lutris)"

section "Logs do Unity (se for jogo Unity)"
users="$prefix/drive_c/users"
find "$users" -path '*LocalLow*' -name 'Player.log' 2>/dev/null | while read -r pl; do
  echo "--- $pl ($(stat -c %y "$pl" | cut -d. -f1))" | sed "s|$HOME|~|"
  grep -nE 'Initialize engine|Device Filter\] (Device Name|D3D12 API)|^Direct3D|Renderer:|Crash!!!|Connecting to|not supported on this GPU' "$pl" | head -15
done
find "$users" -type d -name 'Crash_*' 2>/dev/null | sort | tail -5 | while read -r c; do
  echo "--- crash: $(basename "$c") (horário UTC)"
  [ -f "$c/Player.log" ] && grep -B2 -m1 'Crash!!!' "$c/Player.log" | head -3
  [ -f "$c/Player.log" ] && grep -oE '\\(d3d[0-9a-z]*|dxgi|wined3d|nvapi64|libvkd3d[-a-z0-9]*|vulkan-1|opengl32)\.dll' "$c/Player.log" \
    | tr -d '\\' | sort -u | tr '\n' ' ' | sed 's/^/módulos gráficos: /'; echo
done

section "lutris.log (fim)"
tail -8 "$CACHE/lutris.log" 2>/dev/null

section "Sistema"
echo "arquiteturas extras: $(dpkg --print-foreign-architectures 2>/dev/null | tr '\n' ' ')"
for p in libgl1:i386 libgnutls30t64:i386 mesa-vulkan-drivers:i386 libvulkan1:i386 python3-protobuf; do
  st=$(dpkg-query -W -f='${Status}' "$p" 2>/dev/null)
  case "$st" in *"install ok installed"*) echo "ok      $p";; *) echo "FALTA   $p";; esac
done
vulkaninfo --summary 2>/dev/null | grep -E 'deviceName|driverName' | head -4
