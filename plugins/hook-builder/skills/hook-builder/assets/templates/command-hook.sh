#!/usr/bin/env bash
# TEMPLATE de command hook em bash (requer jq). Troque os pontos marcados com AJUSTE.
# Contrato: JSON no stdin; exit code + no máximo UM objeto JSON no stdout.
# Sem `set -e`: um erro inesperado não pode virar exit 1 (aviso não bloqueante) nem 2 (bloqueio).

input="$(cat)"
event="$(jq -r '.hook_event_name // empty' <<<"$input")"

# Stop/SubagentStop: nunca peça continuação de dentro de uma continuação.
if [[ "$event" == "Stop" || "$event" == "SubagentStop" ]] &&
   [[ "$(jq -r '.stop_hook_active // false' <<<"$input")" == "true" ]]; then
  exit 0
fi

# AJUSTE: filtro barato. Ex.: só comandos git no PreToolUse do Bash.
cmd="$(jq -r '.tool_input.command // empty' <<<"$input")"
[[ "$cmd" == git\ * ]] || exit 0

# AJUSTE: decisão. Monte JSON com jq -n --arg (nunca por concatenação de string).
jq -n --arg ev "$event" --arg ctx "AJUSTE: fato útil para o Claude sobre $cmd" \
  '{hookSpecificOutput: {hookEventName: $ev, additionalContext: $ctx}}'
exit 0

# Para bloquear (PreToolUse, UserPromptSubmit, Stop...):
#   echo "motivo do bloqueio" >&2
#   exit 2
