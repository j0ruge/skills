# Tipos de handler: custo, limite e quando usar

Fonte: https://code.claude.com/docs/en/hooks#hook-handler-fields, `#prompt-based-hooks`,
`#agent-based-hooks` e `#run-hooks-in-the-background` (lido em 2026-09-30, Claude Code 2.1.283;
timeouts e limites reconferidos contra a doc em 2026-10-07, com a 2.1.291 instalada).

## Escolha rápida

| Tipo | Use quando | Custo por disparo | Timeout padrão |
|---|---|---|---|
| `command` | a regra é determinística (regex, arquivo, estado, git) | um processo | 600 s (30 s em `UserPromptSubmit`, `Pre/PostModelSwitch`; 10 s em `MessageDisplay`) |
| `http` | a decisão mora num serviço | uma requisição | 600 s (30 s e 10 s nos mesmos eventos do `command`) |
| `mcp_tool` | a decisão é uma ferramenta de um servidor MCP já configurado | uma chamada MCP | 600 s (30 s e 10 s nos mesmos eventos do `command`) |
| `prompt` | é preciso **juízo** sobre o input do hook, e o input basta | uma chamada ao modelo de background | 30 s |
| `agent` | o juízo exige ler arquivo ou rodar teste | até 50 turnos de subagente | 60 s |

Padrão: comece por `command`. `prompt` e `agent` no `Stop` atrasam o fim de **todo** turno,
e o `Stop` dispara ao fim de cada resposta, não só no fim da tarefa. Um filtro determinístico
que decide "vale chamar o modelo?" só existe dentro de um `command`, porque os hooks do mesmo
evento rodam **em paralelo** e um não pode ligar o outro.

## Campos comuns

`type` (obrigatório), `if` (só em evento de ferramenta), `timeout` (segundos),
`statusMessage` (texto do spinner) e `once` (só respeitado em frontmatter de skill).

## `command`

| Campo | Nota |
|---|---|
| `command` | na forma shell é a linha inteira; na forma exec, só o executável |
| `args` | se presente, **forma exec**: sem shell, e cada item é um argumento literal. Recomendada sempre que houver `${CLAUDE_PLUGIN_ROOT}` e afins |
| `shell` | `bash` (padrão) ou `powershell`. Ignorado com `args` |
| `async` | roda em background. **Não decide nada** (`decision`, `permissionDecision` e `continue` não têm efeito). O `additionalContext` e o `systemMessage` chegam no próximo turno. O `timeout` não é aplicado. Não há deduplicação entre disparos. No `-p`, é morto no fim |
| `asyncRewake` | roda em background e **acorda o Claude com exit 2**, mostrando o stderr (ou o stdout) como system reminder. O `timeout` é aplicado |

Forma shell: `sh -c` no Linux/macOS e Git Bash no Windows. Um profile que faz `echo` sem
`[[ $- == *i* ]]` suja o stdout e quebra o JSON. Forma exec no Windows exige um `.exe` real
(`.cmd` e `.bat` só funcionam em shell). Para Node, use `"command": "node", "args": [script]`.

Os campos `rewakeMessage` e `rewakeSummary` aparecem no plugin oficial `security-guidance`,
mas **não estão na referência**. Não dependa deles sem capturar o efeito.

## `http`

`url`, `headers` (com interpolação de `$VAR`, liberada por `allowedEnvVars`). O status HTTP
sozinho não bloqueia: responda 2xx com o mesmo JSON de saída dos command hooks. Em settings
gerenciado, `allowedHttpHookUrls` e `httpHookAllowedEnvVars` restringem.

## `mcp_tool`

`server`, `tool`, `input` (aceita `${tool_input.file_path}`). A saída de texto da ferramenta é
lida como stdout de command hook. Servidor de plugin: `plugin:<plugin>:<servidor>`. Não roda
no `SessionStart` de abertura nem no `Setup`, porque os servidores ainda não conectaram.

## `prompt`

`prompt` (use `$ARGUMENTS`; sem ele, o JSON de input é anexado ao fim), `model` (padrão: o
modelo de background), `continueOnBlock`. O modelo responde:

```json
{ "ok": true, "reason": "obrigatório quando ok=false", "impossible": false }
```

O que `ok: false` faz depende do evento:
- **`Stop`/`SubagentStop`:** o `reason` vira a próxima instrução e o turno continua. Se
  `impossible: true`, o turno termina.
- **`PreToolUse`:** nega a ferramenta e **encerra o turno**, a menos que `continueOnBlock: true`.
- **`PostToolUseFailure`, `TaskCreated`:** vira erro de ferramenta e o turno continua.
- **`PermissionRequest`, `PermissionDenied`:** sem efeito. Use command hook.

O modelo recebe **só o JSON do hook**. No Stop, isso é o `last_assistant_message` e o
`transcript_path` como string. Ele não lê o transcript. O `/goal` é um prompt hook de Stop
com escopo de sessão.

## `agent` (experimental)

A doc diz: "For production workflows, prefer command hooks". O subagente usa Read, Grep e Glob,
faz até 50 turnos e responde `{ok, reason}`, sem `impossible` e sem `continueOnBlock`. Um
`ok: false` é tratado como prompt hook com `continueOnBlock: true`. Não roda em
`PermissionRequest`.

## Paralelismo e deduplicação

Todos os hooks que casam com um evento rodam **em paralelo**. O mesmo handler definido em mais
de um arquivo de settings roda uma vez, mas a cópia de um plugin ou de uma skill fica separada.
Com vários `updatedInput`, vence o último a terminar, em ordem não determinística. Um `deny`
de um hook não impede os efeitos colaterais dos irmãos.
