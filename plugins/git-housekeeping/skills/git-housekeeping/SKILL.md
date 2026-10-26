---
name: git-housekeeping
description: "Safely deletes merged git branches, local and remote, and their worktrees. A read-only scan proves each merge by merge commit or by the merged PR's head sha; only the approved plan is deleted, with sha leases and two confirmations. Triggers — merged branches, branch cleanup, delete merged branches, stale worktrees, git housekeeping, prune branches."
metadata:
  version: 0.4.0
---

# git-housekeeping

Apaga as branches que já foram mergeadas, locais e no remoto, e os worktrees delas, sem perder
trabalho. Quem decide é o dado: um script que só lê prova cada merge, e outro só apaga o que o
usuário aprovou, provando de novo na hora.

## Armadilhas

O que faz a limpeza feita à mão perder trabalho, e que os scripts já tratam. Os quatro últimos itens
foram medidos no git 2.43.0 em 2026-10-20, num repo descartável.

- `git branch --merged` não vê squash merge, e `-D` numa branch squash-mergeada apaga junto o commit
  que entrou depois do merge.
- Apagar no remoto a branch que é gatilho de deploy (`on.push.branches`) ou head de PR aberto quebra
  o deploy ou fecha o PR.
- O plano editado à mão para aprovar só parte dele falha calado: um filtro que não casa (o tipo
  gravado é `local-branch`, não `branch`) dá `nada a apagar neste escopo` com rc 0, igual a um
  plano vazio (medido em 2026-10-24). O `--only` recusa o nome que não casa com rc 2.
- `git worktree remove`, sem `--force`, apaga os arquivos ignorados (`.env.local`, `node_modules/`)
  com rc 0, sem aviso.
- `git worktree add -b X <wt> origin/main` deixa `X` rastreando a `main`, e o fast-forward publicado
  (`push origin HEAD:main`) deixa a ponta num commit da `main`, como a de uma branch nunca usada.
  Quem os separa é o reflog local: com commits feitos nela, todos na default, a branch sai (evidência `reflog`). Medido em
  2026-10-25: quatro `retrofit-*` ficavam presas como se fossem a branch default.
- O `.venv` que é symlink para o do checkout aparece entre os ignorados sem a barra final, porque
  para o git o link é arquivo. O `git worktree remove` apaga só o link, e o destino fica: medido em
  2026-10-26 em 5 worktrees do magic_tutor, com um processo rodando do `.venv` do checkout. O
  relatório marca o link (`.venv → <destino> (link: só o link sai)`).
- `%(upstream:track)` não diz `[gone]` enquanto a ref remote-tracking velha existe. O "sumiu do
  remoto" só sai confiável do `git ls-remote`.
- `git remote get-url` aplica o `insteadOf`. O `owner/repo` do GitHub sai da URL crua
  (`git config --get remote.<r>.url`).
- `git push --porcelain` com pre-push que recusa não imprime linha de ref nenhuma. A ausência da
  linha é o sinal.
- A config do usuário muda o git "padrão": com `fetch.prune`/`fetch.pruneTags`, um `git fetch` comum
  apaga a ref órfã e as tags locais; com `status.showUntrackedFiles=no`, o `git status` não mostra o
  arquivo não rastreado, e o `git worktree remove` o apaga. Os scripts passam os flags explícitos
  (`--no-prune --no-prune-tags`, `--untracked-files=normal`).

## O que a limpeza libera de verdade

Diga ao usuário antes de prometer disco: **apagar uma branch libera quase nada.** A ref tem bytes, e
os objetos só saem com `gc` depois que o reflog expira. O espaço sai dos **worktrees** que vão
embora, com tudo o que tinham dentro. O relatório mostra os dois números separados.

## Os scripts

`SCRIPTS` é a pasta `scripts/` ao lado deste arquivo (o Claude Code mostra a pasta da skill ao
carregá-la, em "Base directory for this skill"). Precisam de Python 3.9+ (só stdlib; o código usa
`str.removeprefix`), git 2.31+ (`rev-parse --path-format=absolute`) e, para provar squash merge, o
`gh` autenticado. As regras de classificação moram em `housekeeping.py`, que as duas CLIs importam:
o `apply_plan.py` reclassifica com o mesmo código que gerou o plano.

| Script | O que faz | rc |
|---|---|---|
| `analyze.py --repo <repo> --remote origin --plan <arquivo>` | `git fetch` (sem prune), consulta o remoto e o gh, grava o plano e imprime o relatório. Não apaga nada. | 0 ok; 2 remoto que não responde, repo inválido ou plano dentro do repo |
| `analyze.py --scan <pasta>` | Uma linha por repo da pasta. Sem rede, sem plano, sem escrever nada. | 0 |
| `apply_plan.py --plan <arquivo> --scope local\|remote [--only <nome>]... [--dry-run]` | Reclassifica cada item `delete` do escopo com os fatos de agora e apaga o que ainda passa. O `--only` restringe aos nomes aprovados. | 0 tudo feito; 1 algo recusado; 2 plano inválido ou `--only` fora do plano |

## Fluxo (um repo)

1. **Analisar.** Grave o plano **fora do repo**: no Claude Code, no scratchpad da sessão; fora dele,
   numa pasta temporária. Dentro do repo, o plano sujaria a árvore, e o script recusa com rc 2.

   ```bash
   python3 "$SCRIPTS/analyze.py" --repo <repo> --remote origin --plan <scratchpad>/plano.json
   ```

   rc 2: mostre o erro e pare. Sem o remoto não há prova, e um plano com dado velho é pior que nenhum.

2. **Mostrar o relatório inteiro**: os três grupos (`SAI`, `NÃO PROVADO`, `FICA`) e o disco. Não
   resuma o que fica: é ali que o usuário vê o que a skill não vai apagar, e por quê. Do worktree que
   sai, leia em voz alta os ignorados que vão junto, sobretudo os marcados com ⚠ (`.env*`). Cite só
   o nome; nunca abra nem imprima o conteúdo.

3. **1ª confirmação: o local** (branches locais, worktrees e refs remote-tracking). Pergunte com a
   lista na frente do usuário. Se ele aprovar só parte, passe um `--only <nome>` por item aprovado
   nos passos 4 e 6, com o nome que o relatório mostra (a branch, ou o caminho do worktree), e rode
   antes com `--dry-run`. Nunca edite o plano à mão. A ref remote-tracking vai pelo nome da branch,
   sem o `origin/` do relatório, e esse `--only` leva a branch local e a ref juntas: o
   `--only origin/<b>` sai com rc 2 (medido em 2026-10-25).

4. **Apagar o local:**

   ```bash
   python3 "$SCRIPTS/apply_plan.py" --plan <scratchpad>/plano.json --scope local
   ```

5. **2ª confirmação: o remoto.** Mostre de novo a lista das branches remotas que saem, com o autor do
   último commit de cada uma: apagar no remoto mexe com quem usa o repo.

6. **Apagar o remoto:** o mesmo comando com `--scope remote`.

7. **Provar.** Rode o `analyze.py` de novo: o grupo `SAI` tem de vir vazio (ou só com o que foi
   recusado). Mostre o disco antes e depois e as linhas `desfazer:` que o `apply_plan.py` imprimiu.

Confirmação negada no passo 3: pare tudo. Negada no passo 5: o local fica feito e o remoto não.

**Autorização dada na própria mensagem.** "Pode apagar o local sem perguntar" é a confirmação do
passo 3: mostre o relatório e siga. Ela não cobre o passo 5. "Do remoto, só me mostra" quer dizer
parar no passo 5 com a lista.

## Quando o apply recusa

rc 1 é um resultado, e não um erro a contornar. Cada `recusado:` diz o que mudou desde o plano: a
ponta andou, o worktree sujou, apareceu PR aberto, o pre-push barrou. Mostre a linha ao usuário. Não
apague o item por outro caminho (`git branch -D`, `git push --delete`, `--force`, `--no-verify`):
a recusa existe porque a prova caiu, e o outro caminho apaga sem prova. Se o usuário quiser o item
fora mesmo assim, rode o `analyze.py` de novo e mostre o motivo novo antes.

## Como ler um "não provado"

| Motivo no relatório | O que quer dizer | O que o usuário pode fazer |
|---|---|---|
| `a ponta andou depois do merge: N commit(s) depois` | Há commit na branch que não está na default. | Abrir PR com o que sobrou, ou decidir que é descartável. |
| `mergeada na staging, não na main` | O código só está na branch de integração. | Esperar a promoção para a default. |
| `a ponta é um commit da main: branch nunca usada, ou fast-forward sem PR` | Não dá para distinguir branch recém-criada de merge fast-forward. Na branch local, o reflog distingue: com commits feitos nela, todos na main, ela sai; aqui chega a nunca usada, ou a que abandonou um commit. | Apagar à mão, se ele souber qual é. |
| `sem prova por PR (...)` | Sem `gh` (ou remoto fora do GitHub), o squash não se prova. | `gh auth login` e analisar de novo. |
| `o PR aberto não pode ser conferido (...)` | Sem `gh`, nenhuma branch remota sai, nem a mergeada: apagá-la fecharia um PR aberto. | `gh auth login` e analisar de novo; a local mergeada sai assim mesmo. |
| `esta ref é o único ponteiro local para esses commits` | O remoto apagou a branch sem merge, e o `fetch --prune` apagaria a última cópia. | Criar uma branch na ponta (`git branch <nome> <sha>`), se o trabalho importa. |

## Proteções

Ficam sempre: a branch default, a branch atual, `main`, `master`, `develop`, `staging`,
`production`, `release/*`, as citadas em `branches:` de algum workflow, as que são head ou base de
PR aberto (sem `gh` para conferir, nenhuma remota sai), a branch de um rebase em andamento, e as do
padrão local do usuário. Também fica o worktree onde a sessão está (o diretório atual), o que tem
rebase, merge, bisect, cherry-pick ou revert parado, o que ganhou arquivo ignorado novo depois do
plano, e o que tem um processo com o diretório atual lá dentro. Esse último sai do `/proc` (Linux e
WSL): pega a sessão aberta no worktree, um terminal ou um servidor. Não pega a sessão que só entrou
pelo shell (o processo dela fica onde foi aberto) nem o processo do lado Windows. Sem `/proc`
(macOS), o cabeçalho do relatório diz `processos nos worktrees: não conferido`. O padrão local:

```bash
git config --add housekeeping.protect 'deploy/*'
```

## Varredura de vários repos

Para "quais repos têm mais branch velha", rode `analyze.py --scan <pasta>` e mostre a tabela. Ela
usa o último fetch de cada repo (a data aparece na linha) e conta só o merge commit como prova. Daí
ofereça o fluxo completo no repo que o usuário escolher, um por vez.

## Desfazer

Cada item apagado deixa uma linha `desfazer:` (`git branch <b> <sha>`,
`git push origin <sha>:refs/heads/<b>`, `git worktree add <path> <b>`), impressas do último item
apagado ao primeiro. Rode-as nessa ordem: o worktree só volta depois da branch dele. Elas funcionam
enquanto o `gc` não levar os objetos, e por isso esta skill nunca roda `gc` nem `reflog expire`. O
worktree volta sem os ignorados: esses não têm cópia.

## Manutenção

`tests/` roda com `python3 -m unittest discover -s tests` (remoto bare e `gh` falso, sem rede).
`assets/trigger-evals.json` é o eval set de gatilho da description, no formato do otimizador da
`skill-creator`: rode-o quando a description mudar.
