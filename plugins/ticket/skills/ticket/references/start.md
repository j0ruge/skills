# Comando `start` — os passos por extenso

> O SKILL.md traz o esqueleto do `start` e as regras; aqui está cada passo com o
> comando completo e a ressalva que o motivou. Placeholders (`${PROJECT}`,
> `$BOARD`, `${BRANCH_PREFIX}`, `${BASE_BRANCH}`) vêm do `.jira-project` (`SKILL.md`
> §Detecção de Projeto). Sprint, pontos e `fixVersion` em detalhe: `campos.md`;
> transições, branch base e vínculos: `workflow.md`; templates: `templates.md` —
> as três o SKILL.md roteia.

## Sumário

- [Sub-fluxo A: Issue existente](#sub-fluxo-a-issue-existente)
- [Sub-fluxo B: Nova issue](#sub-fluxo-b-nova-issue)
- [Registrar cartão SEM começar o trabalho](#registrar-cartão-sem-começar-o-trabalho)

## Sub-fluxo A: Issue existente

1. **Buscar dados da issue:**

   ```bash
   # Dados básicos (summary, status, assignee)
   acli jira workitem view ${PROJECT}-XXX

   # Sprint e story points (custom fields, não aparecem no view padrão)
   acli jira workitem view ${PROJECT}-XXX --fields "customfield_10016,customfield_10020" --json
   ```

   - `customfield_10016` = story points (número ou null)
   - `customfield_10020` = array de sprints (pegar a com `"state": "active"`)
   - Se o comando falhar (issue não encontrada), informar o dev e abortar
   - ⚠️ Esses IDs são **do site jrcbrasil**, não uma constante do Jira. Se vierem
     vazios num projeto novo, **descubra**: `acli jira workitem view <KEY> --fields "*all" --json`
     lista os ~100 campos (o `--json` sem `--fields` traz só 5 e **nenhum**
     custom field). A sprint é o array com `boardId`/`state`; story points é o
     número solto. Ver `campos.md` §Descobrir os IDs.

2. **Mostrar resumo ao dev:**

   ```text
   📋 ${PROJECT}-XXX — {summary}
   📊 Status: {status}
   👤 Responsável: {assignee ou "Nenhum"}
   🏃 Sprint: {sprint ou "Nenhuma"}
   🎯 Score: {story points ou "Nenhum"}
   ```

3. **Verificar responsável:**
   - Se assignee está vazio/nulo:
     - Perguntar ao dev: "Essa issue não tem responsável. Quer se atribuir como responsável?"
     - Se sim: `acli jira workitem edit --key "${PROJECT}-XXX" --assignee "@me"`
       ⚠️ **Use `@me`, não o e-mail.** O e-mail da sessão (`userEmail`) não é
       necessariamente a identidade da conta Jira — e quando não é, o `acli`
       responde `✗ Failure: ... can't be edited: unexpected error, trace id: …`,
       que não nomeia o campo nem a causa.
       Para atribuir a **outra pessoa**, o caminho é o accountId via REST —
       comando pronto em `workflow.md` §Gotchas do `acli` (o SKILL.md roteia).
     - Se não: continuar sem responsável
   - Se já tem assignee: mostrar e continuar

4. **Verificar sprint:**
   - Se a issue **não está em nenhuma sprint** (campo sprint vazio/nulo):
     - Perguntar ao dev: "Essa issue não está em nenhuma sprint. Quer adicionar à sprint atual ou informar outra?"
     - Se sim:
       1. Descobrir a sprint ativa: `acli jira board list-sprints --id $BOARD --state active --json`
          — a ativa é a de `"state": "active"`. **Não descarte uma sprint pelo
          `endDate` no passado**: times deixam a sprint correr meses além da data
          planejada e ela continua `active`. Se a lista vier vazia, ver
          `campos.md` §Quando não aparece sprint ativa.
       2. Extrair o `id` (pedir ao dev para escolher se houver mais de uma)
       3. Atribuir via MCP: `mcp__atlassian__editJiraIssue(issueIdOrKey: "${PROJECT}-XXX", fields: { "customfield_10020": SPRINT_ID })`
          — o valor é o **número puro** (`405`), não `{ "id": 405 }`.
          ⚠️ Para issue **já existente** este é o único caminho automatizado: o
          `acli` **não escreve custom fields no `edit`** (ver `SKILL.md`
          §Armadilhas). Se o MCP não estiver disponível, diga isso ao dev em vez de
          seguir como se tivesse funcionado.
     - Se não: continuar sem sprint (registrar que o dev optou por pular)
   - Se já tem sprint: mostrar qual é e continuar

5. **Verificar score (story points):**
   - Se story points está vazio/nulo/zero:
     - Perguntar ao dev: "Essa issue não tem score. Quer atribuir story points? (ex: 1, 2, 3, 5, 8, 13)"
     - **Não devolva a pergunta em branco.** Você acabou de ler o summary e a
       descrição da issue — proponha um número com uma justificativa de uma
       linha (escopo, arquivos/serviços afetados, se há migração ou teste
       novo) e deixe o dev confirmar ou corrigir. Ancorar a conversa numa
       estimativa é o que destrava a pontuação; pedir um número do nada é o
       que faz o campo ficar vazio.
     - Se sim: atribuir via MCP: `mcp__atlassian__editJiraIssue(issueIdOrKey: "${PROJECT}-XXX", fields: { "customfield_10016": N })`
       (mesma ressalva do passo 4 — `acli edit` não grava este campo)
     - Se não: continuar sem score
   - Se já tem story points: mostrar e continuar

6. **Confirmar que gravou (releitura obrigatória):**

   Uma escrita de custom field pode retornar "ok" e não aplicar — e o sintoma é
   silencioso: o cartão fica no backlog, fora da sprint, e ninguém percebe até a
   daily. Depois de mexer em sprint/score, **releia e compare**:

   ```bash
   set -a; . ~/.hermes/.env; set +a
   curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
     "https://jrcbrasil.atlassian.net/rest/api/3/issue/${PROJECT}-XXX?fields=status,assignee,fixVersions,customfield_10016,customfield_10020"
   ```

   Um `GET` só traz os cinco campos, e responde **na hora** — inclusive numa
   issue criada há um segundo. O `acli view --fields` também lê sprint e pontos,
   mas não lê `fixVersions`, então o REST evita alternar ferramenta por campo.

   ⚠️ **Não confira por JQL logo depois de criar.** `key = X AND sprint in
   openSprints()` tem **lag de indexação** e devolve vazio por alguns segundos
   com o campo já gravado (medido). Anunciar "ficou no backlog" com base nisso é
   o alarme falso que este passo existe para evitar. Mesma coisa, por outra
   causa, com `sprint list-workitems`, que pagina (~30 itens) e perde o cartão
   novo. Detalhe e desempate em `campos.md` §Conferir que gravou.

   ⚠️ **O exit code do `acli` não é sensor de nada.** Ele imprime `✗ Failure: …`
   e **sai 0** — cadeia `&&` e checagem de `$?` são decorativas aqui. E um
   `workitem search` que não casa nada não imprime **nada**: nem linha, nem
   "0 results", nem erro. O que diz a verdade é a releitura do campo.

   Se o valor não bateu com o que foi pedido, **avise o dev explicitamente**
   ("a sprint não foi aplicada — o cartão continua no backlog") em vez de
   reportar sucesso no resumo final.

7. **Verificar status e transicionar:**
   - Se não está "Em andamento": `acli jira workitem transition --key "${PROJECT}-XXX" --status "Em andamento"`
   - Se já está "Em andamento": pular

8. **Criar branch Git:**

   - Gerar nome: `${BRANCH_PREFIX}-XXX_descricao_curta` (snake_case, sem acentos, max ~50 chars, baseado no summary da issue)
   - Verificar que está em `${BASE_BRANCH}` e atualizado:

     ```bash
     git checkout ${BASE_BRANCH}
     git pull origin ${BASE_BRANCH}
     git checkout -b ${BRANCH_PREFIX}-XXX_descricao_curta
     # poka-yoke: a branch nasceu MESMO da base atual?
     git fetch origin -q
     git rev-list --left-right --count HEAD...origin/${BASE_BRANCH}   # espera `0	0`
     ```

   ⚠️ **Não canalize o `pull` para `tail` dentro de uma cadeia `&&`**: o exit
   status de um pipeline é o do **último** comando, então um pull que falhou
   (mudança não commitada + rebase configurado é o caso comum) deixa a cadeia
   seguir e a branch nasce de base não verificada, sem nada avisar. Por isso a
   verificação acima mede a base em vez de confiar no pull.

   **Árvore viva: worktree, não checkout.** Quando um serviço roda do checkout da
   base (uma unit com `WorkingDirectory` nele, um servidor de dev apontado para
   ele), o `checkout` acima troca o código que o próximo restart carrega, e o
   `pull` na base já é deploy. Confira (`systemctl --user show <unit> -p
   WorkingDirectory`; serviço de sistema, sem `--user`) ou pergunte ao dev, que também
   pode pedir a worktree. A
   branch nasce ao lado, e a árvore viva não se mexe:

   ```bash
   WT="../$(basename "$PWD")-${PROJECT}-XXX"
   git fetch origin
   git worktree add --no-track -b ${BRANCH_PREFIX}-XXX_descricao_curta "$WT" origin/${BASE_BRANCH}
   git -C "$WT" rev-list --left-right --count HEAD...origin/${BASE_BRANCH}   # espera `0	0`
   ```

   O `--no-track` é o que impede a branch de rastrear a base: criada de
   `origin/${BASE_BRANCH}` sem ele, `git -C "$WT" rev-parse --abbrev-ref '@{u}'`
   responde `origin/main` (medido em 05/10/2026 num repo descartável), e um
   `git push` ou `git pull` sem argumentos ali aponta para a base. O close faz
   `push -u` para a própria branch. Caso real: no EDS-65 (05/10/2026) o
   `estimates-os_mcp` servia o MCP da `main`; o trabalho foi em
   `../estimates-os_mcp-EDS-65`, e a `main` só andou no merge autorizado. O close
   remove a worktree (`close.md` step 10).

9. **Output:** Mostrar resumo final:

   ```text
   ✅ Issue: ${PROJECT}-XXX — {summary}
   🌿 Branch: ${BRANCH_PREFIX}-XXX_descricao_curta
   📋 Status: Em andamento
   👤 Responsável: {assignee}
   🔗 Sprint: {sprint ou "Nenhuma"}
   🎯 Score: {story points ou "Nenhum"}
   ```

## Sub-fluxo B: Nova issue

1. **Perguntar ao dev:**
   - Nome/summary da issue
   - Descrição (pode ser breve — será formatada no template)
   - Tipo: Tarefa, História, Bug (default: Tarefa)
   - **Story points** — perguntar sempre, não tratar como detalhe opcional que
     some no meio do fluxo: "Quantos pontos? (1, 2, 3, 5, 8, 13)". Se o dev não
     souber, ofereça uma estimativa sua com a justificativa (escopo/arquivos
     afetados) para ele confirmar ou corrigir — é mais fácil ajustar um número
     proposto do que produzir um do zero. Só siga sem score se ele disser que
     não quer pontuar.
   - Sprint: mostrar sprints ativas para escolha, ou usar sprint corrente. **Se o dev não informar sprint, perguntar explicitamente:** "Quer adicionar à sprint atual?" — não pular silenciosamente.
   - **fixVersion** (rótulo de release, ex.: `0.8.0`): perguntar sempre que o
     projeto versione releases. Liste o que existe e proponha o próximo número,
     em vez de pedir do nada — ver `campos.md` §fixVersion, que
     traz o detalhe que morde: **`acli` e MCP são cegos nesse campo**, e a flag
     `released` no Jira **não é sensor de release** (é metadado marcado à mão,
     que atrasa em relação ao mundo). Quem sabe se lançou é o repo:
     `origin/main` + a versão no `package.json`.

2. **Descobrir a sprint ativa (antes de criar):**

   ```bash
   acli jira board list-sprints --id $BOARD --state active --json
   ```

   Pegar o `id` da sprint com `"state": "active"` — **ignorando o `endDate`**,
   que frequentemente já passou sem a sprint ter sido fechada. Se houver mais de
   uma, perguntar ao dev; se vier vazio, ver `campos.md` §Quando não aparece sprint ativa.

3. **Criar issue no Jira — já com sprint e story points:**

   O caminho confiável é `--from-json` com `additionalAttributes`, que aceita
   custom fields **na criação**. Isso é o que impede o cartão de nascer no
   backlog: criar primeiro e tentar editar depois depende do MCP autenticado, e
   quando ele não está o cartão fica órfão.

   ```bash
   cat > /tmp/${PROJECT}-new.json <<'JSON'
   {
     "projectKey": "SQ",
     "type": "Tarefa",
     "summary": "{nome}",
     "description": { "version": 1, "type": "doc", "content": [
       { "type": "paragraph", "content": [ { "type": "text", "text": "{descrição}" } ] }
     ] },
     "additionalAttributes": {
       "customfield_10016": 3,
       "customfield_10020": 405
     }
   }
   JSON
   acli jira workitem create --from-json /tmp/${PROJECT}-new.json
   ```

   - `customfield_10016` = story points (número); `customfield_10020` = **id da
     sprint como número puro** (`405`, não `{"id": 405}`)
   - Omitir uma chave de `additionalAttributes` quando o dev não informou o valor
   - `description` aqui é **ADF**, não markdown (o `--from-json` não converte)
   - Capturar a key retornada (ex.: `RS-605` ou `SQ-32`)
   - Se a versão do `acli` não tiver `--from-json`, criar sem custom fields
     (`create` simples) e gravá-los via `mcp__atlassian__editJiraIssue`,
     avisando o dev que sprint/score dependem do MCP autenticado

   **Quando houver fixVersion, prefira o REST — ele faz tudo numa chamada.** O
   `--from-json` do `acli` não escreve `fixVersions`. O comando, os dois ids
   (`project`/`issuetype`) que o corpo exige, por que montar o ADF num script
   gravado em arquivo e a varredura de marks antes do POST estão em `campos.md`
   §Criar a issue numa chamada só (o SKILL.md roteia).

4. **Confirmar que a issue nasceu completa** — cada campo pelo sensor que o
   enxerga (é literalmente diferente por campo):

   ```bash
   # Um GET só: o REST lê os cinco campos, e o fixVersion SÓ ele lê
   # (o `acli view --json` devolve [] mesmo com o campo gravado).
   curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
     "https://jrcbrasil.atlassian.net/rest/api/3/issue/${PROJECT}-XXX?fields=status,assignee,fixVersions,customfield_10016,customfield_10020"
   ```

   ⚠️ **Não troque essa leitura por uma JQL aqui**: recém-criada, a issue ainda
   não está indexada, e `sprint in openSprints()` volta vazia com a sprint já
   gravada (`campos.md` §Conferir que gravou).

   Se algum campo não veio como pedido, dizer isso ao dev — o cartão está no
   backlog ou sem rótulo de release. Não reportar sucesso sem essa releitura.

5. **Criar branch Git:**

   - Gerar nome: `${BRANCH_PREFIX}-XXX_descricao_curta` (snake_case, sem acentos, max ~50 chars)
   - Verificar que está em `${BASE_BRANCH}` e atualizado:

     ```bash
     git checkout ${BASE_BRANCH}
     git pull origin ${BASE_BRANCH}
     git checkout -b ${BRANCH_PREFIX}-XXX_descricao_curta
     ```

6. **Transicionar issue:**

   ```bash
   acli jira workitem transition --key "${PROJECT}-XXX" --status "Em andamento"
   ```

7. **Output:** Mostrar resumo:

   ```text
   ✅ Issue criada: ${PROJECT}-XXX — {nome}
   🌿 Branch: ${BRANCH_PREFIX}-XXX_descricao_curta
   📋 Status: Em andamento
   🔗 Sprint: {sprint}
   🎯 Score: {story points ou "Nenhum"}
   ```

## Registrar cartão SEM começar o trabalho

O fluxo acima assume que criar a issue é o primeiro passo de programar: ele cria
branch e transiciona para "Em andamento". Existe um caso comum em que isso está
errado — **registrar trabalho que será agendado depois**: defeitos achados numa
rodada de QA ou de code review, dívida técnica levantada de passagem, itens que
saem de uma reunião.

Nesse caso, **pule os passos de branch e de transição**. O cartão nasce em
"Tarefas pendentes", que é onde quem planeja a sprint espera encontrá-lo. Criar
uma branch por defeito registrado enche o repositório de branches vazias, e
transicionar para "Em andamento" mente sobre o estado: ninguém está trabalhando
nele ainda.

O resto continua valendo — sprint, story points e `fixVersion` se aplicam
igualmente, e a releitura de confirmação também. Se forem vários cartões de uma
vez, o REST em lote é mais direto que o `acli` um a um (ver
`campos.md` §fixVersion), e vale ligá-los ao cartão que eles
bloqueiam (ver `workflow.md` §Vínculos entre issues).

Pergunte ao dev qual dos dois é o caso quando não estiver claro pelo pedido:
"abrir para já começar" e "registrar para o time priorizar" produzem cartões
diferentes.
