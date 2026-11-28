---
missao: 20261127-retrofit-watch-050
fase: EXEC
status: done
sessao: 01a2220f-19ad-7372-9904-8c9b247e321f
data: 2026-11-28 09:20
gate: "Em 0321097be5c1e3c9090238a7c4a4b4c4daa606fa, `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp GIT_CEILING_DIRECTORIES=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c '. .sdd/config.sh && eval \"$TEST_CMD\"'` → rc 0, 154 testes da loja (3 pulos nativos configurados) e 144 do Stop. Adaptadores, catálogo e versões válidos. `(env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_live.LiveTest.test_setup_keeps_pending_when_main_redirects_during_validation test_lean_live.LiveTest.test_setup_and_advance_accept_packed_main_with_empty_loose_dir test_lean_live.LiveTest.test_setup_rejects_missing_main_ref test_lean_live.LiveTest.test_advance_reports_unreadable_main_ref_separately >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py >/dev/null); echo $?` → 0, com as quatro regressões e a jornada de QA."
---

# Handoff — EXEC — Retrofit de skills locais listadas

> Escrito no fim de cada fase. A próxima fase é uma **sessão nova sem memória**: se algo que ela
> precisa saber não está aqui (ou nos artefatos linkados), está perdido.

## TL;DR

I1–I4 e R1–R17 concluídos. O setup mantém a pendência se a main deixar de ser direta,
e aceita a main empacotada válida. O avanço distingue HEAD ilegível de ref da main ilegível.
Check R17, jornada de QA, 174 regressões dirigidas e TEST_CMD verdes. Comece a QA pelo Check de R17.
A suíte ampla manteve os mesmos casos vermelhos da base no sandbox.

## Estado do repo

- **Branch:** `feat/retrofit-watch-050-loja` — base de comparação `origin/main` local.
- **Último commit de produto:** `0321097` — valida a ref da main na liberação do clone.
- **Working tree:** limpo após o commit de checkpoint, notas e handoff.
- **Suíte:** `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp GIT_CEILING_DIRECTORIES=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c '. .sdd/config.sh && eval "$TEST_CMD"'` → rc 0 em `0321097`. 154 testes da loja, 3 pulados, e 144 do Stop. Adaptadores, catálogo e versões válidos.
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

- `1ca718d` — R10 substitui a limpeza da cópia após uma recusa final por uma retentativa vinculada à origem original. O Red reproduziu a perda de um arquivo local. O Green preservou o arquivo e o diretório, recusou origem diferente e validou a mesma origem após corrigir a regra Git. Passaram 34 testes de clone e 146 regressões dirigidas.

### Rodada de revisão r5

- `fb134ce` — R11 vincula a instalação e a retomada à identidade do checkout e de `.git`. Confere a origem declarada e efetiva, a `main` e a trava de commit no worktree principal antes de remover o marcador. No POSIX, a remoção é relativa ao descritor do diretório validado. Não troca o ramo nem apaga arquivos de trabalho para completar o setup. O Red reproduziu os achados com Git real em bares locais e manteve verde a prova de R10.
  Em `fb134ce`, `PYTHONDONTWRITEBYTECODE=1 python3 scripts/anonymity-gate.py --camada1 --base origin/main --repo "$GIT_DIR"` confirmou a camada 1 limpa. A base local era `e14062c`.

### Saídas preservadas

O Red do plano sobre `6329df5` foi medido por `check-checkpoint.sh --red` antes da aprovação.

```text
  ok    checkpoint.md: I1 is red at HEAD (prints '1', wants '0')
  ok    checkpoint.md: I2 is red at HEAD (prints '1', wants '0')
  ok    checkpoint.md: I3 is red at HEAD (prints '1', wants '0')
  ok    checkpoint.md: I4 is red at HEAD (prints 'falhou', wants '0.5.0 0.12.0')
  ok    checkpoint.md: 4 pending Check(s), every one red at HEAD
```

Na sessão de EXEC de R9, o evento 66 de `EXEC-20261128-060553-1106da0e.stream.jsonl` registrou os controles e o resultado das mutações.

```text
Controle: 11 provas verdes, sem pulos.
Controle: 11 provas verdes, sem pulos.
34 mutações detectadas.
```

Na revisão r4 de `eaf78b0`, o evento 22 de `REVIEW-20261128-055449-1327db7a.stream.jsonl` registrou a jornada de QA. Os SHAs abaixo são de remotos de fixture.

```text
Ensaio verde, retenção auto-dry, bare preservado 05f7df0e9fcd
Emenda reteve o bare, nova aprovação publicou 6f219e3586d0 no bare, local/ci, registro e clone
Janela cumprida, sem approve, bare, local/ci, registro e clone em fa80c40b0f02
Revert reiniciou janela, ensaio reteve bare em c10946779f0f
```

Na sessão de EXEC de R11, o evento 111 de `EXEC-20261128-063256-e4d3042e.stream.jsonl` preserva exemplos da contraprova. A sessão verificou a contagem de 33 mutações detectadas.

```text
Não verifica invariantes no caminho definitivo → LiveTest.test_setup_retry_does_not_finalize_wrong_branch
Ignora origem efetiva na etapa final → LiveTest.test_setup_checks_effective_origin_at_the_final_path
Entrega o clone sem finalizar o marcador → LiveTest.test_setup_clones_main_with_worktree_lock
Recoloca a finalização pelo caminho tolerante que R11 removeu → LiveTest.test_setup_does_not_finalize_missing_or_replaced_destination
Grava o hook no caminho errado → LiveTest.test_setup_clones_main_with_worktree_lock
```

### Revisão r6 e correção de R12

- `39490d1` — o Red reproduziu dois casos. Após o Green, o setup preserva espaços significativos no caminho da trava e mantém o marcador se o ramo muda no mesmo checkout durante a validação da origem. A suíte de `test_lean_live` passou com 46 testes.
- Em `39490d1`, a leitura do checkpoint confirmou a saída dos 16 Checks. Passaram também 158 testes dirigidos, a jornada da QA em fixture, a regressão de Stop, o TEST_CMD, a camada 1 e os três testes de distribuição no host.

### Revisão independente e correção de R13

- A r7 reproduziu a troca de ramo durante a leitura do hook e a validação da origem no ramo anterior. Em `ea37315`, a versão de `HEAD` acompanha a identidade do clone. A liberação reconfere essa versão e preserva o marcador caso a troca ocorra durante sua remoção.
- Os três Reds reproduziram as falhas. Em `ea37315`, passaram os 49 testes do clone, 17 Checks, 161 regressões dirigidas, a jornada em fixture, a suíte e a distribuição no host.

### Revisão r8 e correção de R14

- `680d355` — o setup avalia o hook efetivo depois da consulta de ramo. A leitura de elegibilidade
  recusa a cópia fora da `main` mesmo se o marcador já foi removido durante uma tentativa recusada.
  O avanço ainda identifica o clone para diagnosticar `fora-da-main`, sem torná-lo elegível.
- Os dois Reds falharam em `a14ae29`, enquanto o controle de R13 passou. Na candidata `680d355`,
  passaram o Check de R14, os 18 Checks, 164 testes dirigidos, o TEST_CMD e a camada 1.
  As 16 sabotagens
  de comportamento foram detectadas em cópia descartável, com controle de 10 provas sem pulos,
  grupo de processos próprio, 20 s e 512 MiB por execução. Comentários, documentação e
  asserções não têm comportamento de produção para sabotar. A duplicação tardia da consulta
  de ramo também foi detectada após restaurar a trava no teste de retomada.
- No host Linux, em `66dd118`, passaram as três provas nativas de distribuição e a camada 1 de anonimização.

### Revisão r9 e correção de R15

- `4ea2ef0` — setup e elegibilidade compartilham a leitura direta de `.git/HEAD`. A validação recusa a referência indireta, conserva o marcador e permite retomar com HEAD canônico. Se o ramo mudar antes do fetch, o avanço distingue a recusa de um clone ausente, registra `fora-da-main` e preserva as refs.
- Em `e184101`, os dois testes dirigidos falharam pelos comportamentos descritos na r9, com o controle de remoção do marcador verde. Na candidata, o Check R15, 167 regressões dirigidas e os 11 testes da retrofit-skill passaram. As 19 sabotagens de comportamento foram detectadas em cópia descartável, com controle de oito provas sem pulos, grupo de processos próprio, 20 s e 512 MiB por execução.
- Depois do EXEC, as três provas nativas de distribuição e a camada 1 de anonimização passaram no host Linux em `42042d1`.
- A suíte ampla no mesmo host, com diretório temporário isolado, executou 612 testes. A única falha foi `test_second_skill_of_the_same_plugin_is_recorded`, reproduzida na base.

  Saída do host em `42042d1`, com `TMPDIR` isolado em `/var/tmp` e `GIT_DIR` e `GIT_WORK_TREE` desarmados.

  ```text
  FAIL: test_second_skill_of_the_same_plugin_is_recorded (test_auto_mode.AutoStopTest.test_second_skill_of_the_same_plugin_is_recorded)
  Ran 612 tests in 267.302s
  FAILED (failures=1)
  ```

### Revisão r10 e correção de R16

- `d0edd66` — a leitura compartilhada recusa uma main que redireciona para outro ramo, mesmo com HEAD direto. O setup conserva o marcador e retoma com uma main direta, inclusive empacotada. Antes do fetch, HEAD ilegível produz `erro` sem busca nem alteração de refs, ao passo que ramo errado continua como `fora-da-main`.
- Em `37c2274`, os dois Reds falharam pela causa esperada. Em `d0edd66`, passaram o Check R16, 169 regressões dirigidas sem pulos, a jornada de QA, o TEST_CMD e a camada 1 sobre a cópia Git do runner (`python3 scripts/anonymity-gate.py --camada1 --base origin/main --repo "$GIT_DIR"`).
- As 19 sabotagens foram detectadas em cópia descartável, com oito controles sem pulos antes e depois, grupo próprio, 20 s e 512 MiB por execução. A extração do caminho de `.git`, quando reescrita com o mesmo caminho anterior, não muda o comportamento. A leitura do arquivo errado foi detectada.
- No sandbox do EXEC, a suíte ampla rodou 614 testes na candidata, com 5 falhas e 176 erros. Em `37c2274` rodou 612, com 5 falhas e 176 erros nos mesmos casos. As fixtures de colheita sob `/tmp` encontraram o marcador `/tmp/.git`. A falha da segunda skill full ganhou a recorrência R16 no TODO.
- Depois do EXEC, as três provas nativas de distribuição e a camada 1 de anonimização passaram no host Linux em `c83293c`.
- O host Linux repetiu a suíte ampla em `e7691a4`, com os mesmos parâmetros de isolamento de R15.

  ```text
  FAIL: test_second_skill_of_the_same_plugin_is_recorded (test_auto_mode.AutoStopTest.test_second_skill_of_the_same_plugin_is_recorded)
  Ran 614 tests in 263.281s
  FAILED (failures=1)
  ```

### Revisão r11 e correção de R17

- `0321097` — a ref da main é conferida antes e após remover o marcador. Um redirecionamento
  mantém a cópia pendente, preserva os arquivos locais e permite retomar com a mesma origem.
  O setup e a elegibilidade aceitam a main empacotada mesmo com diretório vazio no caminho
  solto e recusam a ref ausente. Antes do fetch, a falha de releitura da ref produz
  `refs/heads/main do clone ilegível`, sem fetch nem alteração de refs.
- Em `2905b0c` com as regressões novas, os quatro casos da r11 ficaram vermelhos.
  Em `0321097`, o Check R17 e a jornada retornaram 0. As regressões dirigidas descritas no boot
  completaram 174 testes sem pulos. A camada 1 passou com
  `python3 -B scripts/anonymity-gate.py --camada1 --base origin/main --repo "$GIT_DIR"`.
- Trinta sabotagens foram detectadas em cópia descartável, cada execução com grupo próprio,
  teto de 20 s e 512 MiB. Os controles antes e depois completaram 12 testes em fixtures com
  SHA-1 e um teste com Git real em SHA-256, sem pulos. As notas registram a sonda que acusou
  cada alteração.
- Na suíte ampla da retrofit-watch, o sandbox registrou 614 testes na base `2905b0c` e
  619 na candidata, com as mesmas 5 falhas e 176 erros. A comparação dos casos descartou
  apenas os endereços de memória das funções exibidos pelo unittest. As duas cópias rodaram
  `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR="$dir" GIT_CEILING_DIRECTORIES=/tmp python3 -B -m unittest discover -s plugins/retrofit-watch/skills/retrofit-watch/tests -p 'test_*.py' -v`,
  com `dir` isolado em `/tmp/r17-base.QS2akf/fixtures-base` e
  `/tmp/r17-base.QS2akf/fixtures-final`, respectivamente. O marcador ancestral `/tmp/.git`
  interferiu nas fixtures de colheita. A falha da segunda skill full também ocorreu nas duas
  árvores. Ambas foram registradas no TODO, sem alteração no código de colheita ou atribuição.
- Depois do EXEC, as três provas nativas de distribuição e a camada 1 de anonimização passaram no host Linux em `7c69dd9`.
- A suíte ampla no host Linux, com um temporário isolado em `/var/tmp`, retornou esta saída em `e3814d3`.

  ```text
  FAIL: test_second_skill_of_the_same_plugin_is_recorded (test_auto_mode.AutoStopTest.test_second_skill_of_the_same_plugin_is_recorded)
  Ran 619 tests in 260.969s
  FAILED (failures=1)
  ```

## Artefatos

| Arquivo | O que contém |
|---|---|
| `docs/handoffs/20261127-retrofit-watch-050/checkpoint.md` | Vinte e um Checks e seus commits. |
| `docs/retrofit-watch/clone-dedicado.md` | Contrato de clone, selo, ensaio, publicação e avanço. |
| `plugins/retrofit-watch/skills/retrofit-watch/tests/test_auto_docs.py` | Cópia de distribuição com contratos dos dois plugins e controles do catálogo. |
| `KAIZEN_LOG.md` e `TODO.md` | Medida da fixture, limite da adoção e achados fora do escopo. |

## Boot da próxima fase

Para QA, leia `00-missao.md`, `01-plano.md` e `checkpoint.md` deste diretório. Comece pelo Check de R17. Em clone pendente da fixture, redirecione a ref da main durante a validação da trava e na remoção do marcador. O clone deve continuar pendente e retomar após corrigir a ref, com os arquivos locais intactos. Confira avanço com main empacotada e diretório solto vazio, recusa quando a main não existe e o diagnóstico `refs/heads/main do clone ilegível` sem fetch quando só a ref falha. Repita R14–R16 para conferir a trava, o ramo errado e o diagnóstico distinto `HEAD do clone ilegível`.
Para reproduzir a jornada de bare local com HOME isolado, use `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py`.
Não é preciso preparar remotos reais nem iniciar serviços. Para as regressões dirigidas, use `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests:plugins/retrofit-skill/tests python3 -B -m unittest test_fixture_private test_lean_auto test_lean_window test_lean_live test_lean_batch test_lean_gate test_auto_docs test_modo_autonomo`.

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

- A r11 pede decisão humana antes de autorizar outra rodada automática de REVIEW. O fechamento de R17 não reavalia as notas da r11.

- A adoção privada fica com cada dono. Inventariar e preservar estado ignorado ou não rastreado
  antes de repontar links. Medir o gate real no ambiente do dono, fora desta missão.

## Riscos e não-feitos

- R17 rodou no Linux com Git 2.43.0 e bares locais. Não houve execução nativa em Windows ou macOS nem adoção privada real.

- R16 foi verificado no Linux com remotos bare de fixture. A cobertura de Windows permanece nos dublês Linux.

- No sandbox da fase EXEC de R15, a suíte ampla da retrofit-watch em TMPDIR=/tmp terminou com 612 testes, 5 falhas e 176 erros. O marcador /tmp/.git interferiu nas fixtures de colheita e a segunda skill full ficou ausente. Ambos foram reproduzidos na base e184101. A falha da segunda skill ganhou a recorrência R15 no TODO.

- R14 não mediu a distribuição nativa. A execução sem os três pulos do TEST_CMD parou no Bubblewrap, antes do registro da loja, porque o sandbox não permite criar o namespace. Repita em um host que permita esse isolamento. Não houve validação em Windows nativo.
- R11 foi exercitado no Linux. No Windows, a remoção ainda usa o caminho entre duas conferências de identidade. O caminho alternativo foi testado com dublê no Linux, não em Windows nativo. Uma troca estritamente entre a última conferência e a remoção pode retirar o marcador do substituto antes de ser detectada. Há um item no TODO para a prova e a remoção ancorada no Windows. O macOS não foi exercitado nativamente nesta rodada.
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
- As três provas nativas passaram no host Linux em `1ca718d`, fora do sandbox de EXEC.
- A camada 1 sobre `origin/main` passou em `1ca718d`. As sinalizações sintéticas anteriores foram resolvidas com mudanças nas referências e nos testes.
- A suíte ampla no host teve a mesma falha preexistente de atribuição no teste da segunda skill full tanto na base (487 testes) quanto no candidato da QA (555 testes).

## Achados fora de escopo

- O temporário sob o marcador Git do sandbox e a recorrência R17 da segunda skill full estão no `TODO.md`. A rastreabilidade do resultado histórico de R15 no host segue no item editorial já citado pela r11.

- A receita que herda a localização Git do runner voltou a desviar as fixtures. O item existente em `TODO.md` ganhou a recorrência R11. A árvore de produto não foi afetada.
- A janela de remoção por caminho no Windows está em `TODO.md`, na seção do clone dedicado.
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
  Em R16, o mesmo ambiente voltou a criar commits vazios e o ref `base`. Após confirmar que a árvore
  era idêntica à de entrada, o EXEC retirou apenas esses efeitos e repetiu a suíte com as variáveis desarmadas.
