# Eventos de hook: os 33

Fonte: https://code.claude.com/docs/en/hooks#hook-lifecycle, `#matcher-patterns`,
`#exit-code-2-behavior-per-event` e `#prompt-based-hooks` (lido em 2026-09-30, Claude Code 2.1.283).
Para ver o que chega de verdade num evento, rode `scripts/capture_payload.py`. Os eventos
PreToolUse, PostToolUse, PostToolUseFailure, UserPromptSubmit, UserPromptExpansion, SessionStart e
Stop foram capturados assim em 2026-09-30, e as fixtures estão em `assets/fixtures/`.

Legenda da coluna **Tipos**: `todos` = command, http, mcp_tool, prompt, agent · `sem modelo` =
command, http, mcp_tool · `cmd+mcp` = command, mcp_tool.

| Evento | Quando dispara | Matcher filtra | Exit 2 | Tipos |
|---|---|---|---|---|
| `SessionStart` | sessão começa ou retoma | `startup` `resume` `clear` `compact` `fork` | não bloqueia; stderr ao usuário | cmd+mcp |
| `Setup` | `--init-only`, ou `-p --init` / `-p --maintenance` | `init` `maintenance` | ignorado | cmd+mcp |
| `UserPromptSubmit` | você envia um prompt, antes do Claude | — | rejeita o prompt | todos |
| `UserPromptExpansion` | um `/comando` ou `/skill` digitado se expande | nome do comando | bloqueia a expansão | todos |
| `PreToolUse` | antes de uma ferramenta (menos `EndConversation`) | nome da ferramenta | bloqueia a chamada | todos |
| `PermissionRequest` | a chamada precisa de decisão de permissão | nome da ferramenta | **não** respeitado; use o objeto `decision` | todos menos agent |
| `PermissionDenied` | o modo auto nega uma chamada | nome da ferramenta | ignorado; `retry: true` no JSON | todos |
| `PostToolUse` | depois de uma ferramenta **bem-sucedida** | nome da ferramenta | stderr ao Claude (a ferramenta já rodou) | todos |
| `PostToolUseFailure` | depois de uma ferramenta que **falhou** | nome da ferramenta | stderr ao Claude | todos |
| `PostToolBatch` | um lote paralelo inteiro termina, antes da próxima chamada ao modelo | — | para o loop | todos |
| `Notification` | o Claude Code envia notificação | `permission_prompt` `idle_prompt` `auth_success` `elicitation_*` `agent_needs_input` `agent_completed` `quota_auto_resume_*` | ignorado | sem modelo |
| `MessageDisplay` | enquanto o texto do assistente é exibido | — | exibe o original | sem modelo |
| `SubagentStart` | um subagente nasce | tipo do agente (`^plugin:nome$` para agente de plugin) | stderr só ao usuário | sem modelo |
| `SubagentStop` | um subagente termina | tipo do agente | impede o subagente de parar | todos |
| `TaskCreated` | `TaskCreate` cria uma tarefa | — | desfaz a criação | todos |
| `TaskCompleted` | uma tarefa vai ser marcada concluída | — | impede a conclusão | todos |
| `Stop` | o Claude termina de responder (não roda em interrupção do usuário) | — | o Claude continua | todos |
| `StopFailure` | o turno termina por erro de API | `rate_limit` `overloaded` `billing_error` … | ignorado (só `terminalSequence`) | sem modelo |
| `TeammateIdle` | um teammate de agent team vai ficar ocioso | — | o teammate continua | todos |
| `InstructionsLoaded` | um CLAUDE.md ou `.claude/rules/*.md` carrega | `session_start` `nested_traversal` `path_glob_match` `include` `compact` | ignorado | sem modelo |
| `ConfigChange` | um arquivo de settings ou de skill muda na sessão | `user_settings` `project_settings` `local_settings` `policy_settings` `skills` | bloqueia a mudança (menos `policy_settings`) | sem modelo |
| `CwdChanged` | o diretório de trabalho muda | — | stderr ao usuário | sem modelo |
| `DirectoryAdded` | `/add-dir` ou `register_repo_root` | `slash_command` `register_repo_root` | debug log | sem modelo |
| `FileChanged` | um arquivo vigiado muda no disco | nomes literais (`.envrc\|.env`) | stderr ao usuário | sem modelo |
| `WorktreeCreate` | um worktree vai ser criado | — | qualquer não-zero falha a criação | sem modelo |
| `WorktreeRemove` | um worktree vai ser removido | — | qualquer não-zero falha a remoção | sem modelo |
| `PreCompact` | antes da compactação | `manual` `auto` | bloqueia a compactação | sem modelo |
| `PostCompact` | depois da compactação | `manual` `auto` | stderr ao usuário | sem modelo |
| `PreModelSwitch` | antes de uma troca de modelo pedida | nome canônico do modelo | bloqueia a troca | sem modelo |
| `PostModelSwitch` | depois que o modelo muda | nome canônico do modelo | stderr ao usuário | sem modelo |
| `Elicitation` | um servidor MCP pede input no meio de uma ferramenta | nome do servidor MCP | nega a elicitação | sem modelo |
| `ElicitationResult` | depois da resposta do usuário à elicitação | nome do servidor MCP | a resposta vira `decline` | sem modelo |
| `SessionEnd` | a sessão termina | `clear` `resume` `logout` `prompt_input_exit` `other` | stderr ao usuário | sem modelo |

## Regras de matcher

- `"*"`, `""` ou ausente: casa tudo.
- **Lista exata:** se o valor só tem letras, dígitos, `_`, `-`, espaço, `,` e `|`, é uma string
  exata ou uma lista de strings exatas. `Edit|Write` e `Edit, Write` são equivalentes.
- **Regex:** qualquer outro caractere transforma o valor em regex JavaScript **sem âncora**.
  `Edit.*` também casa `NotebookEdit`. Use `^…$` para casar a string inteira.
- `FileChanged` e `StopFailure` só aceitam letras, dígitos, `_` e `|` no modo exato.
- Ferramenta MCP se chama `mcp__<servidor>__<ferramenta>`, e a de plugin
  `mcp__plugin_<plugin>_<servidor>__<ferramenta>`. Para um servidor inteiro: `mcp__memory__.*`.
- Um matcher num evento sem suporte a matcher é **ignorado em silêncio**. O `lint_hooks.py`
  avisa.
- **`if`**, que filtra por nome + argumento com a sintaxe de permissão (`Bash(git *)`,
  `Edit(*.ts)`), só é avaliado em `PreToolUse`, `PostToolUse`, `PostToolUseFailure`,
  `PermissionRequest` e `PermissionDenied`. Em qualquer outro evento, o hook com `if` **nunca
  roda**. É uma regra só, sem `&&`, e best-effort.

## Os dois caminhos de uma skill

- **Claude chama a skill:** vira uma chamada da ferramenta `Skill`, com `tool_input` =
  `{"skill": "<plugin>:<nome>" | "<nome>", "args": "…"}`. O `PreToolUse` e o `PostToolUse` com
  `matcher: "Skill"` veem essa chamada. O `if` aceita `Skill(nome)`.
- **Qual forma de nome aparece:**
  - skill ou comando de **plugin** vem sempre com o prefixo (`codereview:coderabbit-pr`);
  - skill **pessoal** (`~/.claude/skills/<n>`) ou de **projeto** (`.claude/skills/<n>`) vem com
    o nome puro (`ticket`).

  O nome puro não diz de onde a skill veio. Para isso, use o path da linha `Base directory`.
- **Você digita `/skill`:** o caminho não passa pela ferramenta. Só `UserPromptExpansion` vê,
  com `command_name`, `command_args` e `command_source` (valores capturados: `projectSettings`,
  `plugin`).
- **Nos dois caminhos**, o transcript ganha uma entrada `type: "user"`, `isMeta: true`, cujo
  texto começa com `Base directory for this skill: <path absoluto>`. Esse é o único sinal que
  traz o **path** da skill. Um plugin só de comandos não grava essa linha. Como ler o transcript
  com segurança está em `patterns.md`.
