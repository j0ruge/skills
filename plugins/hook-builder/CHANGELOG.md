# Changelog — hook-builder

## [0.2.0] — 2026-10-27

Suporte ao Codex CLI. Um hook que precisava rodar igual no Claude Code e no Codex mostrou que a
skill só sabia do Claude, e que o caminho natural dela (forma exec com `args`) deixa o hook mudo
no Codex.

### Por quê

O Codex CLI 0.164.0 tem hooks com o mesmo contrato, mas com diferenças que não aparecem num teste
por pipe:

- não existe `args`, e a chave é ignorada sem erro;
- o hook novo ou alterado é pulado até receber trust por hash;
- a edição chega como `apply_patch`, que o matcher `Write|Edit` casa por alias.

Tudo isso foi conferido no código da tag `rust-v0.164.0` (arquivo e linha na reference nova) e
num probe ao vivo com `codex exec`. O mesmo probe, e outro com `claude -p` na 2.1.309, mostrou
que o payload de uma edição traz o conteúdo do arquivo, e que o próprio `capture_payload.py`
gravaria um segredo em disco se a captura fosse feita contra um `.env` real.

### Added

- **`references/codex.md`:** onde mora a config e o trust de projeto, os 14 eventos (12 na doc),
  o handler sem `args`, as variáveis e a substituição no plugin, o trust por hash, os aliases de
  matcher, o payload real, um `hooks.json` para os dois hosts e a receita de captura com
  `codex exec --dangerously-bypass-hook-trust`.
- **`lint_hooks.py --host codex|both`:** acusa `args`, `if`, type `http`, handler
  `prompt`/`agent`, timeout não inteiro, chave de topo além de `description`/`hooks`, evento fora
  dos 14 e `${CLAUDE_PROJECT_DIR}`.
  - A forma (`hooks` objeto, eventos com lista de grupos, grupo com `hooks`) é conferida igual nos
    dois hosts.
  - A guarda de `stop_hook_active` vale em `Stop` e `SubagentStop`, que no Codex também traz o
    campo, e com `${CLAUDE_PLUGIN_ROOT}` ou `${PLUGIN_ROOT}`. Um script citado que o lint não
    acha vira aviso, em vez de sumir da conferência.
  - `command` que não é texto e `args` que não é lista dão erro, sem traceback.
  - No Codex, `once` e `CLAUDE_PLUGIN_OPTION_*` também dão aviso.
  - Com `--host both`, nenhum aviso sai duas vezes.
- **`capture_payload.py --host codex`:** imprime um `hooks.json` do Codex na forma shell POSIX. O
  env capturado agora inclui `CODEX*` e `PLUGIN_*`.
  - A lista do `<redacted>` ganhou `PASSW`, `PASSPHRASE`, `AUTH`, `CRED`, `COOKIE` e `PRIVATE`.
    Não ganhou `PASS`, que esconderia um `BYPASS`.
  - Os arquivos saem 0600, porque o stdin cru traz conteúdo de arquivo. O DIR que a captura cria
    sai 0700, e um DIR que já existe fica como está. A escrita usa `O_EXCL`, então um symlink
    plantado no nome faz a captura falhar, em vez de ser seguido.
  - O nome do evento é saneado antes de virar nome de arquivo.
  - Uma falha da captura vai para o stderr, em vez de sumir.
- **`tests/`:** 19 testes (`python3 -m unittest discover -s tests`, na pasta da skill) para os dois
  scripts. Contra os scripts do `b0d5c6c`, o primeiro commit da 0.2.0, 26 deles ou dos seus
  subtestes ficam vermelhos.
- **Fixtures capturadas e normalizadas:**
  - no Codex 0.164.0, `codex-posttooluse-apply_patch.json`, `codex-posttooluse-bash.json`,
    `codex-stop.json` e `codex-sessionstart.json`;
  - no Claude 2.1.309, `posttooluse-write.json` e `posttooluse-edit.json`.
- **`patterns.md` §8, "arquivo vigiado mudou":** `PostToolUse` com `Write|Edit` + `Bash` refazendo
  o hash (sem interpretar o comando) + varredura no `SessionStart`/`Stop`. Vale nos dois hosts.
- **`safety.md` §9, hook que trata arquivo de segredo de propósito:** conteúdo lido do disco,
  estado só com hash, stdin em vez de argv, saída sem valores, captura sintética, canário e
  destino menos exposto que a origem.
- **3 casos em `trigger-evals.json`:** dois de Codex e um de `UserPromptExpansion`.

### Changed

- **Description e `plugin.json`:** citam o Codex CLI, e `platforms` ganhou `codex`. Nos Triggers,
  `UserPromptExpansion` deu lugar a `Codex hooks`, para caber nos 8 termos. O evento continua no
  corpo (passo 1, gotchas) e ganhou um caso de gatilho.
- **Passo 6 do `SKILL.md`:** a recomendação da forma exec agora tem a ressalva "se o hook também
  roda no Codex, só a forma shell".
- **`safety.md`:** a regra oficial "não toque em `.env`" continua na lista. Logo abaixo, numa linha
  própria e marcada como desta skill, vem a exceção que aponta o §9.
- **Opção sem valor nos dois scripts** (`--host`, `--plugin-json`, `--matcher`): agora é uso
  inválido, com rc 2. Antes, `lint_hooks.py x --host` caía em `claude` sem avisar, e `--matcher` no
  fim dava `IndexError`. `--matcher ""` continua valendo como "sem matcher".
- **Gotchas:** +5 linhas: trust no Codex, `args` ignorado, `apply_patch`, payload com conteúdo e
  `MultiEdit`, que não existe na 2.1.309. A linha do trust limita o
  `--dangerously-bypass-hook-trust` a captura e E2E num `CODEX_HOME` descartável.

### Revisão antes da publicação

O `/codereview` da faixa, antes do push, achou 4 MEDIUM e 15 LOW na primeira rodada e 4 MEDIUM e
5 LOW na segunda, que revisou só o conserto. Os consertos entraram nesta mesma versão, que ainda
não tinha saído:

- **O `lint_hooks.py --host codex` aprovava um `hooks.json` malformado.** `{"hooks": []}` dava
  rc 0, e o caminho Claude dava rc 1.
- **A receita de worktree do `patterns.md` §8 errava a partir de um subdiretório.**
  `git rev-parse --git-dir` sai absoluto e `--git-common-dir` sai relativo (`../../.git`), então o
  checkout principal parecia worktree. Agora a receita usa `--path-format=absolute`.
- **O gotcha mandava usar o bypass de trust "na automação", sem escopo.**
- **Os scripts não tinham teste.** Os demais itens são ponteiros e fontes nas references.
- **Na segunda rodada, o lint dava traceback** com `"args": 5` ou `"command": 123`, e saía com o
  mesmo rc 1 de "achou erro".

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
