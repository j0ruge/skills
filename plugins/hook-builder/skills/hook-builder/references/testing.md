# Testar e provar que o hook dispara

Fontes: https://code.claude.com/docs/en/hooks#debug-hooks e
https://code.claude.com/docs/en/hooks-guide#limitations-and-troubleshooting (lido em
2026-09-30, Claude Code 2.1.283).

Um hook só está pronto quando **as quatro camadas** passaram. O pipe sozinho não prova nada
sobre a sessão real: o evento pode estar errado e o teste passa igual.

## 1. Payload real, antes de escrever o parser

```bash
CFG=$(python3 scripts/capture_payload.py --print-config Stop,PostToolUseFailure /tmp/probe)
claude -p --settings "$CFG" "rode o comando false e depois responda ok"
ls /tmp/probe   # stdin-<Evento>-*.json e env-<Evento>-*.txt
```

- **Como funciona:** `--settings '<json>'` soma hooks só para aquela execução, sem tocar nos
  seus settings. Os valores de variáveis com `TOKEN`, `SECRET`, `KEY` ou `PASSWORD` no nome são
  gravados como `<redacted>`.
- **Para `UserPromptExpansion`:** crie uma skill de projeto descartável em
  `.claude/skills/probe-skill/` e rode `claude -p "/probe-skill"`.
- **Depois:** troque os paths da máquina por genéricos e salve como fixture.

## 2. Unidade: fixture no pipe

```bash
python3 scripts/hook_test.py 'python3 hooks/meu_hook.py' assets/fixtures/stop.json --expect-no-output
python3 scripts/hook_test.py 'python3 hooks/meu_hook.py' caso-positivo.json \
  --expect-json-key hookSpecificOutput.additionalContext
python3 scripts/hook_test.py 'python3 hooks/meu_hook.py' assets/fixtures/stop-active.json --expect-no-output
```

**Casos mínimos:**
- um positivo (o hook age);
- um negativo (o hook fica calado);
- `stop_hook_active: true`, se o hook for de Stop;
- stdin inválido: exit 0 para hook de conveniência, exit 2 para gate;
- estado ausente ou corrompido.

**Fixtures de `assets/fixtures/`:** elas trazem a **forma** real do payload, mas com paths
genéricos (`<HOME>/my-project`, gravado como `/home` + `/user/my-project`) que não existem no disco. Um hook que usa `cwd` ou
`transcript_path` (git, leitura de arquivo) fica calado contra elas, e isso é um falso
negativo. Copie a fixture e troque os paths por um repo ou transcript real da máquina.

**Hook com estado e transcript:** escreva um `unittest` que monte um JSONL sintético num diretório
temporário e aponte `HOME` e `CLAUDE_PLUGIN_DATA` para lá. O plugin `retrofit-watch`, no mesmo
marketplace, tem um exemplo completo em `skills/retrofit-watch/tests/test_retrofit_watch.py`.

## 3. Configuração

```bash
python3 scripts/lint_hooks.py plugins/meu/hooks/hooks.json --plugin-json plugins/meu/.claude-plugin/plugin.json
claude plugin validate plugins/meu
```

O lint pega:
- evento inexistente e tipo não suportado no evento;
- matcher ignorado e `if` que nunca roda;
- placeholder sem aspas;
- `"hooks": "./hooks"` no manifesto;
- script de Stop sem `stop_hook_active`.

O `claude plugin validate` pega o formato do plugin.

## 4. Ao vivo

1. **Carregar:**
   - plugin: `claude --plugin-dir plugins/meu`, ou `/reload-plugins` numa sessão;
   - settings: o file watcher carrega sozinho.
2. **Conferir no `/hooks`:** o hook aparece com a origem certa (Plugin Hooks ou User Settings).
3. **Disparar o evento de verdade e ler o debug log:**

   ```bash
   claude -p "…" --plugin-dir plugins/meu --output-format stream-json --verbose \
     --debug-file /tmp/hook-debug.txt
   grep -n "Hook\|hook" /tmp/hook-debug.txt | head
   ```

   O `--debug` sozinho grava em `~/.claude/debug/<session-id>.txt` e **não imprime no
   terminal**. Para mais detalhe de matcher, use `CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose`. No meio
   da sessão, `/debug` liga o log.
4. **Ver o efeito:**
   - o `additionalContext` mudou a resposta do Claude?
   - o `systemMessage` apareceu para você?
   - o bloqueio bloqueou?
5. **Caso negativo ao vivo:** a mesma sessão, sem a condição, não dispara.

## Mensagens do debug log e o que significam

| Mensagem | Significado |
|---|---|
| `Hook output does not start with {, treating as plain text` | o stdout não é JSON (lixo de profile, `print` extra) |
| `Hook JSON output had unrecognized keys` | campo no lugar errado, por exemplo `additionalContext` fora de `hookSpecificOutput` |
| `Failed with non-blocking status code: /bin/sh: …: No such file or directory` | path do script errado. Um gate assim fica desligado em silêncio |
| `<hook> hook error` no transcript | exit ≠ 0 e ≠ 2 sem JSON válido, JSON fora do schema, ou `decision: "block"` no Stop |

## "Não dispara": checklist

1. O evento certo? `PostToolUse` não roda em falha, e o `/skill` digitado não passa pelo
   `PreToolUse`.
2. O matcher bate, com caixa exata? Lembre que o regex não tem âncora.
3. `if` num evento que não é de ferramenta? Então o hook nunca roda.
4. Plugin recarregado (`/reload-plugins`)? Trust aceito, se o hook vem de settings de projeto?
5. `disableAllHooks` ativo em algum nível?
6. O script sai antes por um filtro que não bate com o payload real? Compare com o capturado.
7. Stop em loop: falta a guarda de `stop_hook_active` ou um limite próprio. O teto do harness é
   8 (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`).
