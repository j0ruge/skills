#!/usr/bin/env bash
# Roda o conferir.js e todos os sensores de sensores/ sobre um curso. Cada execução ganha a própria pasta,
# <bancada>/execucoes/<AAAAMMDD-HHMMSS>-<pid>/, com conferir.out, capturas/, <sensor>.out e resumo.txt:
# duas execuções ao mesmo tempo não se pisam. Os seis sensores de aula rodam só em lessons/*.html.
# Sai 1 se o conferir.js ou algum sensor falhar. Sai 2 sem os dois argumentos, se a bancada ou o curso
# não existem, se o curso não tem lessons/*.html, ou se o resumo.txt não traz uma linha para o conferir.js e
# uma para cada arquivo de sensores/: sem isso, nem tudo foi medido.
# Uso: bash rodar-tudo.sh <bancada do preparar.sh> <pasta do curso>
set -u
[ $# -eq 2 ] || { echo "uso: bash rodar-tudo.sh <bancada do preparar.sh> <pasta do curso>" >&2; exit 2; }
B="$1"; E="$2"
AQUI="$(cd "$(dirname "$0")" && pwd)"
[ -d "$B/pw/node_modules/playwright" ] || { echo "erro: $B não é uma bancada do preparar.sh (falta pw/node_modules/playwright)" >&2; exit 2; }
[ -d "$E" ] || { echo "erro: a pasta do curso $E não existe" >&2; exit 2; }
B="$(cd "$B" && pwd)" || exit 2
E="$(cd "$E" && pwd)" || exit 2
export NODE_PATH="$B/pw/node_modules"
LESS=()
for f in "$E"/lessons/*.html; do [ -e "$f" ] && LESS+=("$f"); done
# Os seis sensores de aula recebem só lessons/*.html. Sem aulas, eles sairiam 2 por falta de argumento.
[ ${#LESS[@]} -gt 0 ] || { echo "erro: $E/lessons não tem nenhum .html; sem aulas, os sensores de aula não rodam" >&2; exit 2; }
SENSORES=("$AQUI"/sensores/*.js)
[ -e "${SENSORES[0]}" ] || { echo "erro: $AQUI/sensores não tem nenhum sensor" >&2; exit 2; }
RUN="$B/execucoes/$(date +%Y%m%d-%H%M%S)-$$"
mkdir -p "$RUN/capturas" || { echo "erro: não consegui criar $RUN" >&2; exit 2; }
echo "execucao: $RUN"
TODAS=()
[ -e "$E/index.html" ] && TODAS+=("$E/index.html")
TODAS+=("${LESS[@]}")
for f in "$E"/reference/*.html; do [ -e "$f" ] && TODAS+=("$f"); done
{
  timeout 900 node "$AQUI/conferir.js" "$RUN/capturas" "${TODAS[@]}" > "$RUN/conferir.out" 2>&1; rc=$?
  echo "conferir.js rc=$rc ok=$(/usr/bin/grep -c '^OK' "$RUN/conferir.out") de $(( ${#TODAS[@]} * 2 ))"
  [ $rc -ne 0 ] && { /usr/bin/grep -v '^OK' "$RUN/conferir.out" | head -10; }
  for s in "${SENSORES[@]}"; do
    n="$(basename "$s" .js)"
    case "$n" in
      rodape-sem-indice|glossario-longe-da-aula|tempo-das-aulas|quiz-zera-ao-voltar|foco-sem-contraste|quiz-certa-so-pela-cor) alvo=("${LESS[@]}");;
      *) alvo=("${TODAS[@]}");;
    esac
    timeout 600 node "$s" "${alvo[@]}" > "$RUN/$n.out" 2>&1 < /dev/null; rc=$?
    echo "$n rc=$rc pass=$(/usr/bin/grep -c '^PASS' "$RUN/$n.out") fail=$(/usr/bin/grep -c '^FAIL' "$RUN/$n.out")"
    [ $rc -ne 0 ] && { /usr/bin/grep -v '^PASS' "$RUN/$n.out" | head -8; }
  done
} | tee "$RUN/resumo.txt"
# O pipe roda em subshell: o resultado vem do resumo. Ele tem de ter uma linha "<nome> rc=N" para o conferir.js e
# para cada sensor; uma execução cortada pelo meio não pode passar por completa.
[ -s "$RUN/resumo.txt" ] || { echo "erro: $RUN/resumo.txt ausente ou vazio" >&2; exit 2; }
ESPERADAS=$(( 1 + ${#SENSORES[@]} ))
LIDAS=$(/usr/bin/grep -Ec '^[a-z.-]+ rc=[0-9]+( |$)' "$RUN/resumo.txt")
[ "$LIDAS" -eq "$ESPERADAS" ] || { echo "erro: o resumo tem $LIDAS linhas de resultado e eram esperadas $ESPERADAS" >&2; exit 2; }
/usr/bin/grep -Eq ' rc=[1-9]' "$RUN/resumo.txt"; g=$?
[ $g -eq 0 ] && exit 1
[ $g -eq 1 ] && exit 0
echo "erro: o grep saiu $g ao ler $RUN/resumo.txt" >&2
exit 2
