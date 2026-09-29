#!/usr/bin/env bash
# listar-afirmacoes.sh — lista os trechos de uma skill com cara de AFIRMAÇÃO
# FACTUAL, para o autor pendurar um sensor em cada um (skill skill-claim-check).
#
# NÃO é gate: não reprova, não tem exit code de erro por achado. Muitos achados
# serão legítimos. O valor está em olhar cada linha e perguntar "qual é o sensor
# disto?" — a pergunta que a skill existe para provocar.
#
# Uso: bash listar-afirmacoes.sh <categoria>/<skill>   (ex: devops/minha-skill)
#      bash listar-afirmacoes.sh <dir-da-skill>         (qualquer harness)

set -uo pipefail

USO="Uso: $0 <categoria>/<skill> | <dir-da-skill>   (ex: devops/minha-skill)"

if [ $# -lt 1 ]; then
  echo "$USO"
  exit 2
fi

case "$1" in
  -h|--help)
    echo "$USO"
    echo "Lista trechos com cara de afirmação factual em SKILL.md e references/*.md."
    echo "Não é gate: rc=0 com ou sem achados; rc=1 diretório inexistente; rc=2 uso inválido."
    exit 0
    ;;
esac

# Diretório existente vale como está (skill fora do layout do Hermes, ou copiada
# para outro harness); senão, <categoria>/<skill> relativo a $HERMES_HOME/skills.
if [ -d "$1" ] && [ -f "$1/SKILL.md" ]; then
  SKILL_DIR="$1"
else
  SKILL_DIR="${HERMES_HOME:-$HOME/.hermes}/skills/$1"
fi

if [ ! -d "$SKILL_DIR" ]; then
  echo "🔴 Diretório não encontrado: $SKILL_DIR"
  exit 1
fi

python3 - "$SKILL_DIR" <<'PYEOF'
import glob
import os
import re
import sys

skill_dir = sys.argv[1]
alvos = [os.path.join(skill_dir, "SKILL.md")]
alvos += sorted(glob.glob(os.path.join(skill_dir, "references", "*.md")))

# Cada padrão é um TIPO de afirmação que apodrece de um jeito diferente. O rótulo
# diz ao autor que pergunta fazer, que é mais útil que só apontar a linha.
PADROES = [
    ("número/limite",
     r"\b\d{1,3}(?:[.,]\d{3})+\b|\b\d+\s?(?:k|KB|MB|GB|chars?|caracteres|linhas|ms|s|min|tokens)\b",
     "de onde sai esse número? o sistema calcula? -> descreva a derivação"),
    ("caminho absoluto",
     r"(?<![\w`])/(?:home|Users|opt|srv|var)/[\w./-]+",
     "existe em outra máquina? -> caminho relativo ou $HERMES_HOME"),
    ("versão fixa",
     r"\bv?\d+\.\d+(?:\.\d+)?\b",
     "validado quando? -> cite o comando que mostra a versão"),
    ("absoluto sobre terceiro",
     r"\b(sempre|nunca)\b\s+\w+",
     "você controla o outro lado? -> diga o que foi OBSERVADO, e quando"),
]

# Um padrão que foi TESTADO E REMOVIDO, para ninguém reintroduzir: linha de
# tabela markdown (`^\s*\|...\|...\|`) como proxy de "lista fechada que o sistema
# gera". Medido contra a skill hermes-agent: 153 dos 168 achados vinham dele, e
# quase nenhum era lista gerada — eram tabelas de roteamento escritas à mão.
# Ferramenta que devolve 168 achados numa skill é ferramenta ignorada, e aí ela
# não previne nada. O sinal ficou nos outros quatro padrões.

# Ignora blocos de código (cerca ``` ou ~~~): comando é o sensor, não a afirmação.
def linhas_fora_de_codigo(texto):
    cerca = None
    for numero, linha in enumerate(texto.splitlines(), 1):
        m = re.match(r"^\s*(```|~~~)", linha)
        if m and cerca is None:
            cerca = m.group(1)
            continue
        if m and m.group(1) == cerca:
            cerca = None
            continue
        if cerca is None:
            yield numero, linha

total = 0
for caminho in alvos:
    if not os.path.exists(caminho):
        continue
    achados = []
    texto = open(caminho, encoding="utf-8").read()
    for numero, linha in linhas_fora_de_codigo(texto):
        for rotulo, padrao, pergunta in PADROES:
            if re.search(padrao, linha):
                achados.append((numero, rotulo, pergunta, linha.strip()[:100]))
                break
    if achados:
        print(f"\n=== {os.path.relpath(caminho, skill_dir)} ===")
        for numero, rotulo, pergunta, trecho in achados:
            print(f"  L{numero:<4} [{rotulo}] {trecho}")
            print(f"        ↳ {pergunta}")
        total += len(achados)

print(f"\n{total} trecho(s) com cara de afirmação factual.")
print("Isto é lista para julgamento, não reprovação: confirme que cada um tem")
print("sensor (como reconferir) ou vire derivação. Ver skill skill-claim-check.")
PYEOF
