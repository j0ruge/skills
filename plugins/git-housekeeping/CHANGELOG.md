# Changelog — `git-housekeeping`

## [0.3.1] — 2026-10-25

### O `--only` da ref remote-tracking é o nome da branch

- **O quê:** no passo 3 do `SKILL.md`, a frase do `--only` diz que a ref remote-tracking vai pelo nome
  da branch, sem o `origin/` que o relatório mostra, e que esse `--only` leva a branch local e a ref
  juntas. O `matches()` do `apply_plan.py` compara o nome cru do item, que o plano grava sem o remoto;
  o prefixo só entra no rótulo impresso.
- **Por quê:** no pós-merge do PR #21 do dotp-remake (2026-10-25), o relatório mostrou
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

Nasceu de uma limpeza no `dotp-remake`: o `analyze.py` pôs 16 itens em `SAI` (9 branches locais, 6
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
