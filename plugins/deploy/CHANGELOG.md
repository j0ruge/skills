# Changelog — deploy

Formato: [Semantic Versioning](https://semver.org/)

## 2026-10-06 — De comando a skill, com o detalhe medido em references — bump 2.5.1 → [3.0.0]

**O quê:** `commands/staging.md` sai e entra a skill `skills/staging/`. A invocação continua
`/deploy:staging`, e no Cursor o nome continua `deploy-staging`. O `SKILL.md` guarda o fluxo: a
introdução, os Passos 0, 1, 2, 2b, 5 e 6, a seção de produção inteira e as armadilhas, agora sob
`### Gotchas`, todos por extenso. Os Passos 0b, 3, 4 e 7 ficam resumidos, com o comando, a regra e o
momento de ler a reference. O texto completo desses quatro passos foi para `references/`, recortado
por intervalo de linhas: `runner-and-billing.md`, `local-gate.md`, `promotion-sensors.md` e
`red-runs-and-proof.md`. O Passo 4 ganhou uma tabela de leitura dos sensores (0 commits, conteúdo
só no alvo, mais de uma base de merge, backlog, workflow alterado). No `install.py`, a entrada
`deploy` passa a `source_type: "skill"`, que copia o `SKILL.md` e as references, e perde a
`cursor_description`. O teste frio da instalação mostrou que a pasta do Cursor (`deploy-staging`)
e o `name` da skill (`staging`) divergiriam, contra a spec, e a `deploy` era a única skill nessa
situação. Por isso o `_install_from_skill_dir` passa a gravar o `cursor_name` no `name` do
`SKILL.md` gerado. Nas outras skills isso não muda nada, como provado na `cicd` e nas quatro da
`skill-quality-audit`. No README, a linha da tabela de plataformas e o bloco `<details>` deixam de
descrever um comando.

**Por quê:** auditoria de 2026-10-06 pedida pelo usuário, que sugeriu a conversão. (1) A
`cursor_description` do `install.py` ainda dizia "Syncs main with develop, merges the current
feature branch into develop, and pushes", o fluxo anterior à 2.0.0, que deployava **produção**
reportando "staging". No Cursor essa frase é a superfície de gatilho, e ela contradizia o corpo.
Como skill, a description sai do próprio `SKILL.md`, e não há mais uma segunda cópia para
envelhecer. O bloco `<details>` do README repetia o mesmo texto. (2) O comando tinha 465 linhas e
24.950 chars (C1 AVISO do `audit_skill_quality.py`, medido numa cópia temporária, porque o auditor
não mede comando), e todo esse texto entrava no contexto a cada invocação.

**Prova de que nada se perdeu:** das 367 linhas não vazias do comando, 359 existem por extenso no
`SKILL.md` ou numa reference. As 8 restantes são as trocas deliberadas: a `description` (mesmo
texto, agora entre aspas), a `version`, cinco "this command" → "this skill" e `### Notes` →
`### Gotchas`. Os 8 parágrafos "Measured" continuam lá, e os blocos de código foram de 19 para 23.

**Como reverter:** `git revert` deste commit restaura o comando e a entrada `command` do
`install.py`.

## 2026-10-06 — Dupla base de merge e timeout de teste no runner que divide o host — bump 2.5.0 → [2.5.1]

**O quê:** o Step 4 ganha um parágrafo depois de "How to read the second one": `--no-merges` vazio
e `merge-tree` limpo não garantem que o GitHub aceite o merge. Um hotfix direto no branch de
produção, com merge de volta no source, pode deixar source e target com **duas** bases de merge; o
`merge-tree` resolve por base virtual e não acusa nada, e o PR de promoção sai `CONFLICTING / DIRTY`.
O sensor novo é `git merge-base --all … | wc -l`, e a saída é o mesmo merge de volta, mesmo sem nada
a reconciliar, conferindo que a árvore não mudou. O Step 7, em "Some red runs mean run it again",
ganha o timeout de teste num job de gate quando o runner self-hosted divide o host com o ambiente.

**Por quê:** promoção da 0.9.1 para produção, depois do hotfix #409 ter ido direto para `main` e
voltado à `develop` pelo #410. (1) O PR `develop → staging` saiu `CONFLICTING / DIRTY` com os dois
sensores do Step 4 limpos: a `staging` tinha a mesma árvore de um commit da `develop` e nenhum
commit próprio, e `git merge-tree` saiu com rc=0. `git merge-base --all` devolveu duas bases (o
bump da 0.9.1 e o merge da promoção anterior). Correção verificada: o merge de volta
`staging → develop` com merge commit deixou a árvore idêntica (`git diff` vazio) e a base única, e o
PR passou a `MERGEABLE`. (2) O `ci-gate-backend` do `cd-staging` caiu em duas varreduras do repo,
com 7,1 s e 6,2 s contra o timeout padrão de 5 s, num host de 4 núcleos com load ~4,5 e 43
containers; o gate local tinha passado as duas. O passo falho vinha antes do build, o ambiente
seguia na imagem anterior, e `gh run rerun --failed` passou. A mesma varredura já tinha derrubado a
1ª tentativa de um `cd-production` na véspera, o que faz dela orçamento de teste a corrigir no
projeto, e não sorte.

**Fica de fora (dívida anterior):** `commands/staging.md` segue acima de 20 mil chars (23,6 mil
antes desta versão), e a `cursor_description` do `install.py` continua descrevendo o fluxo anterior
à 2.0.0.

## 2026-10-06 — Bump antes do gate, e e2e vermelha depois do deploy não é veredito — bump 2.4.1 → [2.5.0]

**O quê:** entra o Step 2b: se o repositório exige bump de versão na promoção (script de release,
arquivo de regra, commits de release anteriores), o bump vem **antes** do gate do Step 3, porque é
ele que cria o commit promovido. O Step 7 ganha a subseção "A red e2e after the deploy is not yet a
verdict on the deploy", com três regras: falha dura é a que nenhuma tentativa passou; o conjunto
duro se compara com a última rodada na imagem anterior pelo **título** do teste, não por
`file:line`; e só o que é novo se reproduz, isolado, da máquina do operador e com `--retries=0`.

**Por quê:** promoção real da 0.9.1 (`develop → staging`). (1) A regra do repo exigia o bump antes
do PR, e a ordem do comando punha o gate antes dele, então o `local/ci` iria para um sha que não
seria promovido. Correção verificada: bump primeiro (`d4052df5`) e o status publicado nesse sha, que
o PR de promoção levou. (2) A e2e contra staging, disparada depois do deploy, saiu cancelada com 11
falhas duras. Comparadas com a rodada da imagem anterior, 8 já existiam (conta de teste com papel de
admin, rede instável do runner), e as 3 novas passaram isoladas em 4 a 6 s. A primeira comparação,
que contava todo ✘, mostrava 37 "só hoje", e a busca por `file:line` errou num spec que a própria
promoção deslocou em 24 linhas. Correção verificada: a triagem separou as três causas.

**Fica de fora (dívida anterior, para tarefa própria):** a `cursor_description` do deploy em
`install.py` ainda descreve o fluxo anterior à 2.0.0 ("Syncs main with develop … and pushes");
`commands/staging.md` já passava de 20 mil chars antes desta versão; e a linha do README parou de
registrar versões na 2.3.0.

## 2026-10-05 — Self-hosted e gate local como padrão, não como plano B — bump 2.4.0 → [2.4.1]

**O quê:** o Step 0b ganha o padrão "self-hosted, sem Actions hospedado". Um job em label hospedado
num `cd-*.yml`, ou num gate de que a promoção depende, passa a ser um achado: propor runner
self-hosted, ou deploy por script/Ansible/SSH. Nunca criar job hospedado novo. O Step 3 deixa de
apresentar o gate local como saída para "quando o CI hospedado não roda": ele é o gate oficial, e o CI
hospedado é informativo.

**Por quê:** pedido do usuário logo após a 2.4.0 ("damos preferência para self-host, sem usar
GitHub Actions"). A 2.4.0 enquadrava o gate local como plano B, o que contradizia a preferência e a
regra global do usuário sobre Actions em repositório privado.

## 2026-10-05 — Gate local sem CI hospedado e dump antes da produção — bump 2.3.0 → [2.4.0]

**O quê:** o Step 3 ganha o ramo "o CI hospedado não roda". O gate passa a ser local: espelha as
`run:` do próprio CI, registra um rc por passo, inclui a suíte de integração e publica o resultado pela
API de Statuses (`local/ci`), nunca `success` sem ter rodado. Em "Promoting to production" entra um
terceiro item: dump do banco de produção antes do merge, verificado com `pg_restore --list`, copiado
para fora do host com sha256 igual nas duas cópias e registrado no corpo do PR.

**Por quê:** numa promoção real `staging → main` (0.9.0, 132 commits, 11 migrations), os 4 jobs do
`ci.yml` do PR ficaram `queued`, sem runner, porque o repositório é privado e estava sob bloqueio de
cobrança. O Step 3 só dizia "espere o CI verde". Correção verificada: o gate local passou em 16/16 e a
integração em 279/279, os status `local/ci` e `local/integration` foram publicados no sha, e o merge veio
depois. O dump foi pedido pelo usuário no meio do fluxo. Correção verificada: `pg_dump -Fc` de 273 KB,
`pg_restore --list` com 15 tabelas, e o sha256 igual no host e na cópia externa.

## 2026-10-02 — Nada a promover não é deploy feito — bump 2.2.1 → [2.3.0]

**O quê:** o Step 4 ganha o ramo "zero commits": quando `origin/$TARGET..origin/$SOURCE` está
vazio, não se abre PR (o Step 5 não teria o que mergear); acha-se o run do `cd-*` no head atual do
alvo e vai-se direto à prova do Step 7.

**Por quê:** numa promoção real (`develop → staging`) a contagem deu `0`, porque o PR de promoção
anterior já tinha levado tudo minutos antes. O fluxo não dizia o que fazer com o zero, e o caminho
natural era um PR vazio — ou concluir "nada a fazer" sem saber se a promoção anterior subiu. Ali os
dois runs anteriores do `cd-staging` tinham falhado. Correção verificada: `origin/staging` = merge
commit do PR de promoção, run do `cd-staging` verde naquele sha, container com a imagem `sha-*`
correspondente e `Created` no mesmo instante da migration, health respondendo.

## 2026-10-01 — PR pulado pelo `paths-ignore` também chega sem gate — bump 2.2.0 → [2.2.1]

**O quê:** o Step 4 ganha um parágrafo: além do bloqueio de cobrança, um PR cujos arquivos casam
**todos** com o `paths-ignore` do CI não gera run nenhum, e "nenhum run" não é verde quando o
linter verifica esses mesmos arquivos. Antes de promover, compare `paths-ignore` com o escopo do
linter e rode o lint do repositório inteiro no `SOURCE`.

**Por quê:** numa promoção real (`develop → staging`) o deploy foi pulado porque o CI do
`cd-staging` reprovou no `prettier --check .` por causa de um único arquivo, `TODO.md`. Ele tinha
entrado por um PR que só mexia em `.md`; o `ci.yml` ignora `**/*.md` e o PR saiu sem nenhum
check, enquanto o Prettier cobre `.md`. A skill só citava o bloqueio de cobrança como origem de
conteúdo sem gate. Correção verificada no projeto: o arquivo foi para o `.prettierignore` e o CI
dos dois PRs seguintes (develop e promoção) passou nos três checks.

## 2026-09-03 — Falha transitória de registry: reexecutar, não re-promover — bump 2.1.1 → [2.2.0]

**O quê:** o Step 7 ganha a seção *"Some red runs mean run it again, not start over"*, e o Step 4
ganha como criar alvo de rollback quando o ambiente só tem tag móvel.

**Por quê:** numa promoção real o `Build & Push` falhou com `ERROR: unknown blob` ao empurrar para
o GHCR — **depois** de todas as camadas subirem (76,7 s), no fechamento do manifesto. Não havia
nada a corrigir: `gh run rerun --failed` passou verde sem uma linha de mudança. A skill só
ensinava o desfecho terminal ("say the deploy did not happen"), então o reflexo disponível era
re-promover, que gera um segundo merge commit na branch de ambiente e não conserta nada.

Três detalhes que a seção fixa, e que não são adivinháveis:

- **Qual passo falhou decide se o rerun é neutro.** Falha em build-and-push acontece antes de
  qualquer deploy; falha em smoke ou cleanup acontece *depois* de a imagem nova estar no ar, e ali
  reexecutar **redeploya**. A prova é o `docker inspect ... {{.Created}}`, não o raciocínio — foi
  assim que se confirmou que staging seguia no container antigo antes de retentar.
- **`gh run rerun --failed` reaproveita o MESMO run id.** O `gh run watch <id>` e os comandos de
  verificação continuam valendo, e o `gh run list` não mostra run novo — quem procura um id novo
  perde tempo achando que o rerun não disparou.
- **Duas falhas iguais no mesmo passo deixam de ser transitórias.** Sem esse limite, "é só
  reexecutar" vira laço.

No Step 4, a lacuna era outra: ele já mandava ter o alvo de rollback pronto, mas o pipeline
publicava só a tag móvel `:staging`, que o próprio deploy re-aponta — depois de promover não
sobra nome para a imagem anterior. A saída é marcá-la **antes** do push, e ela sobrevive ao
`docker image prune -f` do próprio deploy porque prune sem `-a` só remove imagem *dangling*.

## 2026-08-28 — Ler o `Config.Image`, e contar o backlog antes de promover — bump 2.1.0 → [2.1.1]

**O quê:** Step 7 passa a dizer como **ler** os dois campos do `docker inspect`, e o Step 4 ganha a contagem do backlog com a consequência de um CD longamente parado.

**Por quê:** o Step 7 já mandava inspecionar `{{.Created}} {{.Config.Image}}`, mas só explicava o `Created`. Medido num host real: o container servia `dsr-web:latest` — **sem prefixo de registry** — enquanto o compose declarava `ghcr.io/<org>/<img>:staging`. Ou seja, aquilo tinha sido buildado à mão no host e o pipeline **nunca** havia entregado ali; por semanas "container up + hostname 200" foi lido como pipeline funcionando. O campo já estava no comando; faltava a leitura. No Step 4, a mesma investigação mostrou por que contar o backlog importa: com o CD parado por seis semanas, o primeiro deploy verde carregaria 15 commits **e** trocaria a imagem feita à mão por uma de pipeline nunca executada naquele ambiente — duas novidades no mesmo instante, e nenhuma forma de separá-las se algo quebrar depois.

## [2.1.0] - 2026-08-28

### Adicionado (a promoção passa a checar se o pipeline-alvo vai RODAR, não só qual branch o dispara)

- **Step 0b — `runs-on` no commit promovido.** Numa sessão real, o `cd-staging.yml` de
  `develop` tinha o job `ci` em `ubuntu-latest` e o org estava com o Actions hospedado
  bloqueado por cobrança: o job **nunca iniciava** (assinatura: `failure` com zero steps,
  `runner_name` vazio, ~3 s, `log not found`; a mensagem só aparece nas annotations do
  check-run). Staging ficou dois meses sem deploy, servindo a imagem antiga, enquanto PRs
  eram mergeados — um deles com zero CI. A skill agora lê o `runs-on` do workflow **na versão
  do commit promovido** e diz, antes do push, se a promoção vai deployar ou só mergear. Se a
  própria promoção move os jobs para self-hosted, é esse push que revive o pipeline.
- **Step 3 — PR em conflito não tem run de `pull_request`.** O GitHub não cria a merge ref,
  então não enfileira o workflow; "esperar o verde" esperava para sempre e o último verde
  encontrado era de um commit antigo. Checar `mergeable` vem antes de procurar o run. E um run
  vermelho com zero steps é o bloqueio de cobrança, não teste falhando.
- **Step 4 — a dívida do alvo vira o seu gate.** Ao reconciliar com o alvo, o conteúdo que
  ele traz entra no CI da promoção inteira: 17 arquivos fora do prettier vindos de um PR
  mergeado sem gate derrubaram o `Lint`. Não é regressão sua, mas é sua para limpar — em
  commit separado, para o merge commit continuar reconciliação pura. Junto:
  `git merge-tree --write-tree --name-only` mede os conflitos antes de tocar o worktree.
- **Step 6 — `paths-ignore` em push.** Promoção só de docs não gera run no alvo, e isso é o
  comportamento esperado, não falha; promoção com código e sem run é o caso do Step 0b.
- **Step 7 — prova pelo dado.** Verde é a opinião do pipeline sobre si mesmo. Sem smoke step,
  provar no ambiente-alvo: `migrate status` no banco de destino, `docker inspect … Created`
  comparado ao horário do run, HTTP no hostname público. Um run verde com container
  `Up 5 days` não é deploy.

### Alterado

- Descrição espelhada (SKILL/`plugin.json`/`marketplace.json`) enxuta, 491 chars: ganha a
  frase sobre `runs-on` e o bloqueio de cobrança; o detalhe fica no corpo do comando.

## [2.0.0] - 2026-08-10

### Corrigido (CRÍTICO — a skill podia deployar produção achando que ia para staging)

- **A topologia de branches deixa de ser presumida e passa a ser descoberta.** A
  versão anterior afirmava que push em `develop` dispara o `cd-staging.yml` e
  mandava `git checkout main && git merge origin/develop --ff-only && git push
  origin main` para "sincronizar". Isso vale no repo onde a skill nasceu — que
  não tem branch `staging` —, mas num repo com a cadeia `develop → staging →
  main` os dois passos estão errados **e o segundo é destrutivo**: `cd-staging`
  escuta `staging`, e push em `main` dispara `cd-production`. Seguir a skill
  deployaria **produção** enquanto reportava "staging".
- Novo **Step 0 — Discover the topology**: lê o bloco `on:` de cada workflow,
  monta o mapa branch → pipeline e exige identificar qual branch é gatilho de
  **produção** antes de qualquer push. Aborta se o alvo de staging coincidir
  com ele.
- **A skill só empurra a branch-alvo.** O `git push origin main` embutido no
  fluxo de staging morreu. Produção virou promoção separada e explícita, com
  confirmação do usuário.
- Step 6 captura o run na **branch-alvo** — antes era `--branch develop` fixo,
  que num repo de topologia diferente monitora o pipeline errado (ou nenhum).

### Alterado

- **Pre-flight derivado do repo** em vez de hardcoded. `yarn test
  --watchAll=false` e `npx eslint src/` eram do stack de origem e viram no-op
  silencioso em npm/pnpm, monorepo ou outro escopo de lint. Agora detecta o
  gerenciador pelo lockfile e roda os scripts que existem no `package.json`.
  Dois gotchas documentados: script de raiz que não existe sai 0 e parece
  aprovação; e `tsc --noEmit` é **no-op** em tsconfig solution-style
  (`"files": []` + project references) — ali é `tsc -b --noEmit`.
- **Gate novo: CI verde no commit exato que está sendo promovido**, conferindo o
  `headSha` (run verde num commit anterior não prova nada sobre este).
- **Promoção por PR com merge commit, não squash.** Branch de ambiente é
  long-lived: o squash cria commit sem ancestralidade com a origem, e a
  promoção seguinte enxerga divergência sobre conteúdo idêntico.
- **Sensores antes de promover**: `git log --no-merges $TARGET..$SOURCE` (o que
  vai), o inverso (conteúdo exclusivo do alvo — vazio é o caso saudável, porque
  merges de promoções anteriores são filtrados) e `git diff --name-only --
  .github/workflows/`, que responde qual pipeline vai rodar quando a própria
  promoção altera os workflows.
- Step 7 pede para reportar **qual ambiente está servindo o código novo**, e
  para conferir que o smoke rodou em vez de ter sido pulado — pipeline verde
  que pulou a verificação não é deploy verificado.

### Motivação

Numa promoção real (`sales_quote`, cadeia `develop → staging → main`), seguir a
skill ao pé da letra teria empurrado `main` e disparado o deploy de produção no
host de produção, enquanto anunciava "staging". A skill foi descartada em favor
do fluxo correto e esta versão nasce daí.

A lição generalizável não é "a topologia certa é develop → staging → main" —
cravar isso reintroduz o mesmo defeito com outros nomes. É que **nome de branch
não carrega significado universal**, e a única fonte de verdade sobre o que um
push dispara é o `on.push.branches` do workflow. Por isso o passo de descoberta
vem antes de tudo, e por isso a skill nunca empurra uma branch que não provou
ser o gatilho do ambiente pedido.

---

## [1.4.0] - 2026-03-16

### Corrigido

- Pre-flight: `npx eslint .` corrigido para `npx eslint src/` (alinhado com CI)
- Pre-flight: `yarn vitest run src/test/` corrigido para `yarn test --watchAll=false` (projeto usa Jest, nao Vitest)

### Alterado

- Step 9 reescrito: agora captura o `run-id` do pipeline triggado pelo push
- Novo step 10: monitora o pipeline com `gh run watch <run-id>` ate completar
- Novo step 11: avalia resultado — se falhar, exibe `gh run view --log-failed`; se suceder, reporta com link
- A skill so considera o deploy concluido quando o pipeline terminar com sucesso

### Motivacao

A versao anterior apenas listava os runs recentes sem monitorar o resultado. O usuario precisava verificar manualmente se o pipeline passou. Agora o fluxo e end-to-end.

---

## [1.3.0] - 2026-03-13

### Alterado

- Plugin renomeado de `deploy-staging` para `deploy` (namespace fix)
- Command file renomeado de `deploy-staging.md` para `staging.md`
- Invocação muda de `/deploy-staging:deploy-staging` para `/deploy:staging`
- Preparado para futuros subcomandos (e.g. `/deploy:production`)

---

## [1.2.0] - 2026-03-13

### Adicionado

- Detecção automática de cenário: branch atual `develop` vs feature branch
- Fluxo simplificado quando já em `develop`: sincroniza main com `origin/develop` (ff-only), pusha commits locais e pula direto para verificação de pipeline
- Steps 6-8 preservados como fluxo completo para feature branches

### Motivação

Quando o usuário já está em `develop`, os passos de merge de feature branch são desnecessários. O fluxo simplificado evita checkouts e merges redundantes.

---

## [1.1.0] - 2026-03-13

### Adicionado

- Passo pre-flight: `eslint --max-warnings 0`, `tsc --noEmit`, `vitest run` antes do push
- Aborta o fluxo se qualquer verificação local falhar, evitando falhas no pipeline remoto

### Motivação

Deploy `23060872731` falhou por warning ESLint (`react-refresh/only-export-components`) que teria sido pego localmente.

---

## [1.0.0] - 2026-03-13

### Adicionado

- Workflow completo: verificar working tree → fetch → sincronizar main com develop → merge feature → push develop → verificar pipeline
- Sincronização automática de `main` com `origin/develop` via fast-forward
- Verificação de pipeline via `gh run list`
- Notas sobre CD staging (GHCR `:staging`, self-hosted runner)
