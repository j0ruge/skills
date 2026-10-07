# Changelog — hook-builder

## [0.1.2] — 2026-10-07

Reparo da dívida que a `skill-quality-audit` apontava desde a 0.1.0: D1 (afirmações factuais sem
veredito) e F4 (sem evals). Autorizado pelo JorUge.

### Por quê

O Claude Code instalado passou da 2.1.283, contra a qual a skill foi escrita, para a 2.1.291.
O sensor das afirmações da skill é a doc oficial, então ela foi relida (hooks, hooks-guide,
changelog e skills) e 18 afirmações de tempo, limite, `if`, exit code e canal foram conferidas
uma a uma. **Nenhuma mudou.** Quatro estavam imprecisas e algumas omitiam ressalvas.

### Changed

- **Sem fonte, saiu:** a versão "2.1.196+" do `prompt_id` (`io-schema.md`) não está na doc nem
  no changelog. Fica o "ausente antes do 1º input", confirmado.
- **`UserPromptExpansion`:** a doc não diz que o `reason` vai só para o usuário. O `SKILL.md`
  separa os dois eventos: no Submit, só para você e o prompt não chega; no Expansion, o `reason`
  aparece e a expansão não acontece.
- **Absolutos viraram o observado:** "skill de plugin vem sempre com o prefixo" (`events.md`)
  agora cita o namespace `plugin-name:skill-name` da doc de skills; "`$CLAUDE_TOOL_OUTPUT` não
  existe" (`SKILL.md`, `io-schema.md`) virou "não aparece no ambiente capturado nem na doc".
- **Ressalvas da doc atual:**
  - o timeout de 30 s ou 10 s vale também para `http` e `mcp_tool`;
  - no `SessionEnd`, um `timeout` maior eleva o orçamento até 60 s;
  - exit 1 com JSON válido deixa o JSON decidir;
  - em hook `async`, o `systemMessage` vai para o Claude;
  - desde a 2.1.288, falha do harness no matching bloqueia a chamada (`patterns.md` §2).
- **Proveniência:** as linhas de fonte do `SKILL.md`, de `events.md`, `handler-types.md` e
  `io-schema.md` e o `compatibility` dizem o que foi reconferido em 2026-10-07 (2.1.291).
  `packaging.md` e `testing.md` mantêm 2026-09-30: não foram relidas.
- **F1** que a 0.1.1 introduziu ("leia `patterns.md` §2" sem dizer quando) corrigido.

### Added

- `assets/trigger-evals.json`: 18 casos de gatilho no formato de eval set do `skill-creator`,
  10 que devem e 8 que não devem disparar, entre eles os quase-acertos (hook do git, webhook do
  GitHub e do n8n, `useEffect`, permissões no settings, status line, atalho de teclado).
  Roteado na tabela de Arquivos. Ainda não foi rodado com LLM.

### Vereditos das outras marcações do D1

As demais marcações do `--claims` ficaram como estão, por três motivos:
- a linha de fonte da própria reference já dá a URL, a data e a versão;
- o sensor está num script da skill: o `lint_hooks.py` acusa o `if` fora de evento de
  ferramenta, e o `capture_payload.py` grava o ambiente real;
- é regra desta skill e não fato sobre terceiro ("nunca segredo real", "nunca aprovação
  silenciosa", "texto curto, menos de 600 caracteres").

O D1 é INFO por natureza: conta candidatos, e a contagem não zera.

## [0.1.1] — 2026-10-07

Lições de um gate `PreToolUse`/`Bash` construído com a skill (barra `mineru parse -o` sem
`--pages`, que no MinerU 4.x converte só as páginas 1–10 com rc=0).

### Fixed

- **"Path errado dá exit 127" estava incompleto.** Vale para o comando ausente. Com o script
  ausente atrás do interpretador, `python3 /nao/existe.py` sai **2** (medido), e no `PreToolUse`
  isso bloqueia toda chamada do matcher: um gate de `Bash` com o script movido trava o Bash
  inteiro. `SKILL.md` (passo 5 e Gotchas) agora diz isso e traz a guarda `[ -f "$f" ]` no
  comando do hook; a matriz de `safety.md` ganhou "script ausente" no caso Falha.

### Changed

- `references/patterns.md` §2: "falha fecha" passa a valer para gate de escopo estreito. Com
  matcher largo (todo `Bash`), uma exceção no parser travaria a ferramenta, e o gate falha
  aberto, bloqueando só na detecção positiva. Novo bloco "Gate sobre o texto do comando Bash":
  posição de comando (wrappers e palavras-chave; sem `do`, o `for …; do X` escapava, e o teste
  pegou com 29 de 30), `shlex` com a quebra de linha como separador, corpo de heredoc removido,
  `2>` fora da saída.
- `references/testing.md` §2: stdin inválido no gate aberto sai 0; testar a string inteira do
  `command` com o caso "script ausente"; redirecionar o log nos testes do caminho de falha
  (sujavam o log real); rodar a suíte contra uma cópia sabotada do hook, que tem de ficar
  vermelha.

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
