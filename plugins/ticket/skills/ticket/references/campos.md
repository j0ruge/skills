# Campos do cartão — sprint, story points, fixVersion e a releitura

> Placeholders `${PROJECT}` e `$BOARD` vêm do `.jira-project` (ver `SKILL.md
> §Detecção de Projeto`). As chamadas REST usam `JIRA_EMAIL`/`JIRA_API_TOKEN`,
> carregados com `set -a; . ~/.hermes/.env; set +a`, e a base
> `J=https://jrcbrasil.atlassian.net/rest/api/3`. Transições, branch base, tipos,
> sub-issues, vínculos e gotchas gerais do `acli` ficam em `workflow.md` (o
> SKILL.md roteia).

## Sumário

- [Sprint e Story Points](#sprint-e-story-points)
  - [Descobrir os IDs dos campos](#descobrir-os-ids-dos-campos-não-confie-nos-números)
  - [Descobrir a sprint ativa](#descobrir-a-sprint-ativa) · [Quando não aparece sprint ativa](#quando-não-aparece-sprint-ativa)
  - [Issue nova — `create --from-json`](#issue-nova--create---from-json-não-precisa-de-mcp)
  - [Issue existente — MCP `editJiraIssue`](#issue-existente--mcp-editjiraissue)
- [fixVersion (rótulo de release)](#fixversion-rótulo-de-release)
  - [Criar a issue numa chamada só (REST)](#criar-a-issue-numa-chamada-só-rest)
  - [Os dois ids que o `POST /issue` exige](#os-dois-ids-que-o-post-issue-exige-e-de-onde-vêm)
  - [A flag `released` não diz se a versão foi lançada](#a-flag-released-do-jira-não-diz-se-a-versão-foi-lançada)
- [Conferir que gravou](#conferir-que-gravou-o-passo-que-evita-o-backlog-silencioso)

## Sprint e Story Points

Estes dois campos são a origem do sintoma mais comum da skill: **o cartão vai
parar no backlog e sem pontuação**. A causa raiz é que a escrita depende de qual
caminho está disponível, e o caminho mais óbvio (criar a issue e editar depois)
é justamente o que falha calado. A ordem de preferência abaixo é por
confiabilidade, não por elegância.

| Situação | Caminho | Precisa de MCP? |
|---|---|---|
| Issue **nova** | `acli jira workitem create --from-json` com `additionalAttributes` | ❌ não |
| Issue **existente** | `mcp__atlassian__editJiraIssue` | ✅ sim |
| Conferir o que gravou | `GET /issue/<KEY>?fields=…` (imediato; a JQL tem lag — ver §Conferir que gravou) | ❌ não |

### Descobrir os IDs dos campos (não confie nos números)

`customfield_10016` (story points) e `customfield_10020` (sprint) são do site
**jrcbrasil** — não são constantes do Jira. Num site/projeto novo, descubra:

```bash
acli jira workitem view <KEY-que-já-tem-os-campos> --fields "*all" --json
```

`*all` traz ~100 campos; sem ele o `--json` devolve só 5 e **nenhum** custom
field (é por isso que o `view` "não mostra" sprint/score). Identifique pelo
formato: sprint é o array cujos objetos têm `boardId`/`state`; story points é o
número solto. O `acli` não tem comando para listar definições de campo
(`acli jira field` só cria/atualiza/apaga).

### Descobrir a sprint ativa

```bash
acli jira board list-sprints --id $BOARD --state active --json
```

Retorna as sprints ativas do board do projeto detectado (ex.: board `10` para
RS, `51` para SQ). Extrair o `id`.

O envelope é `{"isLast":…, "maxResults":…, "sprints":[…], "startAt":…, "total":…}`
— a chave é **`sprints`**, não `values` e não uma lista nua. Um parser escrito
por analogia com outras APIs do Jira quebra com `'str' object has no attribute
'get'`, que não sugere em nada o formato certo:

```bash
acli jira board list-sprints --id $BOARD --state active --json \
  | python3 -c 'import json,sys;[print(s["id"], s["name"], s["state"]) for s in json.load(sys.stdin)["sprints"]]'
```

> ⚠️ **A sprint ativa é a de `"state": "active"` — ponto.** Não a descarte
> porque o `endDate` já passou: times deixam a sprint correr meses além da data
> planejada sem fechá-la, e tratá-la como "vencida" é exatamente o que faz o
> cartão cair no backlog.

#### Quando não aparece sprint ativa

1. **`$BOARD` errado ou de outro projeto** — a causa mais frequente. Conferir:
   `acli jira board search --name "<projeto>"` e `acli jira board list-projects --id $BOARD`.
2. **Descobrir pela issue, sem depender do board** — JQL resolve:
   `acli jira workitem search --jql "project = $PROJECT AND sprint in openSprints()" --fields "customfield_10020" --json`
   → o array de sprint das issues já traz `id` + `boardId` da sprint corrente.
3. **Board scrum sem sprint aberta** (todas `closed`/`future`): não invente uma —
   avise o dev e pergunte se deve criar (`acli jira sprint create`) ou deixar no
   backlog conscientemente. Se já existe uma `future` (projeto Scrum novo nasce com uma), ela é
   a terceira opção: o id dela em número puro no `customfield_10020` grava, e a releitura mostra
   `state: future` (medido no SBM-1, sprint 573). Iniciar a sprint continua sendo decisão do dev.
   Board **kanban** não tem sprint: nesse caso o campo simplesmente não se aplica.

### Issue nova — `create --from-json` (não precisa de MCP)

O template oficial (`acli jira workitem create --generate-json`) inclui
`additionalAttributes`, que aceita `customfield_*` **na criação**. Validado em
2026-08-04 no projeto SQ: a issue nasceu com sprint `405` e 3 story points sem
nenhuma chamada MCP.

```json
{
  "projectKey": "SQ",
  "type": "Tarefa",
  "summary": "Título da issue",
  "description": { "version": 1, "type": "doc", "content": [
    { "type": "paragraph", "content": [ { "type": "text", "text": "Descrição em ADF." } ] }
  ] },
  "additionalAttributes": {
    "customfield_10016": 3,
    "customfield_10020": 405
  }
}
```

```bash
acli jira workitem create --from-json /tmp/nova-issue.json
# ✓ Work item SQ-66 created: https://jrcbrasil.atlassian.net/browse/SQ-66
```

- Sprint é o **id como número puro** (`405`). `{"id": 405}` não é o formato aqui.
- `description` é **ADF**, não markdown — o `--from-json` não converte.
- Omitir a chave quando o dev não informou o valor (não mandar `null`).

### Issue existente — MCP `editJiraIssue`

```text
mcp__atlassian__editJiraIssue(issueIdOrKey: "${PROJECT}-XXX", fields: { "customfield_10020": 405 })
mcp__atlassian__editJiraIssue(issueIdOrKey: "${PROJECT}-XXX", fields: { "customfield_10016": 8 })
```

> ⚠️ **`acli edit --from-json` NÃO aceita `additionalAttributes`** — falha com
> `json: unknown field "additionalAttributes"` (v1.3.22). A assimetria é real:
> `create` aceita custom fields, `edit` não. Também não existe comando de sprint
> que mova work items (`acli jira sprint` só faz create/update/view/delete/
> list-workitems). Portanto, para issue já criada **não há caminho sem MCP** —
> se ele não estiver disponível, diga isso ao dev (ele pode arrastar no board)
> em vez de seguir como se tivesse dado certo.

> **MCP não-autenticado ou sem as tools de escrita?** Numa sessão nova o servidor
> atlassian pode expor só `authenticate`/`complete_authentication`. Antes de
> tratar como problema de login, **confira o endpoint**: o transporte HTTP+SSE
> (`https://mcp.atlassian.com/v1/sse`) foi descontinuado em **30/jun/2026** e
> precisa virar Streamable HTTP —
> `claude mcp add --transport http atlassian https://mcp.atlassian.com/v1/mcp`
> (em JSON, no `~/.claude.json` por projeto ou no `.mcp.json`:
> `{"type": "http", "url": "https://mcp.atlassian.com/v1/mcp"}` — o `"type": "sse"`
> antigo é o sintoma).
> Se a autorização não completar, use `https://mcp.atlassian.com/v1/mcp/authv2`:
> sondando os dois (2026-08-04), só o `authv2` devolve
> `WWW-Authenticate: Bearer resource_metadata="…"` — o discovery OAuth
> (RFC 9728) que permite ao cliente achar o servidor de autorização sozinho.
> Depois de corrigir, chame `mcp__atlassian__authenticate` e repasse a URL ao dev.
> Enquanto isso, transição (`--status "<status-destino>"`) e comentário (ADF via
> `--body-file`) seguem funcionando pelo `acli`.

## fixVersion (rótulo de release)

**Este é o campo com os piores sensores das ferramentas locais** — `acli` não
escreve **nem lê**, e o MCP não confirma (verificado 2026-08-24). Tudo aqui é
REST.

| Operação | Caminho | `acli`/MCP servem? |
|---|---|---|
| Listar versões do projeto | `GET /rest/api/3/project/<KEY>/versions` | `acli jira project view --json` lê, mas o REST é a fonte |
| Criar versão | `POST /rest/api/3/version` com `{"name","projectId"}` | ❌ não existe |
| Marcar lançada | `PUT /rest/api/3/version/<ID>` com `{"released":true,"releaseDate":"AAAA-MM-DD"}` | ❌ |
| Pôr no cartão | `POST /rest/api/3/issue` (criação) ou `PUT /rest/api/3/issue/<KEY>` | ❌ `acli edit` não tem a flag (e **sai 0**) |
| **Ler** | `GET /rest/api/3/issue/<KEY>?fields=fixVersions` | ❌ `acli view --json` devolve `[]` **mesmo com o campo gravado** |

```bash
set -a; . ~/.hermes/.env; set +a     # JIRA_EMAIL / JIRA_API_TOKEN
J=https://jrcbrasil.atlassian.net/rest/api/3
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$J/project/SQ/versions"          # listar
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -X POST -H 'Content-Type: application/json' \
  -d '{"name":"0.8.0","projectId":10050}' "$J/version"                     # criar (devolve o id)
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$J/issue/SQ-107?fields=fixVersions"                                     # ÚNICO sensor de leitura
```

**Versão que ainda não existe, no `start`:** só crie depois de o dev confirmar o nome — é ato de
projeto, não de cartão. Use o `id` da resposta (não o `name`) em `fixVersions:[{"id":…}]` do
`POST /issue`, e confira pela releitura. Medido em 2026-10-01: `0.10.0` no SQ → `id` 10110, e o
`GET ?fields=fixVersions` devolveu `['0.10.0']`. A receita esteve sempre nesta tabela; o que
faltava era o B1 do `start` apontar para ela quando a versão proposta não existe.

⚠️ **`updated` não é sensor**: o Jira não bumpa `fields.updated` numa mudança de
`fixVersions`. Concluir "não gravou" pelo timestamp é errado.

### Criar a issue numa chamada só (REST)

**Quando houver fixVersion, prefira o REST — ele faz tudo numa chamada.** O
`--from-json` do `acli` não escreve `fixVersions`, então o caminho dele exige
um segundo passo que só existe via REST de qualquer forma. `POST
/rest/api/3/issue` aceita `fixVersions`, `customfield_10016` (pontos) e
`customfield_10020` (sprint, **número puro**) juntos, com `description` em
ADF — uma chamada, um ponto de falha:

```bash
set -a; . ~/.hermes/.env; set +a
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -X POST -H "Content-Type: application/json" \
  --data-binary @/tmp/nova-issue.json \
  "https://jrcbrasil.atlassian.net/rest/api/3/issue"
# fields: { project:{id}, issuetype:{name}, summary, description(ADF),
#           fixVersions:[{id}], customfield_10016: N, customfield_10020: SPRINT_ID }
```

`project` e `issuetype` vão por **id**, que o `.jira-project` não guarda —
duas chamadas os descobrem, uma vez por projeto (subseção seguinte).

Monte o ADF com um script **gravado em arquivo** (`cat > /tmp/build-adf.py`),
não com um heredoc canalizado para `python3 -`: um erro de sintaxe no meio de
um heredoc longo aponta para "linha N de stdin" e obriga a repassar o script
inteiro, enquanto o arquivo se conserta numa linha e roda de novo. Escrever
JSON à mão é pior ainda: um `description` malformado é recusado **sem dizer
qual nó** está errado — e montar por script não basta, porque o script também
erra. **Rode a varredura de marks antes do POST** (`templates.md` §Antes de
postar: valide o ADF, que o SKILL.md roteia): ela troca o 400 mudo por um
diagnóstico exato em segundos, e pega o erro mais comum — um helper de marks que
recebe string em vez de lista.

### Os dois ids que o `POST /issue` exige (e de onde vêm)

O corpo pede `project` e `issuetype` por **id** — e nem um nem outro aparece em
lugar nenhum da configuração da skill (`.jira-project` guarda a *key*, não o id).
Duas chamadas resolvem, e o resultado vale para o projeto inteiro:

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$J/project/$PROJECT" \
  | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["id"], d["key"], d["name"])'
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$J/issue/createmeta/$PROJECT/issuetypes" \
  | python3 -c 'import json,sys;[print(t["id"], t["name"]) for t in json.load(sys.stdin)["issueTypes"]]'
```

Medido em SQ (2026-09-10): projeto `10050`; tipos `10000` Epic · `10009` História ·
`10018` Tarefa · `10019` Subtarefa · `10020` Bug · `10271` Referência. Confirme
antes de reusar — tipos são configuração de projeto e mudam.

Anote o que descobriu como comentário datado no `.jira-project`: a próxima criação
não repete as chamadas, e a data diz quando conferir de novo. O do EDS guarda projeto
`10005`, `Tarefa` `10030` e a fixVersion `0.1.0` = `10004` (medidos em 05/10/2026).

### A flag `released` do Jira não diz se a versão foi lançada

O campo é metadado que alguém precisa marcar à mão, então ele atrasa em relação
ao mundo: uma versão aparece `unreleased` semanas depois de estar em produção,
com o bump já em `origin/main`.

**Antes de afirmar ao dev que uma versão não foi lançada, confira o artefato:**

```bash
git branch -r --contains <sha-do-bump>          # origin/main aparece?
git show origin/main:package.json | grep version   # ou o arquivo de versão do projeto
```

Se o repo diz que foi, corrija o Jira (`PUT /version/<ID>` com `released` e
`releaseDate`) em vez de repassar o metadado defasado.

## Conferir que gravou (o passo que evita o backlog silencioso)

**Um `GET` do REST lê os cinco campos de uma vez** — status, assignee,
`fixVersions`, pontos e sprint — e responde **na hora**, inclusive para uma issue
criada há um segundo. É o sensor pós-criação:

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$J/issue/${PROJECT}-XXX?fields=status,assignee,fixVersions,customfield_10016,customfield_10020"
```

Não é preciso alternar ferramenta por campo: o `acli view --fields` lê sprint e
pontos, mas não `fixVersions` (§fixVersion), então o REST cobre os dois casos.

<CRITICAL>
**A JQL não serve como conferência logo após a criação — ela tem lag de
indexação.** Medido em 2026-09-10, segundos após um `POST /issue` que nasceu com
`customfield_10020: 405`:

```text
key = SQ-122 AND sprint in openSprints()   → {"issues":[]}          ← ainda não indexado
GET /issue/SQ-122?fields=customfield_10020 → [(405,"Formulário")]   ← já gravado
```

Segundos depois a mesma JQL devolveu a issue. Quem seguisse a regra *"se não
bater, reportar a falha"* anunciaria ao dev que o cartão ficou no backlog —
exatamente o alarme falso que esta seção existe para evitar, e que já derrubou o
`sprint list-workitems` (adiante). **Todo sensor desta skill já falhou de um jeito
diferente**: paginação, lag, silêncio. Por isso o veredito é da leitura do campo,
não da busca.
</CRITICAL>

⚠️ **`sprint list-workitems` é falso-negativo por paginação.** Ele lista ~30
itens; cartão recém-criado cai fora da primeira página e "some" — estando na
sprint.

⚠️ **`acli workitem search` que não casa nada imprime NADA** — sem linha de
resultado, sem "0 results", sem erro, e ainda sai 0. Saída vazia é
indistinguível de comando quebrado, então não a leia como veredito.

A JQL continua útil **depois** — para conferir de novo mais tarde, ou quando a
leitura do campo já disse que gravou e você quer o cruzamento. Nesse caso, o
desempate entre "não está na sprint" e "ainda não indexou" é uma query só:

```bash
# Se `key = X` sozinha também vier vazia, é índice, não sprint.
acli jira workitem search --jql "key = ${PROJECT}-XXX" --fields "key"
```

Se a **leitura do campo** não bater com o pedido, reportar a falha
explicitamente. Um "issue criada ✅" sem essa releitura é como o cartão some no
backlog sem ninguém notar.
