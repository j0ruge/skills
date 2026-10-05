# Comando `close` — os passos por extenso

> O SKILL.md traz o esqueleto do `close` e as regras; aqui está cada passo com o
> comando completo e a ressalva que o motivou. Transições em `workflow.md`,
> templates do resumo e do ADF em `templates.md`, sensor do `fixVersion` em
> `campos.md` — as três o SKILL.md roteia.

1. **Detectar issue:**

   - Extrair `${PROJECT}-XXX` da branch corrente (regex `^(${BRANCH_PREFIX}-\d+)`)
   - Se não encontrar, pedir ao dev
   - **Conferir status de partida e responsável** — o `close` assume um cartão em andamento e com
     dono, e nem sempre é:

     ```bash
     set -a; . ~/.hermes/.env; set +a
     curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
       "https://jrcbrasil.atlassian.net/rest/api/3/issue/${PROJECT}-XXX?fields=status,assignee"
     ```

     `assignee` nulo → avisar e oferecer `acli jira workitem edit --key "${PROJECT}-XXX" --assignee "@me"`
     (com a releitura do A6). Status ainda na categoria `new` ("Tarefas pendentes") → dizer ao dev
     que o cartão nunca foi iniciado e confirmar que vai direto ao "done"; nem todo projeto tem
     transição direta (o SBM tem, id `41`; ver o step 6). Medido em 04/10/2026: o SBM-3 foi fechado
     com o trabalho em produção, ainda em "Tarefas pendentes" e sem responsável — fechar sem
     olhar deixaria o cartão sem dono no relatório da sprint.

2. **Verificar sub-issues:**

   ```bash
   acli jira workitem search --jql "parent = ${PROJECT}-XXX"
   ```

   - Se houver sub-issues não "Finished", alertar o dev e perguntar se quer continuar

3. **Auto-gerar resumo:**

   - Coletar dados:

     ```bash
     git log ${BASE_BRANCH}..HEAD --oneline
     git diff ${BASE_BRANCH}...HEAD --stat
     acli jira workitem view ${PROJECT}-XXX
     ```

   - Montar resumo usando template de `templates.md`:
     - **Visão Geral:** Extrair da descrição da issue no Jira
     - **Solução:** Sintetizar a partir dos commit messages
     - **Teste:** Inferir dos arquivos de teste modificados; se não houver, pedir ao dev

4. **Apresentar rascunho ao dev** — Mostrar o resumo gerado e pedir confirmação ou edições

5. **Comentar na issue — preferir MCP atlassian com markdown:**

   O MCP `mcp__atlassian__addCommentToJiraIssue` aceita markdown direto e converte
   para ADF server-side (multi-parágrafo, listas, tabelas, blocos de código e
   bold/itálico renderizam idêntico ao ADF — validado 2026-05-20). Sem ele, o
   caminho é montar ADF JSON e postar via `acli --body-file`.

   ```text
   mcp__atlassian__addCommentToJiraIssue(
     cloudId: "<cloud-id-da-jrcbrasil>",        # `getAccessibleAtlassianResources` se não souber
     issueIdOrKey: "${PROJECT}-XXX",
     commentBody: "<resumo em markdown — ver template em templates.md §Markdown>",
     contentFormat: "markdown"
   )
   ```

   ⚠️ **O campo é `commentBody`, não `body`** — e o engano custa o resumo
   inteiro. A validação roda no servidor **depois** de o corpo ter sido
   transmitido, então um `body:` responde
   `MCP error -32602: ... Required at commentBody` só no fim, e a correção é
   reenviar o comentário todo. Medido em 18/09/2026.

   **Fallback (sem MCP atlassian disponível):** montar ADF JSON manual — markdown
   e Wiki Markup **não** funcionam fora do MCP (renderizam como texto puro); ver
   `templates.md` §ADF (legado) para a estrutura e rode a varredura de marks antes.
   **Prefira postar pelo REST:** o código HTTP é um sensor de verdade (`201` =
   gravado; 400 = ADF recusado), ao contrário do `acli`, que sai 0 em falha.
   Validado em 04/10/2026 (SBM-3, `201` e releitura `dict 9`):

   ```bash
   set -a; . ~/.hermes/.env; set +a
   # /tmp/comment.json = {"body": <doc ADF>}  — o doc vai DENTRO de "body"
   curl -s -o /dev/null -w "%{http_code}\n" -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
     -H "Content-Type: application/json" -X POST --data @/tmp/comment.json \
     "https://jrcbrasil.atlassian.net/rest/api/3/issue/${PROJECT}-XXX/comment"
   # espera: 201
   ```

   Sem `curl`/credencial REST, o `acli` serve:

   ⚠️ **O comando é `comment create`, não `comment`.** `acli jira workitem comment`
   é um grupo com subcomandos (`create`/`list`/`update`/`delete`/`visibility`), e
   passar `--key` direto nele devolve `✗ Error: unknown flag: --key` — que soa
   como flag errada, não como subcomando faltando:

   ```bash
   acli jira workitem comment create --key "${PROJECT}-XXX" --body-file /tmp/comment.json
   ```

   🔴 **Confirme por REST, NUNCA por `acli comment list`.** O `acli` imprime
   `✓ Comment ... successfully added` e **sai 0 mesmo quando falha** (a regra geral
   do `SKILL.md` §Armadilhas), então o veredito tem de vir de uma releitura. E a
   releitura óbvia mente: `acli jira workitem comment list --json` **achata o ADF
   para texto puro** na exibição, então um comentário perfeitamente armazenado
   aparece como string crua — medido em 11/09/2026, e quase virou um defeito
   reportado que não existia. Só o REST mostra o formato **armazenado**:

   ```bash
   set -a; . ~/.hermes/.env; set +a
   curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
     "https://jrcbrasil.atlassian.net/rest/api/3/issue/${PROJECT}-XXX/comment?orderBy=-created&maxResults=1" \
     | python3 -c "import json,sys; b=json.load(sys.stdin)['comments'][-1]['body']; print(type(b).__name__, len(b.get('content',[])) if isinstance(b,dict) else b[:80])"
   # espera: dict <N>   ·   se vier `str`, o ADF NÃO foi aceito
   ```

6. **Transicionar até o status "done" — descobrir as transições, não cravar nomes:**

   A sequência é **específica do projeto** (ver `workflow.md`). Listar
   as transições disponíveis e caminhar até o status final:

   ```text
   mcp__atlassian__getTransitionsForJiraIssue(cloudId, issueIdOrKey: "${PROJECT}-XXX")
   # escolher a transição cujo to.name é o status "done" do projeto e aplicar por id:
   mcp__atlassian__transitionJiraIssue(cloudId, issueIdOrKey: "${PROJECT}-XXX", transition: { id: "<id>" })
   ```

   - **RS:** `Em andamento → Aprovação → Finished` (duas transições, por nome).
   - **SQ:** `Em andamento → Concluído` direto (**não há `Aprovação`**) —
     `acli --status "Concluído"` funciona (casa pelo nome do **status de
     destino**); alternativamente, MCP transição **id `31`** ("Itens concluídos").
   - **SBM** (team-managed): de "Tarefas pendentes" o `GET` listou transição para
     todos os status; `Concluído` = id `41` ("Itens concluídos"), direto.
   - **Sem MCP — REST por id** (preferido: `204` é sensor, o `acli` sai 0 em falha;
     validado em 04/10/2026 no SBM-3):

     ```bash
     set -a; . ~/.hermes/.env; set +a
     U="https://jrcbrasil.atlassian.net/rest/api/3/issue/${PROJECT}-XXX/transitions"
     curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$U" | python3 -c "import json,sys; [print(t['id'], t['name'], '->', t['to']['name'], t['to']['statusCategory']['key']) for t in json.load(sys.stdin)['transitions']]"
     # escolha o id cujo destino tem categoria `done` e aplique:
     curl -s -o /dev/null -w "%{http_code}\n" -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
       -H "Content-Type: application/json" -X POST --data '{"transition":{"id":"<id>"}}' "$U"
     # espera: 204 — e releia o status pelo GET do A6
     ```

   - Fallback `acli` (pelo nome do **status de destino**): `acli jira workitem transition --key "${PROJECT}-XXX" --status "<status-destino>"`.

7. **Conferir o `fixVersion` — o ticket saiu em qual release?**

   O `start` pergunta fixVersion; o `close` não perguntava, e o resultado é um
   ticket que foi a produção sem rótulo de release (aconteceu em 11/09/2026: a
   issue fechou com o trabalho servindo em produção e o campo vazio). Leia o
   campo e compare com a realidade do repo:

   ```bash
   set -a; . ~/.hermes/.env; set +a
   curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
     "https://jrcbrasil.atlassian.net/rest/api/3/issue/${PROJECT}-XXX?fields=fixVersions"
   git tag --sort=-v:refname | head -3      # o que de fato saiu
   ```

   - **Campo preenchido e coerente** → siga.
   - **Vazio, e a versão existe no projeto** → ofereça atribuí-la, dizendo qual.
   - **Vazio, e a versão NÃO existe no Jira** → **pare e pergunte.** Criar
     `fixVersion` é ato de nível de projeto: afeta o planejamento de release do
     time, não é detalhe de fechar um ticket. Diga qual versão falta e deixe a
     decisão com o dev.

   ⚠️ Não use a flag `released` do Jira como sensor de release — ela é metadado
   marcado à mão e atrasa (medido: versões já lançadas constavam
   `released=False`). Quem sabe se lançou é o repo: a tag em `origin/main`.

8. **Commitar mudanças pendentes:**

   - Verificar `git status` — se houver mudanças não commitadas (staged ou unstaged):
     - Mostrar as mudanças ao dev e perguntar se deve commitar
     - Incluir arquivos untracked relevantes (perguntar ao dev)
     - Gerar mensagem de commit no padrão Conventional Commits (`fix:`, `feat:`, etc.)
     - Incluir a key da issue no body do commit (ex.: `${PROJECT}-XXX`)
   - Após commitar, rodar o lint do projeto (o mesmo que o CI roda — ex.:
     `yarn lint` num repo Node)
     - Se houver erros de lint, corrigir e commitar o fix antes de prosseguir
   - Se não houver mudanças, pular para o próximo passo

9. **Criar Pull Request:**

   - Push da branch:

     ```bash
     git push -u origin ${BRANCH_PREFIX}-XXX_descricao_curta
     ```

   - Criar PR com `gh`. O body do PR usa **Markdown** (GitHub renderiza Markdown, igual ao MCP atlassian — se você usou markdown no step 5, pode reaproveitar o mesmo body aqui):

     ```bash
     gh pr create --base ${BASE_BRANCH} --title "${PROJECT}-XXX: {summary}" --body-file "/tmp/${PROJECT}-XXX-pr-body.md"
     ```

   - Se PR já existir para a branch, mostrar a URL existente (`gh pr view --web`)
   - O body do PR deve conter o mesmo conteúdo do resumo. Se você usou o caminho
     MCP no step 5, **é o mesmo markdown** — sem duplicação de trabalho.

10. **Voltar para `${BASE_BRANCH}`:**

   ```bash
   git checkout ${BASE_BRANCH}
   git pull origin ${BASE_BRANCH}
   ```

   > Se o dev pediu para **permanecer no branch atual** (fluxo direto no
   > `${BASE_BRANCH}`, sem feature branch e sem PR — como no commit direto em
   > `main`), pular os steps 9-10.

   > **Se o PR já foi mergeado**, pular os steps 8-10 inteiros. Fechar o cartão
   > *depois* de mergear é o caso comum — não a exceção —, e ali não há pendência
   > a commitar, PR a abrir nem base para voltar: você já está nela. Tentar o
   > step 9 abre um PR vazio de uma branch já integrada.
   >
   > ⚠️ E é justamente aí que o **step 1 falha**: a branch corrente é a base, e o
   > regex `^(${BRANCH_PREFIX}-\d+)` não casa nada. Antes de pedir a key ao dev,
   > olhe o commit de squash — ele carrega a key no subject:
   >
   > ```bash
   > git log -1 --format='%s'      # ex.: "SQ-133: o consultor vê ... (#172)"
   > ```
   >
   > Confirme com o dev o que encontrou, em vez de assumir: o último commit da
   > base pode ser de outro cartão se alguém mergeou no meio.

   > **Worktree (start A8, árvore viva):** não há checkout a voltar, e o `pull` na
   > árvore viva não faz parte do close: atualizar a base dela é deploy, decisão à
   > parte com o dev (no EDS-65, `merge --ff-only` e restart do serviço, autorizados
   > antes). Depois do merge, saia da worktree e remova-a:
   >
   > ```bash
   > git worktree remove ../<repo>-${PROJECT}-XXX   # recusa se houver mudança não commitada
   > ```
   >
   > A recusa é o sensor de que nada ficou para trás: veja o `git -C <worktree>
   > status` antes de pensar em `--force`. A branch fica, local e no origin. O step 1
   > detecta a issue de dentro da worktree; removida ela, a key está no subject do
   > commit, como acima.

11. **Output:**

   ```text
   ✅ Issue ${PROJECT}-XXX fechada
   📋 Status: Finished
   💬 Resumo postado como comentário
   🔀 PR criada: {URL}
   🌿 Voltou para ${BASE_BRANCH}
   ```
