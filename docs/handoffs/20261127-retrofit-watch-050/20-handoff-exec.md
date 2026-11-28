---
missao: 20261127-retrofit-watch-050
fase: EXEC
status: done
sessao: 01a22167-6577-7980-b294-7f3292691515
data: 2026-11-28 06:14
gate: "Em c445ff702ac82ddf8fdb76f7d5443dab7e709e3d, env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval \"$TEST_CMD\"' → rc 0 (154 testes da loja, 3 pulados; 144 do Stop; adaptadores, catálogo e versões válidos). Os 13 comandos do checkpoint deram a saída esperada. env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests:plugins/retrofit-skill/tests python3 -B -m unittest test_fixture_private test_lean_auto test_lean_window test_lean_live test_lean_batch test_lean_gate test_auto_docs test_modo_autonomo → 145 testes sem pulos. env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py → rc 0, com retenção, aprovação, janela v2, revert e rota manual em remotos de fixture."
---

# Handoff — EXEC — Retrofit de skills locais listadas

> Escrito no fim de cada fase. A próxima fase é uma **sessão nova sem memória**: se algo que ela
> precisa saber não está aqui (ou nos artefatos linkados), está perdido.

## TL;DR

I1–I4 e R1–R9 concluídos. O setup preserva o destino concorrente e permite repetir
após recusa da origem final. O startup avisa quando o avanço não consegue iniciar.
Suíte, 13 Checks e jornada de fixture verdes em `c445ff7`. QA começa pelo Check R9.

## Estado do repo

- **Branch:** `feat/retrofit-watch-050-loja` — base de comparação `origin/main` local.
- **Último commit de produto:** `c445ff7` — instala o clone sem substituir o destino e avisa falha no lançamento.
- **Working tree:** limpo após o commit de checkpoint, notas e handoff.
- **Suíte:** `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval "$TEST_CMD"'` → rc 0 em `c445ff7`. Loja 154 (3 pulados), Stop 144, adaptadores, catálogo e versões válidos.
- **E2E:** sem `E2E_CMD` na config. Jornada automatizada em `sonda-qa.py` com remotos bare de fixture. Nenhum deploy ou repo privado real.

## O que foi feito

- `d929f44` — elegibilidade por origem e janela v2 local, com ensaio quando a prova não é suficiente.
- `785c388` — clone dedicado, avanço `--ff-only`, triagem, worktree e selo por origem.
- `ff7025b` — porta privada, revisão e aprovação por patch, status `local/ci`, startup e retro manual.
- `04a1a77` — manifesto, metadata, catálogo, README e CHANGELOGs sincronizados. O sensor de release ficou vermelho nas versões antigas, passou nas novas e acusou 17 mutações em cópia descartável sob grupo próprio, 10 s e 512 MiB por processo.

### Rodada 1 de revisão

- `fe68792` — R1 inclui no digest privado todos os arquivos alterados da skill, inclusive os caminhos
  reservados às listas no fluxo público.
- `bc8a164` — R2 mantém slug e servidor associados na classificação, porta, status e avanço.
- `30d619b` — R3 limpa a reserva do setup quando a criação falha, confere o ramo e a árvore novamente
  após o fetch e separa os registros por slug completo. O startup distingue falta de registro
  de JSON inválido. Controle de 20 testes do clone e 43 mutações detectadas com tetos de 30 s e 512 MiB.

### Rodada 2 de revisão

- `4f9d3cb` — R4 mantém a chave da lista separada do caminho efetivo e distingue origens com o
  mesmo slug fora da equivalência do GitHub público. O Check e a sonda passaram, com 11 contraprovas.
- `def54f4` — R5 conserva a origem de transporte do Git e entrega ao `gh` o servidor sem a porta SSH.
  Preserva a porta HTTPS não padrão e o fallback bare da fixture. As duas formas SSH da
  elegibilidade usam loopback, sem alterar o scanner. Red por divergência no argumento do `gh`,
  Check R5 e 130 regressões verdes, 13 mutações detectadas em cópias descartáveis com grupo próprio,
  teto de 20 s e 512 MiB por processo. As 62 âncoras do TODO passaram.

### Rodada 3 de revisão

- `8744b1d` — R6 distingue destinos Git cuja equivalência não foi comprovada. Os controles
  verificam inelegibilidade e retenção antes do fetch em caso de troca de destino.
- `38c46e3` — R7 deixa a porta HTTPS não padrão na URL absoluta da API, não em `--hostname`.
  A regressão ficou vermelha no comando antigo e comparou o SHA publicado no bare, capturado
  no status e recebido no clone. A variante SSH manteve a URL relativa sem sua porta de transporte.
  O Check, 132 regressões dirigidas sem pulos e 63 âncoras do TODO passaram. As oito mutações da
  implementação falharam nas regressões, com controles íntegros antes e depois, grupo próprio,
  teto de 20 s e 512 MiB por processo. README, CHANGELOG, contrato do clone e referência acompanham R7.

### Correções anteriores à próxima revisão

- `af9095a` — R8 prepara o clone e a trava em diretório temporário. O Red reproduziu o clone visível antes da trava e a perda de um arquivo criado no destino. O Green preservou a retentativa, o arquivo local e a validação da origem efetiva.
- `3162507` — a referência da retro privada define a auditoria a partir da loja configurada e mantém o alvo na pasta da skill.
- `b5512cb` — o plano liga a revisão exata da Ponytail e as fixtures SSH usam endereços de teste. A camada 1 da branch passou.
- As receitas citadas na r3 têm aspas de shell nos blobs de `9432d56`. A leitura dos bytes confirmou o argumento do scanner e a receita literal de `40-review-r2.md:98` executou o TEST_CMD com rc 0 em `b5512cb`. Os escapes necessários permanecem nos campos YAML.

### Rodada 4 de revisão

- `c445ff7` — R9 usa movimentação exclusiva para preservar até diretórios concorrentes vazios.
  Se a validação final recusar a origem, a cópia identificada como da tentativa volta ao
  temporário e o setup pode ser repetido depois de corrigir a regra. Falha ao lançar o
  avanço gera aviso imediato, mantém o resultado anterior e não interrompe os demais avisos.
  O Red reproduziu os três defeitos em `82b2530`. O Green passou nas 145 regressões dirigidas,
  inclusive no teste offline, e na jornada. Em cópia descartável, 34 mutações foram detectadas
  com controles verdes antes e depois, grupo próprio, teto de 20 s e 512 MiB por processo.

## Artefatos

| Arquivo | O que contém |
|---|---|
| `docs/handoffs/20261127-retrofit-watch-050/checkpoint.md` | Treze Checks e seus commits. |
| `docs/retrofit-watch/clone-dedicado.md` | Contrato de clone, selo, ensaio, publicação e avanço. |
| `plugins/retrofit-watch/skills/retrofit-watch/tests/test_auto_docs.py` | Cópia de distribuição com contratos dos dois plugins e controles do catálogo. |
| `KAIZEN_LOG.md` e `TODO.md` | Medida da fixture, limite da adoção e achados fora do escopo. |

## Boot da próxima fase

Leia `00-missao.md`, `01-plano.md` e `checkpoint.md` deste diretório. Comece pela célula R9,
que confere a identidade do diretório vazio concorrente, a retentativa depois de retirar a
regra Git exclusiva do destino e o aviso de startup mesmo com registro anterior `ok`.
Rode também `test_lean_live.StartupTest.test_offline_advance_is_in_child_and_reported_on_next_startup`
com o mesmo ambiente do Check R9. A sonda da célula reproduz a jornada em bare de fixture,
sem serviço real para iniciar. Depois repita os Checks anteriores. Não use um `TMPDIR` com
ancestral Git.
Desarme `GIT_DIR` e `GIT_WORK_TREE` do runner antes de executar testes que criam repos.
A jornada que muda para o usuário é o Stop de uma skill em repo listado, seguido de pedido, selo, revisão e porta.
Comece com `PrivateWorld` em `plugins/retrofit-watch/skills/retrofit-watch/tests/fixture_private.py` e
`test_lean_gate`. Compare o SHA do bare antes do ensaio e depois de aprovar. Emende o patch aprovado, confira
a retenção, depois compare o SHA publicado no bare, no status capturado `local/ci` e no clone em uso.
Repita com a janela cumprida, após revert e pela rota manual com e sem confirmação. Preserve a prova de
atribuição da 0.4.1 no Stop.

Para R3, use `test_lean_live`. O Check reproduz erro no setup, troca de ramo durante o fetch,
colisão de basenames e JSON inválido. Execute também `sonda-qa.py` conforme a célula do checkpoint.
O clone continua em `<live_dir>/<repo>`. O registro que alimenta o startup agora fica em
`<dados>/live/<dono>/<repo>.json`, sem migração. O aviso de um repo não substitui o de outro.

Para R4 e R5, use os Checks do checkpoint. R4 cobre caminhos diferentes com o mesmo slug.
R5 mantém a publicação no bare de fixture e captura o status após o push. A variante SSH usa
o servidor sem a porta de transporte e o controle HTTPS conserva sua porta explícita.
A camada 1 da rodada usa a base `1f1b008`. No EXEC delegado, o `HEAD` descoberto sem
`GIT_DIR` era anterior ao commit novo. Para o scanner, que desarma essa variável, confirme
primeiro o SHA descoberto pelo Git. Em um checkout comum da candidata, rode a célula sem adaptação.
Para conferir somente o scanner sobre a cópia delegada, use
`python3 scripts/anonymity-gate.py --camada1 --base 1f1b008 --repo "$GIT_DIR"`.

Para R6, confira que os destinos Git não equivalentes ficam manuais ou retidos antes do fetch.
Para R7, rode a célula do checkpoint. Ela confere o POST do status na porta HTTPS explícita,
o hostname sem porta e o controle SSH. O `gh` 2.85.0 real, com ambiente isolado, recusou o argumento
antigo e tentou conectar a `127.0.0.1:8443` com a nova chamada. O sandbox bloqueou o socket.
A jornada local verifica o status capturado, não a resposta de uma API real.

Em `04a1a77`, além do TEST_CMD, os contratos `test_auto_docs test_modo_autonomo` passaram com 44 testes.
`TMPDIR=/var/tmp python3 -m unittest discover -s plugins/retrofit-skill/tests -v` passou com 11.
`python3 scripts/validate-versions.py` e `python3 plugins/retrofit-skill/scripts/check_release_sync.py`
com cada um de `retrofit-watch` e `retrofit-skill` passaram, assim como `claude plugin validate` nos
dois diretórios de plugin (com avisos). `python3 scripts/check-private-names.py` saiu com rc 0.

Para a distribuição, em host com Bubblewrap, rode `env -u GIT_DIR -u GIT_WORK_TREE
SKILLS_SKIP_NATIVE_DISTRIBUTION=0 python3 -m unittest discover -s tests -p 'test_codex_distribution.py'`.
O executor não abriu PR, não alterou repos reais e não repontou links.

## Pendências / Decisions for a Human

- A adoção privada fica com cada dono. Inventariar e preservar estado ignorado ou não rastreado
  antes de repontar links. Medir o gate real no ambiente do dono, fora desta missão.

## Riscos e não-feitos

- A instalação exclusiva foi exercitada no Linux. A seleção das APIs de macOS e Windows
  foi verificada com dublês, sem execução nativa. O setup recusa a instalação se não houver
  operação de movimentação sem substituição.
- As três provas nativas de distribuição ficaram puladas no TEST_CMD deste sandbox.
- O avanço reconfere o checkout depois do fetch, mas essa conferência e o merge são comandos
  Git separados. O clone é dedicado e não deve ser usado como checkout de desenvolvimento.
- Registros do caminho anterior não são migrados. O próximo avanço grava no novo caminho.
- `/var/tmp` era somente leitura no EXEC, e o marcador vazio `/tmp/.git` contaminou a
  detecção nas fixtures de colheita. Sob controle que ignorou só esse marcador no processo principal,
  `TMPDIR=/tmp python3 -B -m unittest discover -s plugins/retrofit-watch/skills/retrofit-watch/tests -v`
  completou as suítes fora do Stop e atingiu o teto de 240 s já na suíte de Stop. Com os 144 testes
  do Stop verdes no TEST_CMD de cada revisão, foram cobertos 555 testes da candidata e 554 da base
  `d28e095`, com as mesmas 7 falhas e 2 erros. Os subprocessos ainda veem o marcador.
  O Check de release não precisa de Git no temporário.
- As três provas nativas passaram no host Linux em `b5512cb`, fora do sandbox de EXEC.
- A camada 1 sobre `origin/main` passou em `b5512cb`. As sinalizações sintéticas anteriores foram resolvidas com mudanças nas referências e nos testes.
- A suíte ampla no host teve a mesma falha preexistente de atribuição no teste da segunda skill full tanto na base (487 testes) quanto no candidato da QA (555 testes).

## Achados fora de escopo

- A receita de status manual da revisão r4 já consta como resolvida em `TODO.md` pelo commit `84a0b0e`.
- Aprovação pública da v1 não vinculada ao patch revisto → `TODO.md`, rulings da retrofit-watch 0.4.0.
- Segunda skill full do mesmo plugin ausente no estado, inclusive na base → `TODO.md`, recorrência I4.
- Corrida residual após a prova de ancestralidade → `TODO.md`, item sobre mover outro ramo
  após a última conferência. Não integra R5.
- kit: o EXEC recebeu as variáveis `GIT_DIR` e `GIT_WORK_TREE` da cópia privada do runner
  (`bin/sdd`, ambiente delegado do EXEC). Testes que criam repos podem operar na cópia do runner
  em vez da fixture. Em R3, a primeira execução criou commits vazios e um ref na cópia do runner.
  O ramo foi recomposto sobre o estado de entrada com a mesma árvore testada. A receita com
  as duas variáveis desarmadas passou, sem alterar o Check externo.
