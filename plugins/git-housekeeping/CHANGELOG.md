# Changelog — `git-housekeeping`

## [0.8.0] — 2026-11-17

### As pastas de rascunho: um segundo fluxo, com prova e quarentena

Nasceu da limpeza de `~/.wt`, logo depois da 0.7.0. A pasta tinha 516 entradas, e só 15 eram
worktrees. As outras (handoffs, `tmp.*`, rascunhos de missão, estudos) ficaram de fora da skill e
foram limpas à mão, com scripts de sessão, num inventário, num cruzamento dos handoffs e em três
lotes aprovados um a um. O dono pediu que esse trabalho virasse parte da skill.

- **O quê:** `scripts/scratch.py` (as regras), `scratch_scan.py` (só lê: grava o plano e imprime
  SAI, SAI SE A LEITURA CONFIRMAR, NÃO PROVADO e FICA) e `scratch_apply.py`. O apply reconfere cada
  item e o move para `<raiz>/.housekeeping-lixeira/<data>/`, com um `desfazer:` por item. O
  `--purge` apaga os lotes velhos e é o único passo sem volta. O `SKILL.md` ganha a seção *Pastas
  de rascunho*, com o fluxo em seis passos. As regras e os casos ficam em
  `references/pastas-de-rascunho.md`.
- **Por quê, regra a regra** (cada uma é um caso da limpeza à mão):
  - **A prova é de conteúdo, não de nome nem de idade.** Do `plan-6a-scratch`, que parecia saída
    regenerável, 1117 dos 4823 arquivos não tinham cópia igual na extração oficial. Por isso existem
    o blob no histórico de um `--repo`, a mensagem de commit, o clone limpo e o `--igual`
    (byte a byte).
  - **A citação segura, e a cadeia também.** O julgamento dos handoffs pelo conteúdo deixou sair 7
    que outros, que ficavam, mandavam ler. Agora o texto de toda entrada que fica é fonte, até parar.
  - **O handoff que é a única descrição de uma pasta que fica, fica.** Eram 3.
  - **O handoff é lido pelo agente.** O script confere os shas, os PRs e os anexos e deixa o handoff
    em `review`. Se as pendências foram cumpridas é julgamento. O apply só o move com `--only`, e o
    passo 3 do fluxo manda ler o `HANDOFF.md` antes da confirmação.
  - **O baseline do retrofit sai só com o diff no histórico.** Um `tmp.*` com `aplicar.py` ao lado
    do `antes.json` era trabalho, e o `diff.txt` pode ser a única cópia de uma edição não publicada.
  - **Quarentena em vez de `rm`.** A pasta solta não tem o `desfazer` do git, e a skill promete um
    para tudo o que apaga. A decisão foi do dono.
  - **O apply reconfere o caminho e o tipo.** Duas pastas de PR que pareciam arquivos foram puladas
    pela guarda de tipo da limpeza à mão. Agora a guarda é do script, com o conteúdo, o processo e a
    citação de agora.
- **Achado no ensaio do scan sobre o `~/.wt` real** (só leitura, 403 entradas, de 89 a 128 s):
  - o `node_modules/` de um bundle extraído para estudo (102,8 MB, sem lockfile) saía como
    regenerável. Fora de um repo, ele agora pede o lockfile ao lado; `build/` e `dist/` não contam;
  - dois dos quatro `--repo` não tinham `origin/HEAD`, e a default caía no HEAD local, 269 commits
    atrás num deles. Agora vem a branch que o remoto anuncia;
  - o sha só de dígitos (3,7% dos shas de 7 caracteres, como o `1719887`) era ignorado. O handoff
    com um commit desses fora da default passaria para a leitura. Era também a causa de um teste
    intermitente.
- **Achado no veredito dos CLAIM do gate:** a prova pelo histórico usava todas as refs do remoto
  (`--remotes`). Um blob que só a ref de uma branch apagada no remoto alcançava contava como cópia,
  e o clone aninhado nessa branch, como limpo. O próximo `fetch --prune` levaria a única cópia. Agora
  só a branch viva prova (existe no `ls-remote`, com a ponta igual ou à frente da local).
- **Testes:** `tests/test_scratch.py`, com 36 testes, um por regra. Dos 31 primeiros, 28 falharam
  contra a 0.7.0; os outros 3 esperavam rc 2, que o python também dá para o script ausente. Por isso
  cada regra foi sabotada (15 sabotagens), e o teste dela ficou vermelho. O `gh` falso da
  `fixture.py` também responde ao `gh api` de issues e PRs. A suíte foi de 86 para 122.
- **Gatilho:** a `description` cita as pastas de rascunho, e o `assets/trigger-evals.json` ganhou 3
  casos positivos e 2 negativos (25 no total). O "meu disco C: tá cheio" continua negativo. O
  otimizador da `skill-creator` não rodou sobre eles: fica como sugestão.
- **Dívida que fica:** o smoke do Codex em `docs/codex/smokes.json` ainda é o da 0.1.0.

## [0.7.0] — 2026-11-17

### A `.godot/` de um projeto Godot é regenerável

Nasceu da limpeza dos worktrees de um projeto .NET com cliente Godot.

- **O quê:** o `regeneravel()` também aceita a pasta `.godot/` quando a pasta-mãe tem o
  `project.godot` (`PROJETO_GODOT`). Uma `.godot/` sem o projeto ao lado continua `sem outra
  cópia`. A armadilha dos ignorados, no `SKILL.md`, cita a regra nova.
- **Por quê:** 7 dos 10 worktrees que saíam listavam a `.godot/` do cliente em `sem outra cópia`
  (de 40 a 46 arquivos e de 11,0 a 12,0 MB cada uma). Ela é o cache de importação, que o Godot 4
  refaz ao abrir o projeto. Os únicos ignorados que se perdiam de fato, dois `.sdd/logs/`,
  apareciam ao lado dela, e foram copiados para fora antes do apagamento. É o mesmo padrão que a
  0.6.0 tirou com o `bin/` e o `obj/` do .NET.
- **Conferido antes de editar:** nos 4 worktrees que restavam com `.godot/`, o `project.godot`
  estava na pasta-mãe; depois da mudança, o `regeneravel()` devolve `True` para essa pasta e
  segue `False` para o `.cache/` do mesmo worktree, que só aquele projeto sabe regenerar.
- **Testes:** `GodotCacheTest` (`test_classify.py`: a `.godot/` com o `project.godot` ao lado, e
  a `.godot/` sem ele). O primeiro falhou contra os scripts da 0.6.0, e o segundo já passava: é a
  guarda da regra. A suíte foi de 84 para 86.
- **Dívida que fica:** o smoke do Codex em `docs/codex/smokes.json` ainda é o da 0.1.0.

## [0.6.0] — 2026-11-15

### `bin/` e `obj/` de projeto .NET são regeneráveis, e a pasta sem outra cópia diz o que guarda

Nasceu da limpeza de dois repositórios, depois do merge de um PR de docs.

- **O quê (1):** o `regeneravel()` também aceita `bin/` e `obj/` quando a pasta-mãe tem um
  arquivo de projeto .NET (`PROJETO_DOTNET`: `*.csproj`, `*.fsproj`, `*.vbproj`). Um `bin/` sem o
  projeto ao lado continua `sem outra cópia`, porque pode ser script de quem usa.
- **Por quê (1):** num projeto .NET, os três worktrees que saíam listavam de 8 a 12 `bin/` e
  `obj/` em `sem outra cópia`. O único ignorado que se perdia de fato, um `.sdd/logs/`, ficou
  enterrado no meio deles. No worktree que ficou, o critério acertou os 16 `bin/` e `obj/`.
- **O quê (2):** o `Item` do worktree ganha `lost_dirs`, com `[arquivos, KiB]` de cada pasta
  `sem outra cópia`, e o relatório mostra `.superpowers/ (44 arquivos, 816 KB)`, em MB de 1 MB
  para cima. O arquivo solto continua só com o nome. O passo 2 do `SKILL.md` manda dizer os dois
  números. O plano segue na versão 1: o campo é opcional, e o `apply_plan.py` lê o plano velho.
- **Por quê (2):** o relatório dizia só `sem outra cópia: .superpowers/`, e a limpeza tinha sido
  autorizada pensando num único rascunho daquela pasta. Um `find .superpowers -type f` à mão
  achou 44 arquivos: briefs, relatórios de revisão e o progresso de uma rodada inteira. Eles
  foram arquivados antes do apagamento. É a mesma checagem à mão que a 0.5.0 registrou.
- **Testes:** `DotnetBinObjTest` (`test_classify.py`: `bin/` e `obj/` com o `.csproj` ao lado, e
  `bin/` sem ele), um em `IgnoradosPorGrupoTest` (a contagem de uma pasta com subpasta) e dois em
  `test_analyze.py` (a linha do relatório, com singular e plural, e a troca para MB). Os cinco
  falharam contra os scripts da 0.5.2; a suíte foi de 79 para 84.
- **Dívida que fica:** o smoke do Codex em `docs/codex/smokes.json` ainda é o da 0.1.0.

## [0.5.2] — 2026-11-05

### Nomes de repositórios privados saem do texto

Nomes de repositórios privados saem do texto, também nas entradas antigas deste arquivo.
Onde a frase dependia do nome, ficou um termo genérico. As medições continuam valendo, sem identificar a origem. O comportamento não muda.

## [0.5.1] — 2026-11-03

### O passo 7 diz o que fazer com o item que o 1º plano não tinha

Nasceu da limpeza de um projeto depois do PR #166.

- **O quê:** o passo 7 (Provar) do `SKILL.md` grava a análise da prova num `--plan` novo, e diz
  que um item do `SAI` que o 1º plano não tinha vem do repo que andou entre as duas análises: o
  agente o mostra e pede uma confirmação nova, porque a dos passos 3 e 5 não o cobre. O 1º plano
  fica como o registro do que foi aprovado; sobrescrito pela prova, um `apply_plan.py` rodado de
  novo levaria junto o que ninguém aprovou.
- **Por quê:** a prova trouxe `SAI (2)`, `chore/todo-85-alvo-do-ataque` e
  `chore/retrofit-atualizar-regras`, que outra sessão mergeou (PRs #173 e #175)
  entre a 1ª análise e a prova. O passo 7 só previa "vazio, ou só com o que foi recusado", e os
  dois não eram recusa. Lidos como falha do apply, ou cobertos pela aprovação dada para os outros
  cinco ramos, eles sairiam sem ninguém tê-los visto.
- **Sem código:** o `analyze.py` não compara com o plano anterior; a comparação é do agente, pelos
  dois relatórios. Os testes não mudam.
- **Dívida que fica:** o smoke do Codex em `docs/codex/smokes.json` ainda é o da 0.1.0.

## [0.5.0] — 2026-11-02

### Os ignorados que vão junto saem em três grupos: sem outra cópia, igual no principal, regeneráveis

Nasceu da limpeza de um projeto depois dos PRs #150 a #152.

- **O quê:** o `Item` do worktree ganha `regen` e `copies`. Regenerável é o ignorado de nome
  conhecido (`REGENERAVEIS`: `__pycache__`, `node_modules`, `build`, `.pytest_cache`…), o
  `*.egg-info`, a pasta com `pyvenv.cfg` (um venv, qualquer que seja o nome) e o link. Igual no
  principal é o ignorado que o worktree principal guarda no mesmo caminho, byte a byte, com a
  pasta comparada só até `TETO_ARQUIVOS` (2.000) e `TETO_BYTES` (64 MiB). O relatório mostra
  `sem outra cópia: …; igual no principal: …; regeneráveis: …`, e o passo 2 do `SKILL.md` manda
  ler em voz alta só o primeiro grupo. O `ignored` não mudou: a recusa por ignorado novo do
  `apply_plan.py` segue igual.
- **Por quê:** o worktree `23d3` listava 16 ignorados num saco só. Entre eles
  estavam 11 caches ou venv (o `.venv-gui/` de 256 MB) e 3 mocks `.impeccable/*.png` iguais aos do
  checkout, e os rascunhos `.superpowers/sdd/` só existiam ali. Separar o que se perdia de fato
  custou três checagens à mão (`cmp` contra o checkout, `find .superpowers -type f`) antes da 1ª
  confirmação.
- **Testes:** `IgnoradosPorGrupoTest` (`test_classify.py`: os três grupos, o teto, a pasta com
  arquivo a mais) e dois em `test_analyze.py` (a linha do relatório e o worktree só com
  regeneráveis). Os novos falharam antes do código; a suíte foi de 74 para 79.
- **Dívida que fica:** o smoke do Codex em `docs/codex/smokes.json` ainda é o da 0.1.0.

## [0.4.0] — 2026-10-26

### O symlink ignorado sai marcado, e o worktree com um processo dentro fica

Nasceu da limpeza de um projeto, do `skills` e do `sdd_agents` depois do PR #115 do primeiro.

- **O symlink ignorado:**
  - **O quê:** o `Item` do worktree ganha `links` (nome → destino, lido com `os.readlink`), e o
    relatório mostra o link como `.venv → <destino> (link: só o link sai)`. O `SKILL.md` ganha a
    armadilha.
  - **Por quê:** os 5 worktrees listavam o `.venv` entre os "ignorados que vão
    junto", sem a barra final, e nada dizia que era link. Ele apontava para o `.venv` do checkout,
    onde o monitor do aluno rodava, e foi preciso conferir à mão com `readlink` antes de aprovar.
    Depois do apply, o `.venv/bin/python` do checkout respondeu (3.12.3) e o monitor seguiu de pé.
  - **Teste:** o `test_symlink_ignorado_sai_e_o_destino_fica` já passava antes do código e agora
    registra esse comportamento do git. O `test_symlink_ignorado_sai_marcado_como_link` cobre o
    relatório.
- **O worktree com um processo dentro:**
  - **O quê:**
    - o `proc_cwds()` lê o cwd de cada processo no `/proc`, sem contar o próprio;
    - o `_classify_worktree` mantém em FICA o worktree onde algum processo está, com o pid e o
      comando no motivo;
    - o `apply_plan` reclassifica com o mesmo código, então um processo que entrou depois do plano
      faz o apply recusar o worktree;
    - sem `/proc` (macOS, não testado), o plano grava `procs_checked: false` e o cabeçalho diz
      `processos nos worktrees: não conferido (sem /proc)`.
  - **Por quê:** o relatório do `sdd_agents` pôs em `SAI` dois worktrees irmãos
    (`sdd_agents-achados-dica-mais-rapida`, `sdd_agents-reincidencia`) que outra sessão podia estar
    usando. Antes, só o cwd do próprio `analyze` protegia um worktree. Num worktree descartável, a
    varredura do `/proc` achou um `sleep` com o cwd dentro.
  - **Limite medido:** o processo do Claude Code fica com o cwd onde foi aberto. Esta sessão continuou
    na pasta de abertura depois de muitos `cd ~/.wt/…` pelo Bash. No mesmo dia, a ponta de
    `sdd_agents-health-pula-catalogo` andou entre duas análises sem nenhum processo com o cwd lá
    dentro. A sessão que só entra pelo shell não segura o worktree.
  - **Testes:** `test_worktree_com_processo_dentro_fica`,
    `test_processo_que_entrou_depois_do_plano_segura_o_worktree`, `ProcessosTest` e
    `CabecalhoTest`. Os de processo pulam onde não há `/proc`. Com a varredura sabotada
    (`procs={}`), os 2 de processo ficam vermelhos.

## [0.3.1] — 2026-10-25

### O `--only` da ref remote-tracking é o nome da branch

- **O quê:** no passo 3 do `SKILL.md`, a frase do `--only` diz que a ref remote-tracking vai pelo nome
  da branch, sem o `origin/` que o relatório mostra, e que esse `--only` leva a branch local e a ref
  juntas. O `matches()` do `apply_plan.py` compara o nome cru do item, que o plano grava sem o remoto;
  o prefixo só entra no rótulo impresso.
- **Por quê:** no pós-merge do PR #21 (2026-10-25), o relatório mostrou
  `ref remote-tracking origin/plano-3-5-b`, e o passo 3 mandava usar "o nome que o relatório mostra".
  `apply_plan.py --scope local --only plano-3-5-b --only origin/plano-3-5-b --dry-run` saiu com rc 2
  (`--only fora do plano neste escopo: 'origin/plano-3-5-b'; o plano aceita: plano-3-5-b`), medido de
  novo na 0.3.0 com o mesmo plano. `--only plano-3-5-b --dry-run` listou os dois itens, e o apply
  apagou os dois. A recusa é segura e diz o nome aceito, mas quem lê o passo ao pé da letra perde uma
  chamada, e pode deixar a ref para trás achando que ela não foi aprovada.
- **Onde:** só no `SKILL.md`, com duas linhas a mais; nenhum script mudou.

## [0.3.0] — 2026-10-25

### O fast-forward publicado sai pelo reflog, e a upstream na default não faz da branch a default

Nasceu de uma limpeza no `j0ruge/skills`: quatro branches `retrofit-*`, criadas com
`git worktree add -b X <wt> origin/main` (a receita do `retrofit-skill`) e publicadas por
`push origin HEAD:main`, todas contidas na `origin/main`, ficaram em `FICA` com o motivo "branch
default do origin". Foram apagadas à mão, com a contenção provada antes de cada `branch -d`.

- **A upstream na default não conta como contraparte remota:** em `_classify_local_base`, a
  proteção era conferida com o nome local e com o da upstream, e a `main` da upstream casava com a
  default. Agora a branch que rastreia a default é julgada pelo próprio nome; as outras proteções
  (PR aberto, `housekeeping.protect`, workflow) continuam valendo para a upstream que não é a default.
- **A prova nova, só para a branch local, `_commits_made_here`:** quando a ponta é um commit da
  default (o caso "branch nunca usada, ou fast-forward sem PR"), o reflog da branch decide. Com pelo
  menos uma entrada `commit…` e todos os shas do reflog contidos na default, a branch sai, com a
  evidência `reflog` e o motivo "fast-forward na main: os N commit(s) feitos nesta branch (reflog)
  estão nela"; o worktree limpo dela sai junto. Sem reflog (desligado ou expirado), só com a criação,
  ou com um sha fora da default (um `reset` ou um rebase que abandonou commit), segue `NÃO PROVADO`.
  A branch remota não muda: ela não tem reflog.
- **No `SKILL.md`:** uma armadilha nova (a receita `worktree add -b X <wt> origin/main` e o reflog
  que separa os dois casos) e a linha da tabela *Como ler um "não provado"* com a exceção do reflog.
- **Testes:** `tests/test_fast_forward_publicado.py`, com cinco casos num repo de fixture: publicada
  com upstream na `main` e sem upstream (saem, o worktree junto), nova e apelido da `main` (nunca
  usadas, não a default), e o commit abandonado por `reset` (não prova). Os testes das publicadas e
  das nunca usadas foram vistos falhando antes do código (3 falhas, com o da `main` verde); o do
  commit abandonado entrou depois, para prender a guarda que nenhum caso prendia. Dos quatro mutantes das guardas novas, três foram mortos;
  o quarto (tirar o `not made` da condição) é equivalente, porque a função já devolve 0 sem commit
  feito, e o `not made` só poupa as chamadas de `is_ancestor`.

## [0.2.0] — 2026-10-24

### A aprovação parcial do plano, sem editar o JSON

Nasceu de uma limpeza: o `analyze.py` pôs 16 itens em `SAI` (9 branches locais, 6
remotas e 1 worktree, todos com merge provado), e o usuário aprovou só a branch local que a tarefa
pedia. O `apply_plan.py` apagava todo item `delete` do escopo, e a skill não tinha como aprovar
parte do plano.

- **O contorno, e a falha dele:** numa cópia do plano, `decision` passou a `keep` nos outros itens.
  O primeiro filtro usou o tipo `branch`, mas o gravado é `local-branch`, e o `--dry-run` respondeu
  `nada a apagar neste escopo` com rc 0, o mesmo de um plano vazio de verdade. Com o tipo certo, o
  dry-run mostrou só o item aprovado e o apply o apagou.
- **`--only <nome>`, repetível, no `apply_plan.py`:** restringe aos itens `delete` do escopo com
  esse nome, o do relatório (a branch, ou o caminho do worktree, comparado por `realpath`). No
  escopo local, o nome de uma branch pega também a ref remote-tracking dela. Os outros itens do
  escopo ficam, e uma linha diz quantos (`fora do --only: N item(s) deste escopo ficam`). As
  recusas de sempre continuam: a branch em uso num worktree que não foi escolhido é recusada.
- **Nome que não casa é uso inválido:** o `--only` que não acha item `delete` no escopo sai com rc 2
  antes de apagar qualquer coisa, com o nome recusado e os que o plano aceita.
- **No `SKILL.md`:** o passo 3 manda um `--only` por item aprovado, nos passos 4 e 6, com
  `--dry-run` antes, e nunca editar o plano à mão; a armadilha do rc 0 calado entrou na lista. O
  `metadata.version` dizia 0.1.0 desde a 0.1.1 e passa a 0.2.0, junto com o `plugin.json`.
- **Testes:** 3 novos em `test_apply_plan.py` (só o aprovado sai, local e remoto; nome fora do plano
  é rc 2 sem mudar nada; o `--dry-run` com `--only`), os 3 vistos falhando antes do código.

## [0.1.1] — 2026-10-22

Distribuição individual no catálogo Codex após instalação isolada, descoberta e smoke seguro de entrada dos workflows. Conteúdo canônico compartilhado com Claude Code/Cursor. Requisitos e limites em `docs/codex/compatibility.md` na raiz do marketplace.

## [0.1.0] — 2026-10-20

### A limpeza de branches mergeadas, com a prova no dado

Nasceu de uma limpeza manual: 4 branches locais e 4 remotas de um repo, cada uma conferida à mão
(ancestralidade, PR mergeado, ponta remota contida na main) antes do `-d` e do `push --delete`. A
skill troca a disciplina de quem roda por dois scripts que fazem a conferência sempre.

- **`scripts/analyze.py`** só lê. A prova de merge é o merge commit (a ponta fica fora da cadeia de
  primeiro pai da default) ou o PR mergeado na default com o mesmo `headRefOid`; o resto fica, com o
  motivo. Só a default conta como integração: mergeada só na `staging` fica.
- **`scripts/apply_plan.py`** só apaga o plano, e reclassifica cada item antes: o plano é a lista do
  que pode sair, não a prova. Local com `update-ref -d <ref> <sha>`; remoto num push com uma
  `--force-with-lease` por branch e sem `--atomic`. O pre-push roda.
- **Medido no git 2.43, e por isso no fluxo:** o `git worktree remove` apaga os ignorados
  (`.env.local`, `node_modules/`) com rc 0, e o relatório os lista pelo nome; o `%(upstream:track)`
  não diz `[gone]` enquanto a ref remote-tracking velha existe, e o "sumiu do remoto" sai do
  `ls-remote`; o `git remote get-url` aplica o `insteadOf`, e o owner/repo do gh sai da URL crua.
- **Testes:** 59 (`python3 -m unittest discover -s tests`), com remoto bare e gh falso. Quatro
  sabotagens vistas falhando: a regra da cadeia de primeiro pai, o `--no-optional-locks` da
  varredura (o teste só a pegou depois de pôr mtime velho num arquivo rastreado do worktree), o sha
  da lease e a regra do HEAD destacado fora da default.

### Revisão final, antes de publicar

Um revisor novo rodou 12 experimentos e 9 sabotagens em repos descartáveis. Os dois críticos vinham do
código do plano, e nenhum teste os via porque a fixture isola a config global do usuário
(`GIT_CONFIG_GLOBAL=/dev/null`): a classe `ConfigHostilTest` põe a config no próprio clone.

- **`fetch.prune`/`fetch.pruneTags` na config:** o `git fetch` do analyze apagava em silêncio a ref
  órfã (o único ponteiro para commits) e as tags locais. Agora `--no-prune --no-prune-tags
  --no-auto-maintenance`.
- **`status.showUntrackedFiles=no`:** o arquivo não rastreado sumia sem volta e os ignorados
  apareciam como "nenhum". Agora `--untracked-files=normal --ignore-submodules=none`.
- **Sem `gh`, a proteção por PR aberto sumia:** agora nenhuma branch remota sai sem `gh` (vira não
  provado); a local mergeada sai.
- **Ignorado novo depois do plano** (um `.env.production` que o usuário não viu) segura o worktree.
- **O worktree onde a sessão está** (o cwd) fica, mesmo com `--repo` apontando para o checkout
  principal.
- **Rebase, merge, bisect, cherry-pick ou revert parado** segura o worktree e a branch do rebase.
- **Item local editado para o escopo remoto** apagava a remota de mesmo nome sem classificá-la: o
  plano com escopo trocado sai com rc 2.

Cada correção tem um teste que falhou antes dela.

### Avaliação

Três cenários em fixture, cada um rodado com e sem a skill (1 execução por ponta, em 2026-10-20):
limpeza local com armadilhas, disco e worktrees, e varredura só leitura. O corretor
(`tests/check_eval.py`) olha o estado do repo e a resposta, não o que o agente diz ter feito.

| | Com a skill | Sem a skill |
|---|---|---|
| Expectativas | 30/30 | 30/30 |
| Tempo médio | 64,2 s | 93,4 s |
| Tokens médios | ~59,7 mil | ~59,3 mil |

- **Nenhuma expectativa discriminou.** Com o pedido explícito e a fixture pequena, a linha de base já
  evitou as armadilhas (squash que andou, `staging`, `deploy/prod`, worktree sujo, remoto intocado,
  segredo do `.env.local` não impresso). A diferença medida é de tempo (-31%): sem a skill, o agente
  refaz a conferência à mão a cada vez (`git cherry`, comparação de sha, dry-run do push).
- **Defeito achado pela execução com a skill, e corrigido:** as linhas `desfazer:` saíam na ordem de
  apagar (o worktree antes da branch), e desfazer exige a inversa. Agora saem do último apagado ao
  primeiro (`test_desfazer_sai_na_ordem_inversa`, vermelho antes da correção).
