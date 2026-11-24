# Pastas de rascunho: as regras, a leitura dos handoffs e a quarentena

O fluxo das pastas de rascunho (`scratch_scan.py` e `scratch_apply.py`) cuida do que não é worktree
numa pasta como `~/.wt`: handoffs, diretórios temporários de retrofits, rascunhos de missão, estudos
e dados soltos. Não há merge para provar. A prova é que nada se perde: cada arquivo da entrada tem
outra cópia ou se recria. Cada regra abaixo veio de um caso da limpeza de `~/.wt` em 2026-11-17, que
tinha 516 entradas, das quais só 15 eram worktrees.

## O que fica sem olhar o conteúdo

| Regra | Por quê |
|---|---|
| a quarentena (`.housekeeping-lixeira/`) | é onde o apply põe o que sai; esvazia-se com `--purge` |
| link | o `mv` move só o link; o destino não é desta raiz |
| é ou contém um `--repo` | o clone limpo de um repo em uso sairia pela regra do clone |
| worktree git (`.git` é arquivo) | quem prova o merge dele é o `analyze.py` |
| processo com o diretório atual dentro (`/proc`) | os mesmos limites do fluxo das branches: não vê o processo do lado Windows nem a sessão que só entrou pelo shell |
| recente: arquivo ou pasta mexido há menos de `--recent-days` (7 por padrão) | trabalho em andamento |
| citada por algo vivo | a citação é o único jeito de saber que alguém ainda conta com a pasta |

**A citação.** Vale o caminho (`<raiz>/<nome>`, como `.wt/untapped-draft-estudo/NOTAS.md`) para
qualquer nome, e o nome solto a partir de 12 caracteres (`NOME_MINIMO`), porque um nome curto casaria
com prosa comum. As fontes:

- cada `--repo`, em dois lugares: a árvore da default (`origin/HEAD`, ou a branch que o remoto
  anuncia) e a cópia de trabalho, com os não rastreados que o `.gitignore` não esconde;
- o `~/.claude/CLAUDE.md`, os `~/.claude/plans/` e as `~/.claude/projects/*/memory/` (desligue com
  `--sem-citas-padrao`), e cada `--cite`;
- o texto (`.md`, `.txt`, `.json`, `.yaml`, `.yml`, `.toml`) de toda entrada que fica, por qualquer
  motivo.

**A cadeia.** A última fonte faz a citação passar adiante. O handoff que fica e diz "continua o
`handoff-X`" segura o X, e a conta se repete até parar. Em 2026-11-17, o julgamento de cada handoff
pelo conteúdo deixou sair 7 handoffs que outros, que ficavam, mandavam ler.

**A única descrição.** O handoff que é o único texto que cita uma pasta que fica também fica. Sem ele,
ninguém sabe mais o que a pasta guarda. Três dos handoffs de 2026-11-17 eram a única identificação de
outra pasta.

## O que sai, e a prova de cada um

A pasta sai quando nada dentro dela fica sem prova. Sobrando algum arquivo sem prova, ela fica em NÃO
PROVADO, e o que dentro dela sai sozinho (o regenerável, o clone limpo, a cópia igual) vira um item
`sub`.

| Prova | Regra |
|---|---|
| vazio | pasta sem arquivo, ou arquivo de 0 bytes |
| no histórico de `<repo>` | o blob do arquivo é alcançável por uma branch viva de um `--repo` (`git rev-list --objects`) |
| mensagem de commit de `<repo>` | o texto do arquivo é a mensagem inteira de um commit de uma branch viva, sem espaço no fim das linhas |
| regenerável | a regra do `regeneravel()` dos worktrees, com duas exceções fora de um repo: `build/`, `dist/`, `htmlcov/` e `.coverage` não contam, porque nenhum `.gitignore` nem projeto os declara; e o `node_modules/` só conta com o lockfile na pasta-mãe |
| clone limpo | `status --porcelain --untracked-files=all --ignored` vazio (o ignorado, só regenerável), sem stash, e o HEAD e as branches contidos nas branches vivas do clone |
| igual em `<destino>` | com `--igual ORIGEM=DESTINO`, cada arquivo da ORIGEM tem cópia igual byte a byte no DESTINO, no mesmo caminho |
| baseline do retrofit | a pasta só tem `antes.json`, `depois.json` e `diff.txt`, e as linhas acrescentadas do `diff.txt` (até 6, as mais longas) estão no histórico de uma branch viva de um `--repo` (`git log -S`) |

**A branch viva.** É a ref remote-tracking cuja branch existe no remoto agora, pelo `ls-remote`, com
a ponta igual à local ou à frente dela. A ref de uma branch apagada no remoto não prova cópia: o
próximo `git fetch --prune` a leva, e o que só ela alcança vai junto. É o mesmo caso do "único
ponteiro local" do fluxo das branches. Sem resposta do remoto, só a default prova.

A ref cuja ponta remota o repo ainda não tem também não prova: o remoto andou depois do último fetch,
e sem o commit não há como saber se ele avançou ou reescreveu. Ela não some calada. O cabeçalho do
relatório a nomeia numa linha `aviso:`, com o `git fetch` a rodar, e o clone aninhado diz o mesmo
no motivo, em vez de "nenhuma branch do clone existe mais no remoto". Medido em 2026-11-24: outra
sessão empurrou entre o fetch e o scan, a única ref viva do repo caiu, e os 551 arquivos de uma
exportação, todos no histórico (um `LICENSE` com o mesmo blob da `origin/main`), saíram sem prova.

Os casos de 2026-11-17 por trás das regras que não são óbvias:

- **O nome não prova nada.** Do `plan-6a-scratch`, uma saída de extração que parecia se refazer pelo
  comando, 1117 dos 4823 arquivos (306 MB) não tinham cópia igual na extração oficial. O `--igual`
  existe para fazer essa conta em vez de supor.
- **O `node_modules/` de um bundle extraído para estudo** (102,8 MB) tinha `package.json` e nenhum
  lockfile. O `npm` não o refaz igual.
- **O baseline com arquivo a mais fica.** Um `tmp.*` com `aplicar.py` e `SKILL.simulado.md` ao lado
  do `antes.json` era trabalho, e não saída do auditor. O `diff.txt` também pode ser a única cópia
  de uma edição que não foi publicada, e por isso o diff precisa estar no histórico. Sem `diff.txt`,
  o retrofit parou antes do gate, e o `antes.json` se refaz.
- **O clone aninhado limpo sai sozinho.** Três clones do kit no `scratch/` de dois handoffs (~100 MB;
  os `.git` tinham 33, 32 e 34 MB) tinham tudo no remoto. O resto do handoff seguiu para a leitura.

## O handoff: SAI SE A LEITURA CONFIRMAR

O script confere o que é mecânico:

- **os shas citados** estão na default de algum `--repo`. O token que mistura letra e dígito e não
  existe em nenhum `--repo` segura o handoff. O token só de dígitos (`1719887`) ou só de letras só
  conta se resolver como commit; sem resolver, é número (`20261117`) ou palavra;
- **os PRs citados** (`#N`, `PR N`, a URL, `dono/repo#N`) estão fechados, pelo `gh api` do repo do
  handoff. O repo vem do nome `handoff-<repo>-<AAAA-MM-DD>`, comparado com o nome do `--repo` ou o da
  pasta-mãe dele. O PR aberto segura o handoff. A issue aberta não segura: o trabalho segue no tracker,
  e o motivo a menciona. Sem `gh`, nenhum `#N` se confere, e o handoff fica;
- **cada anexo além do `HANDOFF.md`** tem uma prova da tabela acima.

Passando tudo, o handoff vai para **SAI SE A LEITURA CONFIRMAR**. Se as pendências foram cumpridas é
julgamento, e o script não finge prová-lo. Antes de pedir a confirmação, leia o `HANDOFF.md` de cada
um:

1. Ache o que ficou por fazer: as seções de pendências, próximos passos e o que falta, as caixas `[ ]`
   e frases como "não fiz", "fica para" e "depois".
2. Para cada pendência, procure onde ela vive agora: um commit ou PR que a fez, uma linha do `TODO.md`
   ou uma issue que a registra. A evidência do item no relatório lista os shas e os PRs já conferidos.
3. A pendência que só existe no handoff o segura. Não passe o `--only` dele, e diga ao usuário qual é
   a pendência e onde ela poderia ser registrada.
4. Mostre, por handoff, o veredito da leitura e a frase do `HANDOFF.md` que o sustenta. A confirmação
   do usuário vale para essa lista.

## Como ler um NÃO PROVADO

| Motivo | O que o usuário pode fazer |
|---|---|
| `N arquivo(s) sem prova de outra cópia (... KB): ...` | Abrir e decidir. Se o conteúdo tem cópia num lugar que o scan não lê, passar `--repo` ou `--igual` e rodar de novo. |
| `N de M arquivos de <x> sem cópia igual em <destino>` | Refazer a cópia, ou decidir que os que faltam são descartáveis. |
| `clone <x>: árvore suja` / `commit(s) fora das refs do remoto` / `tem stash` | Publicar ou descartar o que só existe no clone. |
| `clone <x>: o remoto andou depois do último fetch do clone (...)` | `git fetch` no clone e rodar o scan de novo. |
| `sha X fora da default de <repo>` | O commit não está na default: está numa branch, ou o `--repo` precisa de um `git fetch`. |
| `sha X não existe em nenhum --repo` | O handoff é de um repo que não foi passado. Passe-o com `--repo`. |
| `PR #N aberto` | Esperar o merge. |
| `sem gh para conferir #N` | `gh auth login` e rodar de novo. |
| `sem sha nem PR que provem o merge` | Ler o handoff; se o trabalho acabou, apagar é decisão do usuário, fora desta skill. |
| `só K de N linhas do diff estão no histórico` | A edição do retrofit não foi publicada inteira: o `diff.txt` pode ser a única cópia. |

Um item NÃO PROVADO nunca sai pelo apply: o `--only` com o nome dele sai com rc 2.

## Quarentena, desfazer e purge

- O apply move cada item para `<raiz>/.housekeeping-lixeira/<AAAAMMDD-HHMMSS>/itens/<nome>` e grava
  `lote.json` com a origem, o destino e o motivo de cada um. É um rename no mesmo disco: instantâneo, e
  o disco não libera nada.
- Cada item movido imprime `desfazer: mv -n -T <destino> <origem>`, do último ao primeiro. O `-T` é do
  GNU mv. No macOS, use `mv -n <destino> <origem>` depois de conferir que a origem não existe, porque
  sem o `-T` uma pasta recriada no lugar recebe o item dentro dela.
- `scratch_apply.py --purge --root <raiz> --older-than <dias>` apaga os lotes mais velhos que isso,
  pela data no nome do lote. É o único passo sem volta. Rode antes com `--dry-run`, mostre a lista e
  peça uma confirmação só para ele.

## Limites e custo

- O scan não faz `git fetch`. A prova usa as refs locais das branches vivas, e um commit publicado
  depois do último fetch não conta. Rode o `analyze.py` de cada `--repo` antes, ou um `git fetch`.
  O remoto que anda entre o fetch e o scan (outra sessão empurrando) derruba as refs dele, e a linha
  `aviso:` do cabeçalho diz quais.
- Uma citação que mora fora das fontes não segura nada: num repo que não foi passado, no lado Windows
  ou em outra máquina. Passe cada repo de onde vêm os handoffs da raiz.
- Medido em 2026-11-17, com 403 entradas (`ls -A ~/.wt | wc -l`) e 4 `--repo`: o scan levou de 89 a
  128 s em quatro rodadas, e o apply com `--dry-run` levou 10 s para os 37 itens que saíam.
