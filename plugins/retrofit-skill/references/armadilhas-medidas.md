# Armadilhas medidas do retrofit — o porquê de cada regra

O comando `retrofit-skill` traz cada regra em uma ou duas linhas. Aqui está a história medida
que a justifica, movida do comando na 0.7.1 sem reescrita. Leia a seção quando quiser contestar
ou afrouxar a regra correspondente: é o que se perde se ela sair.

Sumário: 1. Symlink, não cópia · 2. Repo atrás do remoto · 3. Outra sessão no mesmo checkout ·
4. Cheque dos quatro lugares · 5. O `--stat` como último sensor · 6. Orçamento da spec

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
