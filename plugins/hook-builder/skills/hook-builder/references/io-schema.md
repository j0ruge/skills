# Entrada e saída de um hook

Fonte: https://code.claude.com/docs/en/hooks#hook-input-and-output, `#json-output`,
`#decision-control` e a seção de cada evento (lido em 2026-09-30, Claude Code 2.1.283). Os
exemplos marcados **capturado** vieram de `scripts/capture_payload.py` nessa versão.

## Conteúdo

1. Campos comuns
2. Campos por evento (os mais usados)
3. Como a saída é lida
4. Campos universais de saída
5. Decision control por evento
6. `additionalContext`

## 1. Campos comuns (stdin)

| Campo | Nota |
|---|---|
| `session_id` | chave natural para o estado por sessão |
| `transcript_path` | JSONL da sessão. **Gravado de forma assíncrona**: pode não ter as últimas linhas do turno |
| `cwd` | segue `cd` e worktree. `${CLAUDE_PROJECT_DIR}` **não** segue: fica na raiz onde a sessão começou |
| `hook_event_name` | nome do evento |
| `prompt_id` | UUID do prompt corrente (2.1.196+). Ausente antes do 1º input |
| `permission_mode` | `default` `plan` `acceptEdits` `auto` `dontAsk` `bypassPermissions`. **Nem todo evento traz**: o SessionStart capturado não trouxe |
| `scratchpad_dir` | 2.1.257+ |
| `effort.level` | `low`…`max` |
| `agent_id`, `agent_type` | só dentro de subagente ou com `--agent`. Use para separar a chamada do subagente da thread principal |

Não existe `$CLAUDE_MODEL` nem `$CLAUDE_TOOL_OUTPUT`. O input chega **só pelo stdin**. O
processo herda o ambiente do Claude Code (menos `OTEL_*`), mais `CLAUDE_PROJECT_DIR`,
`CLAUDE_PLUGIN_ROOT` e `CLAUDE_PLUGIN_DATA` quando se aplicam.

## 2. Campos por evento (os mais usados)

| Evento | Campos próprios |
|---|---|
| `PreToolUse` | `tool_name`, `tool_input`, `tool_use_id` |
| `PostToolUse` | acima + `tool_response` (saída estruturada da ferramenta) + `duration_ms`. **Capturado:** o `tool_response` do Bash é `{stdout, stderr, interrupted, isImage, noOutputExpected}`, **sem exit code** |
| `PostToolUseFailure` | `tool_name`, `tool_input`, `tool_use_id`, `error`, `is_interrupt`, `duration_ms`. **Capturado:** Bash com exit 1 → `"error": "Exit code 1"` |
| `PostToolBatch` | `tool_calls[]`, cada um com o `tool_response` serializado que o modelo vê |
| `UserPromptSubmit` | `prompt` |
| `UserPromptExpansion` | `expansion_type` (`slash_command`\|`mcp_prompt`), `command_name`, `command_args`, `command_source`, `prompt` |
| `SessionStart` | `source` (`startup`\|`resume`\|`clear`\|`compact`\|`fork`); opcionais `model`, `agent_type`, `session_title` |
| `Stop` | `stop_hook_active`, `last_assistant_message`, `background_tasks[]`, `session_crons[]` |
| `SubagentStop` | os campos do Stop + `agent_id`, `agent_type`, `agent_transcript_path` |
| `SessionEnd` | `reason` (`clear`\|`resume`\|`logout`\|`prompt_input_exit`\|`other`) |
| `PreCompact` / `PostCompact` | `trigger`, `custom_instructions` / `trigger`, `compact_summary` |
| `Notification` | `message`, `title`, `notification_type` |

O schema do `tool_input` de cada ferramenta (Bash, Write, Edit, Read, Glob, Grep, WebFetch,
Agent, AskUserQuestion, ExitPlanMode) está em `#pretooluse-input`. Para as outras, capture.

## 3. Como a saída é lida

- **stdout JSON:** o stdout é parseado como JSON só se, sem os espaços das pontas, começar com
  `{` e terminar com `}`. Um profile de shell que imprime texto quebra isso.
- **stdout em texto:** com exit 0, o stdout vai para o **debug log**. As exceções são
  `UserPromptSubmit`, `UserPromptExpansion`, `SessionStart` e `PostModelSwitch`, onde o texto
  puro vira contexto para o Claude.
- **stderr com exit 0:** só debug log.
- **Exit 2:** bloqueia nos eventos que bloqueiam (tabela em `events.md`), e nenhum JSON
  `allow` desfaz isso. A mensagem é o `reason` do JSON ou, sem ele, o stderr.
- **Outro exit:** aviso não bloqueante (`<hook> hook error` com a 1ª linha do stderr) e a
  ação segue. Se houver JSON válido, o JSON decide e o exit é ignorado.
- **JSON que falha o schema:** aviso não bloqueante com a mensagem de validação.
- **Timeout:** a saída é descartada e não há decisão. No `PreToolUse`, a ferramenta segue.

## 4. Campos universais de saída

| Campo | Efeito |
|---|---|
| `continue: false` + `stopReason` | para tudo, acima de qualquer decisão do evento |
| `systemMessage` | aviso **para o usuário**. O Claude não recebe |
| `suppressOutput` | **nenhum** (aceito e ignorado) |
| `terminalSequence` | OSC 0/1/2/9/99/777 e BEL (notificação, título, sino). `/dev/tty` não está disponível |

`additionalContext`, `systemMessage`, `initialUserMessage` e o stdout em texto têm cap de
**10.000 caracteres cada**. Acima disso, o texto vai para um arquivo e o Claude recebe o path e
os primeiros 2.000 caracteres.

## 5. Decision control por evento

| Eventos | Como decidir |
|---|---|
| `UserPromptSubmit`, `UserPromptExpansion`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Stop`, `SubagentStop`, `ConfigChange`, `PreCompact` | `{"decision": "block", "reason": "…"}`. `"block"` é o **único** valor; para liberar, omita. **Quem lê o `reason`:** no `UserPromptSubmit` e no `UserPromptExpansion`, **só o usuário**, porque o prompt não chega ao Claude e o `reason` não entra no contexto (o stderr do exit 2 vai pelo mesmo caminho). No `UserPromptSubmit`, `suppressOriginalPrompt: true` tira o texto do prompt da mensagem de bloqueio. Nos eventos de ferramenta e no Stop, o Claude lê |
| `PreToolUse` | `hookSpecificOutput.permissionDecision`: `allow`\|`deny`\|`ask`\|`defer`, com precedência deny > defer > ask > allow; mais `permissionDecisionReason`, `updatedInput` (substitui o input inteiro) e `additionalContext`. O `approve`/`block` de topo está depreciado |
| `PermissionRequest` | `hookSpecificOutput.decision.behavior`: `allow`\|`deny`, com `updatedInput`, `updatedPermissions`, `message`, `interrupt` |
| `PostToolUse` | também `updatedToolOutput` (no formato da ferramenta) e `classifierContext` |
| `TaskCreated` | exit 2 ou `decision: "block"` |
| `TeammateIdle`, `TaskCompleted` | exit 2 ou `continue: false` |
| `SessionStart`, `SubagentStart`, `PostModelSwitch` | só contexto. O SessionStart aceita ainda `initialUserMessage`, `sessionTitle`, `watchPaths` e `reloadSkills` |
| `Setup`, `Notification`, `SessionEnd`, `PostCompact`, `InstructionsLoaded`, `StopFailure`, `CwdChanged`, `DirectoryAdded`, `FileChanged` | nenhuma decisão: só efeito colateral |

**Stop e SubagentStop** têm duas formas de fazer o Claude continuar. As duas passam pela
guarda de `stop_hook_active` e pelo teto de 8:

- `{"decision":"block","reason":"…"}`: o `reason` é a instrução, e o transcript mostra
  **hook error**. Serve para "isto está errado, corrija".
- `{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"…"}}` (2.1.163+):
  aparece como **Stop hook feedback**, sem erro. A doc indica essa forma quando o hook "está
  funcionando como projetado e dá orientação ao Claude".

## 6. `additionalContext`

É embrulhado como system reminder e entra no ponto em que o hook disparou:

| Evento | Onde entra |
|---|---|
| `SessionStart`, `SubagentStart` | no começo |
| `UserPromptSubmit`, `UserPromptExpansion` | junto do prompt |
| `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch` | junto do resultado da ferramenta |
| `Stop`, `SubagentStop` | no fim do turno, e a conversa continua |
| `PostModelSwitch` | no próximo request |

Escreva **fatos**, não ordens de sistema. Um texto com cara de comando fora de banda pode
disparar a defesa contra prompt injection, e aí o Claude mostra o texto para você em vez de
usá-lo. Quando vários hooks do mesmo evento devolvem `additionalContext`, o Claude recebe
todos. No `--resume`, o texto dos eventos do meio da sessão é **reaproveitado** do transcript,
não recalculado. Um valor que envelhece, como o SHA, deve ser recalculado no `SessionStart` com
`source: resume`.
