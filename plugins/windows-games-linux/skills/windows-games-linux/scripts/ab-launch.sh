#!/usr/bin/env bash
# ab-launch.sh — lança um .exe direto pelo umu-run (sem o Lutris) e diz RUNNING, CRASH ou EXITED.
# Serve para o teste A/B: roda direto? Então a diferença está no env/DLLs que o Lutris injeta.
#
# Uso:
#   ab-launch.sh --prefix DIR --exe CAMINHO.exe [opções]
# Opções:
#   --protonpath DIR    Proton a usar (padrão: o GE-Proton mais novo em ~/.local/share/Steam/compatibilitytools.d)
#   --wined3d           exporta PROTON_USE_WINED3D=1 (o que o Lutris faz quando dxvk: false)
#   --overrides STR     WINEDLLOVERRIDES, ex.: 'd3d12,d3d12core=n;winemenubuilder='
#   --env K=V           variável extra (pode repetir)
#   --log ARQ --ok REGEX   sucesso = ARQ modificado depois do início e contendo REGEX
#                          (Unity: o Player.log e algo como 'Connecting to|Direct3D:')
#   --crash-dir DIR     crash = surgiu entrada nova em DIR (Unity: .../Temp/<Empresa>/<Produto>/Crashes)
#   --timeout N         segundos de observação (padrão 60)
#   --keep              não encerra o jogo depois do veredito (use no teste que deve ficar aberto)
#   --dry-run           só imprime o comando
#
# Avise o usuário antes: o jogo abre na tela dele, e sem --keep é encerrado no fim.
# Encerra com pkill -x pelo nome do processo (truncado em 15 chars), nunca pkill -f,
# que casaria com o próprio shell que contém o nome do exe.
set -u

prefix="" exe="" protonpath="" overrides="" log="" ok="" crashdir=""
timeout=60 keep=0 dry=0 wined3d=0
extra=()
while [ $# -gt 0 ]; do
  case "$1" in
    --prefix) prefix="$2"; shift 2;;
    --exe) exe="$2"; shift 2;;
    --protonpath) protonpath="$2"; shift 2;;
    --wined3d) wined3d=1; shift;;
    --overrides) overrides="$2"; shift 2;;
    --env) extra+=("$2"); shift 2;;
    --log) log="$2"; shift 2;;
    --ok) ok="$2"; shift 2;;
    --crash-dir) crashdir="$2"; shift 2;;
    --timeout) timeout="$2"; shift 2;;
    --keep) keep=1; shift;;
    --dry-run) dry=1; shift;;
    -h|--help) sed -n '2,25p' "$0"; exit 0;;
    *) echo "opção desconhecida: $1" >&2; exit 2;;
  esac
done
[ -n "$prefix" ] && [ -n "$exe" ] || { echo "faltou --prefix e/ou --exe (veja --help)" >&2; exit 2; }
[ -f "$exe" ] || { echo "exe não existe: $exe" >&2; exit 2; }

umu="${XDG_DATA_HOME:-$HOME/.local/share}/lutris/runtime/umu/umu-run"
[ -x "$umu" ] || umu="$(command -v umu-run || true)"
[ -n "$umu" ] || { echo "umu-run não encontrado" >&2; exit 2; }
if [ -z "$protonpath" ]; then
  protonpath=$(ls -1d "$HOME"/.local/share/Steam/compatibilitytools.d/GE-Proton*/ 2>/dev/null | sort -V | tail -1)
  protonpath="${protonpath%/}"
fi
[ -d "$protonpath" ] || { echo "PROTONPATH inválido: '$protonpath' (use --protonpath)" >&2; exit 2; }

envs=(WINEPREFIX="$prefix" GAMEID=umu-default PROTONPATH="$protonpath")
[ "$wined3d" = 1 ] && envs+=(PROTON_USE_WINED3D=1)
[ -n "$overrides" ] && envs+=(WINEDLLOVERRIDES="$overrides")
envs+=("${extra[@]}")

name=$(basename "$exe"); pname="${name:0:15}"
echo "env: ${envs[*]}"
echo "exe: $exe   (processo: $pname)"
[ "$dry" = 1 ] && exit 0

if pgrep -x "$pname" >/dev/null; then
  echo "já existe um '$pname' rodando — feche-o antes (o teste ficaria ambíguo)" >&2; exit 3
fi

n0=0; [ -n "$crashdir" ] && n0=$(ls "$crashdir" 2>/dev/null | wc -l)
t0=$(date +%s)
out=$(mktemp -t ab-launch.XXXXXX.log)
( cd "$(dirname "$exe")" && env "${envs[@]}" "$umu" "$exe" >"$out" 2>&1 ) &

verdict="TIMEOUT"; seen=0
for _ in $(seq 1 $(( timeout / 2 ))); do
  sleep 2
  if [ -n "$crashdir" ] && [ "$(ls "$crashdir" 2>/dev/null | wc -l)" -gt "$n0" ]; then verdict="CRASH"; break; fi
  if [ -n "$log" ] && [ -f "$log" ] && [ "$(stat -c %Y "$log")" -ge "$t0" ] && grep -qE "$ok" "$log"; then verdict="RUNNING"; break; fi
  if pgrep -x "$pname" >/dev/null; then seen=1; elif [ "$seen" = 1 ]; then verdict="EXITED"; break; fi
done
echo "veredito: $verdict após ~$(( $(date +%s) - t0 ))s   (saída do umu/Proton: $out)"

if [ "$keep" = 0 ]; then
  pkill -x "$pname" 2>/dev/null && echo "encerrado: $pname"
fi
case "$verdict" in RUNNING) exit 0;; CRASH) exit 10;; EXITED) exit 11;; *) exit 12;; esac
