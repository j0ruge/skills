# Armadilhas medidas do retrofit — o porquê de cada regra

O comando `retrofit-skill` traz cada regra em uma ou duas linhas. Aqui está a história medida
que a justifica, movida do comando na 0.7.1 sem reescrita (as seções 7 e 8 nasceram aqui, na
0.7.3). Leia a seção quando quiser contestar
ou afrouxar a regra correspondente: é o que se perde se ela sair.

Sumário: 1. Symlink, não cópia · 2. Repo atrás do remoto · 3. Outra sessão no mesmo checkout ·
4. Cheque dos quatro lugares · 5. O `--stat` como último sensor · 6. Orçamento da spec ·
7. Windows chamando o WSL · 8. A cópia instalada atrás da fonte

## 1. `~/.claude/skills/<nome>` costuma ser um symlink, não uma cópia

Medido em 11/09/2026, e custou um clobber. A pasta local e a do marketplace
parecem dois diretórios com os mesmos arquivos — `ls -la` mostra arquivos reais
(`-rw-rw-r--`), `md5sum` dá igual, e a conclusão natural é "são duas cópias, vou
ressincronizar no fim". **Errado:** o `ls -la` está listando o conteúdo
*através* do link.

A consequência é pior que perder tempo. Um `cp marketplace/… local/…` de
"ressincronização" escreve **através do symlink**, de volta no marketplace — e
se os caminhos não corresponderem exatamente, sobrescreve o arquivo errado. Foi
o que houve: `plugins/<skill>/CHANGELOG.md` (versionado) copiado por cima de
`plugins/<skill>/skills/<skill>/CHANGELOG.md` (registro por sessão), apagando 91
linhas de histórico. Os dois são distintos de propósito, e cada um diz isso no
próprio cabeçalho.

## 2. Repo atrás do remoto

Sincronize o repo alvo com o remoto **antes de tocar em qualquer arquivo**. Numa
sessão real isto evitaria um push rejeitado: o clone local estava atrás do
`origin/main` (outra máquina/CI havia empurrado commits), então o `git push`
falhou e exigiu fetch+rebase no meio do caminho — com o commit já feito sobre
uma base defasada.

## 3. Outra sessão no mesmo checkout

**Árvore suja com arquivos que não são seus = outra sessão viva no mesmo
checkout.** O índice do git é **um só** para todas as sessões: o que você pôs nele
com `git add` sai no commit de **quem commitar primeiro**. Medido em 02/10/2026:
um retrofit deixou 5 arquivos no índice enquanto pedia confirmação, outra sessão
commitou o trabalho dela com `git commit` e levou o retrofit inteiro dentro de um
commit com o título dela, já empurrado para a `main`. Os arquivos compartilhados
(`marketplace.json`, `README.md`) pioram o caso: os dois trabalhos caem no mesmo
arquivo, e nenhum `git add <arquivo>` separa um do outro.

**Árvore limpa no início não prova nada.** Medido em 04/10/2026, num retrofit da `codereview`: o
`git status -sb` saiu limpo no começo; entre ele e a primeira escrita, outra sessão gravou cinco
arquivos do `windows-disk-cleanup` (18:14–18:16) e, minutos depois, `marketplace.json` e
`README.md`, os mesmos que o retrofit ia bumpar. Quando a descoberta vem depois de editar, o
conserto é refazer as edições no worktree pelo mesmo script, conferir cada arquivo com `cmp` contra
a cópia do checkout compartilhado e só então `git restore -- <os seus arquivos>` lá. Nunca
`checkout -- .`, que levaria junto o trabalho da outra sessão.

## 4. Cheque dos quatro lugares

Hoje em `scripts/check_release_sync.py`; até a 0.7.0 era um bloco Python embutido no comando.

⚠️ Este passo existe porque falhou na prática: um retrofit atualizou a
description em 2 dos 3 arquivos e deixou o README numa versão antiga. O erro
só apareceu na sessão seguinte, quando outra pessoa rodou o validador.

⚠️ **O plugin pode não ter `SKILL.md` — e pode ter vários.** A forma
anterior lia `plugins/<nome>/skills/<nome>/SKILL.md` como se todo plugin
tivesse exatamente um, com o nome do plugin. Dois casos reais quebram isso:
um plugin **só de comandos** (o `retrofit-skill` é um) não tem `skills/`, e
o cheque estourava em `FileNotFoundError` — um cheque que não roda é pior
que um que reprova, porque o erro parece problema do ambiente; e um plugin
**multi-skill** (o `dotnet-wpf` tem quatro, com nomes próprios) tem uma
`description` por skill, que **legitimamente difere** da do `plugin.json`.
Daí o `glob`: sem skill, ele diz que o canônico é o `plugin.json`; com
várias, imprime uma linha por skill para você julgar — em vez de colapsar
tudo num booleano que mente nos dois casos.

⚠️ **O fim da `description` é a próxima chave do frontmatter — e chave pode ter hífen.**
A forma anterior parava em `\n[a-z_]+:`, e `argument-hint:` (campo real do Claude Code)
não casa: a captura atravessava até `metadata:` e o cheque dizia `False` para uma
description idêntica (medido no retrofit do `ticket` v1.6.1: 511 chars capturados × 456
reais). Um falso negativo ensina a ignorar o cheque, que é o mesmo dano de um falso positivo.

⚠️ **E o cheque do README já foi ele próprio o sensor cego.** A forma
anterior perguntava `f"| {pj['version']} |" in rd` — se a string existe em
*algum lugar* do arquivo. Ela responde `True` porque **outro** plugin está
naquela versão, e o README tem duas tabelas com uma linha do seu plugin em
cada (compatibilidade, onde o campo 2 é `✓`, e versões). Foi medido: um
`python3` que morreu numa `AssertionError` sem escrever o README, seguido
deste cheque dizendo `versao no README: True`. Por isso a forma acima extrai
a versão **da linha do seu plugin** e a imprime para comparação, em vez de
devolver um booleano — um cheque que não consegue reprovar não é cheque, e
um que imprime o valor encontrado deixa o erro visível mesmo quando a
comparação está errada.

## 5. O `--stat` como último sensor

Um arquivo que você não pretendia tocar é **sinal, não ruído** — e foi o
único sensor que pegou o clobber do PASSO 0 (`CHANGELOG.md | 567 ++++----`
num arquivo que o retrofit não deveria ter alterado). O `validate-versions`
passou limpo, a releitura da description passou, e mesmo assim havia dano
no commit: os gates olham o que você mudou de propósito, e nenhum deles
olha o que você mudou sem querer. Contar arquivos é barato e é a última
chance antes de o erro virar histórico.

## 6. Orçamento da spec

Retrofit só soma texto, e é assim que uma skill passa do orçamento: a auditoria de 2026-09-28
achou `SKILL.md` com 970 linhas e outro com 110 mil chars (~27k tokens) no marketplace. A régua
é a spec aberta (https://agentskills.io/specification) e as boas práticas do mesmo site:

**Conte caracteres, não bytes.** O C1 do auditor compara o `len()` do texto com 20 000, e o `wc -c`
conta bytes: em PT-BR com travessão a diferença passa de 1 %. Medido em 04/10/2026, o `SKILL.md`
da `codereview` 2.9.2 dá 20 150 bytes e 19 959 caracteres (`wc -m` com `LANG=C.UTF-8`; com
`LC_ALL=C`, o `-m` volta a contar bytes). Lido pelo `-c`, um arquivo abaixo do teto parece acima.

## 7. Windows chamando o WSL: `/tmp` que some e `cd` que falha calado

Com o harness no Windows e o clone no WSL, cada comando é um `wsl.exe -e bash -lc '…'` novo.
Medido em 04/10/2026:

- **O `/tmp` não sobrevive entre chamadas.** Sem processo vivo, a distro para por ociosidade, e o
  systemd recria o `/tmp` quando ela volta. Um worktree em `/tmp/wt-retrofit-codereview` e os
  baselines de `mktemp -d` sumiram em minutos: o `/tmp` e os `systemd-private-*` nasceram às
  18:19:14, depois do worktree, que o `git worktree list` passou a mostrar `prunable`. O segundo, em
  `~/.wt/`, durou a sessão inteira. O scratchpad do harness também não serve: é caminho do Windows,
  e o git do WSL em `/mnt/c` traz CRLF e 0777.
- **Baseline perdido se refaz da base, não da árvore editada:** `git archive origin/main
  plugins/<p> | tar -x -C <dir>` e audite `<dir>`.
- **A chamada começa no diretório do Windows** (`/mnt/<disco>/<repo-da-sessão>`), não no clone. Um
  `cd` que falhou deixou o script de versão rodar no repositório da sessão; só não gravou nada
  porque o primeiro arquivo que ele abria (`plugins/<p>/CHANGELOG.md`) não existia lá, e o
  `README.md`, que vinha depois, existia. `cd <clone> || exit` em toda chamada.
- **O clone não é sibling do repositório do Windows.** Procure no WSL:
  `wsl.exe -e bash -lc 'ls -d ~/repos/skills ~/repos/skills_commands_manager'`.

## 8. A cópia instalada atrás da fonte

As lições saem do que a sessão usou, e a sessão usou a cópia instalada. Medido em 04/10/2026: o
cache tinha a `codereview` 2.9.1 e a fonte estava na 2.9.5. Das sete lições candidatas, duas já
estavam na fonte: o selo P1/P2 do Codex (`reviewer-registry.md`) e o atraso do `headRefOid` logo
depois do push (`thread-resolution.md`, 5.0). E o texto deste comando que a sessão recebeu ainda
pedia `--no-changelog-required`, que a 0.7.2 tirou. Antes de propor, compare a versão instalada com
a da fonte e procure cada lição na fonte (`grep -rn`).
