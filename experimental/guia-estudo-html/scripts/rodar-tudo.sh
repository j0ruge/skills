#!/usr/bin/env bash
# Roda o conferir.js e todos os sensores de sensores/ sobre um curso. Cada execução ganha a própria pasta,
# <bancada>/execucoes/<AAAAMMDD-HHMMSS>-<pid>/, com conferir.out, capturas/, <sensor>.out e resumo.txt:
# duas execuções ao mesmo tempo não se pisam. Os seis sensores de aula rodam só em lessons/*.html.
# Sai 1 se o conferir.js ou algum sensor falhar.
# Uso: bash rodar-tudo.sh <bancada do preparar.sh> <pasta do curso>
set -u
B="${1:?informe a bancada}"; E="${2:?informe a pasta do curso}"
AQUI="$(cd "$(dirname "$0")" && pwd)"
B="$(cd "$B" && pwd)"; E="$(cd "$E" && pwd)"
export NODE_PATH="$B/pw/node_modules"
RUN="$B/execucoes/$(date +%Y%m%d-%H%M%S)-$$"
mkdir -p "$RUN/capturas"
echo "execucao: $RUN"
LESS=()
for f in "$E"/lessons/*.html; do [ -e "$f" ] && LESS+=("$f"); done
TODAS=()
[ -e "$E/index.html" ] && TODAS+=("$E/index.html")
TODAS+=("${LESS[@]}")
for f in "$E"/reference/*.html; do [ -e "$f" ] && TODAS+=("$f"); done
falhas=0
{
  timeout 900 node "$AQUI/conferir.js" "$RUN/capturas" "${TODAS[@]}" > "$RUN/conferir.out" 2>&1; rc=$?
  echo "conferir.js rc=$rc ok=$(/usr/bin/grep -c '^OK' "$RUN/conferir.out") de $(( ${#TODAS[@]} * 2 ))"
  [ $rc -ne 0 ] && { falhas=1; /usr/bin/grep -v '^OK' "$RUN/conferir.out" | head -10; }
  for s in "$AQUI"/sensores/*.js; do
    n="$(basename "$s" .js)"
    case "$n" in
      rodape-sem-indice|glossario-longe-da-aula|tempo-das-aulas|quiz-zera-ao-voltar|foco-sem-contraste|quiz-certa-so-pela-cor) alvo=("${LESS[@]}");;
      *) alvo=("${TODAS[@]}");;
    esac
    timeout 600 node "$s" "${alvo[@]}" > "$RUN/$n.out" 2>&1 < /dev/null; rc=$?
    echo "$n rc=$rc pass=$(/usr/bin/grep -c '^PASS' "$RUN/$n.out") fail=$(/usr/bin/grep -c '^FAIL' "$RUN/$n.out")"
    [ $rc -ne 0 ] && { falhas=1; /usr/bin/grep -v '^PASS' "$RUN/$n.out" | head -8; }
  done
} | tee "$RUN/resumo.txt"
# O pipe roda em subshell: o resultado vem do resumo, não da variável.
/usr/bin/grep -Eq ' rc=[1-9]' "$RUN/resumo.txt" && exit 1
exit 0
