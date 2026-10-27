# Codex CLI — o mesmo contrato, com diferenças que mordem

O Codex CLI tem hooks no mesmo formato do Claude Code: evento, JSON no stdin, exit code e JSON no
stdout, configurados num `hooks.json` com `{"hooks": {Evento: [{matcher, hooks: [handler]}]}}`. Um
hook bem feito pode servir aos dois hosts. As diferenças abaixo são as que fazem o hook ficar mudo
num deles.

Fontes:
- doc oficial: https://learn.chatgpt.com/docs/hooks (lida em 2026-10-27);
- código na tag `rust-v0.164.0` de https://github.com/openai/codex, com o arquivo e a linha de cada fato;
- dois probes ao vivo (`codex-cli 0.164.0` e `Claude Code 2.1.309`, 2026-10-27), que viraram as fixtures `assets/fixtures/codex-*.json`.

Versão local: `codex --version`. Quando a doc e o código divergirem do que está aqui, vale o código
da versão instalada. Registre a divergência no arquivo de fontes desatualizadas da skill.

## 1. Onde mora a config

| Local | Quando carrega |
|---|---|
| `~/.codex/hooks.json` ou `[hooks]` no `~/.codex/config.toml` | sempre (usuário) |
| `<repo>/.codex/hooks.json` ou `[hooks]` no `<repo>/.codex/config.toml` | só com a camada `.codex/` do projeto **confiável** |
| plugin: `hooks/hooks.json` ou a entrada `hooks` do manifesto | com o plugin habilitado, e ainda depende do trust (§5) |

O `hooks.json` aceita só `description` e `hooks` no topo (`HooksFile` com `deny_unknown_fields`,
`config/src/hook_config.rs:10-17`). Um settings do Claude com `permissions` ao lado é recusado.

## 2. Eventos

São 14 no config (`HookEventsToml`, `hook_config.rs:38-66`). A doc lista 12, e `PreModelRequest`
e `PostModelRequest` existem só no código: trate esses dois como instáveis.

| Codex | No Claude Code |
|---|---|
| `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `SubagentStart`, `SubagentStop`, `Stop` | mesmo nome |
| `Interrupt` | não existe |
| `PreModelRequest`, `PostModelRequest` | não existem (sem doc no Codex) |
| — | `PostToolUseFailure`, `PostToolBatch`, `UserPromptExpansion`, `FileChanged` e os demais: **não existem no Codex** |

O matcher é ignorado em `UserPromptSubmit`, `Stop` e `Interrupt`. Ferramentas hospedadas (como o
`WebSearch`) não passam pelo caminho de hook, e a doc avisa que "some specialized tool paths can
opt out". Hook de ferramenta é guarda útil, não fronteira completa.

## 3. Handler

`HookHandlerConfig` (`hook_config.rs:178-218`):

| `type` | Campos | No Codex |
|---|---|---|
| `command` | `command`, `commandWindows`, `timeout` (inteiro, s), `async`, `statusMessage`, `additionalContextLimit` | roda |
| `mcp_tool` | `server`, `tool`, `input`, `timeout`, `statusMessage` | roda |
| `prompt`, `agent` | — | lido e **pulado** |
| `http` | — | não existe |

- **Não existe `args`.** O handler não tem `deny_unknown_fields`, então a chave é ignorada e o
  `command` roda **sem os argumentos**. Um `{"command": "python3", "args": ["hook.py"]}` vira
  `python3` lendo o JSON do stdin como código. Use a forma shell.
- **`if` e `once` também são ignorados.** Um `if` do Claude vira "roda em toda chamada do
  matcher".
- **`timeout`:** o padrão é 600 s. Em `SessionEnd` e `Interrupt`, é 1 s. O comando roda com o
  `cwd` da sessão. O Codex não define `CLAUDE_PROJECT_DIR`.
- **`async: true`** roda em background, como no Claude.

## 4. Plugin

O Codex põe no ambiente do hook de plugin `PLUGIN_ROOT`, `PLUGIN_DATA`, `CLAUDE_PLUGIN_ROOT` e
`CLAUDE_PLUGIN_DATA`, e substitui `${CHAVE}` dessas quatro **dentro da string** do `command`
(`hooks/src/engine/discovery.rs:299-307,608-610`). Por isso
`"command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/hook.py\""` funciona nos dois hosts. Instalar
ou habilitar o plugin não dá trust aos hooks dele.

## 5. Trust

Todo hook que não é managed precisa de trust na definição **exata**. O Codex guarda o hash em
`[hooks.state."<id>"] trusted_hash` no `config.toml`. O estado sai de
`hook_trust_status` (`discovery.rs:893-910`):

| Situação | Estado | Efeito |
|---|---|---|
| hash igual ao gravado | `Trusted` | roda |
| hash diferente | `Modified` | pulado até revisar |
| sem hash | `Untrusted` | pulado até revisar |
| managed (system, MDM, cloud, `requirements.toml`) ou builtin | `Managed`/`Trusted` | roda |

- **Hook pulado não dá erro:** ele simplesmente não aparece. Revise e aprove em `/hooks` no CLI.
- **Automação:** `codex exec --dangerously-bypass-hook-trust` roda os hooks habilitados sem trust
  gravado, só naquela invocação (`utils/cli/src/shared_options.rs:61-64`). Serve para capturar
  payload e para E2E; numa sessão interativa normal, o trust continua valendo.

## 6. Nomes de ferramenta e matcher

O matcher é regex sobre o nome da ferramenta, e alguns nomes têm alias de compatibilidade
(`core/src/tools/hook_names.rs`):

| No payload (`tool_name`) | O matcher também casa | Fonte |
|---|---|---|
| `apply_patch` (edição de arquivo) | `Write`, `Edit` | `hook_names.rs:28-37` |
| `Bash` (shell) | — | `hook_names.rs:55` |
| subagente | `Agent` | `hook_names.rs:44-49` |

Então `"matcher": "Write|Edit"` pega a edição nos dois hosts, mas o script recebe
`tool_name: "apply_patch"` no Codex e `Write`/`Edit` no Claude. Trate os dois.

## 7. Payload real (codex-cli 0.164.0, capturado em 2026-10-27)

Campos comuns: `session_id`, `transcript_path`, `cwd`, `hook_event_name`, `model`,
`permission_mode`; `turn_id` nos eventos de turno. Não há `prompt_id` nem `duration_ms`.

| Evento | O que muda em relação ao Claude |
|---|---|
| `PostToolUse` + `apply_patch` | `tool_input` = `{"command": "<texto do patch>"}`; `tool_response` é **texto** (`Exit code: 0 … Success. Updated the following files:\nA <caminho>`) |
| `PostToolUse` + `Bash` | `tool_input` = `{"command": "…"}`; `tool_response` é texto (vazio quando o comando não imprime) |
| `Stop` | `stop_hook_active` e `last_assistant_message`, como no Claude |
| `SessionStart` | `source` (`startup`, …) |

Os caminhos editados ficam nas linhas `*** Add File: `, `*** Update File: `, `*** Delete File: `
e `*** Move to: ` do patch (`apply-patch/src/parser.rs:39-42`). No probe, o caminho veio
**absoluto**. Aceite absoluto e relativo ao `cwd`:

```python
MARKERS = ("*** Add File: ", "*** Update File: ", "*** Delete File: ", "*** Move to: ")
def patch_paths(patch, cwd):
    for line in patch.splitlines():
        for m in MARKERS:
            if line.startswith(m):
                p = line[len(m):].strip()
                yield p if os.path.isabs(p) else os.path.join(cwd, p)
```

No Claude, o caminho é `tool_input.file_path`, absoluto, em `Write` e `Edit` (fixtures
`posttooluse-write.json` e `posttooluse-edit.json`, 2.1.309). O `MultiEdit` não apareceu na
2.1.309: nem a doc nem a lista de ferramentas o citam. Não conte com ele no matcher.

⚠️ **O payload carrega o conteúdo.**
- No Claude: `tool_input.content` e `tool_response.originalFile` no `Write`/`Edit`.
- No Codex: as linhas `+…` do patch.

Um hook que loga o stdin grava o arquivo inteiro. Para vigiar arquivo com segredo, use a receita
de "hook que trata arquivo de segredo de propósito" da reference de segurança (§9).

## 8. Um `hooks.json` para os dois hosts

- **Forma shell** com o placeholder entre aspas. Nada de `args`.
- **Só eventos que existem nos dois** (tabela do §2), e sem `if` nem `once`.
- `timeout` inteiro. Topo só com `description` e `hooks`.
- **Matcher de edição:** `Write|Edit` (o Codex mapeia o `apply_patch`). Shell: `Bash`.
- **Teste:** `python3 scripts/lint_hooks.py hooks/hooks.json --host both`.
- **No plugin:** o Codex lê o mesmo `hooks/hooks.json`, mas ainda exige o trust de cada hook (§5).

## 9. Capturar e testar no Codex

```bash
T=$HOME/.wt/codex-probe; mkdir -p "$T/home" "$T/out" "$T/work"   # fora do /tmp (abaixo)
ln -s ~/.codex/auth.json "$T/home/auth.json"                     # só a credencial, sem a config pessoal
python3 scripts/capture_payload.py --print-config PostToolUse,Stop "$T/out" --host codex > "$T/home/hooks.json"
cd "$T/work" && git init -q
CODEX_HOME="$T/home" codex exec --yolo --dangerously-bypass-hook-trust --skip-git-repo-check \
  -C "$T/work" "use apply_patch para criar demo.txt com a linha x=1 e responda ok" < /dev/null
ls "$T/out"    # stdin-PostToolUse-*.json reais
```

- **`< /dev/null` é obrigatório.** Sem ele, o `codex exec` fica em `Reading additional input from
  stdin...` até o timeout (medido: rc 124).
- **`CODEX_HOME` sob `/tmp`** dá `Refusing to create helper binaries under temporary dir`.
  Prefira `$HOME/.wt/...`.
- **`--yolo`** é alias de `--dangerously-bypass-approvals-and-sandbox` (`shared_options.rs:53-59`).
  Use só numa pasta descartável.
- **Herança de ambiente.** Um Codex lançado de dentro do Claude herda o `CLAUDE*` do processo pai,
  e o `env-*.txt` mostra `CLAUDECODE=1`. Isso não vem do Codex.
- **Ao vivo:**
  1. confira o hook em `/hooks` (trust);
  2. dispare numa sessão real;
  3. veja o efeito: arquivo de estado, `systemMessage`, `additionalContext`;
  4. rode o caso negativo, em que o mesmo comando, sem a condição, não dispara.
