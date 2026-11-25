# retrofit-watch: modo autônomo nas skills locais — desenho

**Data:** 2026-11-25 · **Base:** `ba3da3c` · **Plugins:** `retrofit-watch` 0.4.0, `retrofit-skill` 0.11.0
· **Estende:** `docs/superpowers/specs/2026-11-23-retrofit-watch-modo-autonomo-design.md` (aqui, "a spec da
v1") · **Antecipa:** a v3 daquela spec (lean), antes da v2 (o kit), na ordem que o dono deu em 2026-11-25

## 1. Por quê

O dono quer que toda skill dele melhore no modo autônomo, onde quer que ela more. A v1 cobre só a skill
da loja (modo full). Uma skill local versionada num repo privado de bibliotecas da empresa, aqui `<repo>`,
só recebe a retro manual hoje, pelo motivo `kit-ou-lean` do `why_manual` (`scripts/rw_auto.py`).

E a cópia em uso dessa skill segue o ramo em que o checkout de desenvolvimento estiver. Medido em
2026-11-25: o link da skill apontava para o checkout de `<repo>`, que estava num ramo com um commit sem
push e sem PR, havia um dia. Uma correção publicada na `main` não chegaria a quem usa a skill.

Este desenho leva as skills locais de uma lista explícita de repos ao fluxo autônomo, com publicação direta
na `main` do repo. A cópia em uso passa a vir de um clone que só segue a `main`.

## 2. Objetivos, não objetivos e anti-objetivos

**Objetivos**

1. Uma lista `lean_auto` na config. A skill local de um repo da lista passa pelo mesmo fluxo da v1: o hook,
   a retro, o revisor, a triagem, o executor e a porta.
2. A publicação vai direto à `main` do repo, pelo gate do próprio repo (o pre-push), e o sha publicado
   ganha o status `local/ci`.
3. A cópia em uso vem de um clone dedicado por repo, que só segue o `origin/main`. A porta e o fluxo
   manual o avançam.
4. **O ensaio antes do push sozinho.** Enquanto a loja não cumprir o critério da v2 da spec da v1 (§5.9:
   10 retrofits autônomos publicados e 14 dias, sem revertido e sem nome vazado), todo repo da lista roda
   como `auto-dry`. O lote para num ramo pronto, e o dono o libera com o `approve`. Com o critério
   cumprido, o push é sozinho, e o aviso de startup diz que isso mudou.
5. O retrofit manual de uma skill de repo da lista também vai por worktree e push na `main`. Ninguém
   commita no clone dedicado.

**Não objetivos**

- O kit (`sdd`): continua manual. A ordem do dono agora põe as skills locais antes dele.
- Skill local de repo fora da lista: continua manual, como hoje.
- As skills do Hermes: são a frente seguinte, com desenho e loja próprios.
- Kits de terceiros copiados para repos do dono: nunca entram, e a lista é o que os protege.
- O código dos pacotes do repo: o escopo é só a pasta da skill.
- Tirar da história pública do git da loja os nomes que a limpeza de 2026-11-25 (`e6eda29`) tirou da
  árvore. Isso pede reescrever a história, e não foi decidido.

**Anti-objetivos** (falha mesmo que funcione)

- Um push autônomo na `main` de um repo de produto, onde a `main` faz deploy.
- Um commit no clone dedicado, ou a cópia em uso num ramo que não é a `main`.
- Um push com `--no-verify`, ou que pule o gate do repo.
- Um push sem supervisão antes do critério do objetivo 4.
- O fluxo escrever no checkout de desenvolvimento do repo ou na árvore de trabalho da sessão.
- Uma lição de uma skill aplicada na skill de outro repo.

## 3. Restrições (medidas em 2026-11-25)

- **O pre-push do `<repo>`** (`.githooks/pre-push`) roda o `npm run gate`: 10 passos, entre eles o pacote
  empacotado e instalado num consumidor vazio em Node 22 e em Node 24, este num container. Ele recusa o
  push cujo sha não é o HEAD e o push com a árvore suja. É ligado pelo `core.hooksPath .githooks`, que o
  `npm ci` grava, e a config vale para todos os worktrees do clone. Por isso o gate precisa de
  `node_modules` no worktree do lote. Um push real do `fc95fca` saiu com `gate: 0 passo(s) reprovado(s)`.
- **A convenção do repo é PR com o status `local/ci`.** O dono escolheu o push direto na `main`
  (2026-11-25). O status fica: ele é a evidência de que o gate rodou naquele sha.
- **A release do repo é uma tag manual e irreversível**, feita pelo dono. O push na `main` não publica
  pacote. O fluxo nunca cria tag.
- **O gate do `<repo>` também lê as skills do Hermes** (`$HERMES_HOME/skills`), na varredura de escrita
  crua. Um arquivo de lá pode reprovar um lote daqui por um motivo fora do diff dele.
- **A cadeia dos links hoje:** `~/.claude/skills/<s>` → `~/.agents/skills/<s>` → `<checkout>/.claude/skills/<s>`.
  O Hermes tem um link relativo para o mesmo checkout. A classificação do hook é pelo `realpath`, e o
  `deny_roots` padrão é `~/.agents` e `~/.hermes`: o clone dedicado tem de ficar fora dos dois.
- **A skill local tem `CHANGELOG.md` na própria pasta e não tem `metadata.version`** (medido na skill do KB).
  O modo enxuto do `retrofit-skill` já registra a lição nesse CHANGELOG e não faz bump.
- **Coautoria:** dos últimos 8 commits do `<repo>`, só um commit de docs tem o trailer `Co-Authored-By`, e
  nenhum retrofit tem. O commit autônomo segue a regra da loja: sem o trailer.
- **18 repos do dono têm skill local versionada.** Dois são produtos cuja `main` faz deploy, e vários trazem
  kits de terceiros copiados.
- **As de sempre** (spec da v1, §3): o hook tem 10 s e só biblioteca padrão; quem despacha os subagentes
  é o agente da sessão; a porta tem `RUN_TIMEOUT` de 900 s. O tempo do gate do `<repo>` não foi medido.

## 4. Caminhos considerados

| Decisão | Caminhos | Escolhido |
|---|---|---|
| Onde publica | (a) um PR que espera o dono; (b) direto na `main`, pelo pre-push | (b), pelo dono: o PR tiraria a pergunta e deixaria o merge |
| A cópia em uso | (A) o checkout de desenvolvimento, com `pull --ff-only` quando ele está na `main` e limpo; (B) um clone dedicado que só segue a `main` | (B), pelo dono: com (A), a porta seguraria sempre que o dono trabalhasse num ramo, como no caso medido |
| A supervisão antes do critério | (A) desenhar agora e construir depois do critério; (B) construir agora, com o repo em `auto-dry` até o critério; (C) push sozinho já | (B), pelo dono: o fluxo vale já, e o push sem supervisão só vem com medida |
| O alcance | uma lista explícita; ou todo repo com skill local, menos uma lista de produtos | a lista explícita, minha: com a lista de exclusão, um repo de produto novo nasceria autônomo |

## 5. O desenho

### 5.1 Configuração

No `~/.claude/retrofit-watch.json`, ao lado das chaves da v1:

| Chave | Valor | Padrão |
|---|---|---|
| `lean_auto` | repos cujas skills locais podem ir ao modo autônomo, pelo `dono/repo` do `origin` | `[]` |
| `live_dir` | onde ficam os clones dedicados, um por repo da lista, em `<live_dir>/<repo>` | `~/.local/share/skills-live` |

A entrada é o `dono/repo` do `origin`, e não um caminho, porque a mesma skill aparece no checkout de
desenvolvimento, no clone dedicado e nos worktrees, e o `origin` é o mesmo nos três. A classificação de
hoje já lê o `origin` para saber se o repo é do dono.

**O modo efetivo de um repo da lista:**

| `mode` | o critério da v2 (o `criterion` de `rw_store.py`) | modo efetivo |
|---|---|---|
| `manual` | qualquer | `manual` |
| `auto-dry` | qualquer | `auto-dry` |
| `auto` | não cumprido | `auto-dry` |
| `auto` | cumprido | `auto` |

O `criterion` já existe e é lido do `origin/main` local da loja, com cache em `<dados>/criterio.json`
(medido em 2026-11-25: zero commits contados).

**O critério é medido sempre, numa janela que recomeça** (o dono, 2026-11-25). Um revert de um commit
autônomo, na loja ou num repo da lista, põe os repos da lista de volta em `auto-dry`. Eles voltam ao `auto`
com 10 retrofits autônomos publicados e 14 dias sem revert nem nome vazado, contados desde o último revert.
O `criterion` da v1 conta a história inteira com zero revertidos, e por isso nunca voltaria a se cumprir
depois de um revert: o modo efetivo precisa de uma variante que conte a partir do último revert. O aviso
de startup diz as duas mudanças, de `auto-dry` para `auto` e a volta.

### 5.2 O clone dedicado

- **Criação:** um verbo do script, que clona o `origin` em `<live_dir>/<repo>` e fica na `main`. Ele
  recusa rodar quando `<live_dir>/<repo>` já existe: nunca recria nem apaga um clone.
- **A trava de commit é por worktree.** O `core.hooksPath` da config comum vale para todos os worktrees do
  clone, e o `npm ci` de um lote o reescreve para `.githooks`. Por isso o clone liga o
  `extensions.worktreeConfig`, e a trava vai só no worktree principal (`git config --worktree
  core.hooksPath <pasta com um pre-commit que recusa>`). Os worktrees dos lotes herdam a config comum, e o
  pre-push do repo vale neles. O clone principal não roda `npm ci`: as skills não precisam do
  `node_modules`.
- **Estado da skill fora da pasta dela** (o dono, 2026-11-25). Uma skill que grava dado próprio dentro da
  própria pasta perderia esse dado na troca dos links. Medido: a skill do KB grava os snapshots de rollback
  da produção do KB em `memory/snapshots/`, pelo `__file__` resolvido. São 149 arquivos, 3,4 MB, de 25/09
  a 23/11, ignorados pelo git e só no checkout de desenvolvimento.
  - Antes da migração dos links, um retrofit dessa skill, com teste, passa o estado para um lugar estável
    fora de qualquer checkout: o padrão sob `$XDG_STATE_HOME`, com uma variável de ambiente para trocar.
  - A migração move os arquivos existentes e confere a contagem e o sha256 de cada um. Ela nunca apaga a
    origem antes de conferir.
  - Para toda skill de um repo da lista, a migração lê antes o `git status --porcelain --ignored` da pasta
    dela. Ela para quando acha um arquivo ignorado ou não rastreado sem destino decidido.
- **Quem o avança:** a porta, depois do push; o fluxo manual, depois do push; e o startup, com um
  processo destacado que faz `fetch` e `merge --ff-only origin/main` e não segura o hook. O resultado sai
  no aviso do startup seguinte. Sem esse terceiro caminho, um PR mergeado pelo dono no GitHub nunca
  chegaria à cópia em uso.
- **Antes de avançar,** confere que o clone está na `main` e com a árvore limpa. Senão, não mexe, e o
  aviso de startup diz "cópia em uso fora da main".
- **A migração dos links é um gesto único, com o OK do dono:** repontar `~/.agents/skills/<s>` de cada
  skill do repo e o link do Hermes para o clone, e provar pelo `realpath` e pela linha
  `Base directory for this skill:` numa sessão. O checkout de desenvolvimento fica onde está.

### 5.3 O fluxo

É o da spec da v1, §5.1, com estas diferenças:

1. **O hook.** No `why_manual`, a entrada lean cujo `origin` está na `lean_auto` deixa de sair por
   `kit-ou-lean` e segue as outras guardas: `lista-manual`, `permissao`, `entrypoint` e `teto`. O
   `sem-loja` vira, para ela, `sem-clone`: falta o clone dedicado, ou ele não é um clone daquele `origin`.
   O kit e a skill lean fora da lista continuam em `kit-ou-lean`.
2. **O pedido** (`pedido.json`) leva o `dono/repo` e o modo efetivo de cada skill.
3. **O revisor, na primeira passada,** lê a skill no `origin/main` do repo, buscado no clone dedicado.
4. **A triagem:** um lote por skill, porque a skill local não tem plugin nem versão.
5. **O `prepare`** cria o worktree do lote a partir do clone dedicado (o objeto e o ramo moram no `.git`
   dele; a árvore dele não muda) e nunca a partir do checkout de desenvolvimento.
6. **O executor** roda o `/retrofit-skill <skill> --auto <dir do lote>` no modo enxuto: edita só a pasta da
   skill, escreve a entrada no `CHANGELOG.md` dela, não faz bump, commita com a marca
   `Retrofit-Mode: autonomous` e sem coautoria, e termina no `seal`.
7. **O revisor, na segunda passada,** responde só as duas perguntas do diff (regra repetida, diff além das
   lições). Não há julgamento de termos: o repo é privado, e o nome da empresa é legítimo lá.
8. **A porta**, na seção 5.4.

### 5.4 A porta do repo privado

| | Guardas |
|---|---|
| **Mantém**, como na v1 | o worktree e o ramo do lote; a árvore limpa; o `fetch` e o rebase; um commit só, e os arquivos só na pasta da skill; o arquivo opaco e o `.gitattributes`; sem coautoria; a marca autônoma; o veredito; a lição dentro do pedido; a lição publicável; a mudança da `description`; as duas perguntas do diff; o gate da `skill-quality-audit` e as fases dele; o teto; o HEAD que mudou; o `auto-dry` (o modo efetivo da seção 5.1) |
| **Mantém, da camada 1,** | só o segredo e o caminho com nome de usuário. Num repo privado o caminho não vaza nada, mas prende a skill a uma máquina |
| **Tira** | o nome, o e-mail e o termo público da camada 1; o `anonimato.json`; o `validate-versions.py` e a instalação pelo marketplace, que são da loja |
| **Troca** | o `sem-bump` vira `sem-changelog`: o `CHANGELOG.md` da skill ganhou uma entrada com a data do commit |
| **Acrescenta** | `gate`: o `npm ci` no worktree e o push `HEAD:main`, que passa pelo pre-push. O push recusado segura o lote com o resumo final do gate. Nunca com `--no-verify` |

**Os achados da camada 1 no repo privado.** O `segredo` nunca se aprova, como na v1: ele sai pelo
executor ou pelo retrofit manual. O `caminho` com usuário entra nos motivos que o `approve` substitui,
porque num repo privado ele não vaza nada, só prende a skill a uma máquina.

**O ensaio vê o mesmo gate que o push.** No modo efetivo `auto-dry`, a porta roda o `npm ci` e o
`npm run gate` no worktree, sem push, antes de segurar o lote, e grava o resumo do gate na linha. O dono
aprova um ramo que o gate já viu. O `approve` fica preso ao `patch_id` do lote (`rw_store.py`): um patch
que mudou depois da aprovação a anula, e o lote volta a pedir a palavra do dono. No push, o pre-push roda
o gate de novo.

Passando tudo:
1. o push;
2. o status `local/ci` como `success` no sha, com a linha final do gate na descrição;
3. a linha `publicado` no registro;
4. o `merge --ff-only` no clone dedicado;
5. a marca no estado da sessão.

A falha no clone fica num campo da linha, como a falha de instalação da v1: o commit já está na `main`.

### 5.5 O retrofit manual

No modo enxuto, quando o `origin` da skill está na `lean_auto`, o `/retrofit-skill` faz o mesmo caminho:
worktree a partir do clone dedicado, a edição e o CHANGELOG, o "sim" do dono (que o modo manual já pede),
o push `HEAD:main` pelo pre-push, o `local/ci` e o avanço do clone. O `pre-commit` do clone é a trava de
quem tentar commitar nele.

### 5.6 O registro e o aviso de startup

- As linhas do `autonomo.jsonl` ganham o `dono/repo`. O verbo `segurados` lista os lotes dos dois tipos,
  com o repo.
- **O que vale como medida:** as publicações nos repos privados não contam no critério da loja. Os
  reverts nesses repos aparecem no aviso de startup, à parte.
- O aviso de startup ganha:
  - o clone dedicado atrás do `origin/main`, ou fora da `main`;
  - a falha do último avanço destacado;
  - a mudança do modo efetivo, de `auto-dry` para `auto`, quando o critério se cumpre.

## 6. Decisões do dono (25/11)

- Toda skill dele no modo autônomo, nesta ordem: a loja, o repo privado de bibliotecas e o Hermes, que
  depois ganha uma loja própria.
- Nos repos privados, o push vai direto na `main`.
- A cópia em uso vem de um clone dedicado que só segue a `main`.
- A construção é agora, com os repos da lista em `auto-dry` até o critério da v2 se cumprir.
- O commit que estava fora da `main` foi para ela antes da troca dos links (`fc95fca`, gate verde, status
  `local/ci` publicado).

Depois da revisão do desenho (25/11):

- O estado que a skill grava sai da pasta dela, por um retrofit com teste, antes da troca dos links. A
  migração move e confere, e nunca apaga antes (seção 5.2).
- O critério é medido sempre: um revert devolve os repos da lista ao ensaio, e a janela recomeça no último
  revert (seção 5.1).

## 7. Decisões minhas, para o dono corrigir

- A lista `lean_auto` pelo `dono/repo` do `origin`, começando só com o `<repo>`. Repo de produto nunca entra.
- O `live_dir` padrão, `~/.local/share/skills-live`, fora de `~/repos` e dos `deny_roots`.
- O clone recusa commit por um `pre-commit` local, e é avançado só com `--ff-only`.
- O avanço destacado no startup.
- O worktree do lote sai do clone dedicado.
- No repo privado, a camada 1 fica com o segredo e o caminho com usuário, e a segunda passada fica só com
  as duas perguntas do diff.
- O `sem-changelog` no lugar do `sem-bump`.
- As publicações privadas não contam no critério da loja.
- O retrofit manual de um repo da lista também publica na `main`.
- A trava de commit do clone vai na config por worktree (`extensions.worktreeConfig`), e o verbo de
  criação recusa um clone que já existe.
- No repo privado, o `caminho` com usuário se aprova pelo `approve`, e o `segredo` nunca.
- No `auto-dry`, a porta roda o gate sem push antes de segurar, e o `approve` fica preso ao `patch_id`.

## 8. O que fica para quem constrói

- Os nomes dos verbos novos (o da criação do clone e o do avanço) e o formato dos campos novos de
  `pedido.json`, do registro e do arquivo da segunda passada.
- Onde mora a variante privada da porta em `rw_gate.py`: uma tabela de guardas por tipo de repo ou um
  módulo à parte.
- Os timeouts do `npm ci` e do push com o gate, depois de medir o gate do `<repo>` num worktree.
- Como achar a pasta da skill dentro do repo (`.claude/skills/<s>` ou `skills/<s>`), pelo `realpath`.
- Os testes: biblioteca padrão; um repo privado fixture (`origin --bare` e um clone) com um pre-push dublê
  que passa ou reprova; cada guarda nova com um caso sabotado e um mutante morto; o hook do clone que
  recusa o commit.
- As versões: `retrofit-watch` 0.5.0 e `retrofit-skill` 0.12.0, com `CHANGELOG`, `marketplace.json` e
  README no mesmo incremento.

## 9. Riscos conhecidos

- **Uma lição errada numa skill que escreve num sistema da empresa** (o KB). Os freios são o ensaio até o
  critério, o revisor e os testes da skill, que o gate roda.
- **O gate do repo lê as skills do Hermes.** Um lote pode ficar segurado por um arquivo de fora do diff. O
  resumo do gate no motivo diz qual.
- **O clone fica para trás em silêncio** se o avanço destacado falhar sempre. O aviso de startup diz.
- **A lacuna da atribuição** (o `TODO.md` da loja, `ba7e11b`): a skill de fora carregada na mesma mensagem
  apaga a atribuição. Vale também para a skill local.
- **O gate é lento** (dois Node, um em container), e roda duas vezes por lote: no ensaio da porta e no
  pre-push. A porta roda em segundo plano, como na v1.
- **A aprovação da v1 não fica presa ao patch.** Achado da revisão deste desenho: o `aprovado.json` da
  loja não guarda o `patch_id`, e uma emenda do executor depois da aprovação subiria sem o dono ver o diff
  novo. Este desenho fecha isso nos repos privados (seção 5.4); na loja, é um item para o `TODO.md`.
