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

O Codex só roda o hook de plugin que tem trust gravado no `config.toml` do `CODEX_HOME`. Hook sem
trust é pulado sem erro. O `install --codex` grava esse trust, e o `--dangerously-bypass-hook-trust`
do `codex exec` (usado na captura) vale só para aquela invocação. O algoritmo abaixo foi lido no
codex-rs na tag `rust-v0.164.0` e conferido contra o próprio Codex: o pacote sintético de
`tests/fixtures/codex-hooks-list-dourado.json` foi instalado pelo `codex plugin add`, e o
`currentHash` que o `hooks/list` do `codex app-server` devolveu para cada hook é o que o teste
compara.

| Peça | Regra | Fonte (`codex-rs/`, tag `rust-v0.164.0`) |
|---|---|---|
| chave | `[hooks.state."<plugin_id>:hooks/hooks.json:<evento snake_case>:<índice do grupo>:<índice do handler>"]`; o `plugin_id` é `<plugin>@<loja>` | `hooks/src/lib.rs:100-130`, `hooks/src/declarations.rs:35-37` |
| campos | `trusted_hash` (a declaração) e `trusted_content_hash` (o pacote); `enabled` fica como está | `config/src/hook_config.rs:28-36` |
| hash da declaração | `{event_name, matcher, hooks: [handler]}` sem os campos nulos, em JSON com chaves ordenadas e sem espaço, no sha256 | `hooks/src/engine/discovery.rs:868-891`, `config/src/fingerprint.rs:54-66` |
| handler normalizado | `type`, `command` (o texto cru, com `${CLAUDE_PLUGIN_ROOT}` sem expandir), `timeout` (padrão 600; SessionEnd e Interrupt, 1 a 3), `async` (sempre presente) e `statusMessage` se houver; `commandWindows` sai | `hooks/src/engine/discovery.rs:545-622`, `:841-863` |
| matcher | descartado em Stop, UserPromptSubmit, Pre/PostModelRequest e Interrupt; nos outros, o texto como está (`*` incluído) | `hooks/src/events/common.rs:114-134` |
| impressão do pacote | sha256 de `codex-plugin-bundle-v1` e de cada entrada da pasta instalada, em pré-ordem, nomes em ordem de bytes: tamanho u64 LE + caminho relativo, e `directory` ou `file` + tamanho + bytes. Pula `__pycache__`, `.venv`, `*.pyc`, `*.egg-info`; symlink é erro | `hooks/src/engine/plugin_fingerprint.rs:15-91` |
| conferência | a cada execução o Codex recalcula a impressão; diferente do `trusted_content_hash`, o hook falha com "plugin contents changed; hook approval required" | `hooks/src/engine/plugin_trust.rs:28-69` |
| quem grava | o `/hooks` grava `trusted_hash = "<declaração>/<conteúdo>"`, e o config writer parte nos dois campos | `app-server/src/config_manager_service.rs:364-390` |
| versão ativa | a pasta de versão em `plugins/cache/<loja>/<plugin>/`; o `install` recusa quando há mais de uma | `core-plugin-common/src/installed.rs:47-68` |

**Medido em 2026-10-27** (codex-cli 0.164.0, `CODEX_HOME` descartável, sandbox apontado para a
página sintética do KB de staging), sem `--dangerously-bypass-hook-trust`:

| Caso | Resultado |
|---|---|
| `install --codex --apply` e `hooks/list` | os 4 hooks `trusted` |
| `codex exec` com `apply_patch` e com `echo >>` | o hook roda e sincroniza; o estado nasce na pasta de dados do Codex |
| `codex plugin add` de novo, mesmo conteúdo | continua `trusted` |
| `codex plugin remove` + `add`, mesmo conteúdo | continua `trusted`: o `remove` apaga o `[plugins."<id>"]`, mas não o `[hooks.state]` |
| um byte mudado no pacote (update) e `add` | `modified`; cada hook sai `Failed` no `codex exec` e a página não muda, até o `install --codex` rodar de novo, que troca só os `trusted_content_hash` |

O que o `codex exec` mostra: sem `--json`, o stderr tem `hook: <evento>` e `hook: <evento>
Completed` (ou `Failed`), mas **não** o `systemMessage`; com `--json`, nenhum evento de hook. A prova
de que o hook rodou é o estado na pasta de dados e a revisão da página.

**Oráculo para a próxima versão do Codex.** O `codex app-server` fala JSON-RPC por linha no stdio:
`initialize` (com `clientInfo` e `capabilities.experimentalApi: true`), a notificação `initialized`
e `hooks/list` com `{"cwds": [<pasta>]}`. Cada hook da resposta traz `key`, `trustStatus` e
`currentHash` (`<declaração>/<conteúdo>`). Reinstale o pacote dourado num `CODEX_HOME` descartável,
compare os `currentHash` com a fixture e, se mudarem, refaça a fixture e o algoritmo.

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

- O trust gravado numa sessão **interativa** do Codex (TUI). O `codex exec` honrou o trust gravado,
  e a descoberta dos hooks é a mesma; o `/hooks` da TUI não foi aberto.
- O `codex plugin marketplace upgrade` de uma loja git (só a loja local foi medida, por reinstall).
- macOS e Windows. No Windows, o Codex usa `commandWindows`, que o `hooks.json` não define.
