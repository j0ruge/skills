# Changelog — retrofit-watch

## [0.3.2] — 2026-10-04

### Fixed

- **No Windows o hook quebrava a cada fim de turno: `import fcntl`.** O módulo só existe em Unix,
  e o Claude Code mostrava `Stop hook error: … ModuleNotFoundError: No module named 'fcntl'` em
  todo `Stop`, com o `python3` do PATH (pyenv-win, 3.9.13). A trava passa a ser `fcntl.flock` no
  Unix e `msvcrt.locking` sobre o 1º byte no Windows (`_lock`/`_unlock`), nas duas que existiam:
  o estado da sessão e a fila.
- **Trocar só o import não bastava.** Com o hook rodando no Windows sobre um transcript sintético,
  apareceram três defeitos calados atrás dele, todos de presumir POSIX:
  - **A skill do marketplace era desclassificada logo depois de carregar.** O `classify_path`
    compara com `/`, e no Windows o `realpath` devolve `C:\Users\…\cache\chewiesoft-marketplace\…`.
    O `Skill` vigiava `full:codereview` pelo nome e, uma linha depois, o `Base directory` caía em
    `None` e zerava o `current`: trabalho 0, retro nunca. `_slashed` normaliza o path, o `home` e
    as `deny_roots`.
  - **A retro era contada e não entregue.** O `stdout` do Python no Windows é cp1252, que não tem
    o `→` do pedido: `UnicodeEncodeError` no `errors.log`, saída vazia, e o estado já tinha somado
    a revisão. A saída agora é JSON em ASCII (`\u2192`), que passa por qualquer página de código.
  - **O payload chegava com mojibake.** O `stdin` também é cp1252, e o Claude Code manda UTF-8 cru:
    `sem lições novas` virava `sem liÃ§Ãµes novas`, e a métrica marcava `lessons`. Agora o hook lê
    `sys.stdin.buffer` e decodifica UTF-8.
- **A raiz do repo vinha em dois formatos.** O git do Windows responde `C:/x/y`, e o `TODO.md` do
  kit é comparado com o `realpath` (`C:\x\y`): a escrita nele não encerrava a retro do kit.
  `_toplevel` passa a raiz pelo `normpath`.
- 2 testes novos (44 no total) reproduzem o stdio do Windows em qualquer SO com
  `PYTHONIOENCODING=cp1252:surrogateescape`. O `run_hook` passa a mandar UTF-8 cru, como o Claude
  Code: o `text=True` e o `ensure_ascii` da fixture escondiam o mojibake. No Windows, o binário do
  kit na fixture ganha `.cmd`, porque lá o `shutil.which` só acha extensão do PATHEXT.
- Suíte verde no Linux (3.12.3) e no Windows (3.9.13). Cinco sabotagens, uma por peça: no Windows
  todas pegas; no Linux só as duas de encoding, porque trava e path só divergem no Windows. Por
  isso o docstring da suíte manda rodá-la lá também.

## [0.3.1] — 2026-10-02

### Documented

- **Limite declarado: a atribuição gruda na última skill carregada.** Nesta sessão do
  `sdd_agents`, o hook atribuiu à `todo-to-github-issues` 54 chamadas e 3 atritos. Ela fez 8
  chamadas sem erro; o resto era a implementação da 0.3.0, outra tarefa, e os 3 "atritos" eram
  `Edit` sem `Read` prévio. O `Scanner` mantém `current` até outra skill carregar.
- **Medido antes de consertar.** Sobre 376 transcripts de 14 dias (150 com skill nossa), 41% do
  atrito atribuído (173 de 421) cai depois de um prompt novo do usuário que não responde a uma
  pergunta. Os pedidos de retro elegíveis quase não mudam (195 → 193), porque trabalho ≥ 5 já os
  dispara: o custo é um pedido a mais, que o filtro de evidência descarta.
- **Correção refutada, por isso não há mudança de código.** "Prompt novo encerra a atribuição,
  salvo resposta a uma pergunta" zeraria 8 atritos possivelmente legítimos do `zitadel-idp` (sessão
  `44820556`): a continuação da tarefa chega como "sim", "roda", "pode empurrar" e um pedido longo
  de ajuste, depois de propostas sem "?". O formato do prompt não separa outra tarefa de
  continuação. A fila headless da 0.3.0 quase não sofre: 5 de 373 fases têm mais de um prompt real.
- O caminho que sobra é atribuir por proximidade a uma ação da própria skill; falta um sinal
  confiável do que é essa ação.

## [0.3.0] — 2026-10-02

### Changed

- **A sessão headless deixa de perder a retro: ela vai para uma fila.** Até a 0.2.0, uma fase do
  `sdd run` (`claude -p`) saía calada no `attended()`, e o atrito de uma skill dentro dela se
  perdia. O plugin já carregava nessas fases (a linha `init` dos logs do `sdd_agents` de
  2026-10-01 lista `retrofit-watch`), só não fazia nada. O humano pediu o hook ligado durante o
  pipeline, com os achados num arquivo que o kit não visse.
- Em sessão desassistida o hook **não devolve nada** à sessão (nem `additionalContext`, que
  compraria um turno pago da fase, nem aviso). Com atrito ≥ 1, grava uma linha em
  `${CLAUDE_PLUGIN_DATA}/queue.jsonl`: sessão, transcript, repo, a fase lida do `GIT_REFLOG_ACTION`
  (`sdd:REVIEW:<sid8>`, que o `run_phase` do kit já passa) e as contagens. Nunca texto do assistente.
- **Fora de qualquer repo, de propósito.** Um arquivo dentro do checkout, mesmo no `.gitignore`,
  seria um escritor a mais na árvore de uma fase cujo `hat_guard_check` e cuja guarda de kit leem
  a árvore. No diretório de dados do plugin, nenhum sensor do kit o vê.
- Só entra com atrito. Trabalho sem atrito numa sessão que já acabou quase sempre dá "sem lições
  novas", e reler o transcript para descobrir isso custa caro.
- Não espera resposta: o adiamento por pergunta no fim do turno (`waiting_for_user`) vale só em
  sessão com gente, porque ninguém vai responder à fase.

### Added

- `SessionStart` `startup` → `retrofit_watch.py pending`: numa sessão interativa com fila, uma
  linha só para o humano (`systemMessage`, fora do contexto) com a contagem e o comando.
- `retrofit_watch.py queue` lista a fila em JSON (com `transcript_exists`); `queue --done <id>`
  tira a entrada depois da retro. `/retrofit-watch:retrofit-watch pendentes` faz a retro da fila,
  pela nova seção 8 do `criteria.md` (ler só o atrito do transcript, nunca ele inteiro).
- `"unattended": "off"` no `~/.claude/retrofit-watch.json` volta ao silêncio da 0.2.0.
- 7 testes novos (42 no total). A passada de sabotagem degradou 11 peças do código novo, cada uma
  com a âncora conferida antes, e as 11 foram pegas.

### Como reverter

`"unattended": "off"` desliga a fila sem reverter o código; `git revert` deste commit volta tudo.

## [0.2.0] — 2026-10-01

### Added

- **Modo `kit`: o hook passa a vigiar o kit `sdd`.** Na sessão da SQ-152 do `sales_quote`, uma
  PLAN inteira com o `/sdd-plan` e o `sdd-planner`, mais o `sdd approve` e o `sdd run`, deixaram
  o estado da sessão com `"skills": {}`. O `/sdd-plan` é comando sem `:`, o subagente chega como
  `Agent` com `subagent_type`, e o CLI é Bash comum. Nada disso era reconhecido, e o atrito real
  do kit (o approve que só comitou o `00-missao.md`, o `sdd status` que travou) só virou achado
  porque alguém pediu.
- Um kit é reconhecido pelo **binário no `PATH`**: o `realpath` aponta o repo, e o `origin` tem
  de ser nosso, a mesma régua do modo lean. Contam como trabalho do kit o comando `/<kit>-*`, o
  subagente `<kit>-*` e o binário chamado no Bash (início do comando ou depois de `;&|(`, para
  `grep sdd arquivo` não contar). `"kits"` no `~/.claude/retrofit-watch.json` muda a lista; o
  padrão é `["sdd"]`.
- A lição de kit vai para o **`TODO.md` do repo do kit**, no formato e com a catraca dele, para
  o `sdd kaizen` triar. O `/retrofit-skill` não é oferecido. `Edit`/`Write` nesse `TODO.md`
  encerra a retro do kit na sessão. A seção 7 do `criteria.md` diz como registrar.
- As fases headless do `sdd run` continuam caladas: a retro precisa de alguém para responder.
- 5 testes novos (35 no total). Oito sabotagens do código novo, uma por peça, foram todas pegas.

## [0.1.1] — 2026-09-30

### Fixed

- **Pitfall contornado sem erro de ferramenta não disparava a retro.** No E2E com a cópia
  instalada, a skill de teste apontava para um arquivo inexistente. O Claude verificou antes de
  ler, achou o arquivo certo por `find` e terminou com trabalho = 4 e atrito = 0: nenhum
  `is_error`, abaixo do limiar de 5. O pitfall mais comum (instrução errada, contornada com
  elegância) passava em branco. Agora o texto do assistente que narra o desvio, com a skill
  vigiada ativa, conta como atrito: `não existe`, `em vez de`, `not in the expected location`,
  `instead of` e afins (`DEVIATION_RE`). Com a mudança, o mesmo prompt produziu a retro com a
  lição e a oferta do `/retrofit-skill`.
- 2 testes novos (narração de desvio conta; narração comum não conta), 30 no total. A mutação
  que remove o sinal é pega pelo teste novo.

### Como reverter

`git revert` deste commit. O limiar volta a depender só de erro de ferramenta, interrupção e
correção do usuário.

## [0.1.0] — 2026-09-30

Primeira versão. Um Stop hook percebe quando uma skill nossa trabalhou na sessão e pede ao
Claude a retro dela, com evidência, oferecendo o `/retrofit-skill`.

### Por que existe

Até aqui, a melhoria das skills dependia de o usuário lembrar, no fim de cada sessão, de pedir a
análise e depois o retrofit. Quando ele não pedia, o pitfall da sessão se perdia. Com o hook, a
retro é puxada pelo processo, no turno em que a evidência ainda está no contexto. O retrofit
continua exigindo confirmação.

### Added

- `hooks/hooks.json`:
  - `Stop` → `retrofit_watch.py stop`;
  - `SessionStart` (`resume|fork`) → `retrofit_watch.py baseline`, para que o histórico copiado
    de um fork não dispare.
- `skills/retrofit-watch/scripts/retrofit_watch.py` (stdlib, com git):
  - **detecção:** lê o transcript por offset e reconhece a carga de skill pela entrada
    `isMeta` `Base directory for this skill:`, tanto na chamada pelo Skill tool quanto no
    `/skill` digitado; o plugin só de comandos é reconhecido pelo nome;
  - **classificação:** full (marketplace, com o argumento igual ao **nome do plugin**) × lean
    (skill rastreada no git de um repo de `j0ruge`/`JRC-Brasil`/`chewiesoft`) × ignora
    (terceiros, `skills-lock.json`, `.agents/skills`, `~/.hermes`, fora do git);
  - **disparo:** adia quando o turno espera o usuário; teto de 2 retros por skill por sessão;
    fica calado em sessão desassistida e na continuação do próprio Stop;
  - **segurança:** nunca grava texto do assistente e nunca derruba a sessão.
- `skills/retrofit-watch/SKILL.md`: como o hook decide, o procedimento da retro e o uso sob
  demanda (`/retrofit-watch:retrofit-watch <skill>`).
- `skills/retrofit-watch/references/criteria.md`: sinais, filtro de evidência, triagem
  skill × projeto × terceiro, auto-audit de segredos e formato do bloco. Adaptado da
  `self-learning` (kulaxyz, MIT) e do loop "Lições" de um agente de propostas de
  um projeto interno.
- `skills/retrofit-watch/tests/test_retrofit_watch.py`: 28 testes com HOME fixture, repos git e
  transcripts sintéticos no formato real. Nove mutações do script (teto, filtro `isMeta`,
  adiamento, guarda de `stop_hook_active`, `.agents`, lock, gate de sessão desassistida,
  supressão pós-retrofit, adiamento em pergunta) são pegas pelo teste certo.

### Decisões

- **`additionalContext` no Stop, e não `decision: "block"`:** a doc indica essa forma quando o
  hook está funcionando como projetado e dá orientação. Aparece como "Stop hook feedback", e o
  `block` apareceria como "hook error" a cada retro.
- **Uma leitura do transcript, e não `PostToolUse(Skill)` + `UserPromptExpansion` +
  `PostToolUseFailure`:** o transcript cobre os dois caminhos de invocação, traz o path e dá o
  atrito sem um processo extra por chamada.
- **Pitfall sem solução entra na retro,** marcado "sem correção verificada", e a proposta é
  investigar antes do retrofit. O E2E mostrou o motivo: com o filtro antigo, que exigia "o que
  resolveu", uma skill que apontava para um arquivo inexistente saiu como "sem lições novas".
  O caso mais grave era justamente o que ficava de fora.
- **Gate de sessão desassistida por `CLAUDE_CODE_SESSION_ATTENDED`:** vale `1` na sessão
  interativa e `0` no `claude -p`, com fallback em `CLAUDE_CODE_ENTRYPOINT` (`cli` ×
  `sdk-cli`). As duas foram observadas na 2.1.283 e não são documentadas.

### Como reverter

Desabilite o plugin, ou use `RETROFIT_WATCH=off` para desligar sem desinstalar. `git revert` do
commit remove o plugin. O estado fica em `${CLAUDE_PLUGIN_DATA}` e sai no uninstall.
