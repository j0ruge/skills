---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 1
status: done
sessao: 01a2210c-6de4-73a3-a979-0895f57f8adc
data: 2026-11-28 04:34
gate: "Em 1f1b0083efbb3bf753559432ca03ba2df4d5c048, env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval \"$TEST_CMD\"' → rc 0, adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 144 do Stop e versões validadas. git status --porcelain → vazio na árvore revisada. env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py → rc 0. O gate de revisão não fecha com R1–R3 pendentes. A camada 1 da branch e a distribuição nativa tampouco estão verdes."
reviewed_head: 1f1b0083efbb3bf753559432ca03ba2df4d5c048
---

# Review — rodada r1 — Retrofit de skills locais com ensaio antes do push autônomo

## TL;DR

Revisão completa de `origin/main...HEAD`. Confirmei sete achados, seis de produto agrupados em três
incrementos. O patch aprovado deixou uma emenda privada passar e o slug confundiu origens de hosts diferentes.
A jornada da QA, os cinco pontos do Review Focus e o TEST_CMD passaram. A publicação não está pronta.

## Nota da rodada

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | O fluxo reaproveita as guardas full, mas reaproveitou também uma exclusão de patch exclusiva da loja e uma chave de estado que não identifica o repo. |
| Type Safety | A | Os formatos privados validam slug e pasta, recusam campos privados incompletos e mantêm leitura dos formatos full legados. |
| Error Handling | B | Falha no setup deixa destino residual e o registro de avanço perde erros na colisão de nomes. |
| Security | C | A publicação aceitou uma emenda fora do patch revisto, e a elegibilidade e a porta confundiram origens de servidores distintos. A varredura não encontrou credenciais literais. |
| Performance | A | A prova direcionada de startup offline passou, com retorno em menos de 1 s no teste. O fetch roda em filho e a leitura da janela tem prazo compartilhado. |
| Test Coverage | B | Os cinco sensores do plano passaram, mas não cobriram a emenda em arquivo ignorado pelo hash nem a colisão de origens que a revisão reproduziu. |
| Documentation | B | As versões e o fluxo básico batem com os artefatos, mas o caminho nominal da auditoria contradiz a variante privada. |
| **Overall** | **C** | Dois limites de autorização falharam em fixture e a cópia dedicada ainda pode avançar um ramo que não é a main. |

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | HIGH | O digest privado herda as exclusões de listas públicas. Com a skill na pasta rastreada `scripts/`, a emenda em `scripts/public-names.txt` preservou o digest, a revisão e o approve. O lote saiu `publicado` com `aprovado=true` e o bare recebeu o conteúdo não revisado. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:516`, `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:894` |
| 2 | HIGH | A identidade joga fora o servidor. Um checkout com `origin` numa forge diferente e um clone no GitHub com o mesmo slug passaram na classificação e em `why_manual`. A porta também aceitou o `origin` efetivo reescrito para outro servidor pelo Git, antes do fetch. O status usa só `repos/<dono/repo>`. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:306`, `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:854`, `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:1137` |
| 3 | MEDIUM | `live-advance` verifica o ramo antes do fetch. O dono trocou para um ramo limpo no intervalo e o avanço retornou `ok`, moveu o ramo do dono e deixou a `main` no SHA anterior. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:993` |
| 4 | MEDIUM | `live-setup` deixa o diretório reservado se falhar. Sem `main` no bare, `git clone` saiu 128. Depois de restaurar a `main`, a repetição recusou com `destino já existe`. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:947` |
| 5 | MEDIUM | Repos listados de donos diferentes com o mesmo basename dividem o registro de avanço. O registro `fora-da-main` do clone existente foi sobrescrito pelo `erro` do segundo repo. O startup mostrou só o segundo. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:1010`, `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_auto.py:920` |
| 6 | LOW | O aviso não distingue registro ausente de JSON presente ilegível. Nos dois casos `live_notice` retornou `None`. A falta de aviso antes do primeiro avanço é legítima. A ausência de sinal para o arquivo inválido não entra na nota como achado de sensor isolado. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_auto.py:921` |
| 7 | LOW | A referência do executor manda usar a auditoria da loja, mas mantém `Q`, `SQA` e `RS` definidos sob o worktree privado. Na fixture o auditor nesse caminho estava ausente, e o mesmo caminho relativo existia no clone da loja. Só prosa. | `plugins/retrofit-skill/references/modo-autonomo.md:13`, `plugins/retrofit-skill/references/modo-autonomo.md:22` |

### Reprodução dos achados

Usando `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -` com fixtures descartáveis no SHA desta rodada:

1. Em `GateTest`, semeei no bare uma skill em `scripts/` com `SKILL.md`, CHANGELOG e `public-names.txt`.
   Preparei lote com `SKILL=PASTA="scripts"`, editei, selei, gravei `diff.json`, observei `auto-dry` e
   aprovei. Emendei apenas o txt, com a mesma mensagem. `store.patch_id` ainda era igual ao de
   `diff.json`. `publish` publicou a emenda. `git show main:scripts/public-names.txt` no bare confirmou
   os bytes. Nenhuma conexão a repo real.
2. Em `PrivateWorld`, configurei `origin` do clone e do desenvolvimento como HTTPS em servidores
   diferentes com `fixture/kb-libs`. `classify_path` atribuiu o mesmo slug e `why_manual` com
   `bypassPermissions` e entrypoint `cli` devolveu `None`. Em `GateTest`, uma regra local `insteadOf`
   trocou o bare por uma forge de fixture com o mesmo slug. `_g_place` devolveu `None` e
   `_private_origin` devolveu a URL reescrita. A prova parou antes de qualquer fetch externo.
3. Em `PrivateWorld`, publiquei uma revisão de fixture no bare. Depois de executar o fetch real da
   fixture no dublê de `_live_fetch`, fiz `git switch -qc ramo-do-dono` no clone dedicado. O HEAD desse
   ramo avançou ao commit novo enquanto a `main` permaneceu intacta. O JSON registrou `ok`.
4. Em `PrivateWorld`, guardei o clone inicial com outro nome e renomeei `main` para `outro` no
   bare. A chamada de `live_setup` falhou e deixou o destino. Restaurei `main` no bare e repeti.
   O destino da tentativa anterior bloqueou a segunda chamada.
5. Em `PrivateWorld`, listei `fixture/kb-libs` e `other/kb-libs` e troquei o clone existente de ramo.
   Rodei `live_advance` para os dois em ordem, como faz a CLI sem argumento. Sobrou só
   `repo=other/kb-libs` no JSON. `live_notice` não mencionou o erro do primeiro.
6. Na mesma estrutura de fixture, comparei `live_notice` antes da primeira gravação e depois de criar
   `live/kb-libs.json` com JSON truncado. Nos dois estados não houve aviso.
7. Depois de `prepare` na fixture privada, usei `Path(worktree) / gate.AUDITOR` e `w.store / gate.AUDITOR`.
   `is_file()` foi `False` no caminho nominal da referência e `True` no da loja.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R1 | 1 | Um teste de emenda em arquivo antes excluído deve acusar revisão desatualizada e manter o bare. A sonda repete a rota de aprovação. |
| R2 | 2 | Dois testes separam hosts homônimos na classificação e na porta, inclusive com reescrita efetiva. A sonda repete a rota privada autorizada. |
| R3 | 3–6 | Quatro testes cobrem retomada do setup, troca de ramo, colisão de registros e registro presente inválido. A sonda repete setup e avanço. |

## O que virou incremento

- `R1` concentra o patch privado. O novo Check prova a retenção da emenda sem mudar a política pública.
- `R2` concentra a identidade da origem e o vínculo dos efeitos ao destino autorizado. Os testes
  verificam negativa para servidores distintos e preservam a identificação nas formas suportadas.
- `R3` agrupa os quatro reparos pequenos de clone e aviso. Cada comportamento tem um teste nomeado.
- A rodada é a primeira e não fez correção de código.

## O que foi refutado

- Uma emenda comum não invalida a aprovação — refutado por `test_changed_patch_invalidates_approval`
  e pela sonda. O achado 1 é a exceção reproduzida quando o arquivo está na lista de exclusão.
- Ausência de pre-push executável deixa o bare avançar — refutado por `test_missing_gate`. Alteração
  permanente do HEAD depois do ensaio também não subiu em `test_head_race_after_rehearsal_does_not_push`.
- Colisão de nome entre a loja e uma skill local mescla lições — refutado por
  `test_same_name_store_and_lean_never_merge`. O achado 5 envolve dois registros de avanço, não triagem.
- A impressão digital e as formas SSH seriam credenciais — refutado pela origem documentada da
  impressão digital pública e pelos literais de fixture no teste. `regex` e `gitleaks` retornaram
  zero achados. Isso não refuta a camada 1 vermelha. A branch não está liberada.
- Os 181 casos vermelhos da suíte ampla seriam regressão da branch — refutado pela comparação dos
  mesmos identificadores de falha com `6d72029`, normalizando apenas endereços de função.
  O resultado tampouco atesta uma suíte ampla verde em host limpo.

## Achados fora de escopo

- Achado 7, prefixos documentais da auditoria privada, registrado na seção **Documentação da loja**.
  Não virou incremento.
- As três sinalizações da camada 1 já estão em **A camada 1 sinaliza evidência sintética da entrega local**.
  A segunda skill full permanece no item preexistente da atribuição. Não dupliquei os itens nem acrescentei
  recorrência para a mesma missão.
- A aprovação pública da v1 vinculada ao patch permanece fora de L2, conforme a missão e o item que já a registra.

## Pendências / Decisions for a Human

Nenhuma decisão nova de produto. Para a liberação, falta um host que permita iniciar Bubblewrap e
ofereça temporário gravável sem marcador Git ancestral. A validação nativa não chegou à instalação.
A camada 1 do diff completo precisa ficar verde antes da publicação, sem isentar credenciais reais.

## Evidência e escopo da codereview

- Base `origin/main` em `9d679b1cd660e577b7d828e0be4154f14e0342b5`. O diff completo tem 15 commits e
  35 arquivos, com 4 módulos Python de produção, 10 arquivos de teste ou fixture, 3 manifestos e
  18 arquivos de texto. A análise da missão não reabriu o diário de notas.
- **Secrets Detection** — `PASS` no escopo de leitura. `git diff origin/main...HEAD --unified=0 --
  . ':(exclude)docs/handoffs/20261127-retrofit-watch-050/checkpoint-notas.md'` entregue a
  `bash /home/joruge/.agents/skills/codereview/scripts/scan_secrets.sh` no SHA revisado retornou 34
  arquivos, 3.110 linhas acrescentadas, zero achados e zero erros. A camada 1, separadamente,
  `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 scripts/anonymity-gate.py --camada1 --base origin/main`
  retornou 1 com as três sinalizações sintéticas já descritas pela QA. `python3 -B scripts/check-private-names.py`
  retornou 0.
- **Cobertura** — os quatro módulos alterados têm cobertura direta ou indireta nas suítes
  `test_lean_auto` (`retrofit_watch`, `rw_auto`), `test_lean_batch` e `test_lean_live` (`rw_store`)
  e `test_lean_gate` (`rw_gate`). Em `1f1b008`,
  `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests:plugins/retrofit-skill/tests python3 -B -m unittest test_fixture_private test_lean_auto test_lean_window test_lean_live test_lean_batch test_lean_gate test_auto_docs test_modo_autonomo`
  retornou 0 com 110 testes. `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s plugins/retrofit-skill/tests -v`
  retornou 0 com 11 testes. Esses números não somam cobertura, pois há contratos em comum.
- **Review Focus** — em `1f1b008`, `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest -v test_lean_batch.BatchTest.test_same_name_store_and_lean_never_merge test_lean_live.LiveTest.test_advance_leaves_wrong_branch_dirty_tree_and_divergence_alone test_lean_gate.GateTest.test_missing_gate test_lean_gate.GateTest.test_changed_patch_invalidates_approval test_lean_live.StartupTest.test_offline_advance_is_in_child_and_reported_on_next_startup` retornou 0 com 5 testes. A primeira seleção
  ampliada usou a classe incorreta `PrivateBatchTest` e foi descartada. O teste correto pertence a `BatchTest`.
- **Jornada** — em `1f1b008`, `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py` retornou 0. O ensaio
  conservou `4d53f9bac1e0`, a nova aprovação alinhou bare, status capturado, registro e clone em
  `970a68f924b1`, auto publicou `a468c847ab30`, o revert voltou a reter em `ceae86b0adc6` e o
  sim da rota manual alinhou `caf236e54e77`. `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B e2e/test_retrofit_watch_stop.py`
  retornou 0 com um teste e silêncio nos três cenários linked, missing e empty.
- **Suíte ampla** — `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/var/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s plugins/retrofit-watch/skills/retrofit-watch/tests -v` retornou 1, 555 testes, 5 falhas e 176 erros em `1f1b008`.
  O mesmo comando na árvore extraída por `git archive 6d72029` retornou 1, 487 testes, os mesmos
  casos. `/var/tmp` devolveu sistema de arquivos somente leitura, com fallback a `/tmp`,
  onde `/tmp/.git` disparou a guarda de colheita. Atribuição da segunda skill também falha na base.
- **Distribuição** — em `1f1b008`, `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 SKILLS_SKIP_NATIVE_DISTRIBUTION=0 python3 -m unittest discover -s tests -p 'test_codex_distribution.py'`
  retornou 1, três casos falharam antes da instalação por falta de permissão para criar namespace
  no Bubblewrap com `codex-cli 0.172.0`.
- **Documentação e versão** — README, catálogos, manifestos e CHANGELOGs acompanham as versões
  0.5.0 e 0.12.0. O ADR, a doc de clone e as referências mantêm separados worktree, clone em uso e
  checkout de desenvolvimento. O achado 7 é a inconsistência encontrada nas instruções de auditoria.
- **Dead Code & Cleanup** — varredura de referências dos símbolos introduzidos ou órfãos no diff,
  sem achados. Busca textual sem ferramenta semântica instalada. O estoque preexistente não foi varrido.
- Nenhum ambiente real foi alterado. Os status de fixture vieram de dublês e não atestam credenciais ou
  publicação no serviço real.

### Recommended Actions

**Must Fix (CRITICAL)**

Nenhum.

**Should Fix (HIGH)**

- `R1` — incluir no digest privado todos os caminhos da skill que a porta pode publicar e usar a mesma
  identidade de patch no selo, na revisão e no approve. Preservar o tratamento das listas na rota pública.
- `R2` — comparar a identidade completa no vínculo entre origem da sessão, clone e destino efetivo.
  Não aceitar equivalência entre servidores só pelo slug. Mantê-la consistente para fetch, push e status.

**Consider Fixing (MEDIUM/LOW)**

- `R3` — recuperar tentativas incompletas, garantir que o avanço não mova outro ramo e mostrar o estado
  do repo correto no startup. Separar a correção documental no backlog.

_Custo da revisão — codereview 2.27.38, dois agentes de código, um lote documental e uma varredura com
gpt-6.1-terra. As análises delegadas retornaram seus marcadores de conclusão e os achados acionáveis
foram reproduzidos nesta sessão._
