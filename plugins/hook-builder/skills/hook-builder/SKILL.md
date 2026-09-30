---
name: hook-builder
description: "Build, package and prove Claude Code hooks against the current official reference: right event and output channel, real payload capture, loop guards, plugin-data state, fixture tests and a live firing check. Triggers — hook, hooks.json, PreToolUse, PostToolUseFailure, Stop hook, UserPromptExpansion, SessionStart, plugin hook."
license: MIT
compatibility: Claude Code 2.1.163+ (Stop additionalContext); verificado contra a 2.1.283 em 2026-09-30. Scripts em Python 3, só biblioteca padrão.
metadata:
  author: JorUge
  version: "0.1.0"
---

# hook-builder

Um hook é um contrato: o Claude Code dispara um **evento**, entrega um JSON no stdin, e o
hook responde com **exit code** e, opcionalmente, **JSON no stdout**. O teste com pipe passa
com qualquer evento e qualquer campo. O erro só aparece na sessão real, quando o hook fica
mudo: evento errado, canal de saída errado ou campo inventado. Esta skill existe para acertar
essas três escolhas antes de escrever código e para provar que o hook dispara de verdade.

Fonte de verdade: https://code.claude.com/docs/en/hooks e `/en/hooks-guide` (lidos em
2026-09-30, Claude Code 2.1.283). Quando algo aqui divergir da doc, vale a doc. Registre a
divergência, quando achar uma, em `references/outdated-sources.md`.

## Quando usar

- "Sempre que X, faça Y" no Claude Code: formatar depois de editar, barrar um comando, injetar
  contexto no início da sessão, revisar algo no fim do turno, avisar quando uma skill roda.
- Empacotar um hook num plugin (`hooks/hooks.json`) ou no frontmatter de uma skill.
- Diagnosticar um hook que "não dispara", dispara em loop ou mostra "hook error".

**Não use hook para:**

- **Regra que nunca muda.** Vai no `CLAUDE.md`, que carrega sem rodar script.
- **Allow/deny rígido.** Use `permissions.deny` / `permissions.allow`. O `if` de hook é
  best-effort (a própria doc diz), e um gate que expira ou não sobe deixa a ação passar.
  Hook complementa a permissão; não a substitui.

## Workflow

### 1. Escolha o evento pelo que ainda dá para mudar

| Quer... | Evento | Observação |
|---|---|---|
| impedir uma ferramenta | `PreToolUse` | exit 2 ou `permissionDecision: "deny"`. É best-effort (wrapper e `eval` passam): o deny rígido vai em `permissions.deny` |
| reagir a uma ferramenta que **deu certo** | `PostToolUse` | não dispara em falha |
| reagir a uma ferramenta que **falhou** | `PostToolUseFailure` | recebe `error` e `is_interrupt` |
| agir sobre um lote paralelo inteiro | `PostToolBatch` | uma vez por lote |
| barrar ou enriquecer um prompt | `UserPromptSubmit` | não reescreve o prompt |
| reagir a `/comando` ou `/skill` **digitado** | `UserPromptExpansion` | matcher = nome do comando; o `PreToolUse` do `Skill` não vê esse caminho |
| contexto no início, retomada ou fork | `SessionStart` | matcher `startup\|resume\|clear\|compact\|fork` |
| revisar ou continuar no fim do turno | `Stop` | exige guarda de loop (passo 5) |
| efeito colateral no fim | `SessionEnd` | orçamento de 1,5 s, sem decisão |

São 33 eventos, e a tabela completa, com matcher e o que o exit 2 faz em cada um, está em
`references/events.md`. Leia quando o evento não estiver acima.

### 2. Escolha o canal de saída por quem precisa ver

| Destino | Canal |
|---|---|
| Claude, como informação | `hookSpecificOutput.additionalContext` (texto factual, até 10 mil chars) |
| Claude, no fim do turno, como orientação | `Stop` + `hookSpecificOutput.additionalContext` (aparece como "Stop hook feedback") |
| Claude, no fim do turno, como erro a corrigir | `Stop` + `{"decision":"block","reason":…}` (aparece como **hook error**) |
| Você (usuário) | `systemMessage` (o Claude **não** vê) |
| Bloquear | exit 2 com stderr, ou o `decision` / `permissionDecision` do evento |
| Explicar um bloqueio de prompt ou `/comando` | o `reason` do `UserPromptSubmit`/`UserPromptExpansion` vai **só para você**: o prompt nunca chega ao Claude. No `PreToolUse`, `PostToolUse` e `Stop`, o motivo vai para o Claude |
| Ninguém (log) | stderr com exit 0 vai só para o debug log |

`suppressOutput` não faz nada. Exit 1 **não bloqueia**: vira aviso não bloqueante e a ação
segue. Ao escrever o parser ou a saída, leia `references/io-schema.md`.

### 3. Filtre barato antes de rodar código

Ordem de custo: `matcher` → `if` (só nos eventos de ferramenta; em qualquer outro evento, um
hook com `if` **nunca roda**) → saída cedo no script → só então lógica pesada. Prefira `command`
determinístico. `prompt` e `agent` custam uma chamada de modelo por disparo e, no `Stop`,
atrasam o fim de **todo** turno. Antes de escolher outro tipo, leia `references/handler-types.md`.

### 4. Capture o payload real antes de parsear

Não adivinhe nome de campo. Isso inclui o "exit code" do Bash e a forma do `tool_input` de uma
ferramenta pouco usada. Ligue um probe que só grava o stdin e o ambiente, dispare o evento uma
vez e escreva o parser em cima do arquivo:

```bash
python3 scripts/capture_payload.py --print-config Stop /tmp/probe   # imprime o JSON do hook-probe
claude -p --settings "$(python3 scripts/capture_payload.py --print-config Stop /tmp/probe)" "responda ok"
ls /tmp/probe    # stdin-*.json e env-*.txt reais
```

O arquivo capturado vira a fixture do passo 6.

### 5. Escreva o script pelo template

Parta de `assets/templates/command-hook.py` (ou `.sh`). O template traz as regras abaixo:

- Leia o stdin inteiro uma vez. Escreva no stdout **só** o objeto JSON: ele é parseado quando
  começa com `{` e termina com `}`.
- **Hook de conveniência:** qualquer exceção sai com exit 0 e um registro em log. Um hook de
  lembrete nunca derruba a sessão.
- **Hook de política (gate):** falha sai com exit 2 e fecha. Confira no primeiro disparo que o
  path existe. Um path errado dá exit 127, vira aviso não bloqueante e deixa o gate desligado
  em silêncio.
- **Stop e SubagentStop:** saia cedo se `stop_hook_active` for `true`. O teto do harness é de
  8 continuações seguidas (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`), e contar com ele é bug.
- **Estado:** em plugin, fica em `${CLAUDE_PLUGIN_DATA}`, que sobrevive a updates. O
  `${CLAUDE_PLUGIN_ROOT}` muda a cada versão. Grave com arquivo temporário e `os.replace`, um
  arquivo por `session_id`, e limpe os antigos.
- **Transcript:** `transcript_path` é gravado de forma assíncrona e pode vir atrasado. Leia só
  até a última linha completa. Para o texto final do turno, use `last_assistant_message`.

Os padrões com estado (revisão no Stop por offset de transcript, priming, `asyncRewake`) e os
exemplos oficiais estão em `references/patterns.md`, para ler quando o hook tiver estado.

### 6. Empacote no lugar certo

| Onde | Quando | Detalhe |
|---|---|---|
| `~/.claude/settings.json` | pessoal, todos os projetos | recarrega sozinho (file watcher) |
| `.claude/settings.json` | do projeto, versionado | só roda depois do trust dialog; em `-p` roda sempre |
| plugin `hooks/hooks.json` | distribuível | **não** declare `"hooks": "./hooks"` no `plugin.json` (a instalação quebra); o arquivo é descoberto sozinho. Recarregue com `/reload-plugins` |
| frontmatter de skill | só depois que a skill roda | `once: true` só vale aqui |

Com path placeholder, use a **forma exec** (`command` + `args`), ou aspas duplas em volta do
placeholder na forma shell. Os detalhes de settings, plugin, trust, `disableAllHooks` e
`CLAUDE_PLUGIN_OPTION_*` estão em `references/packaging.md`, para ler antes de empacotar.

### 7. Teste e prove que dispara

1. **Unidade:** `python3 scripts/hook_test.py <hook-cmd> <fixture.json> --expect-exit 0 --expect-json-key hookSpecificOutput.additionalContext`.
   Cubra um caso positivo e um negativo, e o `stop_hook_active` se for Stop.
2. **Config:** `python3 scripts/lint_hooks.py <hooks.json|settings.json> [--plugin-json <plugin.json>]`.
3. **Ao vivo:**
   - carregue: `/reload-plugins` para plugin, ou o watcher para settings;
   - confira `/hooks`: o hook aparece com a origem certa;
   - dispare o evento de verdade num `claude -p … --debug-file <arquivo>` ou numa sessão;
   - procure o hook no debug log. `Hook JSON output had unrecognized keys` significa campo no
     lugar errado.
   - O `--debug` **não** imprime no terminal: grava em `~/.claude/debug/<session-id>.txt`.
4. Veja a saída com os olhos: o `additionalContext` chegou ao Claude? O `systemMessage` chegou
   a você?

Ao testar, leia `references/testing.md`: harness, fixtures, debug log e o roteiro E2E com `claude -p`.
Threat model, matriz comportamental (loop, dupla execução, segredo, falha) e rollback estão em
`references/safety.md`, que é leitura obrigatória para hook de política.

## Gotchas

| Sintoma | Causa | Correção |
|---|---|---|
| Hook de "falha do Bash" nunca dispara | `PostToolUse` só roda em sucesso | `PostToolUseFailure` |
| `/skill` digitado não é visto | `PreToolUse`/`PostToolUse` com `matcher: Skill` só pega a chamada do modelo | Some o `UserPromptExpansion`, ou leia a linha `Base directory for this skill:` do transcript (em `references/patterns.md`) |
| Gate não bloqueia | exit 1, timeout ou path errado (127) | exit 2; confira o primeiro disparo no debug log |
| O Claude "não viu" o aviso | `systemMessage` vai para o usuário | `additionalContext` |
| Cada turno mostra "Stop hook error" | orientação mandada por `decision:"block"` | `hookSpecificOutput.additionalContext` no Stop |
| Stop em loop até o teto | sem guarda de `stop_hook_active` e sem estado | guarda + estado por sessão + limite próprio |
| Mudei o `hooks.json` do plugin e nada mudou | o plugin não recarrega sozinho | `/reload-plugins` (settings recarrega sozinho) |
| `claude plugin install` falha com `hooks: Invalid input` | `"hooks": "./hooks"` no `plugin.json` | remover (descoberta automática) ou `"./hooks/hooks.json"` |
| Estado sumiu depois do update | gravado em `${CLAUDE_PLUGIN_ROOT}` | `${CLAUDE_PLUGIN_DATA}` |
| Hook com `if` nunca roda | `if` em evento que não é de ferramenta | tirar o `if` e filtrar no script |
| JSON "sem efeito" | stdout com lixo (`echo` no profile) ou JSON em várias linhas | stdout só com o objeto; em profile, guarde o `echo` com `[[ $- == *i* ]]` |
| Script lê `$CLAUDE_TOOL_OUTPUT` e nunca age | essa variável não existe | o input vem no stdin |
| Hook dispara em `claude -p` de cron ou CI | o hook não distingue sessão desassistida | gate por sessão assistida (se precisar, leia `references/patterns.md` §7) |
| Resposta velha depois de `--resume` | o `additionalContext` de eventos do meio da sessão é regravado, não recalculado | recalcule no `SessionStart` (`source: resume`) |

As 11 divergências entre a skill oficial `plugin-dev/hook-development` e a doc atual estão em
`references/outdated-sources.md`, para ler antes de copiar de lá.

## Arquivos

| Arquivo | Leia/use quando |
|---|---|
| `references/events.md` | quando o evento não está na tabela do passo 1, ou para saber o efeito do exit 2 num evento |
| `references/io-schema.md` | ao escrever o parser ou a saída: campos comuns, campos por evento, decision control |
| `references/handler-types.md` | quando considerar `prompt`, `agent`, `http`, `mcp_tool`, `async` ou `asyncRewake` |
| `references/packaging.md` | ao decidir onde o hook mora, ou ao mexer em trust e variáveis de plugin |
| `references/patterns.md` | quando o hook tem estado, lê transcript ou revisa no fim do turno |
| `references/testing.md` | ao testar: harness, fixtures, debug log, E2E |
| `references/safety.md` | quando o hook é gate de política, tem efeito colateral ou toca segredo |
| `references/outdated-sources.md` | antes de reaproveitar exemplo de terceiros ou do `plugin-dev` |
| `scripts/capture_payload.py` | passo 4: gravar o payload e o ambiente reais |
| `scripts/hook_test.py` | passo 7: rodar o hook contra uma fixture e checar exit e JSON |
| `scripts/lint_hooks.py` | passo 7: validar `hooks.json`/settings e o `plugin.json` |
| `assets/templates/command-hook.py`, `assets/templates/command-hook.sh`, `assets/templates/hooks.json` | passo 5: ponto de partida do script e da config |
| `assets/fixtures/pretooluse-bash.json`, `assets/fixtures/posttooluse-bash.json`, `assets/fixtures/posttoolusefailure-bash.json`, `assets/fixtures/userpromptexpansion.json`, `assets/fixtures/sessionstart-resume.json`, `assets/fixtures/stop.json`, `assets/fixtures/stop-active.json` | passo 7: payloads **capturados** na 2.1.283, com paths genéricos |
