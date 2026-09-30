# Fontes desatualizadas e erros de memória

Material sobre hooks envelhece rápido: a referência oficial ganhou eventos, tipos e campos ao
longo de 2026. Antes de copiar um exemplo, confira contra https://code.claude.com/docs/en/hooks.

## A skill oficial `plugin-dev/hook-development`

Em `anthropics/claude-plugins-official/plugins/plugin-dev/skills/hook-development/SKILL.md`, o
último commit é de 2026-02-05. Ela diverge da doc atual (lida em 2026-09-30) em pelo menos 11
pontos:

| # | A skill diz | A doc atual diz |
|---|---|---|
| 1 | settings.json sem o invólucro `hooks` | settings.json também usa `{"hooks": {...}}` |
| 2 | prompt hook responde `approve`/`deny` | responde `{ok, reason, impossible}` |
| 3 | placeholders `$TOOL_INPUT`, `$TOOL_RESULT`, `$USER_PROMPT` | só `$ARGUMENTS` |
| 4 | Stop com `decision: approve\|block` | só `"block"`; para liberar, omita |
| 5 | stdout com exit 0 aparece no transcript | vai para o debug log, com 4 exceções (UserPromptSubmit, UserPromptExpansion, SessionStart, PostModelSwitch) |
| 6 | `systemMessage` é "mensagem para o Claude" | é mostrado ao **usuário** |
| 7 | `suppressOutput` esconde saída | não tem efeito |
| 8 | timeout padrão de command de 60 s | 600 s |
| 9 | campos `user_prompt`, `tool_result`, `reason` no Stop | `prompt`, `tool_response`, `stop_hook_active` |
| 10 | hooks não recarregam a quente | settings recarregam pelo watcher; plugin com `/reload-plugins` |
| 11 | prompt hooks só em 4 eventos | em 12 (lista em `handler-types.md`) |

Outros pontos:
- Os campos `rewakeMessage` e `rewakeSummary` do plugin `security-guidance` não constam na
  referência.
- O Stop hook do `hookify` bloqueia sem checar `stop_hook_active` e depende do teto de 8.

## Erros que um agente comete de memória

Observados em 2026-09-30, pedindo hooks a um subagente sem esta skill e sem consulta à doc. É
a linha de base que motivou a skill.

| O agente escreveu | O certo |
|---|---|
| hook de "Bash falhou" em `PostToolUse`, adivinhando `exit_code`/`exitCode`/`status` no `tool_response` | `PostToolUseFailure` (`error: "Exit code 1"`); o `tool_response` do Bash não tem exit code |
| gate de `/deploy` por regex no `prompt` do `UserPromptSubmit` | `UserPromptExpansion` com matcher `deploy` |
| "plugin hooks não recarregam; saia e abra de novo" | `/reload-plugins` |
| "`claude --debug` imprime no stderr" | grava em `~/.claude/debug/<id>.txt` ou em `--debug-file` |
| estado do plugin em `~/.claude/<nome>/` | `${CLAUDE_PLUGIN_DATA}` |
| orientação de fim de turno via `decision: "block"` | `hookSpecificOutput.additionalContext` no Stop (sem "hook error") |
| revisão no 1º Stop depois do gatilho, mesmo com o turno esperando resposta | adiar quando o turno termina em pergunta ou `AskUserQuestion` (`patterns.md` §5) |
| bloqueio de `rm -rf /` e de force push só por hook | `permissions.deny` para o rígido; hook como complemento |

## Hooks de terceiros com bug conhecido

O `self-improvement` do pskoett (o `error-detector.sh` da pasta de scripts dele, versões com hooks até
`pskoett-ai-skills` @ 2026-06-12) lê `$CLAUDE_TOOL_OUTPUT`, uma variável que não existe. O hook
nunca dispara. O input chega pelo stdin.
