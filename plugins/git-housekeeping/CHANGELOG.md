# Changelog — `git-housekeeping`

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
