# Changelog — codereview

Formato: [Semantic Versioning](https://semver.org/)

## [2.26.4] — 2026-10-20

### O achado que o backlog já carrega sai do backlog no mesmo commit, com cada citação viva dele (coderabbit-pr 4.5.4)

- **O quê:** `skills/coderabbit-pr/references/fix-loop.md` ganhou a seção *A finding already in the backlog*,
  e o passo 2 do loop aponta para ela. Antes do conserto, procurar o achado no `TODO.md` e nas issues abertas;
  quando ele é um item, o commit do conserto retira o item (pela regra do projeto: apagado, ou `RESOLVED by`) e
  reescreve as citações vivas do `#N` que ainda o dão como atual: o parágrafo da doc, a entrada do changelog ou
  do KAIZEN, o corpo do PR, um texto proposto ainda não aplicado. Elas se acham pelo número e pelo símbolo,
  fora dos artefatos congelados das fases passadas.
- **Por quê:** no PR #33 do magic_tutor (2026-10-20), o 1º P2 do Codex era o `TODO.md` #17, um resíduo que a
  rodada de revisão da missão tinha estacionado. Depois do conserto, o #17 seguia citado como defeito aberto em
  `docs/monitor.md`, duas vezes no `KAIZEN_LOG.md`, no corpo do PR e num texto ⛔ da fase DOCS. A sessão achou
  as citações por `grep` porque procurou; nenhuma reference mandava. `55e17a5` apagou o item e reescreveu as
  citações, `57ccb0b` aplicou o texto proposto sem a frase, e o `check-todo.sh --anchors` deu `0 off target`.
- **Onde:** só na reference. O `SKILL.md` muda só o `metadata.version`: está em 19.991 caracteres, a 9 do AVISO
  do C1, e já manda ler o `fix-loop.md` antes do primeiro conserto de lógica.

## [2.26.3] — 2026-10-20

### O `commit_id` de um comentário inline segue o head; o commit revisado é o `original_commit_id` (coderabbit-pr 4.5.3)

- **O quê:** `skills/coderabbit-pr/references/reviewer-registry.md`, *Coverage Per Commit*, ganhou um
  parágrafo: depois de um push, o comentário inline ainda ancorado responde o head novo como
  `commit_id`; o commit que o revisor viu é o `original_commit_id` (e o `commit_id` do objeto de review,
  que não se move). A cobertura se lê nas reviews, e o retrato de um achado inline (Fase 3.1, passo
  1.5) no `original_commit_id`.
- **Por quê:** no PR #13 do dotp-remake (2026-10-20), o P2 do Codex postado às 21:19Z sobre `ed3729c`
  respondeu `commit_id` `85f7475`, a correção empurrada perto das 21:42Z, com `original_commit_id`
  `ed3729c` (`gh api repos/j0ruge/dotp-remake/pulls/comments/4330439724`); o objeto de review ficou em
  `ed3729c`. Lido pelo `commit_id`, o achado antigo parecia levantado de novo no head corrigido. A
  sessão não errou por isso (conferiu o `created_at` e o estado do Codex), e nenhuma reference citava
  o `original_commit_id`.
- **Onde:** só na reference. O `SKILL.md` muda só o `metadata.version`: está em 19.991 caracteres, a 9
  do AVISO do C1, e a *Phase 2* já manda ler o registry para a cobertura por commit.

## [2.26.2] — 2026-10-20

### Todo diff de agente sai como `git -P diff`, e o agente não julga um doc pela própria atribuição (codereview 2.26.2)

- **O quê:**
  1. Os dois prompts de lançamento do `SKILL.md` (Fase B e B2), o passo 2 de
     `references/per-file-agent.md` e de `references/sweep-agent.md` e os diffs que
     `references/configuration.md` manda escrever por extenso num prompt (`head=`, `worktree`,
     vários repos, a árvore vazia, o snapshot `git stash create`) passam de `git diff` para
     `git -P diff`. O bullet do `/usr/bin/grep` nos dois contratos ganha o caso do git, com o sensor:
     um diff que mostra `--- Changes ---` ou `lines truncated` foi reescrito, e roda de novo como
     `/usr/bin/git -P diff`. *Base and batching* ganhou o bullet irmão do de `grep`.
  2. `references/per-file-agent.md`, *What to apply*: o modelo, a atribuição de commit e a data no
     prompt do agente são dele (roda em Sonnet), não da sessão. Um modelo ou trailer
     `Co-Authored-By` num doc se confere no repo (`git log --format=%B`, o CLAUDE.md) ou fica como
     está.
- **Por quê:**
  1. Na revisão do kit-bitlocker (rodadas 1 e 2, duas sessões), o hook rtk 0.42.3 reescreveu o
     `git diff` simples de cada agente para `rtk git diff`, que tira as linhas de contexto e corta
     hunks em `... (N lines truncated)`: 10 diffs perderam de 21 a 210 linhas (o do `Sistema.psm1`,
     210; o diff inteiro do sweep, blocos de 65, 27 e 93). `rtk rewrite` sai com rc 1, sem
     reescrita, para `git -P diff`, `git -P -C <repo> diff`, `--no-index` e `$S`, e reescreve
     `--no-pager`, `command git`, `env git` e `cd … && git`. Pelo hook real, `git -P diff` saiu cru.
     `-P` é flag do git, sem caminho de máquina, e custou 3 caracteres por prompt.
  2. Na rodada 2, o agente do plano acusou como errado o `Co-Authored-By: Claude Opus 5.5` do plano,
     porque o próprio lembrete dele dizia Sonnet 5.5. A atribuição da sessão e os 16 commits do
     branch diziam Opus 5.5; a Fase C refutou o achado.
- **Fora daqui, sem correção verificada:** em 9 de 9 agentes das Fases B e B2, nas duas sessões, o
  primeiro lote (contrato, `detection-passes.md` de 53 KB, diff, arquivo) foi repetido inteiro no
  segundo turno, depois de anexos do harness, e o primeiro diff não tinha falhado. A causa não está
  no prompt da skill; fica para investigar à parte.
- **Onde:** o `SKILL.md` foi de 19.993 para 19.999 caracteres (o AVISO do C1 é acima de 20.000);
  o resto da lição está nas references.

## [2.26.1] — 2026-10-20

### O achado que pede o inverso da correção revisada ganha veredito, não edição (codereview 2.26.1)

- **O quê:** `references/configuration.md`, *Re-review rounds*, ganhou um bullet logo depois de
  "The agents never see the earlier reports", o caso irmão dele. A faixa de uma re-revisão é a
  correção da rodada anterior. Na Fase C, antes de aceitar um achado, o orquestrador lê o diff da
  faixa sobre aquelas linhas: uma sugestão que devolve o que uma linha `-` tirou, ou tira o que uma
  linha `+` pôs, desfaz o que a última rodada aceitou. Nesse caso não se edita de novo. O
  orquestrador escreve o veredito que decide entre as duas formas pelo que o sensor ou o caso de
  fato prova, põe-no sob a *Findings Table* e onde o orquestrador da rodada seguinte o lê (a tabela
  de vereditos de um handoff), e ele não conta contra a regra de parada. O bullet também avisa que
  tirar uma afirmação, como *Docs this session wrote* recomenda, é uma dessas correções.
- **Por quê:** na revisão do plano da `@jrc/object-storage` (lighthouse_project, branch
  `docs/plano-object-storage-lib`, o plano revisado como CODE), a correção da rodada 29 (`1ae5181`)
  exigiu `COPY vendor/ vendor/` "exatamente e sem opções", cláusula que só o caso `COPY --from=…`
  provava. A rodada 30 (`base=8c788d6`) deu LOW nela, e a correção (`5734ee4`) tirou a cláusula. A
  rodada 31 (`base=1ae5181`) deu LOW pedindo para pô-la de volta, porque `--chown` e `--link`
  ficavam indefinidos. Fechou por um veredito escrito, não por outra edição: o caso de dois estágios
  já fixa que o `--from` não conta, e as outras opções não mudam a origem do `COPY`, então qualquer
  escolha do executor passa certo ou reprova alto. O veredito entrou na tabela "Vereditos já dados"
  do handoff (lighthouse_project `a567958`), e a série parou ali, com A em todas as linhas. O bullet
  irmão só cobria o achado **descartado** que volta; este é o achado que desfaz uma correção
  **aceita**, e aceitá-lo de novo faria o texto oscilar entre as duas formas.
- **Onde:** só na reference. O `SKILL.md` está em 19.993 caracteres, no teto de ~20 mil da spec,
  e só o `metadata.version` mudou nele.

## [2.26.0] — 2026-10-20

### A cópia carregada mais nova que o `installPath`, o código que um doc carrega e a faixa que leva as seções que a regem (codereview 2.26.0)

- **O quê:**
  1. `references/configuration.md`, *Stale copy*: a seção compara primeiro as duas versões
     (`sort -V`) e passa a ter dois ramos. O da cópia mais velha é o texto de antes, inteiro. O novo,
     *Loaded copy newer than the installPath*, manda seguir com a cópia carregada e nunca trocá-la
     pela do `installPath`; confere pelo rc de um `/usr/bin/diff -rq` contra o clone do marketplace
     (`installLocation` do `known_marketplaces.json`) que ela é a publicada; e põe as duas versões no
     Cost footprint. O `.orphaned_at` na pasta carregada não muda nada. No `SKILL.md`, o Phase A diz
     "older or newer" em vez de "is a stale copy", e o `report-template.md` ganhou o terceiro caso do
     rodapé (`loaded 2.25.2 = marketplace, installed 2.19.0`).
  2. *Code inside docs*: vale também sem foco, quando o diff tem 0 CODE e um doc traz comandos que um
     passo posterior executa (os Checks de um plano, as receitas de uma spec, as condições de um
     handoff); "the doc that carries the named code" virou "the code"; e a linha `File:` de cada
     agente de faixa nomeia as seções do doc que regem a faixa.
  3. *Re-review rounds*: corrigir uma decisão emendada pede `grep -n` do id dela no doc, e todas as
     citações mudam no mesmo commit.
  4. `SKILL.md`: a rota do `configuration.md` diz "a doc holds code a step runs", e a sonda de testes
     encurta e cita o `==` sozinho, que o zsh aborta com `= not found`.
- **Por quê:**
  - Cópia mais nova: em 2026-10-20 a sessão carregou a 2.25.2 com o `installPath` na 2.19.0, gravado
    em 2026-10-18 pelo último `claude plugin update codereview`. Outra sessão rodou
    `claude plugin marketplace update` e depois `claude plugin update` só de outro plugin: a 2.25.2
    entrou no cache no mesmo segundo que versões novas de três outros plugins, e só o nomeado foi ao
    registro. O `/reload-plugins` da sessão de revisão carregou a 2.25.2; um `claude` aberto uma hora
    depois carregou a 2.19.0 e gravou `.orphaned_at` na 2.25.2 um segundo depois de subir. A 2.25.2
    batia com o clone do marketplace (rc 0); a 2.19.0 diferia dele no `SKILL.md` e em cinco
    references. A regra antiga, seguida ao pé da letra, rodaria a revisão na 2.19.0, doze releases
    atrás.
  - Código em doc: na revisão do plano da `@jrc/object-storage` (lighthouse_project, sem foco, 0
    CODE), o plano revisado como CODE deu à rodada 1 os seus dois MEDIUM, os dois em Checks: a
    sabotagem `*.tgz` deu 34/0 em vez de 33/1, e o piso de um Check já estava verde no HEAD.
  - Faixa: o agente das linhas 354–645 do mesmo plano apontou como lacuna a docstring no I3 e no I4,
    que o § Contexto, nas linhas 105–106, já exigia para todo arquivo novo. Acima de ~600 linhas o
    agente lê só as regiões alteradas (`per-file-agent.md`).
  - Decisão emendada: a correção da P10 deixou mais três lugares que a citavam.
- **Não aplicado:** "frase que volta rodada após rodada se tira". A lição já está em *Docs this
  session wrote* ("recommend removing the claim, not adding evidence") e em *A text finding in code
  converges* ("or delete it"), e a sessão não trouxe medida nova para somar a elas.
- **Onde:** o `SKILL.md` foi de 247 linhas e 19.995 caracteres para 247 e 19.993; o detalhe ficou no
  `configuration.md`. Dívida que já existia e segue igual: os três C2 de contrato de subagente e o D1.
- **Sugestão, fora do escopo:** o `coderabbit-pr` (`references/pr-branch.md`, *Is this run the
  installed copy?*) manda parar e pedir `/reload-plugins` em todo `STALE`. Com a cópia carregada mais
  nova que o `installPath`, foi um `/reload-plugins` que a carregou (medido em 2026-10-20), e pedir
  outro deve carregar a mesma de novo (não medido).

## [2.25.2] — 2026-10-20

### "Nenhum teste cobre isso" se confere nos testes (codereview 2.25.2)

- **O quê:** a seção *Findings Table* do `references/report-template.md`, que a Fase C lê no passo 10
  antes de escrever o relatório, ganhou um parágrafo. Antes de dizer que a entrada de um achado não tem
  teste, ou que a correção precisa de um caso novo, procurar essa entrada nos testes. Um teste que já a
  usa e exige a saída errada é a forma 6.12 (*a test that pins the shape the code produces*), e vai na
  ação do achado e nas Notes da cobertura como teste que a correção muda.
- **Por quê:** no `/codereview` do magic_tutor sobre `9d0eda3..a569b03`, o relatório disse que nenhum dos
  14 testes novos punha uma mágica entre dois gatilhos iguais. O
  `test_gatilho_repetido_do_oponente_vira_uma_linha` tinha um Shock entre eles e exigia o `(×3)` errado, e
  a correção (magic_tutor `466f154`, PR #23) teve de reescrevê-lo. Numa revisão completa, nenhum arquivo
  de teste vai para um agente, e a 6.12 só roda com o foco `tests`: a afirmação saiu sem sensor.
- **Onde:** só na reference. O `SKILL.md` está em 19.995 caracteres, no teto de ~20 mil da spec, e só o
  `metadata.version` mudou nele.

## [2.25.1] — 2026-10-19

### Uma sabotagem interrompida fica no arquivo (coderabbit-pr 4.5.2)

- **O quê:** o passo 4 do `references/fix-loop.md` (*Sabotage the fix*) ganhou um parágrafo. Depois de
  qualquer interrupção, recontar o texto afrouxado de cada sabotagem (`grep -cF`): toda contagem tem de
  dar 0 antes de confiar na suíte.
- **Por quê:** no PR #21 do magic_tutor, a sessão caiu durante a última de uma série de 5 sabotagens da
  narração do oponente. A restauração roda depois das sondas e não rodou, e o `monitor/replays.py` ficou com
  `"jogo": 0`. Com a correção ainda sem commit, o `git status` já mostrava o arquivo mudado e não
  separava a correção da sabotagem. Só a contagem do texto afrouxado achou a linha.
- **Não entrou:** responder na thread com o caminho que inclui o número do PR. O
  `references/thread-resolution.md` já traz `repos/$REPO/pulls/$PR/comments/<ID>/replies`; o 404 da
  sessão veio de ler a reference só até a 5.1.

## [2.25.0] — 2026-10-19

### A série fecha numa rodada sobre o HEAD final, a linha anterior à branch não é da rodada, e o texto no código converge quando é verdade em todo caminho

Lições da série de rodadas de fix do importador do Untapped no magic_tutor (branch
`fix/importador-untapped`, 12 rodadas, com o LOW por rodada caindo de 9 para 2 até o grade A). O
`SKILL.md` muda só a versão e fica com os mesmos 19.995 chars. Todo o resto vai para as references.

- **`configuration.md`, *Re-review rounds*, quatro bullets novos:**
  - *A text finding in code converges when the sentence is true on every path, or leaves.* Junta
    duas lições. A cauda de LOW da doc fechou quando a frase incluiu o caso sem aviso (um log sem
    hora deixa o arquivo com a hora da gravação, calado), e a rodada seguinte da doc deu *No
    findings*. Um aviso que dizia "ficaram com a hora da gravação" era falso no caminho em que a
    pasta guardou outra data (o ext4 corta o ano 3000 em 2446). Ele só deixou de voltar quando passou
    a dizer apenas que a data não é a do fim. A skill dizia isso só para a doc e para a lista de fix
    do orquestrador.
  - *The clean round covers the head it read, and nothing committed after it.* A rodada sobre um
    commit de duas linhas de comentário trouxe um LOW num comentário que a branch tinha escrito duas
    rodadas antes (a resolução de 2 s atribuída ao exFAT), e as duas rodadas anteriores o tinham lido
    sem apontar.
  - *A line older than the branch is not the round's.* O agente por arquivo lê o arquivo inteiro.
    Por isso a rodada sobre aquele comentário também trouxe um `--log` digitado errado em
    `arquivar.py:229`, código de `5a941e7d`, que é ancestral da base da branch
    (`git merge-base --is-ancestor`, rc 0). Fora do dead code (Bucket B), a skill não tinha regra
    de "pre-existing", e um achado desses segurava a regra de parada. Agora o Phase C faz o
    `git blame` e o `--is-ancestor`, rotula o achado, e o usuário decide se ele entra.
  - *A doc that describes what the series changed belongs to every round.* O passo 7 lê só a doc em
    CHANGED_FILES da rodada. O `docs/monitor.md` teve a rodada limpa antes de a releitura da data e
    o aviso dela existirem, e três rodadas passaram sem ele. Foi escrever a frase que faltava que
    expôs o texto falso do aviso.
- **`detection-passes.md`, 6.12, um bullet novo:** *An ordering guard tested in the order the
  directory already gives.* O `os.listdir.__doc__` diz "The list is in arbitrary order". No ext4,
  o glob listou `nova` antes de `antiga`. O teste espera `antiga`, então o mutante sem `sorted()`
  fica vermelho. Com nomes que o sistema de arquivos já lista na ordem certa, o teste passaria sem
  a ordenação.

Dívida que já existia e não foi mexida aqui: 3 INFO C2 (os contratos dos subagentes, lidos por
caminho absoluto de propósito) e os claims D1 que a auditoria lista em toda execução.

## [2.24.0] — 2026-10-19

### Base velha, branch já mergeada, worktree isolada, e o código que a rodada de fix escreveu vai para agente

Lições de uma sessão no magic_tutor: a revisão do PR #17, que já estava mergeado, e mais 5 rodadas
de fix até o grade A, numa sessão isolada em worktree. O `SKILL.md` muda uma frase e a versão, e
passa de 19.993 para 19.995 chars. Todo o resto vai para as references.

- **`configuration.md`, seção nova *Base and batching*.** O passo 2 do Phase A aponta para ela.
  - Sem `origin/HEAD`, a cadeia parava no `main` local, que estava 24 commits atrás. O range saía
    com 22 commits e dois PRs já mergeados.
  - A branch já mergeada dava diff vazio contra o `origin/main`. O range do PR é
    `git merge-base <merge>^1 HEAD`, com o merge achado por
    `git log --merges --ancestry-path HEAD..origin/main`. Medido: deu exatamente os 9 commits.
  - Uma sessão isolada em worktree recusa a cadeia de git, o heredoc da sonda de docstrings e um
    argumento calculado em runtime. A saída é uma chamada simples por comando, `/usr/bin/git` e
    scripts no scratchpad.
  - A justificativa do lote ("every extra orchestrator turn is a main-model round-trip…") saiu do
    `SKILL.md` e foi **movida** para essa seção: o espaço pagou o ponteiro sem passar do teto de
    20 mil chars.
- **`grep` por caminho absoluto** (`configuration.md`, `per-file-agent.md`, `sweep-agent.md`). Pelo
  hook do rtk, o `grep` mostrou só as linhas `def` e `[+32 more]`, enquanto o `/usr/bin/grep`
  mostrou as quatro linhas que a checagem cross-file precisava. No sweep, uma referência escondida
  vira código morto.
- **`configuration.md`, *Re-review rounds*: o código que a rodada de fix escreveu vai para um
  agente**, como já fazia o doc da sessão. Com ≤3 CODE, o atalho inline punha o orquestrador para
  dar nota ao próprio fix. Nas rodadas 2 a 4, o agente achou o único MEDIUM de cada uma, e um
  teste escrito antes ficou vermelho em cada caso.
- **`configuration.md`, *Runtime evidence*: operação de arquivo num destino montado se reproduz no
  destino real**, com um arquivo descartável que é apagado em seguida, entre rodadas e com a pasta
  nomeada no relatório. Um LOW `needs reproduction` sobre `os.utime` virou HIGH: o `/mnt/g` (drvfs,
  arquivos do root) respondeu `PermissionError [Errno 1]`, e toda cópia para o Drive falhava desde
  o commit.
- **`configuration.md`, mutante que não compila.** O filtro ganhou `IndentationError` e o resumo
  `1 error` do pytest (erro de coleta, sem `failed`). Um mutante que apagou a única linha de um
  `if` foi contado como morto até a troca por `pass`.
- **`report-template.md`**: a sonda de docstrings em heredoc é recusada numa worktree isolada; o
  script vai para o scratchpad.

Dívida que já existia e não foi mexida aqui: 3 INFO C2 (os contratos dos subagentes, lidos por
caminho absoluto de propósito) e os claims D1 que a auditoria lista em toda execução.

## [2.23.2] — 2026-10-19

### A prova da sabotagem conta o texto no arquivo, não no `git diff`

`coderabbit-pr` 4.5.1. Lição do `/coderabbit-pr` do PR #8 do magic_tutor (três rodadas do Codex,
fix-loop com sabotagem em cada achado). Só a reference muda; os dois `SKILL.md` mudam só a versão,
com o mesmo número de chars (19.991 e 19.993).

- **`fix-loop.md`, passo 4.** A prova de que a sabotagem entrou no arquivo era ver a linha no
  `git diff`. Na segunda sabotagem da sessão (`tm_year < 2026` virou `< 2027` por `sed`),
  `git diff tests/test_replays.py | grep '^+.*2027'` não imprimiu nada, embora os dois testes
  tivessem ficado vermelhos. Num repositório de rascunho com o mesmo arquivo: `git diff` e
  `rtk proxy git diff` mostraram a linha; `rtk git diff` saiu com rc 1, porque indenta cada linha
  mudada (`  +…`); `grep -c 'tm_year < 2027'` no arquivo contou 1. O hook do `rtk` troca o comando
  em umas chamadas e não em outras (na primeira sabotagem da sessão o `grep '^+'` achou a linha),
  então quem chama não sabe qual saída vai receber. Agora o passo manda contar com
  `grep -cF '<texto>' <arquivo>`.
  - **Por quê:** uma conferência vazia lida como "não entrou" refaz uma sabotagem que já valia; o
    caso pior é o contrário, uma conferência que não olha nada deixando passar a sabotagem que
    não entrou.

## [2.23.1] — 2026-10-19

### `diff` pelo caminho absoluto, lista de caminhos fora de variável, sonda no worktree e mutantes numa cópia

Lições da revisão das mudanças não commitadas do `magic_tutor` (coach do monitor ao vivo), em modo
`worktree` e três rodadas até a nota A. Só as references mudam; o `SKILL.md` muda só a versão e
continua com 19.993 chars.

- **`/usr/bin/diff` na checagem de cópia velha** (`configuration.md`, *Stale copy*). O `diff` passou
  pelo hook do `rtk` e respondeu `[ok] Files are identical`, rc 0, para os `SKILL.md` 2.21.2 e
  2.23.0, que diferem em quatro trechos; o `/usr/bin/diff -q` respondeu `differ`, rc 1. Lido como
  igual, a revisão teria rodado as instruções da 2.21.2, sem agente para os docs escritos na sessão;
  na rodada 1 esses agentes trouxeram 5 achados, 3 mantidos.
- **Lista de caminhos nunca numa variável sem aspas no zsh** (`configuration.md`, *Path-scoped
  reviews*). A regra já existia dentro do item das exclusões; ganha item próprio, com a consequência
  medida: `git diff HEAD --stat -- $F` não imprimiu nada, e o mesmo `$F` entregou um diff vazio ao
  pré-scan de segredos, que só não passou calado pelo erro `empty input`. A sessão chegou a culpar o
  `rtk` por isso; o `git diff` pelo `rtk`, com os caminhos escritos, funcionou no pipe.
- **Sonda de docstrings no modo `worktree`** (`report-template.md`). A sonda lê `HEAD` e compara
  `{MERGE_BASE}...HEAD`; no `worktree` a base é o próprio `HEAD`, então ela não vê linha nova. Lá, o
  diff é `git diff -U0 HEAD -- <file>` e o arquivo é lido do disco; assim a sonda listou o módulo,
  a classe e as duas funções tocadas.
- **Mutantes numa cópia** (`configuration.md`, *Reproduce between rounds*). Com os testes que
  precisam só de poucos arquivos, o módulo e os testes copiados para a scratchpad recebem os
  mutantes enquanto os agentes ainda leem a árvore, que não muda: 9 mutantes, todos mortos, e o
  `git status` igual ao de antes. Um deles (M8) sobreviveu na primeira passada e ganhou o teste que
  faltava.
- **`git stash create` medido numa revisão de verdade** (mesmo item). O retrato tirado antes das
  correções foi a base das rodadas 2 e 3, e o `git stash list` continuou vazio; antes a skill só
  dizia que ele tinha sido conferido num repo de rascunho.
- **Dívida que continua:** o `SKILL.md` segue a 7 chars do aviso do C1 (20.000).

## [2.23.0] — 2026-10-19

### Doc de pipeline vai para agente e stale copy segue o texto instalado

Duas lições do PR #10 do dotp-remake (a fatia 3.2a, entregue pelo `sdd run` do kit `sdd_agents` e
revisada em mais duas rodadas até a nota A).

- **Doc escrito por um pipeline da sessão também vai para agente** (`SKILL.md`, Fase B;
  `configuration.md`, *Docs this session wrote*). A 2.22.0 mandava para agente só o doc que o
  orquestrador escreveu. O doc escrito pela fase DOCS do `sdd run` ficava no passo 7 da Fase C, e
  ninguém o lia contra o código: a REVIEW do kit roda antes da DOCS, e o passo 7 confere o doc contra
  o diff. Na rodada 2 do PR #10, o agente que recebeu esse doc deu o único MEDIUM da rodada. A fase
  DOCS tinha reescrito a célula do `Add` e posto um ponteiro para ela, e a célula deixava de fora a
  forma `FE_NUM_COLOURS` com `OP_GREATER_THAN`, que o parser aceita num arquivo fora da faixa. Agora
  o doc de um pipeline que a sessão roda ou acompanha conta como escrito na sessão. O `SKILL.md` ganha
  16 chars (19.977 → 19.993).
- **Trecho que muda um passo segue o texto instalado** (`configuration.md`, *Stale copy*). A 2.22.0
  parava e pedia `/reload-plugins` diante de um trecho de passo. Na sessão, a 2.20.0 carregada
  diferia da 2.22.0 instalada em sete trechos além da versão, um deles de passo: a Fase B com agente
  para o doc escrito na sessão. Lido da pasta instalada, junto com a seção que ele cita, esse passo
  foi seguido, e foi ele que deu o MEDIUM acima. A regra antiga teria parado a rodada na Fase A.
  Agora o trecho e as seções que ele cita, lidos da pasta instalada, são o texto a seguir; com
  trechos em várias fases, ler o `SKILL.md` instalado inteiro. O `/reload-plugins` sai do caminho
  da rodada e vira recomendação no relatório final, para a próxima execução.
- **Dívida para uma tarefa própria:** o `SKILL.md` fica a 7 chars do aviso do C1 (20.000). O próximo
  retrofit não cabe sem uma passada da `skill-refactoring` (extrair ou comprimir).

## [2.22.0] — 2026-10-19

### Doc escrito pela sessão vai para agente, sonda por literal de registro e stale copy que lê o diff

Três lições do PR #9 do dotp-remake (7 rodadas até a nota A).

- **Doc escrito pela própria sessão vai para um agente da Fase B** (`SKILL.md`, Fase B;
  `configuration.md`, *Docs this session wrote*; `per-file-agent.md`). A Fase B só mandava CODE (e
  TESTS no foco de testes) para agente, e o DOCS ficava no passo 7 da Fase C, feito pelo
  orquestrador. Quando foi ele quem escreveu o doc, aquilo era autorrevisão. Na sessão, o agente
  lançado à mão para o doc de conhecimento e o handoff que o orquestrador escreveu achou todos os
  MEDIUM das rodadas 2 a 6 (2, 2, 1, 1, 1). Agora o doc com afirmações factuais escrito na sessão vai
  para o agente com o prompt padrão e a categoria `DOCS (written this session; evidence: <path>)`,
  também quando a Fase B rodaria inline. O contrato do agente ganha a linha do DOCS (6.5 no centro,
  cada afirmação contra a evidência), e o prompt de lançamento continua sem texto extra. Junto, a
  lição de convergência: numa série que acha a próxima frase do mesmo doc, recomendar tirar a
  afirmação, não acrescentar evidência (cada palavra nova virou achado nas rodadas 3 a 6).
- **Sonda de teste pelo literal de registro** (`configuration.md`, depois do parágrafo de C#). Um
  tipo que os testes nunca nomeiam (registrado por string num catálogo) escapava da sonda por tipo.
  Medido no PR B do dotp-remake (14 classes `internal sealed` de palavra-chave, 37 testes alterados):
  nenhum teste nomeia o tipo, e os acertos do `-w` eram texto de carta nas fixtures, um
  `d.Defender` sem relação e um literal de id inválido. O id entre aspas achou 14 de 14, todos em
  testes de palavra-chave; sem aspas, `reach` casa 6 arquivos contra 2. Em 4 dos 14 o único acerto é
  a lista do registro, o que prova o registro e não o comportamento, e a Fase C diz qual dos dois.
- **Stale copy lê o diff antes de parar** (`configuration.md`, *Stale copy*). A regra parava em
  qualquer linha além do `version:`. Na sessão, a 2.20.0 carregada diferia da 2.21.2 instalada em
  quatro trechos, nenhum de passo (ponteiro para `assets/`, razão da nota de custo, frase do só
  leitura reescrita, ponteiro do stale copy), e a revisão seguiu com a pasta instalada até a nota A.
  Agora o trecho que muda um passo (comando, fase, portão, limite, contrato ou prompt de agente)
  ainda para; os outros vão listados no Cost footprint.
- **`SKILL.md` no teto do C1:** a rota nova da Fase B coube fundindo os dois parênteses da lista de
  *References* que repetiam os prompts de lançamento do próprio `SKILL.md` ("it carries your
  instructions, scope and output format"; "it carries the two buckets, the guardrails and the
  return template"). 19.999 → 19.977 chars.

## [2.21.2] — 2026-10-18

### Casos de gatilho, claims datados e os C2 que a auditoria já entende

Tratamento da dívida que a `skill-quality-audit` apontava na `codereview`, com autorização de reparo
do dono.

- **F4, `assets/trigger-evals.json`:** a `codereview` não tinha casos de gatilho (o `coderabbit-pr`
  tinha). Entram 17, no formato dele: 9 que devem disparar (revisão pré-PR, rodada `base=<sha>`,
  segredos e código morto, foco em bugs, repo de um commit) e 8 que não (comentários de bot no PR,
  CI vermelho, abrir PR, explicar arquivo, refatorar, auditar skill, merge, escrever testes). O
  `SKILL.md` o cita em *References* ("read before changing the `description`"), porque asset não
  citado é AVISO B1 de órfão. Para caber no teto do C1, o parágrafo *Read-only* foi reescrito no
  lugar sem perder conteúdo (Estratégia B da `skill-refactoring`; o `repetidos.py` não achou texto
  repetido a retirar com prova).
- **D1, 113 claims (`--claims`), um veredito cada:** 97 não são afirmação (número de pass ou seção,
  como `6.10` e `§6.9`, e os títulos 1.1 a 4.2 do catálogo TOCTOU), 11 já estavam datados, 1 tem
  sensor (`metadata.version`: `validate-versions.py` e o primeiro cabeçalho deste CHANGELOG) e 4
  ganharam data. O `SKILL.md` dizia que um agente sem `model: "sonnet"` cobra "2.5× to 5×" o preço
  do Sonnet; nos preços de 2026-10 o Opus 5.5 custa 2× o Sonnet 5.5 ($4/$20 contra $2/$10 por MTok),
  e passa a dizer isso. No `report-template.md`, o incidente do cache 2.1 com a 2.6.0 instalada
  ganha a data (2026-10-03, entrada 2.8.0) e as duas leituras que não são cópia velha também
  (2026-10-06, entrada 2.13.0). O D1 segue como INFO: ele conta candidatos, e a contagem não zera.
- **C2:** os 3 avisos (`per-file-agent.md`, `sweep-agent.md` e `detection-passes.md` citam outras
  references por `{SKILL_DIR}/references/`) saem INFO desde a `skill-quality-audit` 0.8.0, que
  reconhece o contrato de subagente. Nada mudou aqui; a auditoria da `codereview` fica com 0 aviso.
- **`SKILL.md`:** 19.999 chars, no limite do C1 (AVISO acima de 20.000). A próxima lição que precisar
  de linha nele pede extração para `references/` antes.

## [2.21.1] — 2026-10-18

- **`references/configuration.md`, *Re-review rounds*:** o renome da rodada 10 trocou **54**
  pares (função, nome), não 55. O número da 2.21.0 foi somado de cabeça, e a soma pelo mapa do
  renomeador dá 54 (25 funções, 34 nomes distintos, 7 arquivos). É o caso da regra *a fix that
  writes "measured" measures the exact line it writes*, na própria lição. Corrigido também na
  entrada da 2.21.0.

## [2.21.0] — 2026-10-18

### A cópia velha que só difere na versão, e o renome por posição de sintaxe

Lições das rodadas 4 a 10 do `/codereview` da S9 do ui24_agent (Python, `e1a6f69..`), que rodaram
com a cópia 2.18.4 carregada na sessão e a 2.19.0 instalada.

- **`SKILL.md`, fase A:** a cópia fora do `installPath` deixa de parar a revisão por qualquer
  diferença do `diff -rq` e manda para a seção nova *Stale copy* de `references/configuration.md`.
  Lá a comparação é entre os dois `SKILL.md`: se só a linha `version:` difere, o `{SKILL_DIR}` passa
  a ser a pasta instalada e a revisão segue, porque as instruções em contexto são as mesmas e o
  resto (os contratos dos agentes, o `scan_secrets.sh`) é lido por caminho absoluto. Outra linha
  diferente continua pedindo `/reload-plugins`. O `diff -rq` das pastas da skill difere em toda
  release dela, porque a linha `version:` muda junto, e a regra da 2.13.0 teria parado a rodada 4 na
  fase A. Medido: a 2.18.4 contra a 2.19.0, e depois contra a 2.20.0, só a linha da versão. O
  `SKILL.md` cai de 19.990 para 19.973 chars.
- **`references/configuration.md`, *Re-review rounds*:** renomear identificador entre rodadas por
  posição de sintaxe (`ast.Name` e `ast.arg` da função, ou os tokens `NAME` para um nome único no
  módulo), nunca por `sed`. O fonte é lido com `io.StringIO(src).readlines()`, porque
  `str.splitlines()` também quebra em `\x0c`, `\x85` e `\u2028`; o `col_offset` conta bytes UTF-8; e
  o diff é provado token a token. Medido: um `cli.py` com um `\u2028` num literal dá 5633 linhas ao
  `splitlines()` e 5632 ao AST, e o renomeador da rodada 4 parou com `StopIteration`; a rodada 10
  renomeou 54 locais em 7 arquivos (182 ocorrências) e a suíte seguiu verde.
- **Dívida pré-existente (não tocada):** os 3 avisos C2 dos contratos que os agentes leem por
  caminho absoluto.
- **Fora do escopo, sugestão:** a `coderabbit-pr` (`references/pr-branch.md`, fase 1.1) segue só
  quando a pasta dela é igual à instalada; a comparação pelo `SKILL.md` valeria lá também, mas não
  foi medida nela.

## [2.20.0] — 2026-10-18

### Cobertura de testes sem os arquivos só de comentário, e a sonda por nome de tipo

Lições da rodada 7 do `/codereview` do PR A da fatia 3.1 do dotp-remake (motor de regras em .NET,
`dbefae4..3f1f721`), que rodou a cópia 2.18.6.

- **`references/report-template.md`, *Test Coverage*:** status novo `DOC_ONLY`, para o arquivo CODE
  cujo diff só muda comentário ou docstring (toda linha `+`/`-` do `git diff -U0` é comentário).
  Ele sai do numerador e do denominador, e o `Total_CODE` passa a descontá-lo; a fase C decide,
  porque a sonda da fase A só vê se o teste existe e se mudou. Na rodada, 6 dos 15 arquivos CODE só
  mudaram XML doc (zero linhas fora de `///`, `//` e `*`): a fórmula deu 67% (10/15), com quatro
  deles como `STALE_TESTS` e dois como `WITH_TESTS` só porque um teste da mesma suíte mudou por um
  renome. Sem eles, 8/9 (89%).
- **`references/configuration.md`, depois dos exemplos de C#/.NET:** onde o import aponta namespace
  e não arquivo (`using` do C#, `import` de pacote do Java e do Kotlin, Go), a sonda `{Base}Tests.cs`
  e o "teste alterado que o importa" quase não acham nada; a sonda passa a ser pelo tipo
  (`git grep -lw <Tipo> -- <pastas de teste>`). Na rodada, pelo nome do arquivo foram 6 de 15, pelo
  tipo mais 7, e sobraram 2 (um testado só pela suíte de outro tipo, um sem teste); o PR anterior do
  mesmo repo mediu 27 de 41 pelo tipo e quase nenhum pelo nome do arquivo.
- **Investigado e descartado:** o hook `rtk` reescreve `cd X && git diff ... --unified=0 | cmd`
  (acrescenta `--stat`, volta o contexto de 3 linhas e um trailer `... (more changes truncated)`),
  mas o `iter_added_lines` do `scan_secrets.py` viu as mesmas (arquivo, linha, conteúdo) que no diff
  cru: 450/450 no intervalo da rodada e 6729/6729 no PR inteiro. O pré-scan não fica cego; nada
  muda na skill.
- **`SKILL.md`:** só a versão muda; segue em 19.990 chars, no teto do C1. Dívida pré-existente
  (não tocada): os 3 avisos C2 dos contratos que os agentes leem por caminho absoluto.

## [2.19.0] — 2026-10-18

### O pre-scan de secrets diz quanto leu, e o `coderabbit-pr` conserta PR já mergeado

`coderabbit-pr` 4.5.0. Lições da missão de release do jrc-libs (2026-10-16 a 2026-10-18): rodadas
de `/codereview` sobre um plano e sobre o `release.sh`, e o `/coderabbit-pr` dos dois P1 do Codex
no PR #3, já mergeado.

- **`scripts/scan_secrets.py`:** `printf '' | scan_secrets.sh` saía com `findings: []`,
  `errors: []` e rc 0, e o relatório leria PASS sobre um diff que ninguém leu. Num quase-acidente,
  o `-- $P` que o zsh não divide deu `--name-only` vazio. Agora o JSON traz
  `scanned: {files, added_lines}` (`files` conta os cabeçalhos `diff --git`, e sem eles os `+++`), e
  a entrada vazia ou só de espaços põe em `errors` um `empty input: …` que diz para refazer o passo
  8. Um `--base` cujo `git diff` falha também cai nesse erro, porque devolvia `""` em silêncio. 4
  testes novos (12 no total); as 7 sabotagens das linhas novas ficaram vermelhas, e a que contava só
  os `+++` pediu um arquivo binário no caso do git. Em dois intervalos do jrc-libs, `scanned.files`
  deu igual ao `--name-only` (62 e 9).
- **`references/report-template.md`, *Secrets Detection*:** linha `Scanned:` e o status `NOT RUN`
  (erro `empty input`, ou `scanned.files` abaixo do CHANGED_FILES). `NOT RUN` nunca é o status
  final: refaz-se o passo 8 com o mesmo range e os mesmos pathspecs do passo 5.
- **`references/configuration.md`, *Re-review rounds*:** dois bullets. *A fix that writes
  "measured" measures the exact line it writes*: na rodada 2 de um plano revisado como CODE, o
  "medido" cobria só a espera (`timeout 590 tail --pid`), e a rodada 3 voltou HIGH no one-liner
  `l=$(mktemp) && nohup … &`, cujo `&` manda a lista `&&` inteira para o fundo. *Reflow prose by
  script, never by hand*: três reflows à mão emendaram linhas, e cada um voltou como LOW. O script
  que resolveu (mantém inteiro o trecho entre crases e falha se as palavras mudarem) vai no bullet,
  testado a partir do próprio texto da reference.
- **`coderabbit-pr`, `references/pr-branch.md`:** seção nova *A PR already merged*. Com `MERGED` na
  1.1, o conserto vai para um worktree num branch novo saído da base (`--no-track`, para um
  `git push` sem argumento não ir para a base), a 5.0 confere o head do PR novo, cada thread do PR
  mergeado recebe uma resposta com o link antes da 5.2, e a 5.3 conta no PR mergeado. No PR #3, os
  P1 chegaram às 23:10 UTC e o usuário mergeou primeiro, às 23:36 (`650f4cb`); o conserto saiu no
  #4, e a contagem deu `total: 2 unresolved: 0`. *Where the fixes are made* ganha o bullet que
  aponta para a seção.
- **`coderabbit-pr`, `references/fix-loop.md`, passo 4:** a saída para a janela que nenhum teste
  alcança, como duas atribuições seguidas num processo shell, que só um sinal acerta. Nesse caso, a
  invariante vai num comentário nas linhas, no commit e no relatório final. No `release.sh` do PR
  #4, 19 de 20 sabotagens ficaram vermelhas, e a verde passava `publica=1` para depois de
  `armado=0`.
- **`coderabbit-pr`, `references/thread-resolution.md`, 5.0:** um pre-push que recusa árvore suja
  recusa também o checklist não rastreado na raiz (`?? codex-review.md`). Antes do push, o checklist
  sai para um diretório de rascunho, nunca com `--no-verify`. A 5.0 também aponta para o PR
  mergeado.
- **`SKILL.md` (os dois):** só a versão muda, porque estão em 19.990 e 19.991 chars, no teto do C1.
- **Não entrou:** "a cópia velha mesmo depois do `/reload-plugins`", que o transcript refutou (a
  regra atual está certa), e o custo da Fase B rodando no contexto principal numa sessão longa, que
  não foi medido.

Dívida pré-existente, não tocada: 3 AVISO C2 no `codereview` (os contratos dos agentes, lidos por
caminho absoluto).

## [2.18.6] — 2026-10-18

### Projeto inteiro num repo de um commit, rodadas sem commit, docstring rebaixada pelo agente e âncora de mutante repetida

Lições de uma revisão "até tudo A" do magic_tutor (Python: monitor ao vivo do MTG Arena e scripts;
repo com um commit só no `main`; 5 rodadas, B → A, com 26, 7, 4, 2 e 0 achados; as correções
ficaram sem commit, como o usuário queria).

- **`references/configuration.md`, linha `worktree`:** no `main` de um repo de um commit só, o
  `worktree` automático revisaria só o pendente (um `TODO.md` e 60 transcrições) e daria "A, sem
  CODE". Pedido o projeto inteiro, o range é a árvore vazia do git (`4b825dc…`) com o diff de dois
  pontos escrito por extenso; o de três pontos falha (`fatal: Invalid symmetric difference
  expression`).
- **`references/configuration.md`, *Re-review rounds*:** `base=<head anterior>` supõe um commit por
  rodada, e sem commit não há ref do que a rodada revisou. Bullet novo: `S=$(git stash create)`
  quando a rodada é lançada, e a seguinte escreve `git diff $S -- <file>` nos prompts. As rodadas 3 e
  4 fizeram o mesmo com cópias no scratchpad e `diff -u`; o `stash create` foi conferido depois num
  repo descartável (árvore, índice e lista de stash intactos; não rastreados ficam de fora).
- **`references/detection-passes.md`, 6.5.1:** os 5 agentes por arquivo registraram como LOW as 43
  lacunas públicas de docstring (um escreveu "the rubric would grade … HIGH; I downgraded it"), e o
  probe deu público 15/58. O agente mantém a severidade da 6.5.1; rebaixar por convenção do projeto
  é decisão da fase C, tomada a partir do probe.
- **`references/configuration.md`, mutante que não compila:** "exact text replacement that must
  change the file" ganhou "occurs once". Depois de uma correção, `except FileNotFoundError:` passou a
  aparecer duas vezes no arquivo, e o assert de unicidade parou o script antes de gravar.
- **`SKILL.md`:** só a versão muda (2.18.4 → 2.18.6, junto com o plugin; a 2.18.5 tocou só o
  `coderabbit-pr`). Continua em 19.990 chars, no teto: as lições foram para as references.

Dívida pré-existente, não tocada: 3 AVISO C2 (os contratos dos agentes, lidos por caminho
absoluto) e INFO F4 (sem evals).

## [2.18.5] — 2026-10-18

### `coderabbit-pr` segue com a cópia em cache igual à instalada e lê o estado do Codex pelo marcador

coderabbit-pr 4.4.5; `codereview` fica em 2.18.4 (não mudou). Lições do PR #7 do dotp-remake.

- **`references/pr-branch.md`, *Is this run the installed copy?*:** `STALE` mandava parar e pedir
  `/reload-plugins` mesmo quando a pasta desta skill é igual nas duas cópias. Na sessão, a skill veio
  do cache 2.18.3 com a 2.18.4 instalada, e o `diff -rq` das duas pastas `coderabbit-pr` deu vazio:
  a 2.18.4 só tinha mudado o `codereview`. Agora um `diff -rq … && echo same` decide antes da parada,
  como o `report-template.md` do `codereview` já fazia no rodapé. A prova é o código de saída: na
  mesma sessão um `diff` reescrito por hook disse "Files are identical" de dois arquivos diferentes.
- **`references/reviewer-registry.md`, Codex:** o resumo do Codex traz um marcador
  `codex-review-state:v1` com `status`, `commit_sha` completo e `has_any_findings`. O comando novo
  lê os três de uma vez, e `completed` no head com `findings=false` é o caso (a). Sem achados o Codex
  não posta review object nem comentário inline (no PR #7: 0 reviews do bot, só o resumo e um 👍).
- **Não entrou:** apontar os agentes do `codereview` para o `installPath` quando a cópia carregada é
  velha. Funcionou uma vez, mas a diferença entre as cópias (o destino dos LOW além do teto) não foi
  exercitada, e o `SKILL.md` está em 19.990 chars.

## [2.18.4] — 2026-10-17

### Os LOW além do teto ficam no relatório: a skill não escreve arquivo

Achado do Codex (P2) na segunda análise da 2.18.3 (j0ruge/skills PR #4): o overflow dos LOW além
do teto de 50 mandava criar um arquivo no scratchpad, e `SKILL.md` *Operating Constraints* proíbe
criar arquivos e diz que o relatório na conversa é a única saída. A lição da 2.18.3 continua (os
LOW cortados precisam de destino, porque o corpo do PR lista todos os adiados), mas o destino passa
a ser o próprio relatório.

- **`references/report-template.md`, *Findings Table*:** sob a tabela, uma linha por LOW cortado
  (`file:line — finding`); sem arquivo e sem caminho absoluto.
- **`SKILL.md`, *More than 50 findings*:** "the rest go to a scratchpad file" virou "the rest one
  line each below it"; o `SKILL.md` fica em 19.990 chars.

## [2.18.3] — 2026-10-17

### PR grande sem corte, LOW além do teto num arquivo, mutante que não compila e `__pycache__` dos agentes

Lições do PR #6 do dotp-remake (motor de regras .NET/C# + um script Python; 3 rodadas, B → B → A;
rodada 1 com 42 arquivos CODE em 15 agentes sonnet).

- **`SKILL.md`, Phase A e *Operating Principles*:** "more than 15 CODE files → prioritize by change
  size, note deprioritized" e "cap analysis at 15 full file reads across all agents" não diziam se era
  para cortar arquivos, e o teto de 15 leituras só cabe cortando. Agrupados 3 por agente, os 42 CODE
  leram 55 arquivos inteiros; o MEDIUM de cobertura da rodada (`CoreConstants.cs`, +61 linhas) estava em
  17º por diff stat e cairia num corte dos 15 maiores. Agora o tamanho só ordena os grupos e todo
  arquivo recebe agente. A frase do teto saiu: foi fundida na regra da Phase A e é desmentida pela
  medição acima.
- **`references/report-template.md`, *Findings Table* (e `SKILL.md`, *More than 50 findings*):** os
  LOW cortados pelo teto de 50 só tinham "rode de novo por arquivo". Rodada 1: 65 LOW, 18 cortados; o
  corpo do PR lista todos os adiados, e eles só chegaram lá por um arquivo do scratchpad. Agora o corte
  vai para esse arquivo, citado pelo caminho absoluto na linha de overflow.
- **`references/configuration.md`, *Re-review rounds*:** bullet novo, "A mutant that does not build is
  not a kill". Um regex sobre uma linha C# partiu uma string interpolada no `;` (CS1002) e um `throw;`
  deixou `catch (… e)` sem uso (CS0168, erro com warnings como erros); o filtro `Passed!|Failed!` não
  imprimiu nada para os três mutantes. Reescritos por troca exata de texto, reprovaram 1, 2 e 1 testes.
- **`references/configuration.md`, mesmo bloco:** `PYTHONPYCACHEPREFIX` virou `-X pycache_prefix=<dir>`.
  Sob `-I` (que ignora toda variável `PYTHON*`) a variável é descartada em silêncio: medido
  `sys.pycache_prefix = None` e o `.pyc` ao lado do fonte; com `-X`, 18 `.pyc` no prefixo e nada no fonte.
- **`references/sweep-agent.md` e `references/per-file-agent.md`:** checagem de sintaxe Python por
  `ast.parse`, nunca `py_compile`. A varredura da rodada 3 rodou `python3 -I -m py_compile` e deixou
  `?? scripts/__pycache__/` no repositório numa revisão read-only; `PYTHONDONTWRITEBYTECODE=1` não
  impede o `py_compile` (medido). `ast.parse` não escreve nada e sai com rc 1 num `SyntaxError`.
- O `SKILL.md` fica em 19.991 chars (era 19.990): as linhas novas foram compensadas pela frase do teto.

Dívida pré-existente, inalterada: 3 avisos C2 (contratos dos agentes lidos por caminho absoluto, por
desenho).

## [2.18.2] — 2026-10-17

### Veredito por parte: a parte de um achado que some em silêncio volta na rodada seguinte

Lição das rodadas do PR #5 do dotp-remake (motor de regras .NET/C#; 3 rodadas, B → B → A).

- **`references/report-template.md`, *Findings Table*:** na rodada 1, o agente de combate listou seis
  ramos sem teste num único achado MEDIUM (509.1h, 506.4 em `Combat.cs:38/69/75`, 704.5f, empate,
  recusa de atacante, poder 0). A calibração da Phase C manteve quatro, descartou um com motivo
  (704.5f, mutante equivalente) e não disse nada do sexto (atacante que sai do combate, 506.4). A
  lista de correções saiu só com os mantidos; a rodada 2 levantou o 506.4 de novo, os mutantes de
  `Combat.cs:38` e `:75` sobreviveram, e o PR custou uma rodada a mais. Agora cada parte descartada
  vai nomeada sob a tabela com o motivo, e a lista de correções nomeia as mantidas. O arquivo é lido
  no passo 10 de toda rodada, a primeira inclusive.
- **`references/configuration.md`, *Re-review rounds*:** o bullet que manda responder a um achado
  repetido citando o veredito anterior ganhou a outra metade: só um veredito escrito por parte pode
  ser citado; parte descartada sem ele conta como achado novo.
- O `SKILL.md` não mudou além da versão: ele está em 19.990 chars, no teto de ~20 mil da spec.

Avaliadas e não aplicadas: mutantes equivalentes (já em 6.12, "measure the boundary first");
Codex como comentário de issue, cota do Copilot e CodeRabbit Free (cobertos pelo `coderabbit-pr`);
`echo ======` no zsh (erro do orquestrador, não instrução da skill); mandar os testes de uma rodada de
correção a agentes com foco `tests` (evidência de uma sessão; a skill já sustenta a nota com mutantes).

Dívida pré-existente, inalterada: 3 avisos C2 (cadeia de references a mais de um nível — os contratos
dos agentes são lidos por caminho absoluto, por desenho).

## [2.18.1] — 2026-10-17

### Read-only também é o HEAD: o agente de sweep que rodou `git checkout`

Lição de uma rodada de re-revisão (`base=6db2ab6`, fim em `3391a14`) num repositório .NET/C#
(dotp-remake), com a `main` já mergeada na mesma árvore do fim do range.

- **`references/sweep-agent.md` e `references/per-file-agent.md`, frase de abertura:** o agente de
  sweep, para fazer grep na árvore do commit revisado, rodou `git checkout --detach 3391a14` e tirou o
  checkout do usuário da `main`. Ele próprio relatou o checkout e voltou à `main`; a árvore ficou
  limpa, mas o HEAD de quem orquestra foi movido no meio da rodada. Os dois contratos diziam só
  "read-only" (sem escrever arquivos), e o agente não leu mover o HEAD como escrita. A proibição de
  `checkout`/`stash` já existia, mas em `configuration.md` (*Re-review rounds*), que o orquestrador
  lê e os agentes não. Agora a frase de abertura dos dois contratos diz que read-only cobre o HEAD e
  o índice, e dá o jeito certo de ler outro commit: `git show <ref>:<file>` ou `git grep <pattern> <ref>`.
  Na rodada seguinte, com a proibição escrita no prompt, os 3 agentes a cumpriram — uma rodada, indício
  e não prova.

Avaliadas e não aplicadas, por já estarem cobertas na fonte: "6.11 never touch the grade gate"
(`detection-passes.md`, 6.11: "not a grade gate: it never forces an F"); `testFilePatterns` em .NET
(`configuration.md`: o exemplo `**/*.Tests/**/*.cs` e os testes que são o produto). Não aplicada por
não ser claramente melhor: seguir com os agentes no `installPath` quando o cache está atrás e só os
arquivos do orquestrador diferem — o `/reload-plugins` que a skill pede continua sendo o caminho.

Dívida pré-existente, inalterada: 3 avisos C2 (cadeia de references a mais de um nível — os contratos
dos agentes são lidos por caminho absoluto, por desenho).

## [2.18.0] — 2026-10-17

### A pasta sem git, o módulo que o probe não via e os testes que nenhum agente lê

Lições das três rodadas do `/codereview:codereview` (2.17.0) numa pasta de scripts Python e shell com
um deck HTML (Windows sob WSL), que fecharam em A em todas as linhas da nota.

- **`references/configuration.md`, seção nova *Folder without git*; `SKILL.md`, *Error Handling* e a
  rota do `configuration.md`; `report-template.md`, Troubleshooting:** a pasta nunca teve repositório,
  e o passo 1 do Phase A deu `fatal: not a git repository (or any parent up to mount point /mnt)`, rc
  128. O *Error Handling* mandava parar, e o Troubleshooting só dizia para rodar onde houver `.git`. O
  que funcionou nas três rodadas: `GIT_DIR=<scratchpad>/review.git GIT_WORK_TREE=<pasta>`, `git init -b
  main` com `core.fileMode false` (o `/mnt/c` entrega tudo como 777), `core.autocrlf false` e `user.*`
  local, commit-raiz vazio como base, arquivos autorais adicionados pelo nome e o prefixo em todo
  comando git, inclusive no prompt de cada agente, com o diff escrito por extenso como no modo
  `worktree`. Foram 6, 6 e 5 agentes sonnet, todos rodaram o diff com prefixo, e nada foi escrito na
  pasta.
- **`references/report-template.md`, probe Python de docstrings:** o probe percorria só funções e
  classes, mas o 6.5.1 conta módulos. O probe da rodada 1, com a linha do módulo, achou 4 de 8 scripts
  sem docstring de módulo, parte do HIGH de Documentation. Dois deles não tinham nenhuma função e não
  teriam linha nenhuma no probe do template. Agora ele imprime `{f}:1 public doc|MISSING <module>`
  antes das funções.
- **`references/configuration.md`, *Re-review rounds*, bullet novo *The tests a fix adds get no
  agent*:** numa revisão completa o Phase B só manda TESTS para agente com o foco `tests`. A rodada 2
  trazia 14 arquivos de teste novos (788 linhas) e nenhum agente; a rodada 3, 8 arquivos (+72/−1). O
  que sustentou as duas notas A de Test Coverage foram 24 + 12 mutantes, um por guarda novo, todos
  mortos. O "Six things decide" da abertura passou a "These decide", porque a contagem deixaria de
  bater.
- **`SKILL.md`, orçamento:** estava a 19.998 chars, como a 2.17.0 avisou. A enumeração do bullet
  *Measure, don't guess* ("the report's last line says which version … whether the sweep ran") saiu
  por já estar no `report-template.md`: a linha do Cost footprint lista esses campos, e a nota abaixo
  dela manda parear com `/cost`. O bullet aponta para lá. Com as duas rotas novas, o arquivo fica em
  19.990 chars.
- **Ficou de fora:** o probe de testes do Phase A não acha o teste de um script com hífen
  (`preparar-ambiente.sh` → `test_preparar_ambiente.py`, já que o `unittest` não importa módulo com
  hífen). A correção não foi verificada e cairia no `SKILL.md`, que está no teto. Dívida
  pré-existente, que não muda aqui: os 3 AVISOs C2 (references lidas pelos agentes por caminho
  absoluto, de propósito).

## [2.17.0] — 2026-10-16

### A âncora que o diff não mostra, a regra que a classificação escondia, e o guarda que respondeu pelo outro

Lições das rodadas 2 a 4 do `/codereview:codereview` na branch `RS-929_apresentacao_manutencao_proativa`
(repos `digital_service_report_api` e `apresentacoes`, `codereview` 2.16.0), que fecharam em A nos dois.

- **`references/detection-passes.md`, 6.5.2, parágrafo novo *Line anchors into a changed file*:** a
  rodada 2 do DSR revisava um diff só de docs, correto em si. As 11 linhas novas numa regra empurraram
  `chaveItem` de 688 para 699, e a âncora `TODO.md:81 → controle-vida-util-consumiveis.md:688` ficou
  fora do alvo num arquivo que não estava no diff. Só o sensor do próprio repo viu
  (`check-todo.sh --check TODO.md`, rc 1, "anchor … is off target"). A fase C passa a rodar
  `git grep -nE '<path>:[0-9]+'` para cada arquivo cujo número de linhas mudou e, quando houver, o
  sensor de âncoras do repo. Fica MEDIUM quando o sensor fica vermelho e LOW nos outros casos.
- **`SKILL.md`, classificação:** `.claude/` ia inteiro para EXCLUDED, mas `.claude/rules/**` é doc viva
  do projeto. A mudança revisada existia para editar `.claude/rules/controle-vida-util-consumiveis.md`,
  e os 2 LOW da rodada estavam nele: uma linha de cerca de 170 colunas e um "tudo abaixo" que
  contradizia a nota logo abaixo. Seguida à letra, a classificação revisaria só o `TODO.md` e a nota.
  Agora: `.claude/ (unless the user names it; rules/ is DOCS)`. São +10 chars, e o arquivo foi a
  19.998, **2 abaixo do aviso C1**. A próxima lição que tocar no `SKILL.md` vai exigir extração
  (`skill-refactoring`), não compressão.
- **`references/detection-passes.md`, 6.12, bullet novo *One case for two guards*:** a correção da
  rodada 1 trouxe dois guardas (`tr -d '\r'` e `[ -s pat ]`) e um único caso (`padroes-vazios`),
  descrito no commit como prova do CRLF. Com uma cópia do script sem o `tr`, o caso continuou dando
  2, porque o guarda de vazio disparava antes. Com os padrões reais em CRLF, a cópia respondeu
  `sigilo ok … 30 padrões`, rc 0, sobre um IP plantado. Ao caso novo `padroes-crlf`, o script sem o
  `tr` responde `exit 0, esperado 1` e o real passa, com 13/13 na suíte. Regra: mutar cada guarda
  sozinho.

Dívida pré-existente, não tocada: os 3 AVISO C2, que vêm dos contratos que os agentes leem por
caminho absoluto, de propósito.

## [2.16.0] — 2026-10-16

### Revisão de vários repositórios, e o sensor que se prova rodando

Lições de um `/codereview:codereview nos repos` na branch `RS-929_apresentacao_manutencao_proativa`
(repos `digital_service_report_api` e `apresentacoes`, `codereview` 2.15.1).

- **`references/configuration.md`, seção nova *Several repositories*:** o pedido nomeava dois
  repositórios e a sessão estava num só. A branch do diretório de trabalho tinha 5 `.md`; o código
  (o sensor de sigilo e o seu teste, o script de medição e o motor HTML do deck) estava na branch de
  mesmo nome no repo irmão. Revisado só o cwd, o relatório daria "A, nenhum arquivo de código" e
  não leria o único HIGH. A seção manda uma fase A por repo (base e varredura de segredos de cada
  um), uma leva só de agentes com o repo escrito no comando de diff, e um relatório com uma coluna de
  nota por repo.
- **`references/detection-passes.md`, 6.11 *Severity*:** a fase C fixa o degrau rodando o sensor
  contra uma cópia da entrada no scratchpad, pelas variáveis que ele já aceita, sem tocar a árvore
  (por isso não espera os agentes, ao contrário do mutante). Um arquivo de padrões com `(` confirmou
  o HIGH (`sigilo ok` com um IP plantado); o caminho do arquivo permitido com byte não UTF-8 não
  reproduziu e caiu para LOW.
- **`SKILL.md`:** a linha que diz quando ler a `configuration.md` ganha "names more than one repo".
  O descritor ": override syntax, presets, code in docs" foi fundido com os gatilhos da mesma frase,
  que já nomeiam os três; o arquivo estava no aviso C1 (20.000) e foi para 19.988.

## [2.15.4] — 2026-10-16

### O Codex que ninguém pediu, e o achado que supõe squash

Lições de um `/codereview:coderabbit-pr` nos PRs #32, #33 e #37 do `lighthouse_project`
(`coderabbit-pr` 4.4.4).

- **`references/reviewer-registry.md`, *Detection Strategy*:** um revisor que só roda sob pedido
  some do relatório quando ninguém pediu. Nos PRs #32, #33, #36 e #37 o Codex não tinha **nenhum**
  evento nos três endpoints, e a Fase 1.2 só lista quem postou: o relatório citaria só o aviso de
  cota do Copilot. O Codex só aparecia onde houve `@codex review` (#29). Pedido, devolveu cinco
  achados reais em cerca de dez minutos. A reference traz o comando que mede a atividade do Codex
  nos PRs recentes (testado no próprio repositório: presente em #29, #32, #33, #36 e #37, ausente
  nos outros cinco) e manda registrar o caso (b) como "nunca pedido" e oferecer o pedido.
- **`references/pr-branch.md`, seção nova:** um achado sobre ancestralidade de commit supõe um
  método de merge. No #37 o Codex afirmou que `3447edb` nunca seria ancestral de `develop`,
  supondo squash; o repositório mergeia com merge commit, e depois de `gh pr merge --merge` o
  `git merge-base --is-ancestor` deu rc 0. A seção diz como ler o método (opções de merge na API e
  `git log --merges`) antes do veredito, e como provar o "não se aplica" depois do merge.
- **`SKILL.md`:** o caso (b) da Fase 2 passa a citar o Codex "never requested". O arquivo estava a
  7 caracteres do aviso C1 (20.000), então a frase foi reescrita sem crescer: 19.993 → 19.991.

## [2.15.3] — 2026-10-15

### O `Completed` do Codex vale só com o sha do head; a pausa do CodeRabbit é lacuna de cobertura

Lições de um `/codereview:coderabbit-pr` no PR #246 do `sdd_agents` e do laço de revisão do PR #252
do mesmo repo, no mesmo dia (`coderabbit-pr` 4.4.3).

- **`references/reviewer-registry.md`, Codex:** o laço de espera aceitava qualquer `Completed`. O
  resumo do Codex é uma linha só, reescrita a cada review, e depois de um push continua dizendo
  `Completed` para o head anterior. Medido no #252 pelo `userContentEdits` do comentário:
  `Completed` no `09681f3` das 19:45 às 23:28 UTC, atravessando o push do `796aa93`. Onde o Codex só
  roda com `@codex review`, o `Completed` velho fica lá até alguém pedir. O comando agora exige o sha
  curto do head na mesma linha e responde `not on <sha> yet` quando ele não está lá (testado em zsh e
  bash: `Completed` no head, `not on 09681f3 yet` no sha anterior). O comando antigo saiu por fusão:
  ele é a primeira metade do novo.
- **`references/reviewer-registry.md`, *Coverage Per Commit*:** o CodeRabbit com
  `reviews.auto_review.auto_pause_after_reviewed_commits` edita o walkthrough para `## Reviews
  paused` e não revisa mais nenhum commit até um `@coderabbitai resume`. A Fase 1.3 descartava o
  aviso como metadado, com razão, e nada o levava para a Fase 2. Medido no #246: a pausa entrou às
  23:53:46Z de 10-11, junto com a review do `0a1f313`, e os três commits da branch e o merge
  seguintes ficaram sem revisor. O grep de cobertura ganhou `Reviews paused`, e a linha de metadados
  aponta para a seção.
- **`references/checklist-template.md` e o registry, severidade:** a tabela punha `🟡` em MEDIUM e
  `Minor` em LOW, e o CodeRabbit escreve sempre o par (`_🟡 Minor_`, `**🟡 Minor**`), então o mesmo
  marcador tinha duas respostas. `Minor` foi para a linha do `🟡`. Medido no sdd_agents (161
  comentários inline do CodeRabbit desde 2026-09-01): 115 com severidade, todos `🟠 Major` (30) ou
  `🟡 Minor` (85), nenhum `🔴` ou `🔵`. As linhas `🔴`, `🔵`, `Low` e `Medium` ficaram: não há prova de
  que estejam obsoletas.
- **`references/pr-branch.md`, seção nova "A PR that does not merge":** o #246 estava `CONFLICTING`
  com todos os achados já corrigidos. Resolver as threads de um PR que não mergeia entrega pela
  metade, porque o merge da base vira um commit que nenhum revisor viu. A Fase 1.1 lê o `mergeable`;
  com conflito, `git merge-tree --write-tree --name-only --no-messages` lista os arquivos sem tocar
  em árvore nenhuma (reproduzido: `ee33e18` × `f0b46fa` → `TODO.md` e `tests/health-baseline.txt`,
  os dois que o merge `383358e` resolveu), e a lista vai ao usuário junto com a autorização de commit
  da 5.0.
- **`SKILL.md`:** só a versão e a linha que roteia o `pr-branch.md` (agora nomeia `conflicts`), de
  19 994 para 19 993 chars.
- **Fora de propósito:** a regra "número de documento que sai de uma receita é afirmação sobre a
  receita" pede o passo 1.5 do `SKILL.md`, que não tem folga. Fica como sugestão: liberar espaço com
  a `skill-refactoring` numa tarefa própria.
- **Dívida pré-existente, não tocada:** os três avisos C2 e o F4 (sem evals) do `codereview`, e o
  `coderabbit-pr/SKILL.md` colado no teto de chars.

## [2.15.2] — 2026-10-14

### Sonda de "apaga no fim" afirma antes o estado gravado

Lição de um `/codereview:coderabbit-pr` no PR #92 do `digital_service_report_api` (RS-925), em que
o fix do achado P2 do Codex grava um marcador `QUEBRADO` e o apaga num refresh ou rollback que dá
certo.

- **`coderabbit-pr/references/fix-loop.md`, passo 1:** uma sonda de algo que o fix grava e depois
  apaga passa verde antes do fix, porque "sumiu no fim" é verdade quando nunca existiu. O passo 4
  ("pelo menos uma fica vermelha") não pega: na sabotagem "o `broken()` não grava o marcador", três
  sondas ficaram vermelhas e a de "um refresh OK apaga o aviso" continuou verde, escondida entre
  elas. Só a leitura de quais ficaram verdes a achou. Medido: com uma afirmação do marcador no meio
  do teste, a mesma sabotagem ficou vermelha e o fix continuou verde (`01a7c87`). O parágrafo novo
  manda afirmar o estado gravado antes da ausência.
- **Fora do `SKILL.md` de propósito:** ele está em 19 994 chars, a 6 do teto do C1, e a reference
  já é roteada na Fase 3.2.
- **Dívida pré-existente, não tocada:** os três avisos C2 e o F4 (sem evals) do `codereview`, e o
  `coderabbit-pr/SKILL.md` colado no teto de chars.

## [2.15.1] — 2026-10-14

### Hash de manifesto não é credencial; a lista de correções do orquestrador também é prosa

Lições de quatro rodadas de `/codereview` sobre a branch RS-925 do `digital_service_report_api`
(scripts bash de refresh de staging), com `base=` encadeado de rodada em rodada.

- **`references/detection-passes.md`, pass 6.10:** o gitleaks (`generic-api-key`) acusou um valor
  hexadecimal de 64 caracteres em `src/test/.integrity.json`, o manifesto com o sha256 de cada
  `*.test.ts`, e o gate forçou F em três rodadas seguidas. Conferido a cada rodada: o valor era
  exatamente o `sha256sum` do arquivo nomeado pela chave. O parágrafo novo diz como provar, mantém a
  regra de nunca remover a linha, e aponta o remédio no repositório: um `.gitleaks.toml` com
  `useDefault = true` e allowlist só do caminho, que o script já passa por `--config`. Medido: com ele,
  o scan da branch voltou `findings: []` com `gitleaks` em `scanners`, e um canário `ghp_…` em outro
  arquivo continuou saindo `github-pat`.
- **`references/configuration.md` §Re-review rounds, bullet novo (agora "Six things"):** duas vezes
  o achado principal da rodada seguinte nasceu do texto que o próprio orquestrador escreveu na lista
  de correções. A mensagem "staging nao foi tocado" para código de saída > 3 voltou HIGH (o ssh devolve
  255 quando a conexão cai depois do comando remoto começar), e "o ponteiro anterior sobrevive a uma
  falha" voltou MEDIUM (o `rollback` passou a confiar no ponteiro velho). Com "nomeie a propriedade,
  não o texto" e "o que o usuário faz depois no caminho mudado" no prompt do corretor, a rodada
  seguinte fechou com 0 HIGH / 0 MEDIUM, depois de reproduzir e refutar as duas MEDIUM alegadas.
  Curva das quatro rodadas: 1H/11M → 1H/2M → 0H/1M → 0H/0M.
- **Investigada e descartada:** a suspeita de que o pre-scan de segredos, recortado por caminho na
  rodada 1, tinha escondido o achado. Rodado no range inteiro do mesmo head sem allowlist, também
  deu 0: o hash acusado só nasceu quando o arquivo de teste foi criado na correção da rodada 1.
- **Dívida pré-existente, não tocada:** os três avisos C2, o `SKILL.md` em 20 000 chars (limite do
  C1) e o F4 (sem evals).

## [2.15.0] — 2026-10-13

### Código dentro de doc vira CODE; o rodapé de custo conta as chamadas pelo harness

Lições de uma revisão do PR #247 do `j0ruge/sdd_agents`: um PR só de docs (plano de missão) cujo
foco era o código que o plano promete (`awk`, regex, Checks), rodado na 2.14.1.

- **`references/configuration.md`, seção nova "Code inside docs":** o diff tinha 10 arquivos, todos
  `.md`/`.txt`. A fase A classificou 0 CODE, e pela regra a fase B não lançaria agente nenhum: o
  relatório daria nota a código que ninguém leu. O que funcionou foi reclassificar o plano como CODE
  e dividir as 1184 linhas em duas faixas na linha `File:` do prompt de lançamento (`1–505`;
  `506–632 + 973–1184`), sem mexer no resto do prompt. Os dois agentes sonnet voltaram com
  achados, e um deles virou o MEDIUM confirmado (`bin/sdd:2978`). A regra irmã já existia: o
  arquivo que o usuário nomeia é CODE, qualquer que seja a extensão (2.11.2).
- **`SKILL.md`:** só a linha que diz quando ler o `configuration.md` ganhou a condição "o foco
  nomeia código num doc". Para caber no orçamento, a lista "(Python, Vue, Node, .NET, shell)" saiu
  da linha e ficou "presets": a lista continua nos títulos do próprio `configuration.md`
  (`grep '^# ' references/configuration.md`). O `SKILL.md` fica em 20 000 chars, no limite do C1.
- **`references/report-template.md` §Cost footprint:** as chamadas de ferramenta de cada agente
  saíam do trailer que o próprio agente escreve. Medido na mesma sessão, os trailers disseram 6 e
  9, e o `<usage><tool_uses>` do harness contou 10 e 14, uns 40% abaixo. Um rodapé feito para
  comparar execuções não pode usar uma estimativa. Agora o número vem do harness quando ele o
  traz, e o trailer fica como recuo e continua sendo a fonte de "files read in full".
- **Dívida pré-existente, não tocada:** os três avisos C2 e o `SKILL.md` encostado no C1, que
  continua sem folga.

## [2.14.1] — 2026-10-07

### A sonda de docstrings lê o arquivo em `HEAD`

- **`references/report-template.md`:** a sonda da 2.14.0 tirava as linhas do diff commitado
  (`base...HEAD`) e lia o arquivo do disco. Com uma edição sem commit no arquivo, as posições se
  desalinhavam: no uso real (SBM-6, 07/10) entrou um `_smtp_send` que o PR não tocou, até a edição ser
  commitada. Num repo descartável, um PR que acrescentava `nova()` saía como `a` (não tocada), e `nova`
  sumia. Agora ela lê cada arquivo com `git show HEAD:./<arquivo>`, o mesmo commit onde o diff termina;
  medido da raiz e de um subdiretório, com o caminho relativo ao diretório atual.
- **Dívida pré-existente, não tocada:** os três avisos C2 e o `SKILL.md` a 5 caracteres do C1.

## [2.14.0] — 2026-10-07

### O scanner externo só vê o diff; decisão registrada encerra o achado; docstrings contadas por visibilidade

Lições de uma revisão do SBM-6 no `~/.hermes` (faixa `47fbe46..HEAD` com pathspec, nota A).

- **`scripts/scan_secrets.py` (correção):** o gitleaks rodava com `--source <repo> --no-git` e o
  ggshield com `secret scan path <repo>`: os dois varriam a pasta inteira, não o diff, e o que
  achavam entrava sem filtro na lista que força a nota F. Reprodução: num repo descartável, um PR que
  só muda `app.py` saía com `('.env', 1, 'github-pat', 'gitleaks')`, com o `.env` ignorado pelo git e
  fora do PR. No `~/.hermes`, o mesmo varrer-tudo estourava os 60 s e o gate ficava só no regex, com
  uma linha em `errors`. Agora `materialize_added_lines` grava numa pasta temporária só as linhas
  acrescentadas, cada uma no seu número; os scanners rodam lá e só fica o achado numa linha
  acrescentada. O `.gitleaks.toml` (por `--config`) e o `.gitleaksignore` (copiado) do repo continuam
  valendo. No caso real, a pré-varredura caiu para 0,1 s com `gitleaks` em `scanners`.
- **`tests/test_scan_secrets.py` (novo):** 8 testes, só stdlib. O do `.env` fora do diff ficou
  vermelho antes da correção; três mutantes (sem o filtro do gitleaks, sem o do ggshield, varrendo a
  pasta do repo) derrubam cada um o seu teste. Os que precisam do gitleaks são pulados sem ele no PATH.
- **Sem medição:** o ggshield não estava instalado na máquina do retrofit. Mudou só o alvo (a pasta
  do escopo) e o filtro, que tem teste com scanner simulado; as flags são as de antes.
- **`references/detection-passes.md` §6.10:** parágrafo novo, o escopo dos scanners externos e o caso
  medido.
- **§6.5.2:** decisão já registrada (handoff, ledger, ADR, "fica fora") encerra o achado que cobre:
  a Fase C cita a decisão em vez de subir a severidade, e lê as docs do projeto atrás da exceção. O
  caso: um MEDIUM "`publico()` falha aberto" era um adiamento escrito no handoff, enquanto a spec
  visual do projeto ainda dizia que nenhum texto de exceção chegava ao e-mail.
- **`references/report-template.md`, cobertura de docstrings:** públicas e privadas contadas à parte,
  a severidade vem da 6.5.1 e não da porcentagem, e uma sonda `ast` para Python. A conta misturada deu
  25/47; separada, públicas 18/22 e privadas 7/25, e as 4 públicas eram as que a 6.5.1 gradua.
- **Dívida pré-existente, não tocada:** os três avisos C2 do baseline (os contratos que os subagentes
  leem por caminho absoluto) e o `SKILL.md` a 5 caracteres do limite de 20 mil do C1; por isso as
  três lições foram para `references/` e o `SKILL.md` só mudou a versão.

## [2.13.0] — 2026-10-06

### A mensagem que pede ação precisa sair quando a ação é feita, e a cópia velha se prova com `diff`

Lições de uma revisão no `sales_quote` (SQ-155), sobre o delta que o pipeline `sdd` não revisou.

- **`references/detection-passes.md` §6.1 (react/node):** item novo, MEDIUM. Uma mensagem que pede ação
  ("confira o endereço", "tente de novo") e não tem caminho que a retire depois da ação continua
  afirmando o que deixou de ser verdade. Uma regra testada numa ordem (editar, depois a mensagem) pede a
  pergunta na outra (a mensagem, depois editar). O achado principal da revisão foi este: um aviso de
  "CEP não encontrado, confira" que sobrevivia à correção do endereço; o teste novo ficou vermelho
  antes do conserto.
- **§6.12:** item novo, "guarda presa numa ordem só". O teste existente provava o silêncio quando a
  pessoa edita **antes** do aviso, e a regressão estava em editar **depois**.
- **`SKILL.md` Fase A:** um `{SKILL_DIR}` fora do `installPath` só é cópia velha se o `diff -rq` contra
  o instalado acusar diferença. Antes, a regra mandava pedir `/reload-plugins` sempre, e a sessão teria
  parado por nada: o cache 2.11.0 e o instalado 2.11.1 eram idênticos na `codereview`.
- **`references/report-template.md` §Cost footprint:** duas leituras que não são cópia velha. A cópia
  idêntica segue e diz isso no rodapé. E o `skill v{X}` é a versão da skill, não a do plugin: num plugin
  com duas skills, a release que só tocou a vizinha deixa esta para trás de propósito (o plugin 2.11.1
  trazia a `codereview` 2.10.0, inalterada). A sessão leu isso como defeito e precisou do histórico do
  git para desfazer o engano.
- **Dívida pré-existente, não tocada:** os três avisos C2 do baseline (instruções que os subagentes leem
  por caminho absoluto) e o `SKILL.md` a 5 caracteres do limite de 20 mil do C1 — a próxima lição que
  entrar nele precisa de `references/` ou de compressão (`skill-refactoring`).

## [2.12.0] — 2026-10-05

### 6.11 ganha a oitava forma: descarte silencioso numa transformação

- **`references/detection-passes.md` §6.11:** "The seven forms" passa a "The eight forms", com
  **Silent drop in a transform**: conversor, ingestão, ETL ou exportação que pula registros por tipo
  sem contar o que descartou, e sem comparação de unidades de saída contra as de entrada. Mais uma
  linha de calibração: filtro que conta ou registra o descarte, ou cujo descarte um teste prende, não
  é achado.
- **Por quê:** numa sessão real (2026-10-05), um conversor de PDF para Markdown descartava toda página
  cujo único bloco vinha marcado como `footer` (dedicatória, epígrafe), com o wrapper dizendo "OK" e
  o validador saindo 0; só a contagem de marcadores contra as páginas do PDF viu. Foi o segundo caso
  no mesmo conversor: no primeiro, tipos de bloco que guardavam o conteúdo em outro campo deixaram
  2.555 itens de lista fora da saída, também sem aviso. Nenhuma das sete formas cobria: o que se
  engole aqui é dado, não erro, e o validador olha a forma do que saiu.
- **Minor, não patch:** a forma nova muda o que a revisão acha.
- O `SKILL.md` não ganha linha (está a ~20 caracteres do aviso C1), só a versão; a `description` já
  fala em silent-blinding sensors.
- **Não entrou:** "sonda cujo escopo não cobre o artefato novo" (a guarda que só varre arquivos
  rastreados). O código da guarda estava certo e o relatório dela dizia o escopo; o erro foi de quem
  leu o verde, e a lição foi para a `kaizen-software` 1.3.6.

## [2.11.2] — 2026-10-05

### `codereview` 2.11.2: doze rodadas até zero achado, e o que cada uma ensinou

Lições de doze rodadas de `/codereview` sobre ~670 linhas de ferramentas Python de um TCC (um
conferidor de citações, a guarda de anonimização e o gerador do `.bib`), em 2026-10-05, até a
rodada 12 sair sem achado. Todas entram em references já roteadas: o `SKILL.md` está a 19 caracteres
do aviso C1 e não ganha linha (só a versão).

- **Rodadas de correção pedem a menor mudança** (`configuration.md`, §Re-review rounds). A curva
  foi 8, 16, 13, 15, 9, 4, 5, 2, 4, 4, 1, 0: a escrita atômica pedida na rodada 3 trouxe 4 dos 15
  achados da 4. Com "um teste, uma docstring ou uma linha antes de função nova" no prompt de quem
  corrige, caiu de 15 para 9 e para 4. Fechar o achado não é aplicar a sugestão: a que enfraquece o
  sensor se recusa com medição.
- **Contagem do CLAUDE.md que o agente chama de velha se confere no arquivo** (mesma seção). Em
  quatro rodadas um agente acusou "1284 testes" com o arquivo já em 1336, 1352, 1362 e 1363: os
  agentes citam o valor do início da sessão.
- **Mutante em Python roda com cache de bytecode isolado** (mesma seção, *Reproduce between
  rounds*). Um mutante que só move um bloco tem o mesmo tamanho; no mesmo segundo do anterior, o
  interpretador reaproveitou o `.pyc` dele e o mutante "passou". `PYTHONPYCACHEPREFIX` numa pasta
  vazia por mutante resolveu, e todos foram refeitos assim.
- **Artefato de build presente resolve um `needs reproduction`** (`configuration.md`, §Runtime
  evidence). Um agente sugeriu recompilar para ver se uma opção do biblatex existia; o log da
  compilação, a declaração no arquivo de estilo e o `pdftotext` do PDF responderam sem escrever nada.
- **Arquivo nomeado pelo usuário é CODE, qualquer que seja a extensão** (`configuration.md`,
  §Path-scoped reviews). Um `.tex` no escopo de uma revisão Python não tinha preset; a regra só
  existia para `.claude/`.
- **6.12 ganha duas formas** (`detection-passes.md`): a mensagem de asserção que nomeia um defeito
  que a asserção não confere (a mensagem posta numa rodada foi o MEDIUM da seguinte) e o mutante do
  lado certo da fronteira (teto 140 sobre um máximo real de 131 não é mutante de um teto de 200).
- **Não aplicada, não é defeito:** o `metadata.version` 2.9.2 da skill numa pasta 2.9.6. Num plugin
  com duas skills, o de cada uma acompanha a última versão em que ela mudou: a 2.11.x só mexeu no
  `coderabbit-pr` e deixou a `codereview` em 2.10.0, e esta a leva a 2.11.2.
- **Dívida mantida:** os 3 avisos C2 são os contratos dos subagentes, lidos por caminho absoluto.

## [2.11.1] — 2026-10-05

### `coderabbit-pr` 4.4.1: o recálculo só no índice deixa a árvore com o valor velho

Lição do `sdd_agents` PR #222 (conserto do achado P2 do Codex, `69eeb4f`), em 2026-10-05, com JorUge.

- **`thread-resolution.md` §5.0.** Quem recalcula um artefato derivado só no índice (ex.:
  `remap.py --cached`) deixa a árvore de trabalho com o valor antigo: depois do commit, o `git diff`
  mostra a reversão como edição pendente, e o próximo `git add -A` desfaz o recálculo. Quando a
  reversão é o diff inteiro do arquivo, `git checkout -- <arquivo>` alinha a árvore antes do commit
  seguinte. Medido: âncora reescrita 2122 → 2132 só no índice; o checkout deixou a árvore limpa e o
  `check-todo.sh --check` verde.
- **Não aplicado, refutado por medição:** o glob `*-review.md` da varredura (Fase 1.1) e da limpeza
  (Fase 6), sob zsh e sem arquivo que case, imprime `no matches found`, mas o pipeline sai com rc 0 e
  o `&&` seguinte roda — medido no `zsh -c`, no `bash -c` e no shell do Bash tool, com o diretório
  vazio e com checklists. O rc 1 visto na sessão era de um `ls *-review.md` do agente, não do comando
  da skill.

## [2.11.0] — 2026-10-05

### `coderabbit-pr` 4.4.0: a cópia velha, as preocupações sem thread, a sabotagem que quebra a sintaxe, o baseline paralelo e os commits por achado

Lições de uma rodada no `sdd_agents` PR #222 (CodeRabbit 5 achados, Codex 2, Copilot sem cota), em
2026-10-05, com JorUge.

- **A Fase 1.1 pega a cópia velha** (`pr-branch.md`, seção nova no topo). A sessão rodou a 2.9.4 do
  cache com a 2.10.0 instalada (`installPath` atualizado às 12:52Z): aberta antes da atualização,
  nunca recarregou. Perdeu a regra de cobertura por commit da 2.9.5, e o relatório final não disse
  que os quatro commits de conserto que ela mesma empurrou não foram revistos por bot nenhum. É a
  guarda que a skill `codereview` ganhou na 2.10.0; aqui ela compara o "Base directory for this
  skill" com o `installPath` do `installed_plugins.json` e pede `/reload-plugins`. O snippet foi
  medido nesta máquina: `STALE` para o diretório 2.9.4, `current` para o 2.10.0.
- **As *Retained concerns* da Security Architecture Review do CodeRabbit vão para o relatório**
  (`reviewer-registry.md`). Ficam no walkthrough, sem thread, e a regra de descartar o walkthrough
  como metadado as engoliu: uma preocupação média (config relida no meio da corrida) só apareceu na
  retro.
- **Sabotagem que quebra a sintaxe não prova nada** (`fix-loop.md`, passo 4). `tbl = 1` → `:` não
  é awk; o selftest ficou vermelho num probe sem relação. Refeita como `tbl = 0`, ficou vermelho no
  probe da regra. O passo já cobria a sabotagem que não se aplica; faltava o inverso.
- **O baseline pode rodar num worktree destacado** (`regression-testing.md`, 4.0), enquanto os
  probes da 3.2 nascem no checkout: 1839 ok em ~8 min sem bloquear o primeiro conserto. Só quando a
  suíte não divide estado fora da árvore.
- **Commit por achado, quando autorizado** (`thread-resolution.md`, 5.0): classificar todo hunk
  antes de pôr qualquer coisa no índice, `git apply --cached` por grupo, artefato derivado
  recalculado contra o índice a cada commit, e `cmp` entre `git diff <base> HEAD` e o patch que a
  suíte aprovou. 14 hunks em 3 arquivos compartilhados viraram 4 commits, `cmp` igual.
- **Espaço:** o `SKILL.md` só mudou a linha que roteia a `pr-branch.md` (+10 caracteres, 19 994); o
  resto mora nas references que cada fase já manda ler.
- **Não aplicadas:** "achado que repete um item de backlog adiado pelo humano é *Not applicable*" —
  o passo 3.1 já manda checar a decisão documentada; e o remapeamento das âncoras do `TODO.md`, que
  é do projeto e foi para a memória dele.

## [2.10.0] — 2026-10-05

### `codereview` 2.10.0: o intervalo que não termina no HEAD, os dados que o código grava, o handoff e a cópia velha

Lições de uma revisão de intervalos já mergeados, em 2026-10-05: `estimates-os_mcp`
`6309d7b..37930f5` (15 commits) e quatro commits do `~/.hermes`, com JorUge.

- **`head=` fecha o intervalo antes do `HEAD`.** O `base=` fixava só o início, e os prompts dos
  agentes mandam `{MERGE_BASE}...HEAD`. O intervalo pedido terminava dois commits antes do `HEAD`;
  os sete agentes revisaram o intervalo certo só porque cada prompt levou o `git diff A..B` escrito
  à mão. Agora `head=` troca o `HEAD` nos passos 4–8 da Fase A e o diff vai por extenso no prompt,
  como no modo `worktree` (`configuration.md`).
- **O laço de sondagem de testes roda em bash.** No zsh, um glob sem correspondência aborta com
  `no matches found` e exit 1, e a Fase A perdia a tabela de cobertura. Resolvido com `bash -c` e
  `shopt -s nullglob`.
- **Evidência de execução inclui os dados que o código grava ou lê.** A §Runtime evidence citava só
  saída de cron e log de serviço. A trilha de auditoria (`audit/consultas.jsonl`) mostrou 6 eventos
  reais de um cliente que o agente por arquivo julgou hipotético, e o achado subiu de LOW para
  MEDIUM; a mesma trilha mostrou duas rodadas de teste gravando em produção onde o handoff dizia uma.
- **Um handoff de revisão é foco em prosa.** O repo trazia `docs/planos/*handoff-code-review.md` com
  16 pontos de risco do autor. A Fase A procura (`git ls-files '*handoff*'`) e a Fase C responde
  ponto a ponto.
- **A Fase A pega a cópia velha antes de revisar.** A sessão carregou a 2.8.0 do cache com a 2.9.5
  instalada: aberta antes da atualização, nunca recarregou. É a segunda vez que uma cópia velha roda
  uma revisão inteira (a primeira está no `report-template.md`, §Cost footprint). Agora um
  `{SKILL_DIR}` fora do `installPath` do `installed_plugins.json` pede `/reload-plugins` antes.
- **Espaço, por fusão provada** (o `SKILL.md` estava a 41 caracteres do aviso C1): o parágrafo de
  fechamento do relatório ficou em duas linhas, porque os três casos e os fallbacks (`A`/`clean`,
  `—`/`Not analyzed`, justificativa de uma palavra) estão no `report-template.md`, §Overall Grade,
  que o passo 10 manda ler antes de escrever; e saiu *"Set `frameworkPatterns=dotnet` for C#/.NET
  projects"*, porque as predefinições .NET estão na `configuration.md`, §Override Syntax, que a
  linha das References já roteia para stack que não é TS. 19 981 caracteres.
- **Não aplicada:** o agente por arquivo afirmou "sem consumidor" depois de um grep estreito. O
  contrato já dizia que a 6.9 não é dele (desde a 2.8.0) e a Fase C descartou a afirmação contra a
  varredura; não falta regra.
- **Dívida mantida:** os 3 avisos C2 são os contratos dos subagentes, lidos por caminho absoluto.

## [2.9.6] — 2026-10-04

### `codereview` 2.9.2 e `coderabbit-pr` 4.3.7: as proibições do projeto no prompt dos agentes, e três casos de uma rodada real com o Codex

Lições de duas fontes no `projeto-final-vdr`: as rodadas 3, 7 e 8 do codereview da D75 (aplicadas
à mão, sem atrito, e aprovadas pelo autor para este retrofit) e a resolução do PR #3 pelo
`coderabbit-pr`, com o Codex, em 2026-10-04.

**`codereview` 2.9.2**

- **Os agentes recebem as proibições do projeto.** O prompt de lançamento proibia acrescentar
  qualquer coisa, e o projeto tinha regras absolutas que os agentes também precisam cumprir (arquivo
  que nunca se abre, valor que nunca se imprime, pasta só de leitura). As três rodadas passaram uma
  linha copiada do `CLAUDE.md`, à mão. Agora os templates da Phase B e da B2 têm o placeholder
  `Hard rules`, e o `per-file-agent.md` e o `sweep-agent.md` dizem que ele vale para todo comando. O
  "nada acrescentado" continua valendo, porque a linha é placeholder do contrato.
- **Caminho em `.claude/` que o usuário nomeia não é EXCLUDED.** Um projeto que versiona as próprias
  skills e agentes em `.claude/` ficava com o `SKILL.md` delas fora da checagem de docs. Nomeado pelo
  usuário, o arquivo cai na classificação normal (`.md` → DOCS).
- **Espaço, por fusão provada** (o `SKILL.md` estava a 2 caracteres do aviso C1): saíram o *"(see
  `references/configuration.md`)"* da entrada de overrides, porque a linha das References roteia o
  mesmo arquivo na mesma condição; a cauda *"…comes back marked so and is reproduced after the
  report"*, que fica *"those come back marked `needs reproduction`"* (reproduzir depois do relatório
  está no `per-file-agent.md` e em `configuration.md` §Re-review rounds); e o gotcha *"Be fair to
  generated code"*, porque o `per-file-agent.md` já diz UI_LIB só CRITICAL e HIGH e a 6.10 sempre
  ligada, e os Special Cases repetem o UI_LIB. 19 959 caracteres.

**`coderabbit-pr` 4.3.7**

- **PR só de revisão com a cabeça espelho.** No PR #3 a cabeça `revisao-d75` espelha a `main`,
  contra uma base anterior ao trabalho. A correção vai na origem e se espelha antes da 5.0 (`git push
  origin main:revisao-d75`, `b1f1224..4b08c16`). A `pr-branch.md` ganhou esse caso entre "mesmo
  branch" e "worktree".
- **A Phase 6 obedece a regra de não apagar.** Em projeto cujo `CLAUDE.md` proíbe apagar arquivo, o
  `rm` vira `mv` para um diretório de rascunho; foi o que a rodada fez com o `codex-review.md`.
- **Falha nova fora do baseline: descartar intermitente antes de chamar de regressão.** A
  `regression-testing.md` 4.2 manda rodar o teste isolado e o módulo, do diretório e com as flags da
  suíte, e conferir se o módulo importa o que mudou. Medido: um `PermissionError` no `tearDown`
  (WinError 32) caiu uma vez na suíte inteira e passou 30 de 30 isolado; rodado da raiz sem `-s
  tests`, o mesmo teste "falhou" 20 de 20 no import.
- **Espaço, por fusão provada:** *"Cleanup runs only on the success path, so an interrupted run leaves
  its checklists where a resume needs them"* repete a `checklist-template.md` §File naming, que a
  mesma frase cita, o gate da 5.3 e a 3.3. 19 984 caracteres.
- **Não aplicadas, à espera do autor:** testes alterados entrando como código na Phase B de um
  *re-review the fix*; e o sweep que não viu um `import re` novo e sem uso que o agente por arquivo
  viu (investigar o `sweep-agent.md` antes).

## [2.9.5] — 2026-10-04

### `coderabbit-pr` 4.3.6: a cobertura do revisor é por commit, não pelo PR

Lição de uma rodada no PR #219 do `sdd_agents`, onde todo achado já estava consertado e toda
conversa resolvida — e mesmo assim o relatório quase disse a coisa errada sobre quem revisou o quê.

- **O caso (b) pode ser parcial.** A revisão do CodeRabbit estava em `b9e95ba`; a cabeça do PR era
  `d8da110`, o commit dos consertos, que ele nunca viu. A skill decidia (a)/(b) por revisor, e um
  revisor com achados nem passava por essa pergunta. Agora a Fase 2 diz que a cobertura é por
  commit, com ou sem achados, e a nova seção *Coverage Per Commit* da `reviewer-registry.md` traz o
  comando que lista o último commit revisado de cada bot contra o `headRefOid`.
- **Uma resposta em conversa não é revisão.** Medido no mesmo PR: a resposta do CodeRabbit numa
  thread criou a revisão `5407103528`, de corpo vazio, em `d8da110`. Uma leitura "último review de
  cada bot" sem filtro dava o commit dos consertos como coberto. O comando usa o mesmo
  `select(.body != "")` da Fase 1.3.
- **O CodeRabbit pula uma revisão incremental em silêncio.** No limite de revisões ele não posta
  revisão nova: **edita** o walkthrough da issue para `## Review limit reached`, com o intervalo
  pulado na linha *"… between <sha> and <sha>"*. A registry chamava esse comentário de "Pure
  metadata"; agora diz que ele nunca é achado, mas é lido para cobertura. Comando de confirmação
  testado no PR #219.
- **Codex sem achados** não cria objeto de revisão: o *Reviewed commit* vem no comentário de issue
  *"Didn't find any major issues"* — registrado na mesma seção.
- **Espaço, por fusão provada** (o `SKILL.md` estava a 28 caracteres do aviso C1): saíram da Fase
  1.2 *"No known reviewer → stop with the "no comments" error"* (o Error Handling traz a mesma
  parada, com a mensagem), da Fase 2 *"(if so, in `references/checklist-template.md`)"* (a abertura
  da Fase 2 e a linha de References já nomeiam o arquivo e os templates (a)/(b)) e da Fase 5 *", to
  read when you reach this phase"* (a linha de References diz *read when you reach Phase 5*).
  Corpo em 19 998 caracteres.
- **Não aplicada, de propósito:** não escrever o checklist numa rodada em que tudo já foi tratado.
  Economiza um `Write` e um `rm`; o comportamento atual não está errado, e o espaço não pagava.

## [2.9.4] — 2026-10-04

### `coderabbit-pr` 4.3.5: os vereditos do D1, o eval de gatilho e o B5 que era do auditor

Os três INFO que sobraram da auditoria da 4.3.4, tratados como tarefa própria (modo reparo da
`skill-quality-audit`).

- **D1 — veredito nos 80 candidatos** (`audit_skill_quality.py --claims`). 76 são números de seção
  (*Phase 1.1*, *4.0 baseline*, *5.3*) que o scanner lê como versão: o sensor é o título na própria
  skill (`#### 1.1`, `## 4.0` da `regression-testing.md`, `## 5.x` da `thread-resolution.md`). O
  `version:` tem o título do CHANGELOG; os dois *first 100 chars of title* são regra da skill, não
  fato de terceiro. **Um só era medição sem data:** *"The projection drops the 30-50KB of
  `diff_hunk`…"*. Medido em 2026-10-04 com `gh api …/pulls/<n>/comments --paginate | wc -c` contra a
  saída projetada: PR #219 do `sdd_agents`, 51 492 → 12 600 bytes; PR #208, 13 715 → 5 346. O valor
  depende do PR, a proporção (61% a 76% cortados) não: o texto agora diz *"most bytes, per `wc -c`"*.
- **F4 — `assets/trigger-evals.json`**, no formato de eval set do `skill-creator` que as skills da
  `skill-quality-audit` usam: 9 casos que devem disparar (CodeRabbit, Copilot, Gemini, Codex, byte
  invisível, revisor sem cota) e 8 quase-acertos que não devem (review pré-PR, abrir PR, CI vermelho,
  comentário de humano, merge, configurar o bot, TODO → issues, release notes). Citado em References,
  *"read before changing the `description`"*.
- **Espaço para a citação, por fusão provada:** o parêntese *(npm, dotnet, cargo, pytest, go, make —
  or ask)* da Fase 4 duplicava a tabela 4.1 da `regression-testing.md`, que é mais completa (tem a
  prioridade 0, o gate que o projeto declara), e o *ask* já está no Error Handling; a cauda *"since its
  case (b) is a coverage gap the user needs to hear about"* do Error Handling repetia o caso (b) da
  Fase 2. Corpo em 19 972 caracteres.
- **B5 não se conserta na skill:** ela não tem CHANGELOG próprio porque no marketplace ele fica no
  plugin, e um segundo partiria o histórico. O conserto foi no auditor (`skill-quality-audit` 0.4.1),
  que agora acha o `<plugin>/CHANGELOG.md` e responde OK. Com ele, esta skill audita sem
  `--no-changelog-required`: rc 0, nenhum ERRO, AVISO ou F4.

## [2.9.3] — 2026-10-04

### `coderabbit-pr` 4.3.4: as duas dívidas da auditoria, fechadas sem mudar o que a skill faz

Reparo autorizado das dívidas registradas na 4.3.3, pela `skill-quality-audit` (modo reparo,
allowlist: as duas linhas abaixo e os arquivos de versão).

- **C2 (AVISO): `fix-loop.md` citava `regression-testing.md`**, cadeia de dois níveis a partir do
  `SKILL.md`. A citação só nomeava o comando de teste, e quem lê o `fix-loop.md` já o detectou: a
  Fase 3.2 manda capturar o baseline da 4.0 antes do primeiro conserto. O passo 5 agora diz *"the
  one detected for the 4.0 baseline"*, sem o salto para outro arquivo; o `SKILL.md` segue roteando
  o `regression-testing.md` direto.
- **F1 (INFO): a `pr-branch.md` citada sem dizer quando ler.** A linha da lista de References dizia
  *"read at Phase 1.1: worktree, …"*, e "at" não é condição. Agora diz *"read at Phase 1.1, before its
  worktree, active-writer check and sweep"*: é antes desses três passos que a reference serve. Corpo
  em 19 971 caracteres (+8), abaixo dos 20 000 do aviso do `validate-versions.py`.

## [2.9.2] — 2026-10-04

### `coderabbit-pr` 4.3.3: o head que ainda não chegou à API, e a conversa que fica sem o porquê

Lições do `/codereview:coderabbit-pr` no PR #219 do `sdd_agents` (quatro achados do CodeRabbit, Copilot
sem cota, Codex ausente).

- **A 5.0 dava falso negativo logo depois do próprio push.** Com o conserto já empurrado, `gh pr view
  --json headRefOid` ainda respondeu o sha de antes (`b9e95ba`) enquanto `git ls-remote` já tinha
  `d8da110`; a consulta seguinte respondeu `d8da110`. Seguida ao pé da letra, a 5.0 parava e pedia ao
  usuário um push que já tinha acontecido. A reference agora manda ler o ref remoto com `ls-remote`
  antes de parar e, se ele bate com o `HEAD`, refazer a checagem segundos depois.
- **A 5.2 responde antes de resolver** quando o veredito foi *Not applicable* ou *Fixed (alternative
  approach)*. O CodeRabbit pediu para reabrir um registro que o projeto tinha decidido; a resposta com
  o motivo, postada na conversa antes da mutação, o fez retirar a recomendação e gravar um aprendizado.
  Resolvida em silêncio, a conversa que a Fase 6 chama de registro de auditoria ficava com a alegação
  do bot e sem resposta, e o mesmo achado voltaria no próximo PR. O ID da resposta é o numérico da 1.3,
  não o `PRRT_…`; achado de corpo de revisão ou fora do diff não tem conversa.
- **Orçamento:** as duas lições moram só na `references/thread-resolution.md`, que a Fase 5 manda ler.
  O corpo do `SKILL.md` não muda (só o `metadata.version`): ele tem 19 963 caracteres, e o aviso do
  `validate-versions.py` dispara acima de 20 000. **Dívida que segue:** o C2 (`fix-loop.md` cita `regression-testing.md`) e o F1
  (`pr-branch.md` citada sem dizer quando ler).

## [2.9.1] — 2026-10-03

### `codereview` 2.9.1: a última citação da `configuration.md` diz quando ler

O F1 do `audit_skill_quality.py` (reference citada sem dizer quando ler) vinha de uma linha só das
quatro que citam a `configuration.md`: a do modo `worktree` na Fase A, *"Empty CHANGED_FILES, dirty
`git status --porcelain` → `worktree` mode (`references/configuration.md`)"*. O conteúdo já era uma
condição; faltava a palavra que a diz. Agora é *"If CHANGED_FILES empty, …"*, e as outras três já
diziam (*"only when `$ARGUMENTS` carries…"*). Dívida registrada na 2.9.0, fechada como tarefa
própria, sem mudar o que a skill faz.

**Orçamento:** +3 caracteres, o `SKILL.md` fica em 19 998 (o C1 avisa acima de 20 000). A forma mais
natural, *"If CHANGED_FILES is empty"*, passava por um.

## [2.9.0] — 2026-10-03

### `codereview` 2.9.0: o teste vácuo ganha passo próprio, e a re-review converge

Lições do `/codereview` no I10 da S8 do `ui24_agent` (quatro rodadas, grade B → A; o pedido em prosa
foi "caçar teste vácuo").

- **Passo 6.12 Test Quality** (`references/detection-passes.md`). O mapeamento `tests → test quality`
  da `per-file-agent.md` apontava para um passo que **não existia em lugar nenhum**. Agora existe, com
  as seis formas que a sessão confirmou por mutante sobrevivente: asserção que vale em todo caminho
  (`not sent` numa conexão nunca armada), substring sem borda (`"1=25"` dentro de `"11=250"` — seis
  de 31 entradas sumiam com o teste verde), fixture com L = R (trocar os lados passava em 587 testes),
  teste que crava a forma produzida contra a prometida, nome que promete o que nenhuma asserção
  confere, e asserção só negativa.
- **A Fase B manda os arquivos TESTS a agentes quando o foco é qualidade de teste** (`SKILL.md`). Só
  CODE ia a agente; os dois agentes de teste lançados à mão acharam os 4 MEDIUM de teste vácuo da
  rodada, que os quatro de código não viram.
- **Vacuidade é `PLAUSIBLE` até um mutante mostrar** (6.12). O agente vê um arquivo de teste só: das
  duas "trocas de lado não testadas" que ele apontou, uma já era pega por um teste vizinho que ele não
  leu. A mutação roda depois do relatório, nos arquivos de teste ligados, não na suíte inteira.
- **Re-review rounds** (`references/configuration.md`, lida em toda rodada com `base=`). Os agentes não
  veem os relatórios anteriores, e o mesmo achado inalcançável ("lote parcial") voltou nas rodadas 2 e
  3: achado já descartado com razão escrita, sem evidência nova, é respondido citando o veredito e não
  conta contra a regra de parada. E com agente ou suíte em background lendo a árvore, comparar outra
  ref é `git show`/`git diff <ref> --`, nunca `checkout`/`stash` — um `git checkout main` de um
  segundo, para ver se um aviso de lint era antigo, invalidou uma suíte inteira.

**Orçamento:** o `SKILL.md` ganhou 62 caracteres e fica em 19 995 (o C1 do auditor avisa acima de
20 000). A próxima lição que precisar do corpo pede um enxugamento com a `skill-refactoring`, como
tarefa própria. **Dívida que segue:** os 3 C2 (references lidas pelos agentes por caminho absoluto,
de propósito) e o F1 (`configuration.md` citada sem dizer quando ler).

## [2.8.2] — 2026-10-03

### `coderabbit-pr` 4.3.2: no zsh, `path` é o `PATH`

Lição do `/codereview:coderabbit-pr` no PR #208 do `sdd_agents` (dois achados do CodeRabbit, Copilot sem
cota).

- **A Fase 5.2 perdeu o `PATH` dentro do laço.** A saída da 5.1 traz três colunas (id, autor, caminho
  do arquivo), e o nome natural para a terceira é `path`. No zsh, `path` é o array amarrado ao `PATH`:
  `read -r id who path` zerou a busca de comandos, e cada `gh` e `sed` do laço morreu com
  `command not found` — nenhuma conversa resolvida, e só a recontagem da 5.3 pegou. Renomeada a
  variável, as mutações responderam `true` e a 5.3 deu `unresolved: 0`. A reference já avisava da
  armadilha vizinha (`for id in $ids` não divide palavras no zsh); agora avisa desta, no mesmo laço, e
  o SKILL.md ganha uma linha em Gotchas que cobre as duas.
- **Orçamento do corpo.** A linha nova levava o `SKILL.md` a 20 096 caracteres (> 20 000, warning do
  `validate-versions.py`). Saíram do corpo duas cópias do que a `references/thread-resolution.md` já
  diz e que a Fase 5 manda ler: o parêntese do `for id in $ids` na 5.2 (agora na linha de Gotchas) e
  o limite de 100 conversas na 5.3. Corpo em 19 963 caracteres.

## [2.8.1] — 2026-10-03

### `coderabbit-pr` 4.3.1: o revisor que só posta na issue, e a sonda que erra depois do conserto

Lições do `/codereview:coderabbit-pr` no PR #73 do `ui24-agent` (Python, um achado do Codex, Copilot
sem cota e CodeRabbit no plano Free).

- **A detecção da Fase 1.2 lia dois endpoints, e o CodeRabbit no plano Free só posta no terceiro.**
  Sem revisão linha a linha, ele não deixa comentário inline nem review object; deixa só um comentário
  na *issue* (walkthrough + *"Your organization is on the Free plan … please upgrade"*). No PR #73,
  `/pulls/73/comments` e `/pulls/73/reviews` devolveram só Codex e Copilot, e o login do CodeRabbit
  apareceu só em `/issues/73/comments`: o relatório sairia sem ele, quando o certo é o caso (b) — ele
  nunca revisou, e isso é buraco de cobertura. Agora a 1.2 é um laço sobre os três endpoints (testado em
  bash contra o PR #73; zsh não testado, ausente na máquina — a lista é literal, não `$var`), a parada
  "nenhum revisor" fala dos três, e o `references/reviewer-registry.md` ganha o terceiro lugar do
  CodeRabbit, a frase do plano Free com o comando que a acha, e a regra de que revisor visto **só** na
  issue vai direto à determinação de zero achados da Fase 2. A nota do Codex que dizia "a Fase 1 não lê"
  esse endpoint virou "a 1.2 vê o login, a 1.3 não extrai nada".
- **Ainda vermelho depois do conserto: julgue a sonda antes do conserto.** O passo 3 do
  `references/fix-loop.md` não dizia o que fazer quando o verde não vem. No PR #73 a sonda ficou vermelha
  pelo motivo certo (a chave nova faltando), e por isso as outras asserções nunca rodaram; depois do
  conserto, as três falhas eram dela — um campo que a saída nunca teve, um valor do fixture suposto em
  vez de lido, um rótulo que o código existente já produzia certo. Entortar o conserto para casar com
  elas teria sido a regressão.

O `SKILL.md` ficou com o mesmo tamanho em caracteres (19 993, medido por `len()` como o
`audit_skill_quality.py` mede; o C1 avisa acima de 20 000): a 1.2 foi reescrita compacta e o detalhe
foi para as references. Dívida pré-existente, não tocada: o C2 de `fix-loop.md` citando
`regression-testing.md` (cadeia de dois níveis).

## [2.8.0] — 2026-10-03

### `codereview` 2.8.0: a versão que rodou, o foco em prosa, o repositório shell e o laço de revisão

Lições de quatro rodadas de `/codereview:codereview` no PR #200 do `sdd_agents` (bash + jq + mawk), da
nota B até todos os critérios em A (11 → 5 → 3 → 0 achados).

- **O rodapé diz qual versão da skill rodou.** A sessão carregou um cache `2.1.1` (`metadata.version:
  2.1.0`) com a 2.6.0 registrada em `installed_plugins.json`, e nada no relatório mostrava isso: o
  `base=<sha>` da 2.2.0 faltou e foi improvisado nas rodadas 2–4. O Cost footprint existe para comparar
  rodadas; sem a versão, a comparação não sabe de qual skill veio cada uma. A Fase A lê o
  `metadata.version` do `{SKILL_DIR}/SKILL.md` no mesmo turno do passo 1–3.
- **Foco em prosa.** O pedido nomeava pontos concretos (o separador do checkpoint, o invariante do
  `jq`), e a skill só aceitava palavras-chave e proibia acrescentar qualquer coisa ao prompt dos agentes
  — o foco era descartado em silêncio na delegação. Agora: roda `full` com os prompts intactos, e a
  Fase C responde cada ponto nomeado, dizendo no relatório onde o conferiu.
- **Repositório shell.** `fileExtensions` não descreve `bin/sdd`, o arquivo principal do repo, que não
  tem extensão; a classificação foi feita à mão. Preset de shell no `configuration.md`, executável sem
  extensão é CODE pelo shebang, e uma nota para o repo cujos scripts de teste SÃO o produto (classificados
  como TESTS, ficariam sem agente por arquivo).
- **"Falha em silêncio se derivar" é palpite do agente por arquivo.** Ele não lê os testes, por contrato,
  e deu MEDIUM dizendo que um leitor (`cut`) ficaria cego se o separador mudasse; a sabotagem desse leitor
  deixou três asserções vermelhas, e o achado caiu para LOW. Novo item na Calibração da 6.11 e uma frase
  no passo 4 da Fase C: achar o teste que prende o sítio antes de manter a severidade.
- **Revisar o conserto, não a branch.** Depois de consertar um relatório, a rodada seguinte usa
  `base=<head já revisado>` e o laço para na primeira rodada sem achado. O achado da rodada 3 estava num
  comentário que a rodada 2 acabara de escrever. Princípio novo no `SKILL.md` e no `base` do
  `configuration.md`.
- **Orçamento:** o `SKILL.md` estava em 20.116 chars (acima de ~20 mil). O "Why a script" e o bloco das
  duas passadas sempre ligadas saíram dele — eram justificativa, já cobertas pela 6.10 e pela 6.11 do
  `detection-passes.md`, que recebeu o que faltava (a lista de exceções; por que a 6.11 não força F).
  Fica em 19.933 chars, 248 linhas.

## [2.7.0] — 2026-10-02

### `coderabbit-pr` 4.3.0: a árvore ocupada, o achado que mora no código e o wrapper que desarma o prazo

Lições do `/codereview:coderabbit-pr` no PR #196 do `sdd_agents`, rodado com o pipeline do kit ainda na
fase PR.

- **Mesma branch, outro escritor ativo: só leitura até ele sair.** A 2.5.0 resolveu o caso em que a
  branch do PR é outra (worktree). O caso oposto ficou com "work here": o checkout estava limpo **na
  branch do PR** enquanto a sessão de PR do pipeline e o catálogo de mutação que ela disparou ainda
  mediam a árvore. Aplicar um conserto em `bin/` mudaria o conteúdo que o carimbo media, e um
  `coderabbit-review.md` na raiz seria atribuído pela guarda de chapéu do runner à sessão em curso,
  parando a linha. Agora: fases 1–3.1 só lendo, checklist fora da árvore, nada aplicado até o escritor
  sair. Nova seção em `references/pr-branch.md` com a detecção por diretório de trabalho (`/proc/*/cwd`,
  testada), o ruído que ela traz (o próprio harness, um daemon do Codex de pé havia 14 dias) e por que o
  worktree não serve (o git recusa um segundo checkout da mesma branch).
- **Achado ancorado em doc pode ser defeito de código.** O CodeRabbit ancorou em `docs/pipeline.md` um
  achado sobre o que o `sdd close` imprime; a frase falsa ("merged and spent" sem merge verificado)
  saía do `bin/sdd`. Consertar só a prosa deixaria o programa mentindo. Passo 3.1, item 1.5, e uma
  armadilha nova.
- **Wrapper sugerido desarma o `timeout --foreground`.** O review propôs envolver o passo em `bash -c`
  para remapear um rc 124 do filho. Com `--foreground` o `timeout` sinaliza só o processo de topo, que
  passaria a ser o wrapper. Medido: rc 124 nos dois casos, e o passo envolvido escreveu seu marcador
  3 s depois do prazo, enquanto o passo direto morreu. Armadilha nova; o caso é "demonstrably wrong"
  do passo 6.
- **Orçamento:** `SKILL.md` 19 862 → 19 993 chars, pago com quatro compressões de texto redundante (o
  porquê do "inline", o erro "no comments", a frase da projeção e a intro da Phase 5). Fica a 7 chars
  do teto de 20 mil: o próximo retrofit move detalhe para `references/`.

## [2.6.0] — 2026-10-02

### `codereview` 2.6.0: interpolação não é senha, escopo por caminho e saída real em produção

Lições do review da skill `sbm-renovacao` (repo `~/.hermes`, Jira SBM-1).

- **`scan_secrets.py`: valor que é inteiro uma interpolação deixa de ser finding.** O pré-scan acusou
  `f'… oauth_token="{self.token}"'` como Generic Password, e a regra do gate (pré-scan é autoritativo,
  nunca rebaixa) forçaria F num relatório sem credencial: o token vinha de `env_value(...)`.
  `looks_like_placeholder()` já aceitava `${VAR}`; agora aceita também `{ident.attr}`, `#{x}` e
  `%(x)s` quando são o valor inteiro. Literal com `{` no meio (`abc{1}xyz`, `{a}{b}hunter2`) continua
  acusado. Verificado com diff sintético (3 literais acusados, 4 interpolações não) e no diff real
  (1 → 0 findings).
- **Review com escopo de caminho: vazio é erro de pathspec, não "No changes".** `P="… :!x"; git diff -- $P`
  no zsh não divide a variável, o git recebe um pathspec só e não imprime nada; um escopo de 32 commits
  voltou como 0. Nova seção `references/configuration.md` §Path-scoped reviews (forma `':(exclude)…'`
  entre aspas e como reconferir), roteada pela regra de "Both empty" da Fase A.
- **Fase C lê as últimas saídas de código que já roda.** O achado mais útil daquele review (um evento
  reanunciando 9 registros perdidos anos antes) só aparecia na saída do cron daquela manhã; nenhum agente
  por arquivo o viu no diff. Nova seção §Runtime evidence, roteada pelo passo 3 da Fase C.
- **Orçamento:** para caber as duas frases novas abaixo de 20 mil chars, dois trechos duplicados foram
  fundidos: "prioritize by change size" (já na Fase A, regra dos 15 arquivos) e "Acknowledge context
  limits" (já na Fase C passo 1, `partially analyzed`, e em Error Handling). `SKILL.md`: 19 832 → 19 929 chars.
- Dívida pré-existente, não tratada aqui: 3 AVISO C2 (contratos de subagente lidos por caminho
  absoluto — intencional), F4 sem evals.

## [2.5.0] — 2026-10-02

### `coderabbit-pr` 4.2.0: worktree em vez de checkout, e só se resolve o que o PR carrega

Lições da corrida no PR j0ruge/sdd_agents#195.

- **Árvore limpa não é árvore parada.** A Fase 1.1 mandava `git checkout <headRefName>` quando a
  árvore estivesse limpa. Ela estava limpa, na branch de uma missão, enquanto um subagente planner
  escrevia os artefatos dessa missão no mesmo checkout: o checkout teria levado os arquivos dele
  para a branch errada. A corrida usou `git worktree add ../sdd_agents-pr195 <branch>` e deixou o
  checkout intocado. Agora, quando a branch atual difere da do PR, o padrão é o worktree; o
  comando, o caso "branch já aberta noutro worktree" e a remoção no fim estão na nova
  `references/pr-branch.md`, junto com a varredura de checklists antigos, que saiu do `SKILL.md`.
- **Fase 5.0: o head do PR tem de conter os consertos.** A skill nunca commita, então ao fim da
  Fase 4 o conserto existe só no disco. Seguida ao pé da letra, a corrida resolveria a conversa
  do CodeRabbit com o head (`3c739aa`) ainda carregando o defeito; o conserto foi empurrado
  (`96532c9`) antes. O passo novo confere `headRefOid` contra o `HEAD` local e a árvore sem o
  conserto pendente, e pede ao usuário o commit e o push antes de resolver
  (`references/thread-resolution.md`).
- O `SKILL.md` estava em 19 996 chars contra o teto de 20 000; as duas lições entram com o
  detalhe nas references e o corpo fica menor que antes.

## [2.4.0] — 2026-10-01

### `coderabbit-pr` 4.1.0: o conserto de lógica tem sensor próprio, um achado por vez

Lição de uma análise do laço de revisão do kit `sdd_agents`, provocada por uma sugestão do
`/insights` ("teste cada conserto antes da próxima rodada").

- **O probe do achado não testa o conserto.** A regressão nasce no código novo: um probe que só
  reproduz o achado fica verde com um conserto que tira o sintoma e abre um fail-open ao lado. Medido
  no kit: no PR #46 o conserto da r1 do CodeRabbit apodreceu a âncora de um mutante e a suíte rápida
  ficou verde; no PR #45 foram três `sdd health` (~22 min cada) para uma branch; no `check-todo.sh`,
  três rodadas seguidas em que o conserto de uma criou o defeito da seguinte.
- **A Fase 3.2 separa lógica de mecânica.** Conserto de lógica (guarda, ramo, parser, regex, código
  de saída) vai no modelo principal, um por vez, pelo laço novo em `references/fix-loop.md`: probe
  vermelho pelo motivo certo, conserto, **sabotagem do conserto** até um probe ficar vermelho, suíte
  rápida (mais a metade barata do catálogo de mutação quando houver) antes do próximo. Prosa, nome e
  formatação continuam em lote, e só esses vão para agentes paralelos acima de 5. Rodar a suíte uma
  vez depois do lote era o que entregava a regressão à rodada seguinte dos bots.
- **Regra de parada.** Duas regressões criadas por conserto na mesma vizinhança: parar de remendar e
  nomear o estado que falta.
- **O gate declarado vence a detecção.** A tabela 4.1 ganha a prioridade 0: `TEST_CMD` do
  `.sdd/config.sh` ou a suíte nomeada no `CLAUDE.md`/`AGENTS.md`. Um kit de bash e markdown não tem
  nenhum dos arquivos da tabela e caía em "pergunte ao usuário".
- Fora de propósito: `git diff --stat` por achado e a proibição de `sed -i` em glob, sugeridas pelo
  `/insights`, sem caso medido que as sustente.

## [2.3.1] — 2026-10-01

### `coderabbit-pr` 4.0.2: o Codex "Running" é pendente, não aprovação

Lição de um `@codex review` no PR JRC-Brasil/sales_quote#402.

- **O resumo vem antes da revisão.** O Codex publicou primeiro um comentário de *issue* com o
  marcador `<!-- codex-pull-request-review-summary -->` e o status `🔄 Running` (21:13:21Z); o review
  e os dois achados P1 inline só chegaram com o status `✅ Completed` (21:17:23Z). Um laço de espera
  que aceitava qualquer comentário do bot saiu no resumo, e a Fase 1 leria zero achados, o que a
  Fase 2 registraria como caso (a), aprovação, quando era o caso (b), pendente. A Fase 2 (b) cita
  agora o resumo em `Running`, e o `reviewer-registry.md` traz o comando que lê o status (rodado no
  PR #402: devolve `Completed`).
- **Registro corrigido.** A linha do Codex dizia *"Inline comments only"*; o medido foram três
  objetos: o resumo de status (fora dos endpoints que a Fase 1 lê), um review `COMMENTED` de corpo
  padrão (metadado, descartar) e os comentários inline com o selo `P<n>` como marcador de severidade.

## [2.3.0] — 2026-10-01

### Modo `worktree`: revisar o que ainda não foi commitado

Lição de uma revisão no `~/.hermes`, repositório em que se trabalha direto na `main`.

- **Diff de commits vazio não quer dizer que não há mudança.** No branch base, `git merge-base main HEAD`
  devolveu o próprio `HEAD` (`243a8c4`). A Fase A mandava parar com "No changes detected", mas havia
  30 arquivos modificados e uma skill inteira sem commit. Agora, com CHANGED_FILES vazio e
  `git status --porcelain` sujo, a skill entra no modo `worktree`, documentado no `configuration.md`:
  lista de arquivos (`git diff HEAD --name-only` mais `git ls-files --others --exclude-standard`),
  diff por arquivo e cabeçalho do relatório `working tree vs HEAD {sha}`.
- **O pre-scan de segredos precisa das duas fontes.** `git diff HEAD` não mostra arquivo novo, e o
  código da skill nova só chegou ao `scan_secrets.sh` pelo `git diff --no-index /dev/null <arquivo>`
  (rc 1 é normal nesse comando). Medido nesta sessão: as duas saídas passaram pelo script, que devolveu
  JSON válido com `errors: []`.
- **Não medido com agentes:** a revisão rodou a Fase B inline (≤3 arquivos de código). A regra de
  escrever o comando de diff por extenso no prompt dos agentes (`{MERGE_BASE}...HEAD` sairia vazio)
  vem da leitura do `per-file-agent.md`, não de uma execução.

O `SKILL.md` ganha 48 chars (19.784 → 19.832, contados como o auditor conta; os "19.965" da 2.2.0
eram bytes do `wc -c`). Para caber, a frase "The outputs are small (file names, stats, a one-line
log)." foi fundida à anterior como "Outputs are small.". Os três avisos C2 continuam como dívida antiga.

## [2.2.0] — 2026-10-01

### Três lições de uma revisão por faixa de commits

Lições da revisão dos 7 commits de correção do QA da SQ-153 no `sales_quote` (`2773ce14..a08f54a6`).

- **`base=<sha>`: revisar uma faixa nomeada em prosa.** O pedido foi "os 7 commits de `8cae117f` a
  `a08f54a6`, sobre `2773ce14`", e a skill só sabia calcular `git merge-base {BASE_BRANCH} HEAD`,
  que revisaria a branch inteira. O passo 4 da Fase A passa a aceitar o commit-base que o usuário
  nomear, mesmo em prosa, e o `configuration.md` ganha a linha `base`. O fim da faixa continua
  sendo `HEAD`; fim diferente não foi medido e não entrou.
- **A sonda de testes também procura quem importa o arquivo.** Procurar só pelo nome achou 5 de
  31 arquivos com teste. Os use cases eram cobertos por uma suíte compartilhada
  (`alcada-solicitacoes.test.ts`) alterada na mesma faixa. Uma sonda por import, medida na
  mesma faixa, achou 15. O `report-template.md` ganha o rótulo `WITH_TESTS (indirect)`, que conta
  no numerador, e o aviso de que a cobertura transitiva (um componente exercitado pelo teste do
  pai) continua sendo julgamento da Fase C.
- **Glob sem aspas no zsh é comando que falhou, não resultado.** `--include=*.ts` sem aspas saiu
  duas vezes com `(eval):1: no matches found`, e um agente por arquivo relatou que o grep sobre
  `docs/routes.md` não tinha rodado. `per-file-agent.md` e `sweep-agent.md` passam a exigir
  glob entre aspas e a tratar `no matches found` como falha, nunca como "zero referências".

O `SKILL.md` fica em 19.965 chars (antes 19.863), abaixo do aviso C1 de 20 mil; o detalhe foi
para as references. O `metadata.version` da skill vai a 2.2.0. Os três avisos C2 (cadeia de
references que os subagentes leem por caminho absoluto) são dívida antiga e ficam como estão.

## [2.1.1] — 2026-10-01

### `coderabbit-pr`: a Fase 5.2 deixa de quebrar no zsh

A Fase 5.2 trazia `for id in <thread IDs from 5.1>; do`, e o jeito natural de preencher o
placeholder é guardar os ids numa variável e iterar com `$ids`. No zsh, que não separa variável sem
aspas, o laço roda uma vez só com todos os ids juntos. A API respondeu `NOT_FOUND … global id of
'PRRT_…\nPRRT_…'` e nenhuma conversa foi resolvida no PR #401 do `sales_quote`. Só a recontagem da
5.3 (`unresolved: 2 of 2`) acusou a falha.

- A 5.2 passa a receber a saída da 5.1 por pipe, com `while IFS=$'\t' read -r id _`, que se
  comporta igual no bash e no zsh. Entra também a nota do porquê, com o erro medido.
- O passo 5.2 do `SKILL.md` ganha a mesma regra numa linha, em vez de um item novo em Gotchas,
  para o arquivo ficar abaixo de 20 mil chars (19.916). O `metadata.version` da skill vai a 4.0.1.

## [2.1.0] — 2026-09-29

### Pass 6.11 ganha duas formas de sensor cego

Duas lições da sessão que integrou a `skill-quality-audit` ao `/retrofit-skill`. As duas são
sensores que ficam verdes sem que nada tenha melhorado, e nenhuma cabia nas cinco formas.

- **Verde por subtração.** Um ensaio apagou, numa cópia desta skill, as citações que os
  subagentes leem em `per-file-agent.md` e `detection-passes.md`. O auditor saiu com `rc=0` e um
  aviso C2 a menos, e os agentes estariam quebrados. Numa revisão, isso aparece como teste
  removido, `.skip`, `eslint-disable` novo ou glob de ignore mais largo, no mesmo diff em que a
  contagem melhora. A calibração exclui o caso em que o próprio objeto da checagem foi apagado.
- **Gate opcional que some.** O gate do `retrofit-skill` 0.5.0 era "se o auditor estiver
  instalado" e apontava para um caminho que não existia. Ele nunca rodou, e nada imprimiu SKIP.

Só a reference muda. O `SKILL.md` está a 137 chars do orçamento de ~20k e não recebeu texto.


## [2.0.0] — 2026-09-28

**Quebra de compatibilidade:** a skill `coderabbit_pr` passa a se chamar **`coderabbit-pr`**. O
comando vira `/codereview:coderabbit-pr` e **o nome antigo `/codereview:coderabbit_pr` deixa de
funcionar** — scripts, aliases, prompts de pipeline e anotações que o invocam precisam trocar o
`_` por `-`. Por isso o bump é MAJOR. O resto da versão é progressive disclosure das duas skills,
pela spec do agentskills.io e a auditoria `skill-quality-audit` v0.2.0. Nenhum fato, comando ou
armadilha saiu: o que deixou os `SKILL.md` foi para `references/`, ou já estava lá e virou apontador.

### `coderabbit-pr` 4.0.0 (antes `coderabbit_pr` 3.6.0)

**Por quê.** **A2 (ERRO):** `name` só aceita a-z, 0-9 e hífen simples, e o `_` de `coderabbit_pr`
viola a spec; como o `name` tem de ser igual ao diretório, os dois mudam juntos. **C1 (ERRO):** 531
linhas e 30.710 chars, acima do teto de 500 linhas e do orçamento de ~20.000 chars do corpo.

- **Renomeada:** diretório `skills/coderabbit_pr/` → `skills/coderabbit-pr/` e `name: coderabbit-pr`.
  O nome para o Cursor no `install.py` já era `coderabbit-pr`; só o `source_dir` muda.
- **`SKILL.md` (531 → 339 linhas, 30.710 → 19.837 chars).** Fica o fluxo inteiro das seis fases, com
  os comandos de 1.1–1.3 e da limpeza da Fase 6 inline, a tabela de decisão da 3.1 e o roteamento de
  modelo (a tabela perdeu a coluna "Why", que virou o parágrafo abaixo dela). "Operating
  Principles" virou **Gotchas**, sem as linhas que só repetiam as fases. Nova seção **References**,
  cada arquivo com a condição de leitura.
- **`references/regression-testing.md` (novo):** a Fase 4 por extenso — quando pular, o baseline
  4.0 e seu formato, a tabela de detecção do comando de teste (4.1), os cinco casos de comparação
  (4.2), a reexecução em cascata e a 4.3. No `SKILL.md` ficam as regras de pular, "baseline antes do
  primeiro fix", "nunca silenciar teste" e a cascata.
- **`references/byte-exact-verification.md` (novo):** o passo 3.1 1.1 — por que o `Read` não é fiel
  a bytes e os comandos `od`/`tr`/`xxd`/`repr()`. No `SKILL.md` fica a regra com o `od -c`.
- **`references/thread-resolution.md` (novo):** os três comandos GraphQL da Fase 5 e o bloco
  `### Conversations`. No `SKILL.md` ficam os três passos, o `true` por linha, o gate
  `unresolved: 0` e o teto de 100 threads. Os comandos continuam rodando inline.
- **`references/checklist-template.md`:** as duas regras que só funcionam em par (nome fixo +
  apagar no sucesso) e a nota de retomada, que estavam na Fase 6, entraram em §File naming; o
  template (b) ganhou a forma genérica ("once the underlying cause clears") que estava no `SKILL.md`.
  Os modelos (a)/(b) da Fase 2 saíram do `SKILL.md`, que agora aponta para cá.
- `metadata.version` 3.6.0 → 4.0.0 (a própria skill quebra compatibilidade pelo nome).

### `codereview` 2.0.0 (antes 1.20.0)

**Por quê.** **B1:** `detection-passes.md`, `per-file-agent.md`, `sweep-agent.md` e
`toctou-patterns.md` eram lidos pelos agentes pelo caminho absoluto do prompt, e o `SKILL.md` não
dizia quando o orquestrador deveria lê-los. **C1:** 22.164 chars. **C2:** `detection-passes.md` e
`report-template.md` citavam um ao outro com o prefixo `references/`. **C3:** `detection-passes.md`
com 500 linhas e sem sumário.

- **Nova seção References** no `SKILL.md`: as seis references, cada uma com quem a lê e quando o
  orquestrador deve lê-la (Fase B ou B2 inline, redo do sweep, recalibração e bloco de remediação
  da 6.10 na Fase C, corrida entre arquivos, step 10). A frase de `configuration.md` saiu do User
  Input para lá.
- **`SKILL.md` (254 → 250 linhas, 22.164 → 19.682 chars)** com as References incluídas: prosa da
  Fase A, B, B2 e do step 10 da Fase C comprimida (o racional de "por que script" já está na 6.10
  de `detection-passes.md`; as regras de renderização do Overall Grade já estão no
  `report-template.md`); "Operating Principles" virou **Operating Principles and Gotchas**, sem as
  linhas duplicadas do roteamento e da Fase A. Os dois prompts de lançamento dos agentes não
  mudaram uma vírgula.
- **`detection-passes.md`:** sumário (`## Contents`) no topo, com âncoras para 5.1–5.5, 6.1–6.11 e a
  Severity Reference. As duas citações a `report-template.md` e a de `report-template.md` a
  `detection-passes.md` passam a usar só o nome do arquivo, dizendo que o `SKILL.md` roteia.
- **Mantido de propósito:** os `{SKILL_DIR}/references/…` dentro de `per-file-agent.md`,
  `sweep-agent.md` e da 6.6 de `detection-passes.md`. São o contrato dos subagentes, e o caminho
  absoluto é o que fez 4 de 4 agentes lerem as references na medição da 1.19.0 (contra 1 de 66
  com caminho relativo). O auditor os marca como C2; aqui o C2 é aceito.
- `metadata.version` 1.20.0 → 2.0.0, alinhado ao plugin (a convenção da 1.20.0).

**Auditor** (`audit_skill_quality.py --external off --no-changelog-required --desc-budget 0`):
`coderabbit-pr` antes 2 ERROS (A2, C1) + 1 AVISO (C1 chars), depois 0 + 0; `codereview` antes 5
AVISOS (B1, C1, C2 ×2, C3), depois 3 AVISOS C2, todos dos contratos de agente acima.

**Como reverter:** `git revert` do commit que traz esta entrada. Quem já trocou para
`/codereview:coderabbit-pr` precisa voltar para `/codereview:coderabbit_pr` depois do revert.

## [1.20.0] — 2026-09-11

Novo passe de detecção **6.11 — Silent-Blinding Sensors**, always-on como o 6.10 mas **sem gate de
nota**. Nasceu de uma revisão escopada real (RS-877, frontend do DSR): dos cinco achados, **três
estavam em código que já havia passado por duas rodadas de review** — porque a família inteira é
invisível a quem procura bug, não sensor cego.

### O que o passe procura

Código cujo trabalho é *notar alguma coisa* — guarda, gate, health check, alarme, etapa de
verificação — e cujo modo de falha é **silêncio**. Silêncio é indistinguível de sucesso, então o
defeito sobrevive ao review, sobrevive ao CI, e só aparece quando alguém pergunta "por que não
recebemos o alerta?". A pergunta que define o passe: *se este sensor quebrar, alguma coisa fica
vermelha, ou ele só para de reportar?*

Cinco formas, todas medidas em código real:

| Forma | Exemplo que motivou |
|---|---|
| Erro engolido no sensor | `2>/dev/null \|\| true` numa leitura cujo valor decidia se um aviso dispara |
| Veredito **negativo** | sucesso = "não casei com `error\|failed`" — deixava passar `Connection refused`, `No such container`, `Permission denied` |
| Gate mirando o alvo errado | gate lia 1 de 5 chunks que o build emitia; verde sobre o arquivo errado |
| Chave de dedup grossa demais | `{regra, dia, entidade}` sem discriminante — a segunda falha real do dia sumia para sempre |
| Asserção sem timeout | `curl` sem `--max-time`: corpo vazio conta zero ocorrências e imprime `ok` |

### Calibração, para não virar ruído

Só conta quando o valor engolido/negativo/sem-timeout **decide um alerta, um gate ou fluxo de
controle**. `2>/dev/null` cosmético, `catch` com fallback observável e retry que loga e desiste alto
não são achado. A distinção é observabilidade, não sintaxe.

Severidade **MEDIUM** por padrão, **HIGH** quando o sensor cego é o único controle sobre aquele
risco, **nunca CRITICAL** — esse degrau é do 6.10, e inflar este faz a escada de severidade parar
de significar alguma coisa.

### Por que always-on mas sem gate

Sensor cego não reporta nada por definição, então foco estreito é justamente quando ele escaparia —
daí always-on. Mas ele não pode forçar F: se forçasse, o banner de BLOCKED deixaria de significar
"uma credencial está exposta". As duas passagens obrigatórias diferem em **consequência**, não em
cobertura.

### Também nesta versão

- `metadata.version` do `SKILL.md` estava em **1.14.0** enquanto o `plugin.json` marcava 1.19.0 —
  divergência pré-existente, alinhada agora em 1.20.0.
- Quatro keywords novas: `silent-failure`, `blind-sensor`, `observability`, `poka-yoke`.

## [1.19.0] — 2026-09-03

Otimização de custo (`/claude-api` → `cost-optimization`, Steps 0–4) da skill `codereview`, **medida**
em 16 sessões REVIEW do pipeline `sdd_agents` (14/08–01/09) que invocaram `/codereview:codereview`
(Opus 5 como orquestrador, Sonnet 5 nos agentes). Relatório completo, simulador e sensores ficaram
fora do repo; aqui vai o que mudou e por quê.

### `codereview` 1.14.0

**O que foi medido.** Uma invocação custava $11–16, 46–65% da sessão REVIEW ($24,40 em média).
Os agentes da Fase B respondiam por $10,33 (42%): $2,5 por agente, 22–65 turnos cada (média ≈ 45)
contra ~6 no desenho. O custo era cache-read acumulado (2,7–7 M tokens por agente), não o tamanho
das references: **1 de 66 agentes leu `detection-passes.md`** (caminho relativo — o agente não achava
e seguia explorando livre); **16 de 16 sessões parafrasearam o prompt de lançamento** (o bloco de
45 linhas virava "adversarial review", "sabotage pass", com sandboxes de repro em `/tmp`); em
**6 de 16 sessões `model:` foi omitido** e os agentes rodaram no modelo principal a 1,6× a tarifa.
O sweep (B2) seguia o mesmo formato: 63–66 turnos de grep um a um. Pelo desenho, a mesma revisão
custaria ≈ $2,7 — o gap é o número de turnos, não o prompt.

- **Contrato dos agentes em arquivo** (`references/per-file-agent.md`, `references/sweep-agent.md`):
  o agente lê as próprias instruções por caminho absoluto (`{SKILL_DIR}/references/…`); o
  orquestrador emite só o prompt de lançamento de ~12 linhas, "nada a mais, nada a menos" — o que
  ele não escreve, não reescreve. As instruções mandam: um lote de leituras no primeiro turno
  (references + diff + arquivo); escopo = o diff e o arquivo (sem sandbox de repro, sem rodar a
  suíte, sem varrer o repo — achado que precisa de reprodução volta marcado `needs reproduction`);
  arquivo > ~600 linhas lido por hunks ±40 mais o bloco de imports; `toctou-patterns.md` só com
  check-then-act; "planeje ~10 tool calls". Trailer `Tool calls | Files read in full` +
  `END_OF_FILE_REVIEW`; no sweep, `TOOL_CALLS:` antes de `END_OF_DEAD_CODE_SWEEP`.
- **`model: "sonnet"` como poka-yoke:** parágrafo no roteamento diz o que acontece sem o campo
  (a mesma análise a 2,5–5× a tarifa) e o footprint devolve o modelo que de fato rodou.
- **Bucket B do sweep opt-in:** a varredura repo-wide de código morto pré-existente (tooling
  `knip`/`ts-prune`/`vulture`…) só roda com foco `dead-code` ou `sweep=full`; a revisão completa fica
  com o Bucket A (o que este PR introduziu ou orfanou). Nos três sweeps medidos, o Bucket B era
  30–40% de $3,1–3,5 e nada dele pertencia ao PR em revisão. Sem o bucket, o relatório traz uma
  linha dizendo como obtê-lo. O prompt de lançamento passa a levar `Focus area` e `Sweep` (antes
  o agente não tinha como saber o foco); chave `sweep` documentada em `configuration.md`.
- **Fase A em três turnos:** passos 1–3 num comando (fallback de branch base em cadeia), passo 4,
  passos 5–8 em paralelo; probe de cobertura de testes num único loop de shell. Defaults inline no
  SKILL.md; `configuration.md` só com override `key=value` ou stack ≠ TS/React.
- **Cost footprint:** última linha de todo relatório —
  `_Cost footprint: N per-file agents (model), sweep …, M files read in full, agent tool calls
  min–max, orchestrator Bash calls K._` — alimentada pelos trailers. `END_OF_FILE_REVIEW` ausente ⇒
  arquivo `partially analyzed`. "Measure, don't guess" entra nas Context Efficiency Rules.
- `detection-passes.md` 6.6: `toctou-patterns.md` por caminho absoluto e só com check-then-act.

**Fora desta versão, por decisão:** Haiku nos agentes e `effort: low` (trade-offs sem eval de
achados para julgar — e `effort` só entra por definição de agente, que o plugin não distribui);
agrupar 5 arquivos por agente e subir o threshold inline (refutado: move a análise para o modelo
principal a tarifa maior); sweep inteiro opt-in (perderia o Bucket A).

**Como verificar (keep/revert):** turnos por agente < 15 e todos os agentes lendo as references
no stream do pipeline; custo dos agentes caindo ≥ 30% **sem** sumir CRITICAL/HIGH entre o relatório
antigo e o novo do mesmo diff. Se um CRITICAL/HIGH sumir, reverter primeiro só a frase "Plan on
roughly ten tool calls" em `per-file-agent.md` e medir de novo.

**Medido depois da publicação (2026-09-03).** Duas invocações headless de `/codereview:codereview`
(`claude -p`, orquestrador Opus 5) sobre o **mesmo diff real** de 18 arquivos (6 de código, `bin/sdd` com
6,6k linhas) no `sdd_agents`, lidas pelo stream com o mesmo sensor do baseline:

| | Baseline (16 sessões, 1.17.x) | Run A | Run B |
|---|---|---|---|
| Custo da revisão (ledger) | $11–16 só o codereview | **$6,62** (Opus $3,07 + Sonnet $3,55) | **$5,92** (Opus $2,64 + Sonnet $3,29) |
| Agente por arquivo | $2,0 (Sonnet), ≈45 turnos, 30–90 tool calls | $0,58 / $0,76 / $1,61 — 3 / 9 / 20 turnos — 13 / 13 / 28 tool calls | $0,73 / $0,83 / $0,87 — 7 / 12 / 11 turnos — 20 / 26 / 15 tool calls |
| Sweep | $3,1–3,5, 63–66 turnos | $0,62, 6 turnos | $0,69, 8 turnos |
| Leu as references | 1 de 66 agentes | 4 de 4 | 4 de 4 |
| Modelo que rodou | Opus em 6 de 16 sessões | Sonnet 4/4 | Sonnet 4/4 |
| Trailer + sentinela | — | 4/4 | 4/4 |
| Relógio | 20–33 min por sessão | 13 min | 11 min |

Achados: nenhum CRITICAL/HIGH nas duas; as duas convergem no mesmo achado principal (fail-open do glob
`0|0.*` no teto de orçamento) e em dois secundários; cada uma achou 1–2 MEDIUM que a outra não achou —
variância normal entre runs. O Bucket B saiu como a linha "não varrido" e o Cost footprint fechou os dois
relatórios. **Veredito: L1–L5 ficam** (custo por agente −50–60%, turnos < 15 em 7 dos 8 agentes,
references lidas por todos). O que a medição **não** cobre: o diff não tinha revisão anterior à 1.19.0,
então "nenhum CRITICAL/HIGH sumiu" fica sem teste; a missão do baseline (`20260901-o-revisor-so-acha`) já
estava mesclada e o seu revisor deixou de invocar o skill a partir da r3 — a comparação é por agente, não
por missão.

### `coderabbit_pr` 3.6.0

Inalterada.

## [1.18.0] — 2026-09-03

Prompt audit (`/claude-api prompt-audit`, modelo-alvo Claude Fable 5.1) nas duas skills do plugin.
Relatórios completos ficaram fora do repo; aqui vai o que mudou e por quê.

### `codereview` 1.13.0

- **Fase A roda inline.** Os sete comandos `git`, a classificação de arquivos e o pré-scan de
  secrets são um plano determinístico — cada passo tem uma resposta certa — executado por um agente
  haiku. O agente era a causa do incidente da 1.12.0 (campo `SECRETS_PRESCAN` que não voltava), e as
  36 linhas de ênfase, template de retorno e fallback tratavam o sintoma. A sonda do auditor mediu
  variação entre runs no mesmo arquivo. Agora os comandos rodam na sessão principal; as saídas são
  pequenas e a Fase C precisava delas de qualquer jeito. A `coderabbit_pr` já tinha feito essa
  migração na 1.17.0. Fase B (sonnet, paralelo) e Fase C (modelo principal) inalteradas.
- **Ênfase:** 28 de 32 linhas em caps voltaram ao tom normal; as 4 que ficam têm a razão ao lado.
  O bloco "Mandatory final sections" (4× "Forbidden", escrito contra Opus 4.x) virou um parágrafo
  que diz o que renderizar e por quê — o modelo-alvo segue uma instrução única.
- **Modelo fixo em prosa:** "opus" era citado 8× como o modelo principal; agora "the main model —
  whichever model the session is running". A description troca `(haiku/sonnet/opus)` por
  "tiered model routing" (489 → 476 chars, idêntica nos 3 lugares).
- `detection-passes.md`: a narrativa do incidente `@sales-quote`/`FORMA_PAGAMENTO` (projeto de
  origem) vira a forma geral do defeito; referências ao "haiku agent" saem.

### `coderabbit_pr` 3.6.0

- **Registry de reviewers corrigido por medição** (`gh api users/` e os 25 PRs mais recentes):
  `copilot-pull-request-reviewer` é a organização, não o bot — o review object vem de
  `copilot-pull-request-reviewer[bot]` e os inline sob um segundo login, `Copilot`, que ninguém
  listava; os dois logins do Codex não existiam (404) — o que existe é `chatgpt-codex-connector[bot]`.
- Frases relativas à versão anterior ("inline **now**", "rows that **still** delegate") e
  arqueologia de PR (`PR #6 de validade_bateria_estoque`, `PR #7`) saem; a regra fica.
- "opus"/"sonnet" fixos viram "main model"/"cheaper model" (o exemplo `model: "sonnet"` fica).
- O baseline de testes (4.0) diz onde de fato roda: no início da 3.2, quando os vereditos indicam
  que algo vai mudar — as duas sondas cegas do auditor travaram exatamente nesse ponto.
- "Address every comment… Never skip" ganha o sensor: `unresolved: 0` da fase 5.3.

## [1.17.2] — 2026-08-26

Higiene de `description`, sem mudança de comportamento: o texto tinha **686 chars**,
acima do cap de 500 do `CLAUDE.md`. A `description` é a superfície de triggering — é só
por ela que o Claude decide invocar a skill —, e descrição longa demais dilui o sinal e
pode ser **cortada em silêncio** na lista `/skills`, piorando justamente o que ela deveria
melhorar.

### Changed

- **Description encurtada de 686 para 489 chars**, espelhada nos três arquivos
  (`SKILL.md`, `plugin.json`, `marketplace.json`). Encurtada **em vez de somada**: o que
  saiu foi a qualificação dos detectores (`GitGuardian-equivalent regex`, `knip/ts-prune/vulture or grep`, o exemplo de contract drift) e o preset `dotnet` — detalhe que continua no corpo da skill, onde é útil de fato.
  Os sinais de disparo (o que a skill faz + os diferenciais que a distinguem das vizinhas)
  foram preservados.

## [1.17.1] - 2026-07-25

### Fixed (coderabbit_pr 3.5.0 → 3.5.1 — quatro defeitos de coerência que uma rodada REAL da v1.17.0 expôs)

Motivação: a v1.17.0 foi testada ao vivo no PR #25 do `ui24-agent`. As quatro mudanças
novas funcionaram (checagem de branch pegou a divergência e trocou sozinha; a varredura
apagou dois checklists do PR #7 parados na árvore desde 28/06; a união dos dois endpoints
achou o Copilot que só aparecia em `/reviews`; o caso (b) registrou "não rodou" em vez de
"aprovou"). Mas a rodada expôs quatro incoerências — três delas **introduzidas pela
própria v1.17.0**:

- **Fase 2 e Fase 6 se contradiziam em rodada de zero achados.** A 2 mandava criar o
  arquivo mínimo "for audit completeness" e a 6 apagava segundos depois — o arquivo nunca
  chegava a ser artefato de auditoria nenhum. Agora o arquivo só é escrito quando
  `--keep-checklists` garante que ele sobrevive; no default a determinação (a)/(b) vai
  para o **relatório final**, que é onde o usuário lê. A determinação em si continua
  obrigatória: é a diferença entre "este PR passou pela revisão" e "ninguém olhou".
- **O "Stop" do Error Handling colidia com o caminho de zero achados da Fase 2.** Ficou
  explícito que parar vale só quando **nenhum bot postou nada** (nem em `/comments`, nem em
  `/reviews`). Um reviewer que postou mas não achou nada — ou que reportou não ter
  conseguido rodar — segue pela Fase 2 e **tem** de ser relatado; parar ali engoliria
  justamente o achado mais importante da rodada.
- **A Fase 4 não tinha ramo "nada mudou".** Ela compara um antes e um depois; sem edição
  não há depois. Agora é pulada quando a Fase 3 não alterou arquivo nenhum, com o motivo
  dito no relatório. Dois custos concretos evitados: minutos de suíte inútil num repo
  grande, e uma falha pré-existente chegando com cara de ter sido causada pela rodada —
  exatamente a confusão que o baseline da 4.0 existe para impedir.
- **O `rm` da Fase 6 não era determinístico** — justo na fase cuja proposta era ser
  determinística. Listava quatro nomes fixos mais um comentário não executável ("plus any
  `{bot-login}-review.md`"). Agora casa pelo **cabeçalho que a própria skill escreve**, o
  que cobre reviewer desconhecido sem lista fixa e **não toca** em doc de projeto que só
  por acaso termina em `-review.md` (`security-review.md`, `architecture-review.md`) — que
  é o que um `rm -f *-review.md` ingênuo apagaria. Mesmo guard já usado na varredura da 1.1.

Editado: `skills/coderabbit_pr/SKILL.md` (Error Handling, Fase 2, Fase 4, Fase 6) e
`skills/coderabbit_pr/references/checklist-template.md` (o arquivo mínimo agora é
condicionado ao `--keep-checklists`). Sem mudança na superfície de triggering.

## [1.17.0] - 2026-07-25

### Changed (coderabbit_pr 3.4.0 → 3.5.0 — as fases mecânicas viram determinísticas e a skill passa a limpar o próprio lixo)

Motivação: numa sessão real (PR #15 do `ui24-agent`, 3 achados do Gemini) as fases
mecânicas mostraram três problemas — dois de confiabilidade e um de sujeira acumulada.

- **Listar comentários e fechar threads eram delegados a subagentes** (haiku/sonnet) com
  prompts em prosa ("return ONLY the unique bot logins", "Run them in parallel. Report how
  many succeeded"). São chamadas de API com UMA resposta certa: o agente no meio só
  adiciona variação, latência e **omissão silenciosa** — uma rodada que pula uma thread é
  indistinguível de uma rodada limpa. Agora rodam inline, com comandos fixos, e a fase 5
  termina numa **asserção `unresolved: 0`** que é o gate da conclusão.
- **A extração agora é uma projeção `--jq` fixa**, separada da *interpretação*. Isso
  resolve melhor o próprio problema que a skill citava (30-50KB de JSON cru poluindo o
  contexto): descarta `diff_hunk`/URLs/reações **antes** de qualquer contexto, em vez de
  absorver tudo num subagente e confiar no resumo. Delegação a sonnet continua, mas com
  gatilho objetivo (>1500 linhas ou 3+ reviewers com body longo). Dois detalhes não
  óbvios ficaram codificados: `\(.line // .original_line)` (o `line` vem **null** quando o
  diff do comentário fica defasado) e `select(.body != "")` (approvals têm body vazio e
  viravam achado fantasma).
- **Nova Fase 6 — limpeza.** No repositório real havia `gemini-review.md` e
  `coderabbit-review.md` do **PR #7 (2026-06-28)** ainda na árvore em **2026-07-25**; o
  `.gitignore` até os declarava efêmeros (`*-review.md`) e mesmo assim nada limpava. Pior:
  para não sobrescrever o registro antigo, a rodada nova nomeou os arquivos
  `gemini-review-pr15.md` — que **escapa do padrão `*-review.md`** e vira arquivo não
  rastreado permanente. As duas regras agora se sustentam em par: **nome sempre fixo**
  `{reviewer}-review.md` e **apagar ao concluir com sucesso** (só no caminho de sucesso,
  preservando a resumibilidade). Flag `--keep-checklists` para quem quer o artefato.
  Varredura de resto de execução anterior na Fase 1.1 como backstop — importante porque o
  cross-reviewer check da 3.1 LÊ esses arquivos e um checklist velho engana a rodada.

### Fixed (dois bugs de correção encontrados na mesma sessão)

- **A skill dizia "All fixes are made on the current branch"** — falso sempre que se
  resolve o PR estando em outro branch. Na sessão o usuário estava em
  `fix/webapp-eco-corretivo` e o PR #15 vivia em `docs/pos-mvp-prd`; seguir a skill ao pé
  da letra teria posto correções de PRD num branch alheio, **sem nunca chegar ao PR e sem
  nada falhar alto**. A Fase 1.1 agora compara `git branch --show-current` com o
  `headRefName` do PR: árvore limpa → checkout e avisa; árvore suja → para e reporta.
- **"Não rodou" era registrado como "aprovou".** O template de zero achados escrevia
  *"reviewer approved without issues"*; o Copilot respondeu **"unable to review — quota
  limit"**, ou seja, a review nunca aconteceu. Agora os dois casos são distintos, o (b)
  registra o texto literal do bot, é marcado como **lacuna de cobertura** e não conta como
  cobertura no resumo final.

Editado: `skills/coderabbit_pr/SKILL.md` (fases 1.1, 1.2, 1.3, 2, 5, nova 6, tabela de
Model Routing e Operating Principles) e `skills/coderabbit_pr/references/checklist-template.md`
(zero achados em dois casos + regra de nomeação). Descrição: acrescentado apenas
"then cleans up its own checklist files" (396 → 436 chars, dentro do alvo).

## [1.16.0] - 2026-06-15

### Changed (pass 6.9 Dead Code — guardrail "over-export" agora distingue dois sub-casos com correções OPOSTAS)

Motivação: numa sessão real de cleanup, o guardrail over-export (introduzido na
v1.15.0) dava UMA correção — "remova o `export`". Mas símbolos usados só dentro do
próprio arquivo se dividem em dois casos com remédios opostos, e aplicar o errado
quebra código vivo:

- **(a) plumbing interno** (não aparece em nenhuma assinatura exportada) → remover
  `export` (como antes). Ex.: `DefField`.
- **(b) superfície de tipo pública** — o símbolo aparece na assinatura de um símbolo
  **exportado** (ex.: `AuthUser` tipando o campo `user` do `UseAuthReturn` exportado;
  `UpdateArgs` dentro do `UseCotacaoMutationsReturn` exportado) → **manter o `export`**.
  Removê-lo quebra o contrato de tipo público e pode disparar o erro TS *"exported X
  has or is using private name Y"* (TS4023/TS4094) sob declaration emit / build
  composto (`tsc -b`). Se a ferramenta ainda reclamar, **marcar intencional** com
  `@public` (o knip honra) ou `@internal` — nunca deletar/narrowing.

O grep within-file/exported-signature agora é **check obrigatório por-símbolo** em
TODO achado "unused export", não uma anedota. (No caso real, um PRD derivado de
review ainda mandou "apagar" `cotacaoQueryKey`/`cotacaoEventosQueryKey` — mesmo padrão
do `DefField` já citado — prova de que a aplicação não era sistemática.)

Editado: `references/detection-passes.md` §6.9 (bullet over-export reescrito em (a)/(b))
e `SKILL.md` Phase B2 (resumo do guardrail espelha os dois sub-casos). Sem mudança na
superfície de triggering — descrição inalterada.

## [1.15.0] - 2026-06-15

### Changed (codereview SKILL.md v1.11.0 → v1.12.0 — calibração do pass 6.9 Dead Code para a saída de `knip`/`ts-prune`)

Motivação: numa sessão real, o agente de Dead Code Sweep (Phase B2) rodou `knip` e
produziu dois falsos-positivos que exigiram correção manual. Esta versão codifica
as duas lições como guardrails, para o agente acertar de forma determinística em vez
de depender de julgamento.

- **Categoria "unused export" precisada** em `references/detection-passes.md`: agora
  distingue *morto de fato* (sem referência em lugar nenhum, inclusive no próprio
  arquivo) de **over-export** (símbolo usado DENTRO do próprio arquivo, mas sem
  importadores externos). `knip`/`ts-prune` reportam over-export como "unused export"
  porque só contam referências *cross-file* — mas o símbolo está vivo.
- **Novo guardrail "Over-exported (used only within its own file)"**: a correção é
  **remover o `export`** (tornar module-private), **não deletar o símbolo**. Flag em
  LOW/cleanup. Motivado por caso real: um helper `DefField` usado 11× no próprio
  módulo, reportado como unused-export — deletá-lo quebraria a página.
- **Novo guardrail "Regenerable / generated scaffolding"** sob `generatedDirs`
  (`src/components/ui/**`, `**/generated/**`): primitivos de design-system (shadcn/ui
  re-adicionáveis via `npx shadcn add`) e saída de codegen. `knip` os surfaceia em
  massa (dump de ~30 arquivos que afoga os achados do PR) → mantê-los em **Bucket B**,
  **Low confidence**, capados, rotulados "regenerable scaffolding"; nunca como
  dead-code acionável do app, salvo se o próprio diff orfanou um.
- **Phase B2 (`SKILL.md`)**: a lista de guardrails do agente de sweep agora cita
  explicitamente over-export e scaffolding regenerável.

## [1.14.0] - 2026-06-13

### Added (codereview SKILL.md v1.10.0 → v1.11.0 — pass 6.9 Dead Code + Phase B2 dedicated sweep agent)

- **Novo pass 6.9 "Dead Code & Unused Symbols" em `references/detection-passes.md`** (no slot livre entre 6.8 e 6.10). Detecta exports não usados, arquivos órfãos, código inalcançável (após `return`/`throw`/`break`), imports/locals/membros privados não usados e dependências mortas. Escopo **híbrido**: Bucket A = código morto introduzido OU orfanado por este diff (primário, sempre reportado); Bucket B = código morto pré-existente surfaceado por tooling do próprio repo (secundário, rotulado "pre-existing", capado em ~10 + contagem total para não afogar o report). Detecção **tooling + grep fallback**: usa `knip`/`ts-prune`/`depcheck` (TS/JS), `vulture`/`ruff` (Python), Roslyn `IDE0051` via `dotnet build` (.NET), `deadcode`/`staticcheck` (Go) quando disponíveis — read-only, mesmo padrão oportunista do ggshield/gitleaks no pass 6.10 — e cai pro deepsearch por grep de referências (incluindo arquivos não-code: HTML/JSON/YAML/SQL) quando não há tooling.
- **Guardrails de falso-positivo são o coração do pass** (recomendar deletar código vivo é pior que deixar passar código morto): public API surface (entry points de pacote, barrels, libs), wiring por framework/reflexão (rotas, DI, decorators, `import()` dinâmico, registries por string, entidades ORM, serialização, test discovery), referências em arquivos não-code, re-exports, utilitários só-de-teste, compilação condicional, scaffolding recém-adicionado. Cada finding carrega **Confidence** (High/Medium/Low).
- **Novo agente paralelo dedicado "Phase B2: Dead Code Sweep" no `SKILL.md`**, lançado no mesmo batch paralelo dos agentes per-file da Phase B. É um agente separado — não um pass per-file — porque dead-code é uma pergunta de **grafo de referências do repo inteiro**: cada agente per-file vê só um arquivo e não consegue saber se um export é usado em outro lugar. Roda em full review, foco `bugs` e foco `dead-code`; é **skipado** em focos estreitos (security/a11y/types/performance/docs/tests) — diferente do 6.10 (secrets), dead-code é higiene, não gate. Para ≤3 CODE files (routing desligado) roda inline no main model. Tem return-template + output-discipline como Phase A/B, mas resultado ausente é **não-bloqueante**.
- **Severidade: MEDIUM** só para itens orfanados pelo diff ou arquivos órfãos inteiros; **LOW** para o resto. **Nunca CRITICAL/HIGH, nunca força grade F, nunca bloqueia o PR.**
- **Phase C ganhou step 9 "Merge dead-code findings"** (produce-report passou a step 10): funde Bucket A/B, respeita Confidence, mantém Bucket B capado, e renderiza a nova seção. Dead-code alimenta Recommended Actions → Consider Fixing e a rationale de Code Quality (Zen) — sem adicionar linha à tabela mandatória Overall Grade (preserva o contrato v1.13.0).
- **`references/report-template.md`**: nova seção **🧹 Dead Code & Cleanup** (após Documentation Sync, antes de Overall Grade) com tabela `Symbol/File | Kind | Location | Origin (PR/pre-existing) | Confidence | Recommended Cleanup`; nova linha **Dead Code (pass 6.9)** na tabela Bug/Security/Performance/Types Summary (só colunas MEDIUM/LOW).
- **Skill description ganhou clause + triggers de dead-code** ("dead code", "unused exports", "cleanup", "code health") espelhados em SKILL.md / `plugin.json` / `marketplace.json`, com a description enxugada (corte do parêntese verboso de contract-drift) pra ficar ≤700 chars e não inchar a superfície de triggering.

### Why (pass 6.9)

Pedido do dono via `/retrofit-skill`: "faça um deepsearch e adicione um agente extra paralelo que procura código morto e recomenda sua limpeza para manter o projeto de código saudável". O gap é real e estrutural, não inventado: os passes existentes 6.1–6.10 são todos **per-file / diff-scoped**. Cada agente sonnet da Phase B recebe **um único arquivo** + seu diff e retorna findings — ele fisicamente não consegue responder "este export é referenciado em algum outro lugar do repo?", que é a pergunta central de código morto. Logo, exports não usados, arquivos órfãos e símbolos que o diff deixou sem nenhum chamador escapam de todos os passes atuais: 6.4 (Type Safety) cobre `any`/casts, 6.1 (Bug) cobre null/async, 6.5.x cobre docs/contract-drift, 6.10 cobre secrets — nenhum olha o grafo de referências do repositório. A escolha de um **agente paralelo dedicado** (não um pass per-file) reflete exatamente essa restrição: dead-code precisa de visão whole-repo via grep/tooling, então merece seu próprio agente rodando em paralelo com os per-file, com escopo híbrido (relevante ao PR primeiro, saúde do projeto como secundário capado) e guardrails fortes pra nunca recomendar deletar código que só *parece* morto (wiring por framework, reflexão, consumidores externos de lib).

## [1.13.0] - 2026-05-22

### Changed (codereview SKILL.md v1.9.0 → v1.10.0 — new detection pass 6.5.3 + mandatory Overall Grade rendering)

**Part 1 — new detection pass 6.5.3 "Contract Drift in Tests":**

- **Novo sub-pass 6.5.3 em `references/detection-passes.md`** logo após 6.5.2 (Project Documentation Sync). Detecta drift entre constantes exportadas (`export const X = [...] as const`, schemas Zod/Yup/literal-union) modificadas no diff e os testes que asserem essa constante com literal-by-literal (`expect(X).toEqual([...])`, `toStrictEqual`, `toMatchObject`, `assertEquals`, `deepEqual`). Severidade: **HIGH** quando o símbolo é parte de contrato público (Zod em `shared-api-types`, enum cross-package, constante espelhada em OpenAPI); **MEDIUM** para constantes internas usadas como fixture-validation; **LOW** quando o teste asserta um superset do export (passa mas precisa cleanup). Pass é skipado quando o teste também está no diff com update casado.
- **Nova linha "Contract Tests" na Documentation Sync table** do `references/report-template.md`, com status `OK / DRIFTED` e exemplo concreto (`FORMA_PAGAMENTO`: test asserts 4 items, export has 7). Status `DRIFTED` exporta a finding para a Findings Table principal.
- **Skill description ganhou triggers** "contract drift", "stale test contract", "exported const drift", "test-vs-source-of-truth drift" para casar pedidos de review que mencionem esse cenário.

**Part 2 — mandatory final-report sections (Overall Grade + Recommended Actions):**

- **Phase C step 9 no `SKILL.md` recebeu bloco novo "Mandatory final sections"** explicitando que `### Overall Grade` e `### Recommended Actions` NUNCA podem ser omitidos, truncados ou substituídos por prosa. Lista os quatro modos de falha conhecidos (token pressure, zero-findings happy path, focus-area run, long-running review com muitas findings) e exige um self-check antes do return: a resposta tem que conter ambos os headers exatamente uma vez cada.
- **`references/report-template.md` ganhou call-out "ALWAYS rendered"** em cima da tabela Overall Grade e da seção Recommended Actions, com instruções específicas para cada modo de falha: rationale terse (`"clean"`, `"3 HIGH"`, `"n/a"`) sob pressão de contexto, grade `—` + rationale "Not analyzed" para focus-area, `_None._` sob cada bucket vazio de Recommended Actions. Render explícito de buckets vazios é importante porque uma "Must Fix" ausente lê como "relatório incompleto", não como "sem critical findings".

### Why (Part 1 — 6.5.3)

Sessão `/speckit-implement` da feature 012 (`SQ-33_codigo_unico_cotacao_sqn_jdb`) no repo `sales_quote`: ao rodar a suite completa do monorepo, vi `packages/shared/api-types/src/__tests__/contracts.test.ts > FORMA_PAGAMENTO contém os 4 valores canônicos` falhando. Reproduzi em baseline via `git stash + rerun` → também falha → declarei "drift pré-existente de outra feature, não introduzido por esta task" no resumo final do speckit-implement.

O usuário pediu `ultrathink` + `superpowers:systematic-debugging` sobre essa decisão. Em ~5 min e 3 greps:
- `grep "export const FORMA_PAGAMENTO" enums.ts` → tupla tem 7 valores + docstring "Conjunto completo restaurado em SQ-22 (rollback do R-022 da spec 011)".
- `grep -n "FORMA_PAGAMENTO" contracts.test.ts:70` → `expect(FORMA_PAGAMENTO).toEqual([...4 items])`.
- `git log --all --oneline -S 'BOLETO_90_DIAS' -- enums.ts` → commit `58f9d4a feat(SQ-22)` adicionou os 3 boletos legados ao tipo e à tupla. Mesma branch tocou `contracts.test.ts` em commit posterior (`5f3179a`) só para renomear VALIDADA→APROVADA. O `toEqual` ficou stale.

Conclusão: a PR do SQ-22 era exatamente o lugar onde um codereview pré-PR deveria ter pegado isso. O diff modificou `FORMA_PAGAMENTO` (4 → 7 valores) com docstring explicando o motivo, e o `contracts.test.ts` em mesma branch continuou afirmando 4. Cross-check trivial: grep do símbolo no codebase → encontra `expect(FORMA_PAGAMENTO).toEqual([` → comparar literal asserted vs export atual → mismatch → flag HIGH. Nenhum dos passes existentes 6.1–6.10 captura isso: 6.5.2 (Documentation Sync) cobre OpenAPI / README / CLAUDE.md / MEMORY.md, mas não testes-como-contrato. 6.4 (Type Safety) cobre `any` e casts, não drift de literal. 6.10 (Secrets) é outro escopo. Gap real.

O 6.5.3 fecha o gap deterministicamente, sem heurística LLM frágil: o pass é um grep simples + comparação de length/content. O pattern é universal (Vitest, Jest, Mocha, xunit, NUnit — qualquer framework com asserções de igualdade profunda contra constantes importadas). Custo: 1 grep extra por export modificado no diff, com short-circuit cedo se nenhum match. Para diffs sem export modificado é no-op total.

O nome do pass — "Contract Drift in **Tests**" — é deliberado: drift de docs já era coberto por 6.5.2; o que faltava é o caso onde o artefato stale é uma asserção de teste em vez de uma linha de doc. A doc fica stale silenciosamente (alguém lê e fica confuso); o teste fica stale silenciosamente também (passa em todas as branches até a próxima refatoração tocar o símbolo, aí o CI lit up e parece "drift de outra feature"). A segunda forma é mais perigosa porque cada novo contribuinte que vê o vermelho repete o ciclo de `git stash` + dismiss. O sub-pass quebra esse loop no review original.

### Why (Part 2 — Overall Grade mandatory render)

Feedback do usuário em paralelo a este retrofit: "quero também que a tabela que apresenta o resultado e o Grade de cada parte analisada volte a SEMPRE aparecer, essa tabela muitas vezes não tem aparecido". Inspeção da Phase C step 9 mostrou que `Overall Grade` aparecia na lista de seções junto com várias outras, mas SEM o modificador `(always present)` que `Secrets Detection table` tinha desde a v1.8.0. Resultado: sob pressão de contexto / zero findings / focus-area run, o opus omite a tabela e fecha o relatório com prosa do tipo "Looks clean, grade A" — perdendo o entry point que o humano usa para triagem.

Mesma família de bug que motivou a v1.12.0 (Phase A agent fazendo todo o trabalho via tool calls mas devolvendo "results above" como final message): a skill confia na disciplina implícita do modelo de "sempre emitir todas as seções", e essa disciplina falha em condições previsíveis. O fix da v1.12.0 foi prompt mais rígido + orchestrator-side fallback. O fix análogo aqui é (a) elevar `Overall Grade` e `Recommended Actions` ao status explícito de "MANDATORY — NEVER omit", (b) listar os modos de falha conhecidos com instruções concretas para cada um, (c) exigir self-check programático antes do return ("a resposta contém `### Overall Grade` e `### Recommended Actions`?"). Mesmo princípio do "verify-before-trust" da v1.10.0 aplicado à camada de output assembly.

A regra do `_None._` em buckets vazios de Recommended Actions é especialmente importante: render do header com bucket vazio comunica "checado, sem entradas"; ausência do header comunica "esqueci de checar isso". Para a UX humana, são respostas qualitativamente diferentes.

### Migration notes

- Sem breaking changes. Comando público `/codereview` inalterado, args inalterados, modelo de routing inalterado.
- Phase A (haiku) e Phase B (sonnet) ganham, na execução, 1 grep extra por export modificado no diff (`grep -rn "expect({SYMBOL})\.toEqual\|toStrictEqual\|toMatchObject" .`). Para diffs sem export modificado, no-op. Para o mediano (1-2 exports modificados), <500ms extra.
- Phase C (opus) cross-reference já trata findings de 6.5.x sem mudança — só precisa reconhecer 6.5.3 como categoria válida na Documentation Sync table.
- A tabela Documentation Sync no relatório ganha uma linha nova quando há finding 6.5.3 (e fica oculta quando não há, igual às demais linhas N/A — comportamento da `render N/A` da tabela já está estabelecido).
- A nova regra do Part 2 (Overall Grade + Recommended Actions sempre presentes) é puramente prescritiva — não muda formato nem args. Em relatórios que já incluíam essas seções, no-op observável. Em relatórios que omitiam (zero findings / focus-area / token-tight), passam a incluir um bloco mínimo com rationale terse — overhead < 20 tokens.

---

## [1.12.0] - 2026-05-20

### Changed (codereview SKILL.md v1.8.1 → v1.9.0 — Phase A output discipline + secrets-gate fallback)

- **Phase A prompt reescrito com return template literal** (mesma forma do `## Output Format` que já existia na Phase B sonnet). O prompt agora abre com um aviso explícito de "the orchestrator only sees the agent's final assistant message — tool-call outputs are NOT propagated to the caller" e termina com um template literal que o agente preenche (`BASE_BRANCH:`, `DIFF_STAT:`, `COMMIT_LOG:`, `FILES:`, `COUNTS:`, `SECRETS_PRESCAN:`, `END_OF_PHASE_A_REPORT`). Substitui o "Return as a structured list + 8 bullets" abstrato anterior, que dependia de o modelo lembrar de paste-back os outputs.
- **Orchestrator-side fallback obrigatório** documentado logo abaixo do prompt da Phase A. Se a resposta do agente for < ~500 chars, faltar a string `SECRETS_PRESCAN:`, faltar `END_OF_PHASE_A_REPORT`, ou for uma frase-status do tipo "done"/"complete"/"results above"/"structured results returned", o orquestrador é obrigado a re-executar os 8 passos no main session via Bash em paralelo e rodar o `scan_secrets.sh` ele mesmo. Ausência de payload de secrets é tratada como "scan não rodou" (warn + re-run), nunca como "scan limpou".

### Why

Sessão de codereview no branch `SQ-22_aplicar_design_navigational_horizon` do repo `sales_quote`: o agente Phase A (haiku, 9 tool uses, 81s) rodou os 8 passos via tool calls com sucesso mas devolveu como final message apenas `"Phase A complete. Structured results returned above."` — sem nenhum dos dados estruturados que o prompt pediu. O orquestrador (Opus) ficou cego: nem o diff stat, nem a classificação, nem o `SECRETS_PRESCAN` JSON chegaram. Tive que rodar `git status`, `git diff --name-only`, `git diff --stat`, `git log` e pipe-ar para `scan_secrets.sh` manualmente em paralelo no main session — anulando completamente o benefício do model routing haiku → opus que a v1.6.0 introduziu.

Comparação direta entre os prompts mostra a causa raiz: a Phase B sonnet (que funcionou — 8 agentes em paralelo, todos devolveram findings estruturadas) termina com `## Output Format` + template literal numbered list + edge case explícito (`"No findings for {FILE_PATH}"`). A Phase A haiku terminava com `"Return as a structured list"` abstrato + bullets de campos. Em modelos menores (haiku) com prompts de 40+ linhas e múltiplos passos, "lista estruturada" não é instrução forte o suficiente — o modelo trata os tool-call outputs como "já entregues" e o final message vira um status executivo. A interface do Agent tool em Claude Code só propaga a última mensagem do agente, não o transcript; um final message status-only equivale a uma resposta vazia.

Pior do que perder o context routing: o gate F de secrets depende do JSON do `scan_secrets.sh` chegar ao Phase C. Se o agente Phase A "esquecer" de paste-back o JSON, o orquestrador não tem como aplicar o gate — a skill pode silenciosamente reportar "Secrets PASS" mesmo com findings reais existindo no diff. É o mesmo modo de falha do v1.9.0 do `coderabbit_pr` (não esconder failures atrás de uma view normalizada) aplicado a outra surface: não confiar que dados existem só porque uma etapa anterior "deveria ter produzido".

O fix tem duas pernas, deliberadamente redundantes:

1. **Prompt mais robusto** — template literal ancorando o formato, warning sobre o que o caller realmente vê, end-marker (`END_OF_PHASE_A_REPORT`) para o orquestrador detectar truncamento. Reduz a probabilidade do agente errar, mas não elimina.
2. **Fallback obrigatório no orquestrador** — validação programática da resposta + re-execução completa no main session quando o agente under-reportar. Garante que mesmo se o prompt falhar, a skill nunca produz um relatório com secrets-gate degradado silenciosamente.

### Migration notes

- Sem breaking changes. Comando público `/codereview` inalterado, args inalterados, output final do relatório inalterado.
- A nova Phase A consome ~30-50 tokens a mais no prompt (template literal). Para o median PR é overhead desprezível; para PRs pequenos (≤3 CODE files) o threshold de v1.6.0 já roteia tudo para o main session sem agente.
- Quando o fallback dispara (agente under-reportou), o orquestrador roda os passos no main session — custo equivalente a antes do model routing existir. Trade-off intencional: prefiro pagar o custo de re-execução do que produzir um relatório com gate de secrets cego.

---

## [1.11.0] - 2026-05-17

### Changed (coderabbit_pr v3.3.1 → v3.4.0 — byte-exact verification for control-character findings)

- **Phase 3.1 gained step 1.1 "Byte-exact verification for control-character claims"** before classifying invisible-character/NUL-byte findings as false positives. When the reviewer mentions `\0`, `0x00`, `^@`, BOM, zero-width chars, non-printable bytes, embedded escape sequences, or anything described as "invisible/control character", the `Read` tool renders those bytes as plain whitespace — `\0create\0` is visually indistinguishable from ` create ` (regular spaces). Confirm against the actual bytes via `awk 'NR==<line>' <file> | od -c | head`, `tr -cd '\000' < <file> | wc -c`, `xxd <file> | grep -i <pattern>`, or `python -c "print(repr(open('<file>').read()))"` as fallback.
- **Skill description updated** to surface the byte-exact verification step in the triggering metadata, so users searching for "NUL", "BOM", "invisible character", or "control character" review feedback get a sharper triggering signal.

### Why

Session resolving PR #62 of `LouvorFlow`: Copilot flagged NUL bytes (`\^@`) embedded in a CommandItem `value` attribute (`` value={`\0create\0${search.trim()}`} ``). My initial analysis used `Read` to inspect line 297 — it rendered the NUL bytes as plain spaces, so the line looked like a harmless leading-space sentinel `` value={` create ${search.trim()}`} ``. Classified the finding as false positive, posted a public "not applicable — Copilot misinterpreted a space as NUL" comment on the thread, and resolved it.

Confirming after the fact with `od -c` showed `\0create\0` — the bytes were real, exactly as Copilot reported. Had to retract the comment publicly, push a follow-up commit replacing the NUL sentinel with `__create__:`, and re-explain the situation. Embarrassing waste of cycles, public retraction noise in the PR, and worse: produced a false-positive verdict on a legitimate, deterministic reviewer finding.

The generalization for `coderabbit_pr`: NUL bytes, BOM markers, zero-width characters, embedded escape sequences, and other non-printable bytes are exactly the kinds of issues that reviewers — especially deterministic parsers like Copilot's — will flag. And those are exactly the cases where `Read` is unreliable: it returns a *normalized text rendering*, not a byte-faithful one, and there is no warning when bytes were collapsed. Same principle as the v1.10.0 "verify before trust" applied to a different surface: don't outsource truth to a normalized view when the finding hinges on the underlying bytes. The cost of `od -c <file> | head` is essentially zero; the cost of a wrong "not applicable" verdict is a public retraction.

### Migration notes

- No breaking changes. Skill continues to resolve PR comments end-to-end.
- New sub-step (1.1) adds at most one `od -c` invocation per item where the reviewer explicitly cites control characters or invisible bytes. For the median PR (no such findings) the change is a no-op.
- If `od`/`xxd`/`tr` are not available (rare on developer workstations, but possible in stripped containers or some Windows shells), fall back to Python: `python -c "print(repr(open('<file>').read()))"` — `repr()` escapes control characters faithfully and works anywhere Python is installed.

---

## [1.10.0] - 2026-05-05

### Changed (coderabbit_pr v3.2.0 → v3.3.0 — verify-before-trust)

- **Phase 3.1 ganhou novo passo "Verify referenced state"** antes de aplicar QUALQUER fix: quando o reviewer cita arquivo, linha, comportamento runtime, ou referencia artefato externo (cached plan, doc, "as documented in X", "see previous session"), confirmar contra estado atual. PR diff e código vivo são autoritários; reviewer pode estar comentando em snapshot obsoleto desde o último push.
- **Operating Principle "Discipline" novo bullet "Verify before trust"**: reviewer claims sobre arquivos, linhas, comportamento ou artefatos externos são hipóteses a validar contra o código vivo, não fatos. Mesmo princípio do anti-silencing do v1.9.0 aplicado em outra direção.
- **Phase 4.2 nota refinada sobre cascade em fixes**: se o primeiro fix revelar pre-existing failures (cenário do v1.9.0 baseline), considere rerun baseline porque MAIS fixes podem revelar MAIS bugs latentes. Cascade fail-fast pode ter múltiplos níveis — não presuma que o segundo bug é o último.

### Why

Sessão de debug do PR #6 do `validade_bateria_estoque`: cached plan da sessão anterior documentava `TypeError: RequestInit signal AbortSignal` (msw v2 + jsdom + undici) como bug ativo bloqueando 44 testes. Verificação primária via `gh run view --log-failed` mostrou que o erro REAL do CI era completamente diferente: `Cannot find package 'jsdom' imported from /node_modules/vitest/...`. Os dois bugs existiam, mas o do cached plan estava mascarado pelo primeiro. Se eu tivesse aceitado o cached plan sem validar, teria proposto fix para o bug errado.

Generaliza para `coderabbit_pr`: reviewers (CodeRabbit, Copilot, Gemini, Codex) podem citar arquivo, linha ou comportamento que mudou desde o snapshot do review. Sem validar contra código vivo, o skill aplica fix em código que já mudou ou propaga diagnóstico incorreto. O princípio é o mesmo do anti-silencing do v1.9.0 (evidência primária antes de qualquer ação) — só que aplicado em outra direção: v1.9.0 dizia "não esconder failures"; v1.10.0 diz "não trustar referências sem validar".

A nota refinada da Phase 4.2 vem do mesmo PR #6: cicd v2.4.0 já documentava cascade fail-fast (bug 1 mascara bug 2). Aprendemos no PR #6 que pode ter MAIS de 2 níveis (bug 1 → bug 2 → bug 3). Após primeiro fix, considere rerun baseline em vez de assumir que o segundo bug é o último.

### Migration notes

- Sem breaking changes. Skill continua resolvendo PR comments end-to-end.
- Novo passo "Verify referenced state" adiciona ~5-30s por item de review (1 leitura extra de arquivo via Read tool). Para PRs com 50+ items, ainda dentro do orçamento (model routing haiku/sonnet do v1.6.0 já estava em vigor).
- Para itens onde o reviewer cita comportamento runtime que não se reproduz contra estado atual, marcar como `[x]` — "Não verificado: reviewer cita comportamento runtime que não consegui reproduzir contra código atual; PR submitter precisa confirmar antes do fix".

---

## [1.9.0] - 2026-05-05

### Changed (coderabbit_pr v3.1.0 → v3.2.0 — baseline-aware regression testing)

- **New Phase 4.0 "Capture Pre-Fix Baseline"** — instructs the skill to run the project's test command BEFORE applying any review fixes, saving pass/fail counts and the list of failing test names as a baseline. Without this, Phase 4.2 can't tell "regression caused by my fix" from "pre-existing latent unmasked by my fix".
- **Phase 4.2 expanded into a 5-way comparison** against the baseline: all-pass, same-failures-as-baseline (don't fix), new-failures (fix), fewer-failures (note but don't claim), mixed (separate). Each branch has explicit instructions about what to do.
- **Anti-silencing rule** added explicitly to 4.2: do NOT use `it.skip`, `if: false` on workflow steps, or `continue-on-error: true` to make CI green. Document and defer.
- **Operating Principle "Discipline"** gained a new bullet: "Don't expand scope to fix latent bugs — pre-existing test failures unmasked by your fixes are NOT yours to fix. Document and open follow-up issue."

### Why

PR #6 on `validade_bateria_estoque` had 8 red CI jobs. The root cause for 6 of them was a single broken `npm run -w <ws> exec --` syntax in 3 workflows — a fail-fast error that aborted in seconds at the Typecheck step, **masking** all subsequent steps. After the fix unblocked CI, **44 frontend tests started failing** with msw/jsdom AbortSignal interop errors, and 2 backend type errors appeared in `auth-sanity.test.ts`. These were ALL pre-existing — the `npm run … exec` failure was hiding them.

Without baseline awareness, Phase 4 of `coderabbit_pr` would treat these 44+2 failures as "caused by the applied fixes" and either (a) try to fix them (scope explosion: msw/jsdom interop is a non-trivial test infrastructure rabbit hole) or (b) silence them (which the skill explicitly should never do). The correct triage is: capture baseline before any fix, distinguish unmasked-latent from caused-by-edit, document the latent, fix only the caused-by-edit, push.

This generalizes beyond CI cascades: any regression-detection workflow needs a baseline to be honest. Without it, the question "did my change break X?" collapses into "is X broken?" — and the answer is often "yes, but not because of you".

### Migration notes

- No breaking changes. Skill still resolves PR comments end-to-end.
- New mandatory step at start of Phase 4 adds ~30s for typical projects (one extra `npm test` run). For PRs with `--skip-tests`, Phase 4 is skipped entirely as before.
- Existing checklists that don't include a "Pre-existing latent failures" subsection are still valid; the skill will add one when applicable.

## [1.8.0] - 2026-04-28

### Changed (codereview v1.8.0 — deterministic secret scanning replaces LLM-simulated regex)

- **New `scripts/scan_secrets.py` + `scripts/scan_secrets.sh` wrapper** — Phase A haiku agent now runs a real Python regex pass against the unified diff. Catalog from pass 6.10 is encoded as `re.compile` patterns with deterministic exception filtering (env-var lookups, placeholder values, `.env.example`/`.env.sample`/`.env.template` paths). When `ggshield` or `gitleaks` are on `PATH`, the script invokes them too and merges results (dedup by `{file, line, kind}`).
- **Phase A agent prompt now explicitly invokes the script** as numbered step 8 — captures the JSON output as `secrets_prescan` field in the structured return. Previously the prompt asked the agent to "apply" the regex catalog mentally; in practice substring shapes like `initialPassword: '<literal>'` (where `password` is a suffix of the keyword) were missed because LLMs aren't regex engines.
- **Phase C merge logic inverted** — `secrets_prescan` from Phase A is the **authoritative** source for the Secrets Detection table and the F-grade gate. Sonnet pass-6.10 findings are now treated as supplemental (context-aware nuance only); they're added to the table only if they reference a concrete literal credential AND match a pass 6.10 category. This eliminates LLM speculation as a gate-trigger while keeping it useful for edge cases regex can't see.
- **`detection-passes.md` corrected** — removed the false claim "this skill is read-only prose produced by LLM agents — it can't shell out to `ggshield`". The skill IS read-only (no `Edit`/`Write`/destructive git ops) but `Bash` invocations of pure scanners are perfectly compatible with that constraint and were always available. Replaced with a section pointing to the script as the single executable source of truth, with a note that the conceptual catalog and the script must be kept in sync (no automated guard yet).
- **Severity nuance preserved in script** — test-file inline literals stay HIGH (not CRITICAL) per pass 6.10 rules; multi-occurrence escalation (3+ in one file or 5+ across PR) still upgrades to CRITICAL. All exception logic (env lookups, placeholders, template files) ported faithfully from the conceptual catalog.

### Why

After PR #2 on `validade_bateria_estoque` (`feat(002-idp-oidc): IdP OIDC via Zitadel`) was blocked by GitGuardian with **3 Generic Password findings** (2 in test integration files at `initialPassword: '<literal>'` shape, 1 false-positive in a docker-compose env-var substitution), the user pointed out that v1.7.0 should have caught these locally before push. Investigation found three distinct gaps:

1. **Phase A pre-scan was a phantom step** — `SKILL.md` had a paragraph saying "the haiku agent runs a fast regex pre-scan" but the actual agent prompt code block never instructed the agent to do this. The pre-scan never ran.
2. **LLM-simulated regex is unreliable** — sonnet agents were asked to mentally apply the regex catalog from `detection-passes.md`. Substring shapes like `initialPassword: '...'` (where `password` is the suffix of `initialPassword`) were missed because the LLM "saw" the field name, not the regex match. False-negative rate was high enough on real-world test fixtures to defeat the purpose.
3. **`detection-passes.md` falsely claimed the skill couldn't shell out** — citing "read-only prose" as the reason. But read-only proibits Edit/Write/destructive git, not pure scanner invocations. The skill could have been running `ggshield secret scan path` or `grep -nE` since v1.0.

The v1.8.0 fix replaces LLM regex simulation with a real Python regex pass, enforced via an explicit numbered step in the haiku prompt. Verification against the actual PR #2 diff (`git diff a8551d2~1..6039813`) catches all 3 GitGuardian findings (and bonus catches a fourth `const SECRET = '<literal>'` that GitGuardian missed).

### Migration notes

- No breaking changes for users who don't customize the skill. Existing invocations like `/codereview` or `/codereview security` work identically; the only difference is the secrets pass actually fires now.
- If you wrote custom skills extending or wrapping this one, the haiku agent's structured return now includes `secrets_prescan: {findings, scanners, errors}`. Old fields (`BASE_BRANCH`, `BRANCH_NAME`, etc.) are unchanged.
- `scripts/scan_secrets.py` requires Python 3.8+ (uses dataclasses + walrus-free syntax for compatibility). No external deps; works in any environment that already has `python3`.

## [1.7.0] - 2026-04-18

### Added (codereview v1.7.0 — hardcoded secrets detection)

- **New pass 6.10 "Hardcoded Secrets Detection"** in `references/detection-passes.md` — explicit regex-based detection for generic passwords, JWT/Bearer, PEM keys, AWS/GCP/GitHub/Slack/Stripe tokens, `.env`-shaped assignments, and credentialed connection strings. Approximates what a dedicated CI scanner (GitGuardian, gitleaks, trufflehog) would reject.
- **Always applied to ALL file categories** — CODE, TESTS, CONFIG, UI_LIB, STYLES. Previously pass 6.2 was vague and `TESTS` files had reduced scrutiny; in practice test-file password literals are one of the most common leak shapes.
- **Always on regardless of focus area** — pass 6.10 runs even when the user asks for `/codereview performance` or `/codereview types`. A leaked credential is the one finding a user cannot afford to miss, so focus flags never silence it.
- **Phase A haiku pre-scan** — haiku agent now runs a fast regex sweep across the full raw diff (`git diff ${MERGE_BASE}...HEAD`) independent of file classification, catching secrets that land in `EXCLUDED`/`DOCS`/`CONFIG` files that per-file analysis would otherwise skip.
- **Anti-false-positive rules** — env-var lookups (`process.env.X`, `import.meta.env.X`, `config.get(...)`, `os.environ[...]`, `ConfigurationManager.AppSettings[...]`), placeholders (`"CHANGE_ME"`, `"xxx"`, `"<your-key-here>"`, empty string, null), and `.env.example`/`.env.sample`/`.env.template` placeholder values are explicitly not flagged.
- **Test-file nuance** — inline test literals (`password: "test123"`) flagged as HIGH (not CRITICAL) since they're less dangerous than prod keys but still rejected by CI scanners; literals pulled from `fixtures/` modules or `process.env.TEST_*` are not flagged.
- **Multi-occurrence aggregation** — 3+ matches in one file or 5+ across a PR collapse to a single aggregate finding with count and line ranges, escalated to CRITICAL. Signals systemic leaks rather than drowning the report.
- **New "Secrets Detection" table** in `references/report-template.md`, rendered before the Findings Table, with masked snippets (`***`), severity column, and Status (PASS/BLOCKED). Always present — shows `PASS` with 0 rows on clean branches to confirm the pass ran.
- **BLOCKED banner + forced grade F** — any pass 6.10 finding forces overall grade to F and prepends a banner linking to [GitGuardian secrets-API-management best practices](https://blog.gitguardian.com/secrets-api-management/). The Grading Scale is updated to reflect this.
- **Full remediation block** — every pass 6.10 finding now includes the four GitGuardian-recommended remediation steps (understand blast radius → env var / secret manager → rotate → rewrite history) plus the recommendation to install `ggshield pre-commit` for durable local defense. Previously the report said only "move to environment variable", which is necessary but insufficient once the secret is already in git history.
- **Masking rule** — findings show the literal masked as `***` rather than echoing the raw credential back into chat history.
- **Trigger phrases expanded** — `"secret detection"`, `"hardcoded credentials"`, `"gitguardian"`, `"ggshield"`, `"leaked password"`, `"api key"`, `"check for secrets"` now trigger the skill.

### Why

PR #5 on `eb-analytics` (`feat(server): cloud sync backend`) was blocked by GitGuardian with **11 Generic Password findings** across two commits (`f0bc35a`, `7257978`): 8 in `auth.test.ts`, 2 in `concurrency.test.ts`, 1 in `server.ts`. The previous pass 6.2 treated "exposed secrets" as a single vague bullet and gave `TESTS` files reduced scrutiny — exactly where most leaks lived. CodeRabbit passed the same PR clean; secret detection is a distinct domain and deserves a dedicated pass with concrete patterns, always-on enforcement, and blocking severity. Aligns with GitGuardian's best practices: use secrets managers, never commit credentials, install `ggshield` as a pre-commit hook, and when a leak happens rotate first and rewrite history second.

## [1.6.0] - 2026-04-12

### Changed (codereview v1.6.0 — model routing)

- **Model routing for token efficiency**: skill now delegates work to cheaper models
  - Haiku agent: git context, file classification, test coverage mapping (pure CLI + pattern matching)
  - Sonnet agents (parallel): per-file analysis using detection passes (pattern matching on code)
  - Opus (main model): cross-file review, severity recalibration, final report production
  - Auto-skip for small PRs (≤3 CODE files) — runs everything in main model
- **Detection passes extracted to reference file**: Steps 5-6 (~350 lines of detection patterns) moved from SKILL.md to `references/detection-passes.md`, keeping SKILL.md as a lean orchestrator (~200 lines)
  - Sonnet agents load only the detection passes + file content in their context
  - Opus receives only structured findings, not raw code — 76-86% less opus tokens
- **Parallel per-file analysis**: each CODE file analyzed independently in its own sonnet agent, enabling parallel execution for faster reviews
- **Cross-file analysis preserved in opus**: race conditions spanning multiple files, schema consistency, and import chain coherence still analyzed by the main model

### Estimated token savings

| PR Size | Before (all Opus) | After (mixed) | Opus Savings |
|---------|-------------------|---------------|--------------|
| Small (3 files) | ~85K | ~20K opus + 50K sonnet/haiku | ~76% |
| Medium (8 files) | ~150K | ~25K opus + 128K sonnet/haiku | ~83% |
| Large (15 files) | ~210K | ~30K opus + 212K sonnet/haiku | ~86% |

## [1.5.0] - 2026-04-12

### Changed (coderabbit_pr v3.0.0 → resolve_pr_reviews)

- **Multi-reviewer support**: now auto-detects and processes CodeRabbit, Copilot, Gemini Code Assist, and Codex reviews on a PR
  - Each reviewer gets its own checklist file (`coderabbit-review.md`, `copilot-review.md`, `gemini-review.md`, `codex-review.md`)
  - Unknown reviewers are handled with a generic parser and `{bot-login}-review.md`
  - New `--reviewer <name>` flag to process only a specific reviewer
- **Model routing for token efficiency**: skill now delegates work to appropriate model tiers
  - Haiku agents: GitHub API calls, data fetching, thread resolution (mechanical tasks)
  - Sonnet agents: comment parsing, code fix execution (pattern matching tasks)
  - Opus (main model): analysis verdicts, spec verification (judgment calls)
  - Auto-skip routing for small PRs (<5 comments) — overhead not worth it
- **Improved analysis quality**: verdicts now check project specs/docs before marking "not applicable"
  - Prevents false fixes on by-design decisions documented in specs
  - "Not applicable" entries now include spec/doc reference
- **Better large-output handling**: sonnet agents absorb 30-50KB+ API responses in their own context and return only structured summaries, keeping the main opus context clean
- **Deduplication improvements**: cross-reviewer dedup, root-cause linking ("Related to item #N")
- **New `references/reviewer-registry.md`**: extensible registry of bot logins, parsing rules, and output file names
- **Severity recalibration**: opus model reassesses reviewer-assigned severities during Phase 3 analysis based on actual code impact (e.g., Copilot defaults everything to MEDIUM but a broken feature flow is HIGH)
- **Cross-reviewer deduplication with audit trail**: items already fixed by another reviewer's round are marked "Already fixed — see {reviewer}-review.md #{N}" instead of re-analyzing
- **Empty reviewer handling**: reviewers with zero findings (e.g., Gemini approval-only) get a minimal `{reviewer}-review.md` for audit completeness

## [1.4.0] - 2026-04-05

### Added

- Detection pass 6.6 Race Conditions & TOCTOU (Time-of-Check to Time-of-Use)
  - Database check-then-act (findUnique + update without atomic claim)
  - Read-modify-write on numeric fields (lost updates)
  - Business rules enforced only in app code (bypass via concurrency)
  - Read outside transaction, write inside (stale data)
  - File system check-then-act (exists then read/write)
  - Cache thundering herd (miss + compute without coalescing)
  - `references/toctou-patterns.md` — full pattern catalog with code examples
- Detection pass 6.7 Accessibility
  - Icon-only buttons without aria-label
  - Form buttons without type="button" (implicit submit)
  - Interactive elements without keyboard support
  - Images without alt text
- Detection pass 6.8 Data Integrity & Schema Safety
  - Cascade delete risks on user/tenant entities
  - Missing database indexes on junction tables
  - URL fields accepting dangerous protocols (javascript:, data:)
  - Inconsistent validation schemas across endpoints
  - Test fakes/mocks missing fields from production schema
- Focus areas `a11y` and `race-conditions` for targeted reviews
- `security` focus now includes 6.6 Race Conditions and 6.8 URL/cascade checks
- `bugs` focus now includes 6.6 Race Conditions

### Changed (coderabbit_pr v2.0.0)

- Fixed parsing of "outside-diff-range" comments from CodeRabbit review body
  - Now correctly extracts findings from `<details><summary>` blocks in review body
  - Previously only inline diff comments were detected (2-5 items); now captures all 20-30+ items
- Added Phase 5: Resolve GitHub Conversations
  - Uses GraphQL API to fetch and resolve all unresolved review threads
  - Resolves threads from all reviewers (CodeRabbit, Gemini, Copilot, etc.)
  - Reports resolution count in checklist
- Improved severity mapping to handle both emoji and text markers
- Added deduplication between inline and review body findings

## [1.3.0] - 2026-03-28

### Added

- Detection pass 6.5 Documentation Sync & Docstring Coverage
  - 6.5.1 Docstring coverage: verifica JSDoc/XML doc/docstrings em funcoes novas/modificadas, detecta idioma se projeto especifica (PT-BR, etc.)
  - 6.5.2 Project documentation sync: verifica se README, OpenAPI, rules, CLAUDE.md e MEMORY.md foram atualizados junto com o codigo
- Focus area `docs` para revisar apenas documentacao
- Suporte a docstrings de Go e Shell scripts
- Grade "Documentation" no relatorio final
- Secao Documentation Sync no report-template.md

### Changed

- Agnostico de linguagem para deteccao de docstrings (TS/JS, C#/.NET, Python, Go, Shell)
- Step 9 agora mapeia focus areas para passes especificos explicitamente

## [1.2.0] - 2026-03-25

### Added

- `dotnet` as `frameworkPatterns` option for C#/.NET projects (WPF, WinForms, ASP.NET, Console)
- .NET-specific checks: `async void`, `IDisposable`, `MessageBox` in service classes, `public static` mutable, `new HttpClient()`, `Thread.Sleep()`, SQL injection, MVVM violations
- .NET file exclusions: `bin/`, `obj/`, `*.Designer.cs`, `*.g.cs`
- .NET test file mapping: `{ProjectName}.Tests/{Base}Tests.cs` patterns
- .NET test root auto-detection via `.csproj` references to xUnit/NUnit/MSTest
- .NET override examples in configuration.md
- .NET report example in report-template.md
- `dotnet test` command detection in coderabbit_pr skill

### Changed

- Zen Principles (§5) and Detection Passes (§6) refactored into universal + framework-conditional blocks
- All React/TypeScript-specific checks now conditional on `frameworkPatterns=react|vue|angular|node`
- Backward compatible: default behavior unchanged when no `frameworkPatterns` override is specified

## [1.1.0] - 2026-03-23

### Adicionado

- Nova sub-skill `coderabbit_pr` — extrai comentarios do CodeRabbit de um PR, cria checklist estruturado, verifica e corrige cada item, e roda testes de regressao
- Mapeamento de severidades CodeRabbit (🔴🟠🟡🔵) para CRITICO/ALTO/MEDIO/BAIXO
- Suporte a `--dry-run` (somente verificacao) e `--skip-tests`
- `references/checklist-template.md` — template do arquivo de checklist gerado
- Deteccao automatica de comando de teste (npm/cargo/pytest/go/make)

## [1.0.0] - 2026-03-13

### Adicionado

- Skill de code review automatizado pré-PR inspirado no Zen of Python (PEP 20)
- Análise de diffs com severidades CRITICO/ALTO/MEDIO/BAIXO
- 5 princípios Zen como lentes de análise (readability, explicit, simple, flat, error handling)
- Passes de detecção: bugs, segurança, performance, type safety
- Avaliação de cobertura de testes (COM_TESTE / TESTE_DESATUALIZADO / SEM_TESTE)
- Nota final por letra (A-F) com critérios por categoria
- Stack-agnostic com defaults TypeScript/React configuráveis
- `references/report-template.md` — template completo do relatório
- `references/configuration.md` — valores default e sintaxe de override

---

## Histórico Pré-Marketplace

A skill existia como v2.0.0 informal no repositório `digital_service_report_frontend` (sem disciplina semver). O histórico abaixo documenta a evolução antes da publicação no marketplace.

- **v2.0.0** (2026-03-10): Reescrita completa — classificação de arquivos por categoria, progressive disclosure via references, override de configuração stack-agnostic, grading scale A-F, cap de 50 findings
- **v1.0.0** (2026-03): Versão inicial com análise básica de diffs e relatório estruturado
