# Hosts: o que o hook recebe e onde o estado mora

Medido em 2026-10-27 no Linux, com o **Claude Code 2.1.309** e o **codex-cli 0.164.0**. A captura
usou o `capture_payload.py` da skill hook-builder, instalado **como plugin** com o mesmo
`hooks/hooks.json` deste plugin (matchers e eventos iguais, só o `command` trocado). Só hook de
plugin recebe as variáveis da pasta de dados, por isso um probe em settings não serviria. Cada
host rodou com o ambiente limpo (`env -i HOME PATH USER LANG TERM`, mais `CODEX_HOME` no Codex):
nenhuma variável `CLAUDE*` veio herdada de um processo pai.

As capturas, anonimizadas, são as fixtures de `tests/fixtures/` (caminhos trocados pela raiz
genérica `<HOME>/my-project`, ids por zeros, `permission_mode` por `default`). `claude-stop-active.json` é a única derivada: é o
`claude-stop.json` com `stop_hook_active: true`.

## 1. Payload por gatilho

Campos comuns aos dois: `session_id`, `transcript_path`, `cwd`, `hook_event_name`. O Claude Code
acrescenta `prompt_id`, `effort` e `permission_mode` (no SessionStart, só `source`); o PostToolUse
dele traz `duration_ms`. O Codex acrescenta `model`, `permission_mode` e, nos eventos de turno,
`turn_id`.

| Gatilho | Claude Code | Codex CLI |
|---|---|---|
| edição | `tool_name` `Write` ou `Edit`; `tool_input.file_path` **absoluto**. O `Write` traz `content`; o `Edit`, `old_string`/`new_string`/`replace_all`. O `tool_response` é objeto e traz `originalFile` | `tool_name` `apply_patch`; `tool_input.command` é o texto do patch, com o caminho **absoluto** em `*** Update File:` e `*** Add File:`. O `tool_response` é texto |
| shell | `tool_name` `Bash`; `tool_input` = `{command, description}`; `tool_response` objeto (`stdout`, `stderr`, …) | `tool_name` `Bash`; `tool_input` = `{command}`; `tool_response` texto (vazio quando o comando não imprime) |
| `Stop` | `stop_hook_active`, `last_assistant_message`, `background_tasks`, `session_crons` | `stop_hook_active`, `last_assistant_message` |
| `SessionStart` | `source` (`startup` na captura) | `source` (`startup`), `model` |

O payload de edição carrega o conteúdo do arquivo nos dois hosts. O hook usa só o caminho e o
comando (`ler_gatilho`), e o conteúdo vem do disco.

## 2. Ambiente do processo do hook

| Variável | Claude Code | Codex CLI |
|---|---|---|
| `CLAUDE_PLUGIN_ROOT` | a pasta do plugin (com `--plugin-dir`, a própria pasta) | `$CODEX_HOME/plugins/cache/<loja>/<plugin>/<versão>` |
| `CLAUDE_PLUGIN_DATA` | `~/.claude/plugins/data/<plugin>-inline` com `--plugin-dir`; a pasta **existe** antes do hook rodar | `$CODEX_HOME/plugins/data/<plugin>-<loja>`; a pasta **não existe** até alguém criá-la |
| `PLUGIN_ROOT`, `PLUGIN_DATA` | ausentes | presentes, com os mesmos valores das `CLAUDE_*` |
| `CLAUDE_PROJECT_DIR` | a raiz do projeto | ausente |
| outras | `CLAUDE_CODE_SESSION_ATTENDED` (`0` no `-p`), `CLAUDE_CODE_ENTRYPOINT`, `CLAUDE_ENV_FILE` no SessionStart | `CODEX_HOME` |

O que isso decide:

- `pasta_de_estado()` procura `CLAUDE_PLUGIN_DATA` primeiro: é a única que os dois hosts definem.
  `PLUGIN_DATA` fica como segunda opção, e o fallback `$XDG_STATE_HOME/env-docs-sync` (ou
  `~/.local/state/env-docs-sync`) atende a CLI à mão e um hook registrado fora do plugin.
- A gravação do estado cria a pasta (`mkdir -p`, 0700), porque o Codex não cria.
- Cada host tem a sua pasta, e os estados não se veem. A mesma mudança é sincronizada uma vez por
  host, e o destino precisa reconhecer conteúdo igual como "sem mudança".
- Com o plugin instalado pela loja no Claude Code, a pasta é `~/.claude/plugins/data/<id>/` (a
  reference de empacotamento da skill hook-builder). Só o caso `--plugin-dir` foi medido aqui.

## 3. Matcher e saída

- **`Write|Edit` é lista exata no Claude Code** (só letras e `|`): não casa `TodoWrite` nem
  `NotebookEdit`. No Codex, o `apply_patch` casa por alias: os três `apply_patch` da captura
  dispararam, inclusive o de `app.txt`, que não é `.env*`. Quem filtra é o script
  (`_algum_vigiado`), não o matcher.
- **`MultiEdit`** não existe no Claude Code 2.1.309 (a skill hook-builder registra isso), e o
  matcher não o cita.
- **Saída.** O schema de saída do Codex 0.164.0 para PostToolUse, Stop e SessionStart aceita
  `systemMessage` e tem `additionalProperties: false`
  (`codex-rs/hooks/schema/generated/{post-tool-use,stop,session-start}.command.output.schema.json`,
  tag `rust-v0.164.0`). O hook escreve só `{"systemMessage": …}`, em JSON ASCII.
- **Síncrono.** Num hook `async` do Claude Code, o `systemMessage` vai para o Claude no turno
  seguinte, não para a pessoa; o processo também é morto no fim de um `claude -p` e o `timeout` não
  vale. O hook é síncrono, com `timeout` 120 em todos os handlers. O caminho sem mudança custou
  ~50 ms num repositório de 2 GB com `node_modules` (9 arquivos na Varredura, 2 chamadas de git).

## 4. Trust no Codex

A captura rodou com `codex exec --dangerously-bypass-hook-trust`, que vale só para aquela
invocação. Numa sessão interativa, o hook do plugin continua precisando de trust em `/hooks`, e o
hook sem trust é pulado sem erro. O `install --codex` (planejado) grava o `trusted_hash`. Se o
Codex honra o hash gravado antes da sessão, e se ele sobrevive a um update do plugin, ainda não
foi medido.

## 5. Receita de captura

Repita a cada versão nova de host. Use só `.env` sintético, porque o probe grava o stdin cru.

```bash
HB=<pasta da skill hook-builder>/scripts/capture_payload.py
W=$HOME/.wt/eds-probe                # fora do /tmp: o Codex recusa CODEX_HOME sob /tmp
# 1. repositório descartável, criado do zero, com .env sintético
# 2. plugin probe: .claude-plugin/plugin.json + hooks/hooks.json deste plugin, com o command
#    trocado por: python3 "${CLAUDE_PLUGIN_ROOT}/capture_payload.py" --capture "<pasta de saída>"
# 3. Claude Code, sem os settings do usuário:
env -i HOME="$HOME" PATH="$PATH" USER="$USER" LANG="$LANG" TERM=dumb \
  claude -p --setting-sources project,local --plugin-dir "$W/claude" \
  --permission-mode bypassPermissions --no-session-persistence "<Edit .env; Write .env.local; Bash; Edit app.txt>" < /dev/null
# 4. Codex, num CODEX_HOME descartável (auth.json linkado, config.toml só com o model):
#    uma loja local com .agents/plugins/marketplace.json e .claude-plugin/marketplace.json apontando o probe
CODEX_HOME=$W/codex-home codex plugin marketplace add "$W/market" --json
CODEX_HOME=$W/codex-home codex plugin add eds-probe@<loja> --json
env -i HOME="$HOME" PATH="$PATH" USER="$USER" LANG="$LANG" TERM=dumb CODEX_HOME=$W/codex-home \
  codex exec --yolo --dangerously-bypass-hook-trust --skip-git-repo-check -C <repo> "<apply_patch .env; …>" < /dev/null
```

Depois, anonimize (caminhos, ids, `permission_mode`) e confira que o sensor
`test_sem_marcas_da_empresa.py` continua verde.

## 6. Ainda não medido

- O disparo do hook **real** (não do probe) nos dois hosts, com o destino de verdade.
- O trust gravado pelo `install --codex` numa sessão interativa do Codex.
- macOS e Windows. No Windows, o Codex usa `commandWindows`, que o `hooks.json` não define.
