# Changelog — hook-builder

## [0.1.0] — 2026-09-30

Primeira versão. Uma skill para construir, empacotar e provar hooks do Claude Code contra a
referência oficial atual (https://code.claude.com/docs/en/hooks, lida em 2026-09-30, Claude Code
2.1.283).

### Por que existe

A skill foi escrita a partir de uma linha de base. Dois subagentes sem ela e sem consulta à doc
escreveram hooks de memória e erraram exatamente onde o teste com pipe não pega:
- reagiram a falha do Bash em `PostToolUse`, que só roda em sucesso, adivinhando campos de
  exit code que não existem;
- gatearam `/deploy` por regex no `UserPromptSubmit`, em vez de `UserPromptExpansion`;
- afirmaram que plugin não recarrega (existe `/reload-plugins`) e que `--debug` imprime no
  terminal (grava em arquivo);
- guardaram estado fora do `${CLAUDE_PLUGIN_DATA}`;
- mandaram orientação de fim de turno por `decision: "block"`, que aparece como erro.

A skill ataca esses pontos pela ordem do workflow: evento → canal → filtro → payload real →
script → empacotamento → prova ao vivo.

### Added

- `SKILL.md`: workflow em 7 passos, tabela de evento por intenção, tabela de canal de saída por
  destinatário, gotchas (sintoma → causa → correção).
- `references/`: `events.md` (os 33 eventos), `io-schema.md`, `handler-types.md`,
  `packaging.md`, `patterns.md` (inclui a revisão no Stop com offset de transcript e a detecção
  de skill pela linha `Base directory for this skill:`), `testing.md`, `safety.md`,
  `outdated-sources.md` (as 11 divergências da skill oficial `plugin-dev/hook-development` e os
  erros da linha de base).
- `scripts/capture_payload.py`: um probe que grava stdin e ambiente reais de qualquer evento via
  `claude -p --settings`.
- `scripts/hook_test.py`: roda um hook contra uma fixture e confere exit e JSON.
- `scripts/lint_hooks.py`: valida `hooks.json`/settings e o `plugin.json` (evento, tipo por
  evento, `if`, matcher ignorado, placeholder sem aspas, guarda de `stop_hook_active`,
  `"hooks": "./hooks"`).
- `assets/templates/` (`command-hook.py`, `command-hook.sh`, `hooks.json`) e `assets/fixtures/`,
  com payloads **capturados** na 2.1.283 e paths genéricos.

### Absorvido

O `references/safety.md` traz o conteúdo de desenho da skill local `hooks-2-0-builder`
(2026-09-09, fora de versionamento): contrato de controle, escopos de estado, matriz
comportamental e rollback, adaptados aos hooks que existem hoje. As "Function Hooks" daquela
skill eram uma proposta, não uma API publicada.

### Como reverter

`git revert` do commit desta versão remove o plugin. Nada fora de `plugins/hook-builder/`, do
`marketplace.json` e do README depende dele.
