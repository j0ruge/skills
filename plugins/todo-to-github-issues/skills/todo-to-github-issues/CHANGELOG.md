# Changelog — skill `todo-to-github-issues`

Registro por sessão da skill; o changelog **versionado** é `plugins/todo-to-github-issues/CHANGELOG.md`.
Cada entrada registra **o que mudou e por quê** — a lição que a motivou, não só o diff.

## 2026-10-19 — migrar à mão, a numeração citada e espelhar da worktree

Publicado como **v2.7.0**. São três lições da migração do `TODO.md` do `magic_tutor`: 6 itens no
formato `## N. Título`, migrados e espelhados no PR #9 de lá.

- **Cada `##` era um achado.** O `--audit` deu `no open marker … (candidates: none)`, e nenhuma das
  duas saídas sugeridas servia. Não havia `##` para o `--open-heading`. Um `## Open` acima do
  primeiro achado deixaria a seção vazia, porque o próximo `##` a fecha.
  - **O que resolveu:** um rascunho não rastreado na raiz do repo. Fora dele, toda âncora falharia
    (ADR 0011 do kit). O sensor do kit deu `ok 6 finding(s) … every anchor on target`, e o
    `--anchors` deu `0 off target`. O plano com `--file` deu `create=6`. Só com o OK do humano o
    rascunho trocou o `TODO.md`, e o `--audit` deu `auto=0 manual=0`.
  - **Agora:** `references/migrar-a-mao.md` §1, roteada da tabela MANUAL.
- **A numeração antiga era citada pelo repo.** O `git grep -nE 'TODO\.md`? ?#[0-9]'` achou 18
  linhas: o `CLAUDE.md`, uma `SKILL.md`, CHANGELOGs, `docs/` e uma mensagem no código. Nenhum
  sensor lê essas citações.
  - **O que resolveu:** manter o `N.` no título. O template deixa o título livre, o sensor aceitou
    e a issue saiu "1. Ver a dica…".
  - **Agora:** a reference §2 traz as duas saídas. A outra é citar a issue, como o kit faz nos
    planos dele.
- **Espelhar da worktree depois do merge.** A sessão estava isolada numa worktree e não podia usar
  a cópia principal do repo. "Espelhe da branch padrão" travaria aí.
  - **O que resolveu:** `git merge-base --is-ancestor HEAD origin/main` deu rc 0, e
    `git diff --stat HEAD origin/main` saiu vazio. O plano deu `permalinks at ffb2c0f`, foram
    criadas 6 issues (#10–#15), e o plano seguinte deu `create=0 update=0`.
  - **Agora:** uma frase em *Erros comuns*.
- **O orçamento:** o `SKILL.md` tinha 19.948 chars, para um C1 que avisa acima de 20 mil. O
  `repetidos.py` não achou nada repetido. Por isso saiu a frase do `test_todo_format.py`, que repetia
  a linha dele na tabela *Scripts disponíveis*.
- **O alinhamento com o kit sdd** (`6366972`): a reference aponta para o template e para o
  `check-todo.sh` do `$SDD_HOME` e não copia tetos, largura nem distância de âncora.

## 2026-10-16 — a dívida da auditoria: claims com sensor, eval de gatilho

Publicado como **v2.6.2**. Reparo autorizado pelo humano, na auditoria da `skill-quality-audit`
0.7.1. O baseline tinha 0 ERRO, 0 AVISO e três INFO: B6, D1 com 22 trechos e F4.

- **F4 (sem evals).** Criado o `assets/trigger-evals.json`, com 10 casos que devem disparar e 9
  quase-acertos que não devem: issue avulsa, ticket do Jira, TODO no código, release notes,
  comentários de PR, migração do GitLab, GitHub Project, checklist e issue velha. Ele é roteado do
  `SKILL.md`, ao lado do teste offline.
- **D1 (22 trechos).** Cada trecho recebeu um veredito. Seis mudaram o texto, cinco no `SKILL.md`
  e um na reference:
  - **derivar:** `≤ 150` passou a `≤ TITLE_MAX` (`todo_format.py`), e "teto de 8 linhas" passou
    a "teto de linhas", porque o teto é do sensor do kit.
  - **datar:** o `WIDTH_CAP` de 120 ganhou "em 2026-10-16"; o 422 da vírgula ganhou "medido em
    2026-09-24, `_label_safe`"; e o 364 da reference ganhou "lighthouse_project, 2026-10-16".
  - **sem medida:** o atraso do índice de busca do GitHub virou "pode atrasar (não medido aqui)".
    Nenhum arquivo do repo registra essa medição.

  Os outros 16 ficam como estão. Treze **têm sensor**:
  - a versão: `validate-versions.py`;
  - Python ≥ 3.8: `kit.py:MIN_PY`;
  - os requisitos e o `SDD_HOME`: `kit.py`;
  - o ORPHAN no commit da remoção: `todo_issues.py:orphan_verdict`;
  - as ADRs do kit: `docs/adr/` do kit;
  - `TODO*.md` sempre backlog: `todo_issues.py:detect_format`; a unidade seção: `report.py`;
  - `UPDATE (anchor)`: `update_kind`;
  - os marcos 2.2.0, 2.3.x e 2.5.0: cada um tem a sua seção no CHANGELOG versionado.

  Os outros três são **instrução, não fato**: "um grupo por vez", "~6 linhas" e "nunca o primeiro
  comando".
- **B6.** O `scripts/__pycache__` foi para a lixeira com `gio trash`. O git o ignora
  (`.gitignore:1`), então ele nunca chegou ao repo, e cada execução dos scripts o recria.
- **Tamanho.** O `SKILL.md` passou de 19 757 para 19 948 caracteres (`wc -m`), abaixo do AVISO
  do C1, que dispara acima de 20 000.
- **Como reverter:** `git revert` do commit desta versão. O eval set é arquivo novo e sai junto.

## 2026-10-16 — o canário não é uma issue só

Publicado como **v2.6.1**.

- Espelho do kit sdd depois do lote 9: o plano dava `create=5 update=1`, e o canário
  `--apply --limit 1` respondeu `created …/277` **e** `updated #271`. O `--apply` faz
  `todo = plan.create[: a.limit]` e logo depois percorre o `plan.update` inteiro, sem corte. O
  `--help` do `--limit` dizia isso certo ("at most N creations"), mas o passo 2 do `SKILL.md` e a
  docstring do script, que é a descrição do `--help`, diziam "uma issue" e "one issue". Aqui não
  houve dano, porque o `UPDATE (text)` do #271 foi conferido no `--dump` antes. Com dezenas de
  `UPDATE (anchor)` depois de um PR que desloca linhas, um renderizador quebrado estragaria todas
  no mesmo canário que existe para pegá-lo numa issue só.
- Corrigido o texto, não o comportamento. O bullet do `--link` no canário foi fundido no novo
  "Contar com o canário para uma issue só", que cobre os dois modos.

## 2026-10-16 — o item aberto já resolvido, e o que conferir numa migração

Publicado como **v2.6.0**.

- Primeiro espelho do `TODO.md` do `lighthouse_project`: o plano parou em rc 4 com 139 violações. O
  `--fix --write` levou a 55, e os 57 `MANUAL` foram conferidos contra o código por quatro
  subagentes só de leitura, antes de uma aprovação única do humano. Dez itens abertos tinham
  `RESOLVED by` com o commit já em `develop`. O `--fix` só apagava `[x]`, e esses passavam no
  sensor e liam `SKIP` no plano. Três ficaram até a pré-visualização do plano depois da migração
  (`skip=4`, um deles legítimo, por não mergeado). Daí a regra `resolved_open`.
- Conferir o `--write` mostrou três armadilhas que nenhum gate da skill vê, agora em
  `references/conferir-o-fix.md`:
  - o recorte da seção aberta casando o marcador citado no preâmbulo;
  - a contingência de um item apagado (o `a7755bc` e a decisão 6);
  - o `docs.test.ts` do repositório, cego depois que `## Resolved` saiu. Ele foi reescrito sobre os
    marcadores e visto vermelho em três sabotagens.

## 2026-10-15 — a âncora sem alvo que era achado fechado

Publicado como **v2.5.2**.

- Primeiro espelho do `TODO.md` do `digital_service_report_api`: o plano parou em rc 4 com 8 âncoras
  fora da ADR 0015 §2, e o `--audit` deu `manual=8`. Ao procurar o alvo da âncora
  `.github/workflows/ci.yml` do item "`tsc --noEmit` como step do CI", o `grep` achou o job
  `typecheck` já no arquivo, e `git log -S"typecheck:"` apontou o commit que o trouxe.
- A célula `MANUAL` mandava só reancorar. Seguida à risca, ela daria âncora nova a um achado
  fechado, e o `--apply` abriria a issue dele: o `SKIP` só reconhece `RESOLVED by <hash>`, que o
  item nunca recebeu. O item saiu do arquivo citando o commit; os outros 7 foram reancorados, o
  sensor aceitou 17 achados e o plano final deu `create=0 update=0 ok=17`.

## 2026-10-15 — o símbolo longe da âncora

Publicado como **v2.5.1**.

- Na sincronização do kit sdd depois dos merges dos PRs #252 e #246, o canário (#255) saiu com a
  âncora num parágrafo e `(`preflight-test`) — …` abrindo o seguinte; a #249 já saía igual. O
  espelho continuava fiel ao `TODO.md`, mas o leitor via um parêntese solto longe do arquivo que ele
  designa.
- O conserto mudava o corpo, e o corpo é o que o `update_kind` compara: a issue antiga leria
  `UPDATE (text)` no próximo deslocamento de linha. Por isso ele aprendeu o layout antigo junto.
- Lição de método: mudar o renderizador de um espelho é mudar o lado vivo de uma comparação. Antes de
  mexer no formato, meça o que o comparador diz sobre os corpos já publicados. O hash não precisou,
  porque nunca leu o corpo.

## 2026-10-13 — a órfã que ainda vive num PR

Publicado como **v2.5.0**.

- Ao registrar um achado no `TODO.md` do kit sdd (PR #250), o plano rodado da branch mostrou
  `ORPHAN #249  removal not found in history · last text unknown — read it before closing`. A #249 é
  o espelho do item do PR #248, ainda aberto: criada por `--apply` na branch dele, 45 s depois de o PR
  abrir. A tabela do plano só oferecia `completed` ou `not planned`, e fechar teria perdido um achado vivo.
- O conserto procura a chave da órfã sem remoção nas cabeças dos PRs abertos e imprime `PENDING`;
  o `--close-orphans` nunca a fecha. Ver o changelog versionado para as medidas.
- Lição de método: uma linha do plano que manda o humano escolher entre duas saídas precisa listar
  também a terceira, "não é com você agora", quando ela existe. "Desconhecido não é ausente" já valia
  para o histórico; valia também para os PRs.

## 2026-10-09 — o espelho parado pelo formato

Publicado como **v2.4.1**.

- Faxina das issues do sales_quote: o `--audit` deu `summary auto=1 manual=206` (175 âncoras sem
  símbolo — o arquivo é anterior à ADR 0015 §2 do kit), e o plano recusa até a migração. O espelho
  estava sem sincronizar desde 2026-09-24, com 8 órfãs abertas.
- Fechadas à mão: `git log --format='%h %ad %s' --date=short -S"<começo do título>" -- TODO.md` deu o
  commit de remoção de 7 delas, e `gh issue close N --reason completed --comment` citou cada um. A 8ª
  (#350) ficou aberta: o commit que a removeu não prova o conserto. Os 10 itens consertados que ainda estavam no arquivo saíram por PR
  (sales_quote #419), com o doc da `Fonte:`, que o contrato de `docs/achados/` daquele repo exige.
- Fora deste retrofit, sem correção verificada: o `--fix` só apaga `[x]` com `merge-base --is-ancestor`,
  que nunca vale num repo de squash merge (PRs #405 e #406 do sales_quote). Registrado no `TODO.md` do kit.

## 2026-10-09 — o backlog que esvaziou de verdade

Publicado como **v2.4.0**.

- Re-sync do kit sdd depois do lote 6 (chore #245, `4f16a6d`): a seção aberta ficou vazia, e o plano
  recusou com rc 2. As 4 órfãs foram fechadas à mão, com o texto que o `--close-orphans` escreveria,
  depois do `--is-ancestor` dos consertos e da remoção.
- Investigado antes de mexer: a recusa vem depois do `sensor_gate`, e o marcador fora do lugar já é
  recusado pelo sensor (testado num repo descartável). Remover a guarda tiraria a última trava humana
  antes de um fechamento em massa; a saída virou `--allow-empty`. Provado no próprio kit: sem a flag,
  rc 2 nomeando a saída; com ela, `create=0 update=0 orphans=0`.
- O `TODO.md` do kit não serve mais de entrada do `test_todo_issues.py` (0 itens, abaixo do piso de 5):
  use o do sales_quote.

## 2026-10-07 — o piso de 5 itens que o teste exigia calado

Publicado como **v2.3.3**.

- Retro da mesma sessão da v2.3.2: rodado contra o `TODO.md` do kit (4 itens depois do chore
  pós-merge), o `test_todo_issues.py` deu `FAIL parsed 4 items (>= 5)` e rc 1, idêntico sem as
  mudanças da v2.3.2. A docstring do teste pedia 5+ itens; o `SKILL.md`, que é o que se lê antes de
  rodar, não.
- Investigado antes de mexer: o piso protege contra vacuidade. `items[:-4]` com 4 itens é lista
  vazia, e o caso das órfãs passaria sem item mantido. Baixar o piso seria trocar um vermelho
  explicado por um verde que não mede. Mudou só onde o mínimo é dito: o `SKILL.md` e a mensagem do
  caso. Com o `TODO.md` do sales_quote (223 itens), 73 de 73.

## 2026-10-07 — a regra de âncora que a skill ainda ensinava, e o espelho feito da branch

Publicado como **v2.3.2**.

- Chore pós-merge do lote 5 do kit sdd. A linha 124 do `SKILL.md` descrevia a regra de âncora da
  ADR 0011 (qualquer símbolo entre crases perto da linha), e o kit mede outra desde a ADR 0015 §2: o
  símbolo designado `` `arq:N` (`símbolo`) `` logo depois da âncora. A defasagem não era só de
  prosa: o `test_todo_format.py` estava vermelho em 5 casos, todos "o sensor do kit aceita o
  fixture". Sondado direto no sensor: a forma antiga dá `designates no symbol`, a nova passa. Com
  os fixtures corrigidos, 39 `ok` (antes 34). É a mesma classe da v2.0.1: a skill não carrega o
  sensor, mas os testes e a tabela dela descrevem a regra, e a regra andou.
- Mudar só a #240 antes do merge: rodado na branch, o plano queria 15 `UPDATE`, 14 deles com o
  texto da branch (`RESOLVED by` ainda não mergeado). O script não filtra por issue. Saída: corpo do
  `--dump`, `gh issue edit`, e o plano pós-merge leu a #240 como em dia.
- O re-sync pós-merge trouxe a #239 e a #236 como `UPDATE (text)` com só a âncora mudada. Causa no
  `update_kind`: ele tira o alvo do link e deixa os colchetes, e os corpos dessas issues tinham sido
  escritos à mão com a âncora sem link. Lição de uso, não de código: editar partindo do `--dump`.
- Visto e não consertado: o `fixed by` cita só o primeiro hash de `RESOLVED by A e B` (#227).

## 2026-10-04 — a órfã consertada que quase saiu como "not planned"

Publicado como **v2.3.1**.

- Re-sync do `TODO.md` do kit depois do lote 3 (PRs #219 e #220): 35 órfãs, 12 com `fixed by`.
  Quatro saíram como `removal not found`, e o `--close-orphans` sugeriu `--reason "not planned"` para
  todas. Uma delas, a #113, estava consertada (`RESOLVED by 0521972`); fechei como `completed` à mão
  porque sabia do conserto, não porque a ferramenta disse.
- Causa, provada com o histórico: o título da #113 tem `` `^  ok    ` ``, o parser normaliza para
  `` `^ ok ` ``, e o `git log -S` com esse trecho acha 0 ocorrência no arquivo. As outras três
  (#143, #154, #158) foram movidas para a seção decidida com o mesmo título, e a contagem 1/1 esconde
  o commit do `-S`.
- Protótipo antes do código: percorrer os commits do arquivo com o teste da chave achou as quatro e
  concordou com o `-S` onde ele já achava. Teste vermelho escrito antes do conserto (título com
  espaços repetidos), sabotagem nos dois sentidos depois.

## 2026-10-02 — a órfã que fechava sem dizer quem a consertou

Publicado como **v2.3.0**.

- Re-sync do `TODO.md` do kit depois dos PRs #196/#197: o plano deu 8 `ORPHAN`, todas de itens
  consertados (`RESOLVED by` no último texto). O `--close-orphans` as fecharia com "O item saiu de
  `TODO.md` em `<HEAD>`" — sem o conserto. Fechei as 8 à mão para citar cada hash; a memória já
  registrava o mesmo trabalho manual com 14 órfãs em 2026-09-25, e o caso inverso (4 órfãs por
  decisão que o `--close-orphans` chamaria de concluídas) em 2026-10-01.
- O script tinha o dado: o commit que removeu o item guarda o texto dele no pai. `last_text()` o lê
  e o plano passa a dizer `fixed by <hash>` ou `no RESOLVED by`; o `--close-orphans` fecha só o que
  foi consertado. Protótipo antes do código: 13/13 casos conhecidos em 1,3 s.
- A sabotagem achou uma regra sem probe (casar pelo título em vez da chave): ganhou o mundo dos
  títulos gêmeos antes do commit.

## 2026-10-01 — a receita de prova que mentia

Publicado como **v2.2.0**.

- O humano pediu para sincronizar o `TODO.md` do kit depois da varredura D15. O plano deu 24
  `UPDATE` e 4 `ORPHAN`. A prova "é só número" pela receita da skill acusou as 24; descontada a
  linha `# título` do `--dump`, sobrou uma (#156) — prova feita à mão, por tentativa. Medida depois
  num espelho já sincronizado, a receita tinha quatro camadas de falso positivo (86 → 59 → 59 → 16
  de 86). A prova saiu da skill e entrou no script: `UPDATE (anchor)` / `UPDATE (text)`.
- As 4 órfãs tinham saído por decisão (`7ee1c3e`), não por conserto. O `--close-orphans` as
  fecharia como concluídas, com o texto "achado fechado". Foram fechadas à mão como `not planned`, cada uma
  com o destino. A tabela passou a dizer isso.
- A sabotagem achou dois probes cegos na primeira versão: o teste roda sem sha (o permalink não
  mudava) e o número "trocado" era acrescentado, não trocado. Os dois foram reescritos e agora mordem.

## 2026-09-26 — a largura que a skill guardava sozinha

Publicado como **v2.0.2**.

- O humano pediu para mergear um PR do kit com o `TODO.md` "em harmonia com a skill". O sensor do
  kit dizia limpo; o `--audit` dizia 42 linhas longas e 6 itens acima do teto. O mesmo `--audit`
  sobre a `main` do kit dava o mesmo — não era o PR. Era a skill: `WRAP = 100` no `todo_format.py`,
  contra `WIDTH_CAP=120` no `check-todo.sh`. Os 100 são mais velhos que a regra do kit; quando o
  kit ganhou a regra, a cópia virou segunda opinião, e o teste da skill (`len(p) <= f.WRAP`)
  concordava consigo mesmo. A skill jurava não carregar cópia do formato e carregava um número.
- A largura passa a ser lida do sensor a cada execução; kit sem ela é recusado, nunca adivinhado.
  Medido: o `--audit` do `TODO.md` do kit foi de `auto=1 manual=6` para `auto=0 manual=0`.
- A sabotagem achou um probe cego: "o nome num comentário não é declaração" passava com a regex
  sem âncora, porque a fixture tinha texto depois do número e nenhuma das duas formas casava.
  Fixture sem esse texto, e o probe morde.
- De carona, um vermelho antigo do `test_todo_issues.py` (`body edit -> 1 update`): a sonda
  editava pela última linha do item, e atribuição se repete. Vermelho pelo motivo errado — o
  espelho estava certo; agora a sonda edita o bloco, que é único.
- Lição de uso, não de código: depois de um PR que desloca linhas de um arquivo ancorado, o plano
  traz `UPDATE` em massa (14 no #170 do kit), e todos eram número de âncora. Normalizar os dígitos
  do `--dump` contra o corpo vivo provou isso antes do `--apply`.

## 2026-09-26 — a regra de âncora do kit, e a cópia que morava fora do repo

Publicado como **v2.0.1**.

- O `test_todo_format.py` tinha 5 casos vermelhos. A hipótese do usuário — "o kit está mudando
  neste momento" — estava certa na causa e errada no tempo: a mudança (ADR 0011, `fb6fb78` +
  `2cf432d`) já estava na `main` do kit, e o `check-todo.sh` do checkout era idêntico ao da
  `origin/main`. Não era trabalho em voo; era a skill defasada.
- O defeito não era só de fixture. `sensor_violations` escrevia o texto em `/tmp`, e a âncora passou
  a ser resolvida contra o repositório do arquivo checado — toda âncora de um `TODO.md` real virava
  "names no file". Sensor que mede uma cópia em outro lugar mede outro arquivo.
- A regra, medida: arquivo **não rastreado** serve (o sensor olha o disco, não o índice); a âncora
  precisa ter forma de caminho (`a:1` não é lida como âncora); e um span entre crases da cabeça do
  item precisa ocorrer no arquivo até 10 linhas da linha ancorada.
