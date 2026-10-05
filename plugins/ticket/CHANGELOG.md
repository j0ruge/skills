# Changelog — ticket

## [1.8.2] — 2026-10-05

### Por quê

Reparo autorizado das duas dívidas que as entradas 1.8.0 e 1.8.1 carregavam: o `argument-hint` no
topo do frontmatter (A4/G2) e a falta de eval de gatilho (F4).

O `argument-hint` **fica no topo, e deixa de ser dívida.** O Claude Code só lê esse campo ali (é o
hint do `/ticket` no autocomplete). Movido para `metadata`, o validador fica verde e a dica some. O
auditor da `skill-quality-audit` (desde a 0.5.0) já o classifica como INFO, custo aceito, porque o
`plugin.json` declara `platforms: ["claude-code"]`. O teste frio mostra o limite: copiada sozinha,
fora do plugin, a skill volta a dar AVISO A4. Por isso a decisão agora fica escrita na própria
skill, no campo `compatibility` da spec, e não só no manifesto.

### O quê

- `SKILL.md` frontmatter: `compatibility` declara Claude Code, explica o `argument-hint` e lista o
  que a skill exige (acli, credenciais Jira). O `argument-hint` não muda.
- `assets/trigger-evals.json` (novo): 20 consultas, 10 que devem disparar e 10 quase-acertos de
  outras skills do marketplace (TODO.md → issues do GitHub, release notes, GitHub Release, review
  de PR, deploy, sprint planning na agenda, mensagem de commit, card no Trello, issue em repo
  público, auditoria da própria skill), no formato do otimizador do `skill-creator`.
- `SKILL.md` §Referências: cita o eval set e quando usá-lo (antes de mudar a `description`). Sem
  isso o `assets/` ficava órfão (AVISO B1).
- Auditoria: antes 0 erro, 0 aviso, 6 INFO; depois 0 erro, 0 aviso, 5 INFO (F4 resolvido; A4 e G2
  seguem INFO por decisão). `SKILL.md` 19.474 → 19.784 chars, abaixo dos 20 mil. O eval set ainda
  não foi rodado com LLM: existe e é válido, mas a taxa de acerto não está medida.

## [1.8.1] — 2026-10-05

### Por quê

Abrindo dois cartões com subtarefas no EDS (EDS-53 e EDS-60), as subtarefas criadas com `parent`
herdaram a sprint da mãe, mas voltaram com `fixVersions: []` no `GET` REST, embora a mãe tivesse
a versão. A skill não avisava, e o `split` nem menciona o campo: o cartão sairia sem rótulo de
release sem ninguém notar. O conserto, um `PUT` por subtarefa (`204`) com releitura, funcionou.
Criar a subtarefa já com o campo, num `POST /issue` com `parent`, funcionou numa chamada só (10
subtarefas, todas `201`), sem a janela entre o `create` e o `edit --parent` do `acli`.

### O quê

- `references/workflow.md` §Sub-issues: o caminho REST numa chamada (`parent` + id do tipo
  Subtarefa + `fixVersions`), apontando para `campos.md` §Os dois ids, e o aviso de que a
  subtarefa herda a sprint mas não a `fixVersion`, com o conserto e a releitura.
- `SKILL.md`: só a versão. O arquivo está no teto de ~20 mil chars, e a roteadora do
  `workflow.md` já cita "ao criar sub-issues".
- Dívida pré-existente, não tratada aqui: `argument-hint` no topo do frontmatter (INFO A4/G2).

## [1.8.0] — 2026-10-04

### Por quê

Fechando o SBM-3 numa sessão sem o MCP atlassian, o fallback da skill era o `acli` — que sai 0
mesmo quando falha, então nem o comentário nem a transição tinham sensor no próprio comando. O
REST do Jira devolve código HTTP de verdade (`201` no comentário, `204` na transição) e foi o
caminho usado, com releitura batendo. E o cartão chegou ao `close` ainda em "Tarefas pendentes" e
sem responsável — o `close` não olhava isso, e fechar assim deixa o cartão sem dono na sprint.

### O quê

- `references/close.md` step 1: `GET ?fields=status,assignee`; `assignee` nulo → oferecer
  `--assignee "@me"`; status na categoria `new` → avisar que o cartão nunca foi iniciado.
- `references/close.md` step 5: fallback sem MCP pelo REST (`POST /issue/<KEY>/comment` com
  `{"body": <ADF>}`, espera `201`); o `acli comment create` fica como segunda opção.
- `references/close.md` step 6: transição por REST (`GET /transitions`, escolher o destino com
  categoria `done`, `POST` por id, espera `204`, releitura); SBM documentado (id `41`, direto de
  "Tarefas pendentes").
- `SKILL.md`: só trocas de texto nos steps 1, 5 e 6 do `close` (o arquivo está no teto de ~20 mil chars).
- Dívida pré-existente, não tratada aqui: `argument-hint` no topo do frontmatter (ERRO G2 / AVISO A4).

## [1.7.0] — 2026-10-02

### Por quê

Pedido "enriquece a descrição atual do SBM-2 com o que evoluímos aqui": a skill só tinha template
para a descrição de issue **nova**. O caminho óbvio, um `PUT` com `description` montada do zero,
substitui o campo inteiro e apaga o texto do autor — no SBM-2, dois relatórios colados.

### O quê

- `references/templates.md` §Enriquecer a descrição de uma issue existente: backup pelo `GET`,
  ADF novo = `original.content + rule + seção datada`, varredura de marks e estrutura no documento
  inteiro, `assert` do prefixo antes do `PUT`, `204` e releitura comparando o prefixo com o backup.
  Validado no SBM-2 em 02/10/2026 (6 → 22 nós, `original preservado: True`).
- `SKILL.md`: a roteadora do `templates.md` passa a citar esse caso.
- Dívida pré-existente, não tratada aqui: `argument-hint` no topo do frontmatter (ERRO G2 /
  AVISO A4 da auditoria; warning do `validate-versions`).

## [1.6.3] — 2026-10-01

### Por quê

O `SKILL.md` fechou a 1.6.2 com 19.999 chars, no limite de ~20 mil, e a próxima lição não caberia
sem estourar o orçamento. Aplicada a `skill-refactoring` (progressive disclosure), sem extrair
narrativa de workflow (o caso real da skill mostra que isso quebra o encadeamento) e sem tocar na
tabela de armadilhas.

### O quê

Três blocos que as references já traziam por extenso viraram ponteiro no `SKILL.md` (19.999 →
19.387 chars, 326 → 311 linhas):

- close step 5: o `curl` que relê o comentário fica em `references/close.md` step 5 (idêntico);
  no `SKILL.md` restam o endpoint e o critério (`body` objeto; `str` = ADF recusado).
- Erros → MCP atlassian: a migração do endpoint (`/v1/sse` → `/v1/mcp`, `authv2`) fica em
  `references/campos.md §Issue existente`, que já tinha a versão completa.
- Detecção de issue pela branch: o pseudo-código JavaScript vira uma frase com o mesmo regex.

Como reverter: `git revert` do commit desta versão.

## [1.6.2] — 2026-10-01

### Por quê

Na abertura do SBM-1 o projeto Jira SBM ainda não existia. O bootstrap da skill só sabia perguntar
key e board de um projeto existente, e o executor teve de descobrir sozinho o `POST /project`, o
template team-managed, o board criado junto e os ids de tipo por projeto. O board novo também só
tinha uma sprint `future`, e o item 3 de "Quando não aparece sprint ativa" oferecia apenas criar
sprint ou deixar no backlog.

### O quê

- `references/workflow.md` ganha `## Projeto novo`: confirmação com o dev, `POST /project` (Scrum
  ou Kanban, team-managed), board pela API agile, releitura do projeto para `id` e `issueTypes`
  (no SBM a subtarefa é `Subtask`, não `Subtarefa`).
- `SKILL.md` roteia o bootstrap para essa seção quando o projeto não existe no Jira.
- `references/campos.md`: sprint `future` existente vira terceira opção (id em número puro grava;
  releitura mostra `state: future`, medido no SBM-1).

## [1.6.1] — 2026-10-01

### Por quê

Na abertura do SQ-153 a fixVersion proposta (0.10.0) não existia no Jira. O B1 do `start` dizia só
"liste as existentes e proponha a próxima" e não tratava o caso de a próxima faltar — ao contrário do
close step 7, que manda parar e perguntar. O executor leu a subseção de criação da issue, não a tabela
de operações da §fixVersion, e remontou o `POST /version` por conta própria. Funcionou, mas por sorte:
a receita estava a uma seção de distância e nada apontava para ela.

### O que mudou

- `SKILL.md` B1: versão proposta inexistente → confirmar com o dev, criar por REST
  (`campos.md §fixVersion`), usar o `id` devolvido no `fixVersions` do POST.
- `references/campos.md §fixVersion`: parágrafo com o caso medido (0.10.0 → id 10110, releitura
  `['0.10.0']`).

## [1.6.0] — 2026-09-28

Progressive disclosure da skill `ticket` pela spec do agentskills.io, a partir da auditoria
`skill-quality-audit` v0.2.0. Nenhum fato, comando ou armadilha saiu: o que deixou o `SKILL.md`
foi para `references/`, e o que já existia lá virou apontador em vez de cópia.

### Por quê

- **C1 (ERRO):** o `SKILL.md` tinha 769 linhas e 34.461 chars — acima do teto de 500 linhas e
  do orçamento de ~5.000 tokens (20.000 chars) que a spec recomenda para o corpo.
- **A4:** `argument_description` e `user_invocable` eram campos de topo fora da spec. O Claude
  Code também não os lia: a doc de skills diz que o nome do campo tem de bater com a tabela, hífen
  incluído, e que campo desconhecido é ignorado sem erro. Os dois eram letra morta.
- **C3:** `references/workflow.md` tinha 468 linhas e nenhum sumário.
- **F1/F2 (info):** references citadas sem dizer quando ler, e nenhuma seção de armadilhas.

### O que mudou

- **Frontmatter:** `argument_description` virou `argument-hint: "start (open) | split | close | status"`,
  o campo real do Claude Code (dica no autocomplete do `/ticket:ticket`), que passa a funcionar
  agora. Ele segue fora da spec aberta, então o auditor ainda o aponta (A4) e um upload para o
  claude.ai o recusaria; fica porque o plugin é só `claude-code` (`platforms`), onde plugin skills
  aceitam todos os campos da tabela do Claude Code. `user_invocable: true` saiu: o
  `user-invocable` do Claude Code já vale `true` por padrão, então o comportamento é o mesmo. `metadata.version` estava em 1.5.0
  (defasado desde a 1.5.1) e foi alinhado em 1.6.0.
- **`SKILL.md` (769 → 323 linhas, 34.461 → 19.685 chars):** fica com a detecção de projeto, o
  roteamento, o esqueleto executável de cada comando (comando principal + regra de cada passo), as
  regras e uma seção nova **Armadilhas e tratamento de erros**, que junta numa tabela os sensores
  que mentem (exit 0 do `acli`, lag da JQL, `@me`, `commentBody`, `comment create`, `comment list`
  achatando ADF, flag `released`). As credenciais REST são carregadas uma vez, no topo, em vez de
  em cada bloco. Cada reference agora é citada com a condição de leitura.
- **`references/start.md` (novo, 297 linhas):** os sub-fluxos A e B e o "registrar sem começar"
  por extenso, como estavam no `SKILL.md`.
- **`references/close.md` (novo, 196 linhas):** os 11 passos do `close` por extenso.
- **`references/campos.md` (novo, 294 linhas, com sumário):** a metade de `workflow.md` sobre
  sprint, story points, `fixVersion` e a releitura, mais a criação por REST com `fixVersion` numa
  chamada e o conselho de montar o ADF num script gravado em arquivo (vindos do sub-fluxo B), e os
  arquivos de config do MCP (`~/.claude.json`/`.mcp.json`) que só estavam no tratamento de erros.
- **`references/workflow.md` (468 → 243 linhas):** fica com transições, branch base, tipos, gotchas
  do `acli`, sub-issues e vínculos; ganhou o comando pronto de atribuir por accountId, que estava
  no sub-fluxo A. Abaixo de 300 linhas, dispensa sumário.
- Citação entre references só pelo nome do arquivo, sem o prefixo `references/`, dizendo que o
  `SKILL.md` roteia o alvo.
- `description` não foi tocada.

**Auditor** (`audit_skill_quality.py --external off --no-changelog-required --desc-budget 0`):
antes 1 ERRO (C1) + 3 AVISOS (A4, C1 chars, C3); depois 0 ERRO + 1 AVISO (A4 do `argument-hint`,
mantido de propósito, ver acima).

**Como reverter:** `git revert` do commit que traz esta entrada.

## [1.5.1] — 2026-09-18

Duas correções de precisão vindas de um `close` real (SQ-133, projeto SQ), as
duas sobre o mesmo ponto cego: o fluxo descrevia o caminho certo com um detalhe
errado, e o detalhe só cobra no fim.

### O campo do MCP é `commentBody`, não `body`

O step 5 do `close` documentava a chamada com `body:`. O servidor recusa com
`MCP error -32602: Invalid arguments for tool addCommentToJiraIssue: Required at
commentBody` — e a validação roda **depois** de o corpo ter sido transmitido, de
modo que o engano custa reenviar o resumo de fechamento inteiro, que é a parte
cara da chamada. Corrigido no exemplo, com o porquê ao lado: o valor da linha não
é saber o nome, é saber que descobri-lo tarde tem preço.

### `close` depois de o PR já estar mergeado

Os steps 8-10 (commitar pendências, abrir PR, voltar à base) assumem que o
`close` é quem publica. Havia ressalva para o commit direto na base, mas não para
a forma mais comum — mergear e **depois** fechar —, em que não há pendência a
commitar, PR a abrir nem base para voltar, e o step 9 abriria um PR vazio de uma
branch já integrada.

Junto vem o efeito colateral que só aparece nessa ordem: com a base em checkout,
o **step 1 não detecta a issue** (o regex casa o nome da branch, e a branch é a
base). A key está no subject do commit de squash — `git log -1 --format='%s'` a
devolve —, e a nova ressalva manda conferir isso com o dev antes de pedir a key,
com a cautela de que o último commit pode ser de outro cartão.

- `description` não foi tocada.

## [1.5.0] — 2026-09-11

Quatro lições de um `close` real (RS-877, projeto RS). Três são sensores que
mentem de formas diferentes; a quarta é um passo que faltava no fluxo.

### `acli jira workitem comment` é um GRUPO, não um comando

`acli jira workitem comment --key ... --body-file ...` devolve
`✗ Error: unknown flag: --key`, que soa como flag errada e manda a investigação
para o lugar errado. O comando é **`comment create`**. A skill dizia "postar via
`acli --body-file`" sem nomear o subcomando; agora nomeia, com exemplo.

### 🔴 `acli comment list --json` achata o ADF para texto puro

O sensor óbvio para "o comentário ficou formatado?" é reler pelo `acli`. Ele
devolve o `body` como **string crua** mesmo quando o ADF foi armazenado
perfeitamente — e a conclusão natural ("o ADF não foi interpretado") é falsa.
Quase virou um defeito reportado que não existia: o REST mostrou o `body` como
objeto, com os 17 nós certos.

A skill já avisava que o **exit code** do `acli` não é sensor. Esta é a mesma
família por outra porta: a **leitura de volta** também não é. O veredito é o
`GET /rest/api/3/issue/<KEY>/comment`, e o comando pronto está no step 5 do
`close`.

### A tabela de transições descrevia convenção como se fosse restrição

A linha do RS dizia "duas transições (`Aprovação`, depois `Finished`)". Medido: a
partir de `Em andamento` existe `id=31 Itens concluídos → Finished`, que **pula a
Aprovação**. O caminho de duas etapas é o **processo do time**, não um limite do
board — e vale segui-lo mesmo assim, porque é o rastro que o time espera; o
atalho economiza uma chamada e apaga a etapa do histórico.

Junto, um detalhe que a Regra 1 implicava sem dizer: **o conjunto de transições
muda conforme o status atual**. De `Aprovação` aparece `id=6 DONE → Finished`,
que não existe a partir de `Em andamento`. Reaproveitar ids de uma leitura
anterior quebra.

### O `close` não perguntava `fixVersion`

O `start` pergunta sempre; o `close` fechava um ticket que foi a produção sem
rótulo de release — foi o que aconteceu na RS-877. Novo step 7 (os seguintes
renumerados): lê o campo, compara com as tags do repo, e trata o caso difícil
com cuidado — quando a versão **não existe** no Jira, para e pergunta, porque
criar `fixVersion` é ato de nível de projeto, não detalhe de fechamento.

## [1.5.0] — 2026-09-11

Quatro lições de um `close` real (RS-877, projeto RS). Três são sensores que
mentem de formas diferentes; a quarta é um passo que faltava no fluxo.

### `acli jira workitem comment` é um GRUPO, não um comando

`acli jira workitem comment --key ... --body-file ...` devolve
`✗ Error: unknown flag: --key`, que soa como flag errada e manda a investigação
para o lugar errado. O comando é **`comment create`**. A skill dizia "postar via
`acli --body-file`" sem nomear o subcomando; agora nomeia, com exemplo.

### 🔴 `acli comment list --json` achata o ADF para texto puro

O sensor óbvio para "o comentário ficou formatado?" é reler pelo `acli`. Ele
devolve o `body` como **string crua** mesmo quando o ADF foi armazenado
perfeitamente — e a conclusão natural ("o ADF não foi interpretado") é falsa.
Quase virou um defeito reportado que não existia: o REST mostrou o `body` como
objeto, com os 17 nós certos.

A skill já avisava que o **exit code** do `acli` não é sensor. Esta é a mesma
família por outra porta: a **leitura de volta** também não é. O veredito é o
`GET /rest/api/3/issue/<KEY>/comment`.

### A tabela de transições descrevia convenção como se fosse restrição

A linha do RS dizia "duas transições (`Aprovação`, depois `Finished`)". Medido: a
partir de `Em andamento` existe `id=31 Itens concluídos → Finished`, que **pula a
Aprovação**. O caminho de duas etapas é o **processo do time**, não um limite do
board — e vale segui-lo mesmo assim, porque é o rastro que o time espera; o
atalho economiza uma chamada e apaga a etapa do histórico.

Junto, um detalhe que a Regra 1 implicava sem dizer: **o conjunto de transições
muda conforme o status atual**. De `Aprovação` aparece `id=6 DONE → Finished`,
que não existe a partir de `Em andamento`. Reaproveitar ids de uma leitura
anterior quebra.

### O `close` não perguntava `fixVersion`

O `start` pergunta sempre; o `close` fechava um ticket que foi a produção sem
rótulo de release — foi o que aconteceu na RS-877. Novo step 7 (os seguintes
renumerados): lê o campo, compara com as tags do repo, e trata o caso difícil
com cuidado — quando a versão **não existe** no Jira, para e pergunta, porque
criar `fixVersion` é ato de nível de projeto, não detalhe de fechamento.

## [1.4.1] — 2026-09-10

Uma sessão real (abertura do **SQ-122** no projeto SQ) cobrou a conferência que a
1.4.0 tinha acabado de alinhar. Todas as lições abaixo foram **medidas**.

### Fixed

- **A JQL de conferência tem lag de indexação — e a 1.4.0 a tinha promovido a
  sensor** (`SKILL.md` sub-fluxos A/B, `references/workflow.md §Conferir que
  gravou`). Segundos após um `POST /issue` que nasceu com `customfield_10020: 405`,
  `key = SQ-122 AND sprint in openSprints()` devolveu `{"issues":[]}` enquanto
  `GET /issue/SQ-122?fields=customfield_10020` já mostrava `(405, "Formulário",
  active)`; a mesma JQL achou a issue segundos depois. Quem seguisse a regra
  *"se não bater, reportar a falha"* anunciaria ao dev um cartão no backlog que
  **estava** na sprint — o alarme falso que a seção existe para evitar, e pelo
  qual o `sprint list-workitems` já tinha sido descartado (por paginação). O
  veredito pós-criação passa a ser a **leitura do campo**; a JQL fica para
  conferência tardia, com o desempate `key = X` sozinha, que separa "não está na
  sprint" de "ainda não indexou". Três sensores desta skill já falharam de três
  jeitos diferentes — paginação, lag e silêncio —, e o texto agora diz isso.
- **`acli workitem search` que não casa nada imprime NADA** — sem linha, sem
  "0 results", sem erro, e ainda sai 0. Saída vazia é indistinguível de comando
  quebrado, então não vale como veredito. Registrado ao lado do `✗ Failure` que
  sai 0.

### Changed

- **Um `GET` do REST substitui o par de ferramentas na releitura.** A 1.2.0 tinha
  tornado a conferência *por campo* ("o sensor difere por campo") e o resultado
  prático era rodar `acli view` para dois campos e `curl` para o `fixVersion`. Um
  `GET /issue/<KEY>?fields=status,assignee,fixVersions,customfield_10016,customfield_10020`
  lê os cinco de uma vez e responde na hora — a assimetria continua verdadeira
  (o `acli` **não** lê `fixVersions`), só deixa de custar duas chamadas.

### Added

- **Os dois ids que o `POST /rest/api/3/issue` exige** (`references/workflow.md`).
  O corpo pede `project` e `issuetype` por **id**, e o `.jira-project` guarda a
  *key* — a receita de criação em uma chamada estava incompleta sem isso.
  `GET /project/<KEY>` e `GET /issue/createmeta/<KEY>/issuetypes` resolvem, com os
  valores medidos em SQ como exemplo (e o lembrete de confirmar: tipo de issue é
  configuração de projeto).
- **O envelope de `board list-sprints --json` é `{"sprints":[…]}`** — não lista
  nua, não `values`. Um parser escrito por analogia com outras APIs do Jira quebra
  com `'str' object has no attribute 'get'`, mensagem que não sugere o formato
  certo.
- **O construtor de ADF vai num arquivo, não num heredoc canalizado**
  (`references/templates.md`). Um typo (`])` onde cabia `]}`) faz o Python apontar
  para "linha N de stdin" e obriga a repassar o script inteiro; em arquivo, o
  conserto é uma linha. E heredoc **quotado** entrega UTF-8 intacto — tirar acento
  "por segurança" só custa a rodada de devolvê-los.

## [1.4.0] — 2026-09-03

Duas frentes: três lições **medidas** numa sessão real de 2026-09-02 (abriu 4 cartões
RS-850…RS-853, criou vínculos de bloqueio e comentou num quinto — o detalhe está em
`skills/ticket/CHANGELOG.md`) e o prompt audit da skill contra o modelo atual
(`/claude-api prompt-audit`, alvo Claude Fable 5.1), a última da rodada de 16 skills do
marketplace. Relatório e diff do audit ficaram fora do repo; aqui vai o quê e o porquê.

### Added

- **Vínculos entre issues (`references/workflow.md §Vínculos entre issues`).** Não havia nada
  sobre `issueLink`, e o campo só existe via REST. O detalhe que morde: em
  `POST /rest/api/3/issueLink` **quem executa o verbo `outward` é o `inwardIssue`** — ler o
  payload da esquerda para a direita monta o oposto do que se queria, e o Jira aceita os
  dois sentidos sem erro. Entram os tipos de link do site, o exemplo na direção certa, a
  releitura de conferência **pela issue-alvo** (mesma disciplina de sprint/story points) e
  a remoção de link errado, um id por chamada (a lista inteira numa URL devolve `HTTP 000`,
  que parece falha de rede).
- **Checagem de estrutura do ADF junto com a de marks (`references/templates.md §Antes de
  postar`).** A varredura da 1.3.0 só olhava `marks`; um helper de lista que repassa strings
  direto para `content` gera `{"type":"paragraph","content":["texto"]}`, sem mark nenhuma, e
  a varredura passava **limpa** — o Jira devolvia o mesmo 400 mudo. Agora todo item de
  `content` tem de ser nó com `type`, o relatório traz o caminho (`root.paragraph.content[1]`)
  e a receita é normalizar string→nó na entrada do helper.
- **Registrar cartão sem começar o trabalho (`SKILL.md §Registrar cartão SEM começar`).** O
  sub-fluxo B assumia que criar issue é o primeiro passo de programar (branch + "Em
  andamento"). Defeito de QA/code review registrado para o time priorizar não é isso: a
  branch nasce vazia e o status mente. A seção diz quando pular branch e transição
  (sprint, pontos, `fixVersion` e releitura continuam), e as Regras distinguem "abrir para
  já começar" de "registrar para priorizar".

### Changed — prompt audit

- **PII fora do corpo.** O e-mail pessoal e o nome de uma pessoa serviam de "prova" da
  regra `--assignee "@me"` em `SKILL.md` e `workflow.md`; a regra e o sintoma
  (`✗ Failure … trace id`) ficam, a identidade sai.
- **Changelog fora do workflow.** O blockquote "Correção de 2026-08-07: esta skill
  afirmava…" era um diff contra uma versão do prompt que o modelo nunca viu; fica só a
  instrução viva ("entre com a saída do comando").
- **Tabela de sensores alinhada.** `workflow.md §Sprint e Story Points` ainda listava
  `sprint list-workitems` como forma de conferir — o comando que a 1.2.0 tirou do papel de
  sensor por paginar. A célula aponta para o JQL `sprint in openSprints()`.
- **Arqueologia vira regra.** Treze trechos "medido no SQ-74 (2026-08-07) e de novo no
  SQ-107…" perderam ticket, projeto e história; ficou a regra com o mecanismo da falha e,
  onde havia, um único carimbo de verificação. As falhas são das ferramentas (`acli` sai 0,
  paginação, 400 mudo, `fixVersion` cego), não do modelo — por isso nenhuma regra saiu.
- **Tom normal nas Regras**: `SEMPRE`/`NUNCA`/`DEVE` em cinco linhas viram frase plana com a
  razão ao lado (o modelo atual sobre-aplica ênfase em caps).
- **`yarn lint` deixa de ser regra** numa skill multi-projeto ("rodar o lint do projeto, o
  mesmo que o CI roda"); `/usr/bin/acli` vira `acli`; fraseado migratório ("elimina o
  ritual", "segundo plano agora", "caminho antigo") reescrito como estado presente; nota do
  template de descrição corrigida (no sub-fluxo B a descrição vai em ADF, não texto puro);
  typo que invertia uma instrução ("não cheque" → "não chute").
- **Description 498 → 456 chars, 10 → 8 gatilhos** (saem `/ticket`, que é invocação por
  slash, e `open`, genérico demais). Estava a 2 chars do cap de 500 que derruba o gatilho em
  silêncio, e crescia a cada retrofit.

Registrados sem mudança: `~/.hermes/.env` ×4 como fonte das credenciais REST (convenção da
equipe; falha alto se faltar), "(Passo 04.1)"/"(Passo 05)", o trecho JS de detecção da
branch, e a leitura das duas references em todo comando.

## [1.3.0] — 2026-08-26

A skill já mandava montar ADF por script e já avisava que malformado é recusado
"sem dizer qual nó". O que faltava era o passo seguinte: **como descobrir qual
nó**. Sem isso, o aviso só antecipa a frustração — não a resolve.

Motivador concreto (RS-822): um helper de comentário recebeu `"strong"` como
**string** onde esperava lista. O loop iterou caractere a caractere e gerou
`{"type":"s"}`, `{"type":"t"}`, `{"type":"r"}`… O JSON ficou sintaticamente
válido, `json.tool` passou, e o Jira devolveu **400 sem nomear nada**. Montar por
script não impediu o erro — o script também erra.

### Added

- **`references/templates.md` ganha §"Antes de postar: valide o ADF"**: a lista
  dos 6 `marks` aceitos (`strong`, `em`, `code`, `link`, `strike`, `underline`)
  e uma varredura de ~10 linhas que percorre o documento e falha nomeando as
  marks inválidas. Troca um 400 cego por um diagnóstico exato.
- **Receita de conserto sem remontar**: quando a varredura acusa marks quebradas
  em caracteres soltos, juntar os caracteres de cada nó e substituir pela palavra
  resultante recupera o payload já montado.
- **Ponteiro para o suspeito seguinte**: se a varredura de marks vier limpa e o
  400 persistir, o problema costuma ser um `type` de nó fora da tabela (`bold` em
  vez de `strong`, `italic` em vez de `em`).

### Changed

- **`SKILL.md` deixa de tratar "monte por script" como suficiente.** O texto
  agora diz explicitamente que o script também erra e aponta para a varredura
  como passo obrigatório antes do POST.

## [1.2.0] — 2026-08-24

Rodada motivada por uma constatação desconfortável: das quatro armadilhas
medidas em 2026-08-07 (SQ-74) e registradas como pendência, **duas voltaram a
cobrar pedágio no SQ-107**, 17 dias depois, do mesmo jeito. Uma lição que não
entra na skill é uma lição que se paga de novo.

### Added

- **fixVersion ganha seção própria em `references/workflow.md`.** O campo não
  existia em lugar nenhum da skill, embora seja parte do que se decide ao abrir
  um cartão. É o campo com os piores sensores locais: `acli` não escreve **nem
  lê** (devolve `[]` sobre valor gravado), o MCP não confirma, e `updated` não
  bumpa. Tudo por REST, com tabela de operação → endpoint.
- **A flag `released` do Jira não é sensor de release.** No SQ-107 a `0.7.1`
  aparecia `unreleased` estando em produção desde 20/ago. Antes de repassar esse
  metadado ao dev, confira o artefato (`git branch -r --contains <sha>` e a
  versão no `package.json` de `origin/main`) e corrija o Jira.
- **`open`/`abrir` como alias de `start`** no roteamento. O comando não existia e
  é o que o dev digita — duas vezes na mesma sessão.
- **Criação por `POST /rest/api/3/issue` numa chamada** quando há fixVersion:
  `fixVersions` + sprint + pontos + `description` em ADF juntos. O
  `create --from-json` do `acli` não escreve `fixVersions`, então o caminho dele
  sempre exigiria um segundo passo que só existe via REST.

### Fixed

- **`--assignee` com e-mail falha; o certo é `@me`.** O `SKILL.md` mandava
  `--assignee "{username}"` e o `workflow.md` exemplificava com e-mail. O
  `userEmail` da sessão não é necessariamente a conta Jira, e o erro
  (`✗ Failure: … unexpected error, trace id: …`) não nomeia campo nem causa.
  Medido em 2026-08-07 e de novo em 2026-08-24. Para outra pessoa: accountId via
  REST.
- **`sprint list-workitems` sai do papel de sensor — entra JQL.** O step 6 vendia
  aquele comando como "confirmação independente"; ele pagina em ~30 itens e o
  cartão recém-criado cai fora da primeira página. Seguir a skill produzia
  exatamente o alarme falso que o passo existe para evitar. Medido no SQ-74 e no
  SQ-107 — nas duas vezes o cartão **estava** na sprint.
- **`acli` imprime `✗ Failure` e sai 0** — agora dito no topo dos gotchas.
  Cadeia `&&` e `$?` são decorativas; o sensor é a releitura do campo.
- **A criação de branch passa a medir a base em vez de confiar no `pull`.**
  `git pull … | tail` dentro de um `&&` devolve o exit do `tail`, então um pull
  que falhou deixa a cadeia seguir e a branch nasce de base não verificada, sem
  aviso. Poka-yoke: `git rev-list --left-right --count HEAD...origin/$BASE_BRANCH`
  deve dar `0	0`.
- **Releitura pós-criação passa a ser por campo**, porque o sensor é literalmente
  diferente para cada um: `acli view --json` serve para sprint/score e mente
  sobre fixVersion, que só o REST GET lê.

### Note

Todas as correções desta versão têm a mesma assinatura: **o passo de verificação
da própria skill é que falhava**, e falhava para o lado que parece seguro (exit
0, cadeia que continua, listagem que "não achou", campo que volta `[]`). Sensor
cego é pior que sensor ausente — ele produz confiança.

## [1.1.1] — 2026-08-07

### Fixed

- **A skill afirmava a branch base errada para o `sales_quote`/SQ.** O `SKILL.md`
  dizia, em dois pontos (exemplo do `.jira-project` e nota da tabela de
  variáveis), que o projeto usa `main`. Usa **`develop`** —
  `origin/HEAD → origin/develop` desde a feature 017, e o fluxo é
  `develop → staging → main`. **Consequência real:** branch nova nasceria da base
  errada e a PR iria para o alvo errado, e o sintoma só aparece no merge, quando
  já custa caro. Detectado na sessão de fechamento da SQ-73, quando a base teve
  de ser corrigida à mão.
- **A nota agora manda detectar, não trocar um chute por outro.** O texto antigo
  avisava "não assuma `develop`" e em seguida cravava `main` — o mesmo erro de
  forma. Passa a ser "não assuma **nem** `main` **nem** `develop`", com o comando
  de detecção como caminho único.

### Added

- **`references/workflow.md § Branch base`** — a seção não existia, e é por isso
  que a afirmação errada sobreviveu: não havia onde ela pudesse ser contradita.
  Traz o comando de detecção (`git symbolic-ref --short refs/remotes/origin/HEAD`),
  o fallback para quando o `origin/HEAD` não está resolvido localmente
  (`git remote set-head origin -a`), tabela de estado conhecido por repo, e a
  instrução de registrar a **saída do comando**, não o que parece razoável.
- **Recomendação de declarar `BASE_BRANCH` no `.jira-project`** em vez de
  redetectar a cada uso. É a única das três camadas que não depende de alguém
  ler a documentação.

## [1.1.0] — 2026-08-04

### Added

- **Issue nova nasce dentro da sprint, com score — sem depender do MCP.**
  `acli jira workitem create --from-json` aceita `additionalAttributes` com
  `customfield_*`, então sprint e story points podem ser gravados **na criação**.
  Validado em 2026-08-04 no projeto SQ (issue descartável criada com sprint
  `405` + 3 pontos, conferida e deletada). O `start` sub-fluxo B passa a usar
  esse caminho. **Por quê:** o fluxo antigo criava a issue "pelada" e tentava
  editar depois via MCP; quando o MCP não estava autenticado a edição falhava e
  **o cartão ficava no backlog sem sprint nem pontos** — o sintoma relatado.
- **Releitura obrigatória depois de escrever sprint/score** (novo step no
  sub-fluxo A e no B), com verificação independente por
  `acli jira sprint list-workitems --board $BOARD --sprint <ID>`. Uma escrita de
  custom field pode "dar ok" e não aplicar; sem reler, a skill reportava sucesso
  enquanto o cartão continuava no backlog.
- **Como descobrir os IDs dos custom fields**, em vez de confiar nos números:
  `acli jira workitem view <KEY> --fields "*all" --json` traz ~100 campos (o
  `--json` sem `--fields` traz só 5 e **nenhum** custom field — motivo pelo qual
  o `view` parecia "não ter" sprint/score). `10016`/`10020` são do site
  jrcbrasil, não constantes do Jira.
- **Fallbacks para "não acho a sprint ativa"** (`workflow.md §Quando não aparece
  sprint ativa`): `$BOARD` errado é a causa mais comum (`board search` /
  `board list-projects`); descoberta independente do board via JQL
  `sprint in openSprints()`; e o caso legítimo de board sem sprint aberta ou
  kanban — avisar o dev em vez de inventar uma sprint.
- **Story points viraram pergunta de primeira classe** no sub-fluxo B: se o dev
  não souber pontuar, a skill propõe uma estimativa justificada para ele
  confirmar. Antes era um "(opcional)" que se perdia no meio do fluxo.

### Changed

- **Endpoint do MCP atlassian: HTTP+SSE → Streamable HTTP.**
  `https://mcp.atlassian.com/v1/sse` foi descontinuado em **30/jun/2026**; a
  config correta é `claude mcp add --transport http atlassian
  https://mcp.atlassian.com/v1/mcp` (`{"type": "http", ...}` no JSON).
  Documentado em `SKILL.md §Tratamento de Erros` e no `workflow.md` como a
  **primeira** coisa a checar quando o servidor expõe só
  `authenticate`/`complete_authentication` — antes esse sintoma era tratado
  apenas como falta de login.
  Registrada também a diferença medida entre os endpoints (2026-08-04): só
  `https://mcp.atlassian.com/v1/mcp/authv2` responde com
  `WWW-Authenticate: Bearer resource_metadata="…"`, o discovery OAuth (RFC 9728)
  — é a variante a usar quando a autorização não completa no `/v1/mcp`.
- `acli` de referência: v1.3.14 → **v1.3.22** (versão em que `--from-json` /
  `--generate-json` foram validados).
- Caminhos das referências passaram de absolutos
  (`~/.claude/skills/ticket/references/…`) para **relativos** (`references/…`) —
  o absoluto só resolvia na máquina que tem o symlink local, quebrando para quem
  instala pelo marketplace.
- `description` reduzida de ~1.400 para 465 chars (teto do repo é 500). A
  descrição é a superfície de triggering; descrições longas são cortadas
  silenciosamente da lista `/skills` e a skill perde o gatilho. O histórico
  detalhado vive aqui no CHANGELOG, não na descrição.

### Fixed

- **Formato do valor de sprint estava errado na doc**: o exemplo mandava
  `{"customfield_10020": {"id": 471}}`; o valor correto é o **id como número
  puro** (`405`). Um objeto ali é rejeitado/ignorado — mais uma rota para o
  cartão terminar no backlog.
- **Corrigida a afirmação "o `acli` não escreve custom fields"**, que era verdade
  só para o `edit`. A assimetria real, medida na v1.3.22: `create --from-json`
  **aceita** `additionalAttributes`; `edit --from-json` rejeita com
  `json: unknown field "additionalAttributes"`. Também não existe comando de
  sprint que mova work items (`acli jira sprint` só faz
  create/update/view/delete/list-workitems) — para issue **existente** não há
  caminho sem MCP, e a skill agora diz isso ao dev em vez de fingir sucesso.

### Origin

Retrofit pedido após sessões em que a skill "jogava os cartões no backlog e não
conseguia definir os pontos", somado ao aviso de depreciação emitido pelo próprio
servidor MCP da Atlassian. As afirmações novas foram verificadas nesta sessão
contra o Jira de produção (boards 51/SQ e 10/RS) e contra os endpoints MCP.

## [1.0.1] — 2026-05-29

### Fixed

- **Correção do "Corolário" da v1.0.0 — `acli --status` casa pelo NOME DO
  STATUS DE DESTINO, não da transição.** A v1.0.0 documentou o **inverso**
  (que `acli --status "Concluído"` falharia e que o flag casava por nome de
  transição). Em uso real (fechamento de **SQ-42** e **SQ-43**, ambos partindo
  de `Em andamento`) o comportamento observado foi o oposto:
  `acli --status "Concluído"` **funciona**, enquanto
  `acli --status "Itens concluídos"` (o *nome da transição*, id `31`) **falha**
  com `No allowed transitions found for given status`. Isso bate com o próprio
  help do `acli` (`--status` = "Status to transition the work item"). Provável
  causa do engano na v1.0.0: a falha original do SQ-41 era em `"Aprovação"`/
  `"Finished"` — status que **não existem** no board SQ —, não por casamento de
  nome; o `--status "Concluído"` nunca tinha sido testado isolado a partir de
  `Em andamento`.
- **Por quê importa:** a guidance anterior mandava evitar um comando que
  funciona e depender desnecessariamente do MCP. Corrigido em `SKILL.md`,
  `references/workflow.md`, `plugin.json`, `marketplace.json` e `README.md`.
  O MCP `transitionJiraIssue(transition:{id})` segue documentado como
  alternativa robusta. A **Regra 1** (descobrir transições / caminhar passo a
  passo) permanece — o mesmo erro também ocorre a partir de um status-fonte
  inválido.

### Added

- Nota em `workflow.md §Sprint e Story Points via MCP`: numa sessão nova o
  servidor atlassian MCP pode expor só `authenticate`/`complete_authentication`
  (as tools de escrita não aparecem no ToolSearch). Chamar
  `mcp__atlassian__authenticate`, repassar a URL ao dev e prosseguir após
  autorizar; **story points/sprint ficam bloqueados até autenticar** (o `acli`
  não escreve custom fields), mas transição e comentário (ADF) seguem via `acli`.

### Origin

Sessão de fechamento de **SQ-42 + SQ-43** (sales_quote): com o MCP atlassian
não-autenticado, a transição foi feita por `acli` — a tentativa pelo *nome da
transição* (`"Itens concluídos"`, conforme a doc v1.0.0) falhou, e o *nome do
status* (`"Concluído"`) funcionou, desmentindo o corolário da v1.0.0.

## v1.0.0 — 2026-05-29

### Added

- **Empacotamento inicial** da skill `ticket` (antes apenas local em
  `~/.claude/skills/ticket/`) no marketplace, com `plugin.json`, este CHANGELOG,
  entrada em `marketplace.json` e linha no `README`. Capacidades existentes:
  comandos `/ticket start | split | close | status`, detecção de projeto
  por-repo via `.jira-project` (`PROJECT`/`BOARD`/`BRANCH_PREFIX`), criação de
  issues/sub-issues, branches, e fechamento com resumo auto-gerado. Prefere
  `acli` + MCP atlassian (markdown em comentários; custom fields como story
  points/sprint que o `acli` não escreve).
- **Lição 1 — transições são por-projeto, não universais.** A documentação
  cravava a sequência do RS (`Em andamento → Aprovação → Finished`) como se
  valesse para todos os boards. O board **SQ não tem `Aprovação`**: vai
  `Em andamento → Concluído` direto, via transição **id `31`** ("Itens
  concluídos"). Agora o `close` e o `workflow.md` mandam **descobrir** as
  transições com `getTransitionsForJiraIssue` e transicionar por **id**.
- **Corolário — `acli --status` casa pelo NOME DA TRANSIÇÃO, não do status.**
  No SQ a transição p/ "Concluído" chama-se "Itens concluídos" — então
  `acli --status "Concluído"` falha, mas `transitionJiraIssue(transition:{id:"31"})`
  funciona. Documentado como o caminho confiável quando o nome diverge.
- **Lição 2 — base de branch é por-projeto.** Novo campo opcional `BASE_BRANCH`
  no `.jira-project`, com **fallback que detecta o branch default do repo**
  (`git symbolic-ref --short refs/remotes/origin/HEAD`). Substituídas todas as
  referências cravadas a `develop` em `start`/`close` por `${BASE_BRANCH}`.
  ⚠️ Não assumir `develop` — `sales_quote`/SQ usa `main`.

### Why / Origin

Sessão de fechamento do ticket **SQ-41** (sales_quote): o `/ticket close`
tentou `acli --status "Aprovação"` e `"Finished"` e falhou 2× com
`"No allowed transitions found for given status"`, porque o board SQ não tem
essa etapa. A correção (descobrir transições por id + base de branch por-projeto)
foi aplicada à skill local; este empacotamento traz a skill para o marketplace
para ganhar versionamento e o fluxo do `retrofit-skill`.
