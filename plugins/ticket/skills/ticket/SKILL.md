---
name: ticket
description: "Jira ticket lifecycle for JRC Brasil projects, integrated with Git — create issues/sub-issues and branches, close with an auto-generated summary. Per-repo config via `.jira-project`; discovers project-specific transitions instead of assuming. New issues are born in the active sprint with story points and fixVersion, each read back by the sensor that can see it. Triggers — ticket, Jira, criar issue, fechar ticket, sprint, story points, fixVersion, acli."
argument-hint: "start (open) | split | close | status"
compatibility: "Claude Code: o argument-hint acima é campo dele e só é lido no topo. Requer acli e credenciais Jira (JIRA_EMAIL, JIRA_API_TOKEN)."
metadata:
  version: 1.10.0
---

# Skill: Ticket — Gestão de Tickets Jira

Gerencia o ciclo de vida de tickets Jira integrado com Git, seguindo o fluxo padronizado da JRC Brasil.

**CLI:** `acli` (Jira CLI — validado na v1.3.22; `--from-json` em
`workitem create` exige ≥ 1.3.2x, confirme com `acli --version`) + MCP
`mcp__atlassian__*` quando disponível
**Projeto Jira:** detectado dinamicamente — ver "Detecção de Projeto" abaixo
**Branch naming:** `${BRANCH_PREFIX}-XXX_descricao_curta` (ex.: `RS-605_...`, `SQ-22_...`)
**REST:** as chamadas `curl` abaixo usam `JIRA_EMAIL`/`JIRA_API_TOKEN` — carregue antes com
`set -a; . ~/.hermes/.env; set +a`. Base: `https://jrcbrasil.atlassian.net/rest/api/3`.

## Referências

Caminhos relativos a esta skill. Leia cada uma quando o passo pedir:

- `references/start.md` — leia **antes do primeiro `start` da sessão**: cada passo dos sub-fluxos A
  e B por extenso, com o comando completo e a ressalva que o motivou.
- `references/close.md` — leia **antes do primeiro `close` da sessão**, pelo mesmo motivo.
- `references/workflow.md` — leia **antes de transicionar** (start step 7, close step 6), quando a
  branch base não estiver declarada, ao criar sub-issues, ao **vincular issues** (a direção do link
  é contraintuitiva) e quando um comando do `acli` falhar sem explicação (gotchas, accountId).
- `references/campos.md` — leia **antes de escrever ou conferir sprint, story points ou
  `fixVersion`**: IDs dos custom fields, sprint ativa que não aparece, `create --from-json`,
  `editJiraIssue`, criação por REST com `fixVersion` e a releitura que confirma o que gravou.
- `references/templates.md` — leia **ao montar texto para o Jira** ou ao **enriquecer a descrição** de
  uma issue existente (acrescentar sem apagar o original): descrição de issue nova, resumo
  de fechamento (markdown ou ADF), a varredura que valida o ADF antes do POST, commit de sub-issue.
- `assets/trigger-evals.json` — use **antes de mudar a `description`**: casos de gatilho (deve e
  não deve disparar) no formato do otimizador do `skill-creator`.

## Detecção de Projeto

A skill **não tem projeto Jira hardcoded** — cada repo declara o seu via arquivo
`.jira-project` na raiz (`$(git rev-parse --show-toplevel)/.jira-project`).
Antes de qualquer comando, ler e carregar as variáveis em escopo:

```ini
# ~/repos/sales_quote/.jira-project (exemplo real)
PROJECT=SQ
BOARD=51
BRANCH_PREFIX=SQ
BASE_BRANCH=develop   # opcional — base de branches/PR; se ausente, detectar (ver tabela)
```

| Variável | Uso |
|---|---|
| `$PROJECT` | `--project` no `create`; regex `${PROJECT}-\d+` na branch; `--jql "parent = ${PROJECT}-XXX"` no `split`/`close` |
| `$BOARD` | `--id $BOARD` em `acli jira board list-sprints` |
| `$BRANCH_PREFIX` | Prefixo da branch (`${BRANCH_PREFIX}-XXX_descricao`); geralmente = `$PROJECT`, pode divergir por convenção do time |
| `$BASE_BRANCH` | Base de branches e PRs. **Opcional**; se ausente, **detectar** — nunca chutar, nem `main` nem `develop`: `git symbolic-ref --short refs/remotes/origin/HEAD` (`origin/develop` → `develop`) ou `git remote show origin \| sed -n 's/.*HEAD branch: //p'` (falhando, `references/workflow.md §Branch base`) |

**Bootstrap se `.jira-project` não existir:** avisar o dev (projeto inexistente: `references/workflow.md
§Projeto novo`) e perguntar **project key** (sugerir pelo nome do repo e pelas entries
`project_jira_*` da auto-memory), **board ID** (`acli jira board list`, ou
`mcp__atlassian__searchJiraIssuesUsingJql` com `project = $PROJECT`; vários → perguntar qual) e
**branch prefix** (default = key). Criar o arquivo versionado no repo, com cabeçalho de origem
(keys e board IDs não são secretos; `.gitignore` só com dado sensível), e seguir com o comando
pedido. Arquivo, e não env var nem auto-memory: é explícito e sobrevive a troca de máquina e à
limpeza de memória.

## Roteamento de Comandos

Analise o argumento passado pelo usuário e execute o comando correspondente:

- `start` (ou `open`, `abrir`) → Seção "Comando: start"
- `split` → Seção "Comando: split"
- `close` → Seção "Comando: close"
- `status` → Seção "Comando: status"
- Sem argumento ou argumento não reconhecido → Mostrar lista de comandos disponíveis

---

## Comando: start

**Propósito:** Iniciar desenvolvimento a partir de uma issue existente ou criar nova issue no Jira, branch Git, e transicionar para "Em andamento".

**Detecção de sub-fluxo:** se o argumento após `start` contém uma **key Jira** (regex
`${PROJECT}-\d+`) ou uma **URL do Jira** (regex
`https?://jrcbrasil\.atlassian\.net/browse/(${PROJECT}-\d+)`), extrair a key e seguir o
**Sub-fluxo A**; caso contrário, **Sub-fluxo B**. Cada passo por extenso: `references/start.md`.

### Sub-fluxo A: Issue existente

1. **Buscar dados:** `acli jira workitem view ${PROJECT}-XXX`; sprint e pontos ficam fora do view
   padrão: `acli jira workitem view ${PROJECT}-XXX --fields "customfield_10016,customfield_10020" --json`
   (`10016` = story points; `10020` = array de sprints, pegar a `"state": "active"`). IDs do site
   jrcbrasil, não constantes do Jira. Issue não encontrada → informar e abortar.
2. **Mostrar resumo** (📋 key — summary · 📊 status · 👤 responsável · 🏃 sprint · 🎯 score).
3. **Responsável vazio** → perguntar se o dev quer se atribuir; se sim,
   `acli jira workitem edit --key "${PROJECT}-XXX" --assignee "@me"` — `@me`, não o e-mail.
4. **Sem sprint** → perguntar se adiciona à atual ou a outra. Sprint ativa:
   `acli jira board list-sprints --id $BOARD --state active --json`, a de `"state": "active"`
   **mesmo com `endDate` no passado**; gravar com
   `mcp__atlassian__editJiraIssue(issueIdOrKey: "${PROJECT}-XXX", fields: { "customfield_10020": SPRINT_ID })`
   (**número puro**, `405`). Issue existente só tem esse caminho: o `acli` não escreve custom fields
   no `edit` — sem MCP, diga isso ao dev. Se ele recusar, registrar que optou por pular.
5. **Sem score** → **proponha um número** com justificativa de uma linha (escopo, arquivos, migração,
   teste novo) e deixe o dev confirmar — pedir do nada deixa o campo vazio. Gravar com
   `editJiraIssue(..., fields: { "customfield_10016": N })`.
6. **Releitura obrigatória** depois de mexer em sprint/score — a escrita pode dizer "ok" e não
   aplicar, e o cartão fica no backlog sem ninguém notar: `GET /issue/${PROJECT}-XXX` com
   `fields=status,assignee,fixVersions,customfield_10016,customfield_10020` (o `curl` no `start.md`
   A6). Não confira por JQL nem pelo exit code do `acli` (ver Armadilhas). Valor que não bateu →
   **avise o dev explicitamente** ("a sprint não foi aplicada — o cartão continua no backlog").
7. **Transicionar** para "Em andamento" se ainda não estiver:
   `acli jira workitem transition --key "${PROJECT}-XXX" --status "Em andamento"`.
8. **Criar branch** `${BRANCH_PREFIX}-XXX_descricao_curta` (snake_case, sem acentos, ~50 chars, do
   summary) da base atualizada (`checkout`, `pull`, `checkout -b`), e medir a base em vez de confiar
   no pull: `git fetch origin -q` e `git rev-list --left-right --count HEAD...origin/${BASE_BRANCH}`
   → `0	0`. Comandos no `start.md` A8; base que é árvore de serviço no ar → worktree, no mesmo
   lugar. Não canalize o `pull` para `tail` numa cadeia `&&`: o pipeline sai com o status do último
   comando, e um pull que falhou deixa a branch nascer de base não verificada.
9. **Output:** ✅ issue · 🌿 branch · 📋 status · 👤 responsável · 🔗 sprint · 🎯 score.

### Sub-fluxo B: Nova issue

1. **Perguntar ao dev:** summary, descrição (breve; vai para o template), tipo (Tarefa, História,
   Bug; default Tarefa), **story points sempre** ("Quantos pontos? (1, 2, 3, 5, 8, 13)" — ofereça
   sua estimativa se ele não souber; só siga sem score se ele recusar), **sprint** (sem resposta,
   perguntar "Quer adicionar à sprint atual?") e **fixVersion** quando o projeto versiona releases
   (liste as existentes e proponha a próxima; `acli` e MCP são cegos nesse campo). A próxima
   **ainda não existe** no Jira → confirme com o dev (criar versão é decisão de projeto, como no
   close step 7) e crie por REST (`references/campos.md §fixVersion`, linha "Criar versão"); o
   `id` devolvido, não o nome, vai no `fixVersions` do POST da issue.
2. **Descobrir a sprint ativa antes de criar** (mesmo comando e regra do A4; mais de uma → perguntar;
   nenhuma → `references/campos.md §Quando não aparece sprint ativa`).
3. **Criar já com sprint e story points** — `acli jira workitem create --from-json <arquivo>` com
   `projectKey`, `type`, `summary`, `description` e `additionalAttributes`
   (`{"customfield_10016": 3, "customfield_10020": 405}`), que aceita custom fields na criação (o
   JSON completo no `start.md` B3). Criar e editar depois depende do MCP autenticado; sem ele, o
   cartão fica órfão no backlog. Sprint = id **número puro**; omitir a chave que o dev não informou; `description` em **ADF**, não
   markdown; capturar a key retornada. `acli` sem `--from-json` → `create` simples + `editJiraIssue`,
   avisando o dev. **Com fixVersion, prefira o REST** (`POST /rest/api/3/issue`, uma chamada grava
   tudo): antes, leia `references/campos.md §Criar a issue numa chamada só` e rode a varredura de marks de
   `references/templates.md` antes do POST.
4. **Confirmar que nasceu completa** com o `GET` do A6 (só o REST lê `fixVersions`). Campo que não
   veio → dizer ao dev; não reportar sucesso sem a releitura.
5. **Criar branch** como no A8.
6. **Transicionar:** `acli jira workitem transition --key "${PROJECT}-XXX" --status "Em andamento"`.
7. **Output:** ✅ issue criada · 🌿 branch · 📋 status · 🔗 sprint · 🎯 score.

### Registrar cartão sem começar o trabalho

Para trabalho que será agendado depois (defeitos de QA ou code review, dívida técnica, itens de
reunião): **pule branch e transição** — o cartão nasce em "Tarefas pendentes", onde quem planeja a
sprint o procura; branch vazia e "Em andamento" mentiriam sobre o estado. Sprint, pontos,
`fixVersion` e a releitura continuam valendo; se forem vários cartões, REST em lote (`references/campos.md §fixVersion`) e
vínculo ao cartão que bloqueiam (`references/workflow.md §Vínculos entre issues`). Pedido ambíguo → pergunte se
é "abrir para já começar" ou "registrar para o time priorizar".

### Regras

- A issue só nasce com confirmação do dev; **"começar" ≠ "registrar"** — só o primeiro cria branch
  e transiciona
- Sprint verificada em issue existente e nova (pular só com o dev sabendo); issue nova **nasce
  dentro da sprint** (`--from-json`), não criada-e-depois-editada
- **Releia depois de escrever** e só então diga que deu certo (A6 / B4)
- A branch parte de `${BASE_BRANCH}` (nunca assumir `develop`); `git status` sujo → avisar antes de
  trocar de branch
- Descrição de issue nova no template de `references/templates.md` (só sub-fluxo B)

---

## Comando: split

**Propósito:** Quebrar issue atual em sub-issues no Jira (Passo 04.1).

1. **Detectar issue atual:** extrair `${PROJECT}-XXX` do nome da branch via regex
   `^(${BRANCH_PREFIX}-\d+)`; se não estiver em branch de issue, pedir a key ao dev.
2. **Perguntar ao dev:** nome/summary da sub-issue e descrição breve (opcional).
3. **Criar sub-issue** e capturar a key retornada (ex.: `RS-606` ou `SQ-33`):
   `acli jira workitem create --project "$PROJECT" --type "Subtarefa" --summary "{nome}" --description "{descrição}"`
4. **Vincular à issue pai:** `acli jira workitem edit --key "${PROJECT}-YYY" --parent "${PROJECT}-XXX"`
5. **Transicionar sub-issue para Em andamento (se o dev confirmar):**
   `acli jira workitem transition --key "${PROJECT}-YYY" --status "Em andamento"`
6. **Não criar branch nova.** Output: ✅ sub-issue criada · 🔗 vinculada a `${PROJECT}-XXX` · 📌
   continuar na branch atual, commitando com `git commit -m "${PROJECT}-YYY: {descrição do commit}"`.

**Regras:** sem branch para sub-issue — os commits vão na branch da issue pai; sub-issues usam o
tipo "Subtarefa" (PT-BR); perguntar se quer criar mais sub-issues (loop até o dev dizer que terminou).

---

## Comando: close

**Propósito:** Fechar issue com resumo auto-gerado e transições de status (Passo 05). Cada passo
por extenso, para ler antes do primeiro `close`: `references/close.md`.

1. **Detectar issue** pela branch (regex `^(${BRANCH_PREFIX}-\d+)`); sem match, pedir ao dev — mas
   com o PR já mergeado veja antes a nota do step 10. Confira status e responsável.
2. **Sub-issues:** `acli jira workitem search --jql "parent = ${PROJECT}-XXX"`; alguma não
   "Finished" → alertar e perguntar se continua.
3. **Auto-gerar resumo** de `git log ${BASE_BRANCH}..HEAD --oneline`,
   `git diff ${BASE_BRANCH}...HEAD --stat` e `acli jira workitem view ${PROJECT}-XXX`, no template de
   `references/templates.md` (leia ao montar): **Visão Geral** da descrição no Jira, **Solução** dos commit messages,
   **Teste** dos arquivos de teste modificados (sem eles, pedir ao dev). Já integrado por
   rebase + ff, sem branch: commits pela key no corpo (`close.md` step 3).
4. **Apresentar o rascunho** ao dev e pedir confirmação ou edições.
5. **Comentar na issue** — preferir `mcp__atlassian__addCommentToJiraIssue(cloudId, issueIdOrKey,
   commentBody: "<markdown>", contentFormat: "markdown")`, que converte para ADF server-side
   (validado 2026-05-20; o campo é `commentBody`, ver Armadilhas). Sem MCP: ADF
   (`scripts/md2adf.py` converte o markdown e roda a varredura) por REST, cujo HTTP é sensor
   (o `acli` sai 0 em falha). 🔴 **Confirme por REST**, nunca por `acli comment list`:
   `GET .../issue/${PROJECT}-XXX/comment?orderBy=-created&maxResults=1` com o `body` como
   **objeto** (`str` = ADF recusado). Comando pronto em `references/close.md` step 5.

6. **Transicionar até o "done"** descobrindo as transições (`getTransitionsForJiraIssue`; aplicar pelo
   `id` da transição cujo `to.name` é o status final) — **RS:** `Em andamento → Aprovação → Finished`; **SQ:**
   `Em andamento → Concluído` direto (`acli --status "Concluído"`, que casa pelo status de destino,
   ou MCP id `31`). Sem MCP: REST por id (close.md step 6).
7. **Conferir o `fixVersion`** (`GET .../issue/${PROJECT}-XXX?fields=fixVersions` contra
   `git tag --sort=-v:refname | head -3`): coerente → siga; vazio com a versão existente → ofereça
   atribuí-la; vazio e a versão **não existe** no Jira → **pare e pergunte** (criar versão é decisão
   de projeto).
8. **Commitar pendências** (`git status`; mostrar e perguntar; untracked relevantes; Conventional
   Commits com a key no body) e rodar o lint do projeto, corrigindo antes de seguir.
9. **Criar PR:** `git push -u origin <branch>` e
   `gh pr create --base ${BASE_BRANCH} --title "${PROJECT}-XXX: {summary}" --body-file "/tmp/${PROJECT}-XXX-pr-body.md"`
   — o body é o mesmo markdown do step 5; PR já existente → mostrar a URL.
10. **Voltar para `${BASE_BRANCH}`** (`checkout` + `pull`; em worktree, `git worktree remove` e nada de
    `pull` na árvore viva: `close.md` step 10). Fluxo direto na base, sem PR → pular 9-10.
    **PR já mergeado → pular 8-10** (é o caso comum): o step 1 não casa a branch, e a key está no
    subject do squash — `git log -1 --format='%s'`; confirme com o dev, pode ser de outro cartão.
11. **Output:** ✅ issue fechada · 📋 status · 💬 resumo postado · 🔀 PR · 🌿 de volta à base.

### Regras

- Resumo mostrado ao dev antes de postar; sub-issues pendentes alertadas antes de fechar
- Transições adaptadas ao status atual (nunca para o status em que já está), pela sequência de
  `references/workflow.md` (ler antes do step 6)
- Markdown escrito uma vez (comentário + PR body); ADF só no fallback sem MCP (`references/templates.md §ADF (legado)`)
- `git status` antes do PR; lint após o commit e antes do push

---

## Comando: status

**Propósito:** Mostrar status atual da issue vinculada à branch.

1. **Detectar issue:** extrair `${PROJECT}-XXX` da branch corrente.
2. **Buscar dados:** `acli jira workitem view ${PROJECT}-XXX` e
   `acli jira workitem search --jql "parent = ${PROJECT}-XXX"`.
3. **Output:** 📋 key — summary · 📊 status · 👤 responsável · 🏃 sprint, e a lista de sub-issues
   (`- ${PROJECT}-601 — {summary} [Em andamento]`); sem sub-issues, omitir a seção.

---

## Detecção de Issue a partir da Branch

Lógica comum a todos os comandos: casar `git branch --show-current` com o regex
`^(${BRANCH_PREFIX}-\d+)` (`$BRANCH_PREFIX` vem da "Detecção de Projeto"). Sem match, perguntar
ao dev: "Não consegui detectar a issue da branch atual. Qual é a key? (ex.: `${PROJECT}-605`)"

---

## Armadilhas e tratamento de erros

Todo sensor desta skill já falhou de um jeito diferente (paginação, lag, silêncio): o veredito é
sempre a releitura do campo pelo REST.

| Armadilha | O que fazer |
|---|---|
| O `acli` imprime `✗ Failure: …` e **sai 0** | `&&` e `$?` são decorativos; `workitem search` sem match não imprime **nada** (nem "0 results"). Releia o campo. |
| JQL logo depois de criar (`sprint in openSprints()`) | **Lag de indexação**: volta vazia por segundos com o campo gravado (medido). `sprint list-workitems` pagina (~30 itens) e perde o cartão novo. Desempate: `references/campos.md §Conferir que gravou`, quando a JQL divergir do `GET`. |
| `--assignee` com o e-mail | O `userEmail` da sessão não é necessariamente a conta Jira; o erro (`✗ Failure: ... can't be edited: unexpected error, trace id: …`) não nomeia a causa. Use `@me`. |
| `json: unknown field "additionalAttributes"` no `edit` | O `acli` aceita a chave **só no `create`**; issue existente → MCP `editJiraIssue` (v1.3.22). |
| `body:` no `addCommentToJiraIssue` | O servidor valida **depois** de receber o corpo: `MCP error -32602: ... Required at commentBody` custa reenviar o resumo inteiro (medido em 18/09/2026). |
| `acli jira workitem comment --key …` | `comment` é grupo (`create`/`list`/`update`/`delete`/`visibility`); dá `✗ Error: unknown flag: --key`. Use `comment create`. |
| `acli comment list --json` como sensor | Achata o ADF para texto puro: comentário perfeito aparece como string crua (medido em 11/09/2026). Confira pelo REST (`references/close.md` step 5). |
| Flag `released` como sensor de release | Metadado marcado à mão, atrasa (versões lançadas constavam `released=False`). Quem sabe é a tag/versão em `origin/main`. |

**Erros:**

- **`acli` falha:** mostrar o erro completo ao dev e sugerir verificar credenciais/conexão.
- **MCP atlassian ausente ou só com `authenticate`:** antes de supor falta de login, confira o
  endpoint (o HTTP+SSE `/v1/sse` caiu em 30/jun/2026): leia `references/campos.md §Issue existente`.
- **Transição falha (`"No allowed transitions found"`):** como no close step 6, listar as reais e
  aplicar pelo `id` do destino (`references/workflow.md`); `acli --status` casa pelo **nome do status
  de destino**.
