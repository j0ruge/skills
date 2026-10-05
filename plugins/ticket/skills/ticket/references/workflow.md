# Workflow de Status — Jira (multi-projeto)

> Placeholders `${PROJECT}` (ex.: `SQ`, `RS`) e `$BOARD` (ex.: `51`, `10`) vêm
> do arquivo `.jira-project` da raiz do repo — ver `SKILL.md §Detecção de Projeto`.
> Sprint, story points, `fixVersion` e a releitura dos campos ficam em
> `campos.md` (o SKILL.md roteia).

## Sequência de Transições

> ⚠️ **As transições são específicas de cada projeto/board — não existe sequência
> universal.** O board RS tem a etapa intermediária `Aprovação`; o board SQ **não**
> tem (vai direto de `Em andamento` para `Concluído`). Cravar a sequência de um
> projeto quebra no outro com `"No allowed transitions found for given status"`.
> **Antes de transicionar, descubra as transições reais da issue** (abaixo) e
> caminhe até o status de destino — não assuma nomes entre projetos.

### Exemplos conhecidos (confirmar antes de usar — boards mudam)

| Projeto | Board | Caminho até "done" | Status final | Como chegar ao done |
|---|---|---|---|---|
| RS | 10 | `Tarefas pendentes → Em andamento → Aprovação → Finished` | `Finished` | duas transições (`Aprovação`, depois `Finished`) — **por convenção do time, não por restrição do board** (ver abaixo) |
| SQ | 51 | `Tarefas pendentes → Em andamento → Concluído` (**sem `Aprovação`**) | `Concluído` | `acli --status "Concluído"` direto (ou MCP transição **id `31`**) |

### ⚠️ O caminho documentado é convenção; o board costuma ser mais permissivo

Medido no RS em 11/09/2026, com a issue em `Em andamento`:

```text
id= 2  Approval          → Aprovação
id=31  Itens concluídos  → Finished     ← atalho: pula a Aprovação
```

Ou seja, a coluna "duas transições" da tabela descreve o **processo do time**, não um
limite do Jira: dá para ir direto a `Finished`. Duas consequências práticas:

- **Prefira o caminho documentado**, mesmo tendo atalho. O passo por `Aprovação` é o
  rastro que o time espera encontrar; pulá-lo economiza uma chamada e apaga a etapa do
  histórico.
- **O conjunto de transições muda conforme o status atual** — não é uma lista fixa da
  issue. A partir de `Aprovação` aparece `id=6 DONE → Finished`, que **não existe** a
  partir de `Em andamento`. Por isso a Regra 1 vale a cada passo: liste de novo depois
  de transicionar, em vez de reaproveitar os ids da leitura anterior.

### Descobrir transições (fazer isto, não chutar)

Preferir o MCP — retorna `id` + `name` + `to.name` (status destino) e permite
transicionar **por id**, o que é robusto quando o nome da transição diverge do
nome do status:

```text
mcp__atlassian__getTransitionsForJiraIssue(cloudId, issueIdOrKey: "${PROJECT}-XXX")
# → [{ id, name, to: { name } }] — escolher a transição cujo to.name é o status desejado:
mcp__atlassian__transitionJiraIssue(cloudId, issueIdOrKey: "${PROJECT}-XXX", transition: { id: "31" })
```

Fallback com `acli` — **transiciona pelo NOME DO STATUS DE DESTINO** (o próprio
help do `acli` descreve `--status` como "Status to transition the work item"),
não pelo nome da transição:

```bash
# Passa o STATUS de destino (ex.: "Concluído"), não o nome da transição:
acli jira workitem transition --key "${PROJECT}-XXX" --status "Concluído"
```

### Regras

1. **Descubra antes de transicionar.** `getTransitionsForJiraIssue` (ou ler o erro
   do `acli`) revela a sequência real. Transição inexistente/fora de ordem retorna
   `"No allowed transitions found for given status"`.
2. **Status/transições em PT-BR**, conforme configurado no projeto.
3. **`acli --status` casa pelo NOME DO STATUS DE DESTINO, não da transição.**
   Verificado 2026-05-29 no SQ, partindo de "Em andamento":
   `acli --status "Concluído"` **funciona**; `acli --status "Itens concluídos"`
   (o *nome da transição* que leva a "Concluído", id `31`) **falha** com
   `No allowed transitions found for given status`. Bate com o help do `acli`
   (`--status` = "Status to transition the work item"). O MCP
   `transitionJiraIssue(transition: { id })` continua útil quando você prefere o
   `id`; para o `acli`, passe o **status alvo**.
   ⚠️ O mesmo erro `No allowed transitions found` também aparece quando a
   transição não é permitida a partir do status **atual** — por isso a Regra 1
   (descobrir/caminhar passo a passo) continua valendo.

## Branch base (`$BASE_BRANCH`)

> ⚠️ **Detecte. Não chute, e não confie na memória de outro projeto.** Cravar
> uma base errada faz a branch nascer do lugar errado e a PR ir para o alvo
> errado — e o sintoma só aparece no merge, quando já custa.

```bash
git symbolic-ref --short refs/remotes/origin/HEAD   # → origin/develop
# se falhar (HEAD remoto não resolvido localmente):
git remote show origin | sed -n 's/.*HEAD branch: //p'
```

Se `refs/remotes/origin/HEAD` não existir na cópia local, criar com
`git remote set-head origin -a` antes de continuar.

### Estado conhecido (confirmar antes de usar — repos mudam)

| Repo | Projeto | `$BASE_BRANCH` | Fluxo |
|---|---|---|---|
| `sales_quote` | SQ | **`develop`** | `develop → staging → main`; PRs vão para `develop` desde a feature 017 |

> Se um repo novo entrar na tabela, entre com a **saída do comando**, não com o
> que parece razoável.

### Declarar em vez de redetectar

Quando o repo já é conhecido, escreva `BASE_BRANCH` no `.jira-project` — é
versionado, explícito, e vale para quem clonar:

```ini
BASE_BRANCH=develop
```

## Projeto novo

Quando o `GET /rest/api/3/project/<KEY>` responde "Nenhum projeto poderia ser encontrado", a key
ainda não existe. Criar projeto é ato de projeto: **confirme com o dev** a key, o nome e o modelo
(Scrum ou Kanban) antes do POST. Medido ao criar o SBM em 2026-10-01:

```bash
set -a; . ~/.hermes/.env; set +a; J=https://jrcbrasil.atlassian.net/rest/api/3
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$J/myself"            # accountId do líder
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -X POST -H 'Content-Type: application/json' \
  -d '{"key":"<KEY>","name":"<nome>","projectTypeKey":"software",
       "projectTemplateKey":"com.pyxis.greenhopper.jira:gh-simplified-agility-scrum",
       "leadAccountId":"<accountId>","assigneeType":"UNASSIGNED"}' "$J/project"
# kanban: ...:gh-simplified-agility-kanban. Os dois criam projeto team-managed (style next-gen).
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://jrcbrasil.atlassian.net/rest/agile/1.0/board?projectKeyOrId=<KEY>"   # $BOARD
```

- **Releia o projeto** com `GET $J/project/<KEY>`: ele traz o `id` (vai no `project.id` do
  `POST /issue`) e os `issueTypes` **deste** projeto, com ids próprios. No SBM a subtarefa veio
  como `Subtask`, e não como `Subtarefa`: confira o nome antes do `split`.
- O board nasce junto (no SBM: `type: simple`), com uma sprint `future` já criada e **nenhuma
  ativa**. Ver `campos.md §Quando não aparece sprint ativa`, item 3.
- Versão e issue seguem os caminhos de sempre (`campos.md §fixVersion`). Depois, grave o
  `.jira-project` com os ids descobertos no comentário de cabeçalho.

## Tipos de Issue (em PT-BR)

- História, Tarefa, Bug, Epic, Subtarefa, Entrevista, Análise, DevOps, Divida Técnica, Idea
- Usar nomes em português: `--type "Tarefa"`, **não** `--type "Task"`

## Gotchas do `acli`

- **`acli` imprime `✗ Failure` e sai com exit 0** (verificado 2026-08-24).
  Consequência: cadeia `&&`, `set -e` e checagem de `$?` são **decorativas** —
  quem automatiza em cima do exit code reporta sucesso sobre falha silenciosa.
  O único sensor confiável é reler o campo.
- `--type` deve usar o nome em PT-BR conforme configurado no projeto
- Transições fora da ordem retornam: `"No allowed transitions found"`
- O comando `view` não aceita `--key`, passar o ID direto: `acli jira workitem view ${PROJECT}-XXX`
- **`view` padrão omite sprint e story points.** Usar `--fields "customfield_10016,customfield_10020" --json` para obter esses campos. `customfield_10016` = story points, `customfield_10020` = array de sprints (pegar a com `"state": "active"`). Para descobrir IDs num site novo: `--fields "*all" --json`
- **`create` escreve custom fields, `edit` não.** `create --from-json` aceita
  `additionalAttributes` (sprint/story points na criação, sem MCP);
  `edit --from-json` rejeita a mesma chave com
  `json: unknown field "additionalAttributes"`. Issue existente → MCP
  `editJiraIssue`. Detalhe em `campos.md` §Sprint e Story Points (o SKILL.md
  roteia essa reference).
- `--generate-json` (em `create` e `edit`) imprime o template aceito por
  `--from-json` — é a forma de checar quais chaves a sua versão suporta, em vez
  de deduzir
- **Não existe `workitem update`.** Usar `workitem edit` para editar campos (summary, assignee, labels, etc.)
- **Para atribuir responsável, use `@me` — não o e-mail.**
  `acli jira workitem edit --key "${PROJECT}-XXX" --assignee "@me"` funciona; com
  e-mail o comando responde `✗ Failure: … can't be edited: unexpected error,
  trace id: …`, que não nomeia campo nem causa. A razão é identidade: o
  `userEmail` da sessão não é necessariamente a conta Jira. Para **outra
  pessoa**, accountId via REST (`GET /rest/api/3/myself` ou
  `lookupJiraAccountId`) + `PUT /rest/api/3/issue/<KEY>` com
  `{"fields":{"assignee":{"accountId":"…"}}}` → 204.
  ⚠️ `lookupJiraAccountId` devolve **lista vazia** para e-mail errado, não erro.
  O comando pronto:

  ```bash
  set -a; . ~/.hermes/.env; set +a
  AID=$(curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
    "https://jrcbrasil.atlassian.net/rest/api/3/myself" | python3 -c 'import json,sys;print(json.load(sys.stdin)["accountId"])')
  curl -s -o /dev/null -w '%{http_code}\n' -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
    -X PUT -H "Content-Type: application/json" \
    -d "{\"fields\":{\"assignee\":{\"accountId\":\"$AID\"}}}" \
    "https://jrcbrasil.atlassian.net/rest/api/3/issue/${PROJECT}-XXX"   # espera 204
  ```
- `acli jira workitem create` retorna a key criada no output (ex.: `RS-605`, `SQ-32`)
- Comentários: usar `comment create` (subcomando), não `comment` direto — `--body-file` para multiline
- `--body-file` aceita ADF JSON nativamente — para comentários formatados via
  `acli`, usar ADF (`{ "version": 1, "type": "doc", ... }`). Markdown e Wiki
  Markup renderizam como texto puro **no `acli`**. **Alternativa preferida:**
  `mcp__atlassian__addCommentToJiraIssue(..., contentFormat: "markdown")` aceita
  markdown direto (Jira converte server-side) — escreve uma vez o markdown e
  reaproveita no body do PR. Ver `SKILL.md §close step 5`.

## Sub-issues

- Tipo: `--type "Subtarefa"`
- Vincular à issue pai: `acli jira workitem edit --key "${PROJECT}-YYY" --parent "${PROJECT}-XXX"`
- **Numa chamada só, pelo REST** (preferido com fixVersion ou várias subtarefas): `POST /rest/api/3/issue`
  com `parent: {"key": "${PROJECT}-XXX"}`, `issuetype: {"id": …}` do tipo Subtarefa (ids em
  `campos.md` §Os dois ids que o `POST /issue` exige), `summary`, `description` em ADF e
  `fixVersions`. Nasce vinculada: some a janela entre o `create` e o `edit --parent`, em que a
  subtarefa fica solta, e o `acli` que sai 0 em falha. Medido em 05/10/2026: 10 subtarefas, todas
  `201`, `parent` conferido na releitura.
- ⚠️ **A subtarefa herda a sprint da mãe, mas não a `fixVersion`.** Criadas sem o campo, 6
  subtarefas voltaram com `fixVersions: []` no `GET` enquanto a mãe tinha a versão, e com a sprint
  já herdada (05/10/2026). Ponha `fixVersions` no próprio `POST`, ou grave depois com
  `PUT /issue/<KEY>` (`204`), e confira pelo `GET` de `campos.md` §Conferir que gravou.
- Sub-issues **não** ganham branches próprias — commits vão na branch da issue pai
- Issue pai só fecha quando **todas** as sub-issues estiverem "Finished"
- Listar sub-issues: `acli jira workitem search --jql "parent = ${PROJECT}-XXX"`

## Vínculos entre issues (issue links)

Um defeito que bloqueia uma release, um cartão que se relaciona a um épico: o
vínculo é o que faz isso aparecer no board de quem planeja. Só existe via REST —
o `acli` não cria nem lê links.

```bash
set -a; . ~/.hermes/.env; set +a
J=https://jrcbrasil.atlassian.net/rest/api/3
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$J/issueLinkType"   # nomes disponiveis
```

No site jrcbrasil: `Blocks` (`is blocked by` / `blocks`), `Relates`, `Duplicate`,
`Cloners`, `Problem/Incident`, `Post-Incident Reviews`.

### 🔴 A direção é invertida em relação à intuição

**Quem executa o verbo `outward` é o `inwardIssue`.** Lendo o payload da esquerda
para a direita você monta o oposto do que queria — e o Jira aceita os dois, então
não há erro que denuncie.

```bash
# QUERO: "RS-850 blocks RS-844"  (o defeito bloqueia a release)
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -X POST -H 'Content-Type: application/json' \
  -d '{"type":{"name":"Blocks"},
       "inwardIssue":{"key":"RS-850"},
       "outwardIssue":{"key":"RS-844"}}' "$J/issueLink"       # 201
```

Invertendo — `inwardIssue=RS-844` / `outwardIssue=RS-850` — o Jira grava
**"RS-844 blocks RS-850"**, exatamente o contrário, e nada avisa (medido 2026-09-02).

### Confira a direção relendo pelo lado do ALVO

Mesma disciplina que a skill já exige para sprint e story points: escrever não é
prova de ter gravado o que se queria. Aqui a releitura tem de ser feita **pela
issue-alvo**, porque é o lado em que o erro fica visível:

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$J/issue/RS-844?fields=issuelinks" | python3 -c "
import json,sys
for l in json.load(sys.stdin)['fields'].get('issuelinks') or []:
    if 'outwardIssue' in l: print('RS-844', l['type']['outward'], l['outwardIssue']['key'])
    else:                   print('RS-844', l['type']['inward'],  l['inwardIssue']['key'])"
# esperado: RS-844 is blocked by RS-850
```

### Remover um link errado

`DELETE /issueLink/<id>`, com o id vindo da releitura acima. **Itere um id por
chamada** — passar a lista inteira de uma vez faz o `curl` montar uma URL só e
devolver `HTTP 000`, o que parece falha de rede e não de uso:

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$J/issue/RS-844?fields=issuelinks" | python3 -c "
import json,sys
for l in json.load(sys.stdin)['fields']['issuelinks']:
    if 'outwardIssue' in l and l['outwardIssue']['key'] in ('RS-850',): print(l['id'])" > /tmp/links.txt
while read -r id; do
  [ -n "$id" ] && curl -s -o /dev/null -w "delete $id -> %{http_code}\n" \
    -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -X DELETE "$J/issueLink/$id"     # espera 204
done < /tmp/links.txt
```

⚠️ Se você criou o link certo **antes** de apagar o errado, os dois coexistem e a
issue mostra a relação nos dois sentidos. Conte os links depois de limpar.
