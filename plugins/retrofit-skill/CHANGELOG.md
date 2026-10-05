# Changelog

## [0.8.0] — 2026-10-05

### Depois do push, a loja e a sessão

O retrofit terminava no push, e o push atualiza o GitHub, não a cópia instalada nem a sessão
aberta. Em 05/10/2026 três plugins estavam atrás da fonte por isso (`codereview` 2.9.5 contra
2.10.0, `retrofit-skill` 0.7.2 contra 0.7.3, `skill-quality-audit` 0.4.1 contra 0.5.0), e a sessão
rodou as versões velhas: o retrofit da `ticket` mediu o orçamento em bytes, com a correção já
publicada na 0.7.3. A §8 das *Armadilhas* tratava o sintoma (comparar a versão antes de propor);
o pedido do JorUge fecha a causa.

- **Modo completo:** depois do push, `claude plugin marketplace update <loja>`, a lista dos
  escopos onde o plugin está instalado (`claude plugin list --json`) e `claude plugin update` em
  cada um; no fim, pedir ao usuário o `/reload-plugins`, porque o agente não roda comando de
  barra.
- **Modo enxuto:** a skill local não passa pela loja; pedir o `/reload-skills`, que também vale
  para a skill do marketplace instalada por symlink em `~/.claude/skills`.
- `references/armadilhas-medidas.md` §8: o caso de 05/10 e o texto dos dois comandos de reload,
  lido do binário do Claude Code.

## [0.7.3] — 2026-10-04

### Worktree e baseline fora do `/tmp` do WSL, árvore limpa conferida de novo, chars em vez de bytes e a fonte antes da cópia instalada

Lições do retrofit da `codereview` 2.9.6, feito de uma sessão com o harness no Windows e o clone
do marketplace no WSL, com outra sessão escrevendo no mesmo checkout.

- **Worktree e baseline vão em `~/.wt/`, não no `/tmp`** (*Armadilhas*, §7, nova). Cada comando era
  um `wsl.exe -e bash -lc` novo; sem processo vivo, a distro parou por ociosidade e o systemd recriou
  o `/tmp` ao voltar. O worktree em `/tmp/wt-retrofit-codereview` e os baselines de `mktemp -d`
  sumiram em minutos (`/tmp` e `systemd-private-*` nascidos às 18:19:14, depois do worktree; o `git
  worktree list` o mostrava `prunable`). O segundo, em `~/.wt/`, durou a sessão inteira. O snippet
  do worktree e o do baseline passam a usar `~/.wt/`. A §7 diz também como refazer o baseline a partir
  da base (`git archive origin/main plugins/<p> | tar -x`), sem a árvore editada.
- **O clone pode estar no WSL, e a chamada começa no diretório do Windows** (§7). Um `cd` que falhou
  deixou o script de versão rodar no repositório da sessão, e ele só não gravou nada porque o primeiro
  arquivo não existia lá. A busca do repo ganhou a linha do harness no Windows, e a §7 traz o `cd
  <clone> || exit` e o `ls -d ~/repos/skills*`.
- **Árvore limpa no início não prova nada** (§3, ampliada). O `git status -sb` saiu limpo; minutos
  depois outra sessão gravou cinco arquivos do `windows-disk-cleanup` e, em seguida, `marketplace.json`
  e `README.md`. O comando manda conferir de novo logo antes da primeira escrita. A §3 traz o conserto
  quando a descoberta vem depois de editar: refazer no worktree pelo mesmo script, conferir com `cmp` e
  `git restore` só nos seus arquivos.
- **O orçamento se mede em caracteres** (§6, ampliada). O baseline usava `wc -lc`, que conta bytes; o
  C1 do auditor conta o `len()` do texto. O `SKILL.md` da `codereview` 2.9.2 dá 20 150 bytes e 19 959
  caracteres. Agora é `wc -lm`, que com `LANG=C.UTF-8` dá o mesmo número do C1.
- **Cada lição se procura na fonte antes de propor** (§8, nova). O cache tinha a `codereview` 2.9.1 e
  a fonte estava na 2.9.5: duas das sete lições candidatas já estavam lá. E o texto deste comando que a
  sessão recebeu ainda pedia `--no-changelog-required`, que a 0.7.2 tirou.
- **Regra de não apagar vence o snippet de limpeza.** Sob uma regra assim (no caso, o `CLAUDE.md` do
  projeto da sessão), o worktree e o branch ficam, e o resumo diz onde.
- **Espaço, por fusão provada** (o comando tinha 19 668 caracteres): a frase sobre o gate da 0.5.0
  vira uma remissão à entrada 0.6.0 deste CHANGELOG, que narra o caso, e fica mais precisa: o
  caminho do Hermes existe numa das máquinas do autor, e o gate não rodava só nas outras; e o histórico do
  B5 no item *Flags* fica na regra e no porquê, com remissão à 0.7.2. O comando fica com 19 967
  caracteres.

## [0.7.2] — 2026-10-04

### As flags do auditor deixam de pedir `--no-changelog-required` no modo completo

A seção *Localizar o auditor* mandava usar `FLAGS=(--desc-budget 0 --no-changelog-required)` no
modo completo, porque o check B5 só olhava `<skill>/CHANGELOG.md` e acusava um falso erro em toda
skill de plugin. A `skill-quality-audit` 0.4.1 consertou o B5: ele acha o `<plugin>/CHANGELOG.md` ao
lado do `.claude-plugin/plugin.json` e responde OK com o caminho. A frase passou a ser falsa, e a
flag passou a esconder o único caso que o B5 ainda deve pegar: o plugin que esqueceu o CHANGELOG.

Agora é `FLAGS=(--desc-budget 0)` nos dois modos. Conferido em 2026-10-04: sem a flag, nenhuma skill
de `plugins/*/skills/*/` deste marketplace sai com `[ERRO] B5`; a `coderabbit-pr` sai rc 0 com
`[OK] B5`; e o aviso do zsh segue valendo com uma flag só (`"$FLAGS"` como string → rc 2; o array →
rc 0).

## [0.7.1] — 2026-10-02

### O comando volta ao orçamento: scripts e reference, sem mudar o fluxo

O comando tinha 450 linhas e ~26,2 mil chars, acima do orçamento de ~20 mil da spec. Refatoração
pela `skill-refactoring`, sem regra nova nem removida:

- **Scripts** (Passo 3 da `skill-refactoring`): os dois blocos Python embutidos viram
  `scripts/check_release_sync.py <plugin>` (cheque dos quatro lugares) e
  `scripts/audit_gate.py <B>` (NOVO/dívida/SUMIU/LER/CLAIM). Provados contra o código original:
  saída idêntica em 5 plugins reais (só e multi-skill, só comandos) e numa skill editada de
  propósito; a sabotagem de versão aparece nos valores impressos.
- **Reference** `references/armadilhas-medidas.md`: as seis narrativas medidas (symlink, repo
  atrás, outra sessão, cheque dos quatro lugares, `--stat`, orçamento da spec) movidas sem
  reescrita. Cada regra fica no comando em uma ou duas linhas e cita a seção (*Armadilhas*, §N).
- **Localizador `$RS`**: o comando acha a própria pasta no marketplace (modo completo) ou no
  cache do plugin (`sort -V`, a versão mais alta); sem ela, o gate é SKIP como o auditor ausente.

Resultado: 357 linhas e ~20 mil chars. Para reverter, `git revert` deste commit.

## [0.7.0] — 2026-10-02

### Outra sessão no mesmo checkout commitou o retrofit

O *ANTES DE EDITAR* ganha o caso da árvore suja com arquivos que não são do retrofit: é outra
sessão viva no mesmo checkout, e o índice do git é um só. O retrofit passa a editar e commitar num
`git worktree` próprio a partir do `origin/main`, e só põe arquivo no índice no mesmo comando do
commit. O `git add -A` do modo completo ganha a mesma ressalva.

**Por quê:** no retrofit do `deploy` v2.3.0, os 5 arquivos foram postos no índice antes da
confirmação. Uma sessão paralela, que mexia no `retrofit-watch`, commitou com `git commit` e levou
o retrofit dentro do commit dela (`1049f71`, título só do `retrofit-watch`), já empurrado para a
`main`. Conteúdo íntegro, autoria do histórico errada, e corrigir exigiria force-push num repo em
uso. `marketplace.json` e `README.md` tinham os dois trabalhos no mesmo arquivo, então nem um
`git add` por arquivo separaria um do outro. Correção verificada: este próprio retrofit foi feito
num worktree.

## [0.6.2] — 2026-10-01

### O cheque da description parava na chave errada

O cheque independente do modo completo achava o fim da `description` do `SKILL.md` pela próxima
chave `\n[a-z_]+:`. Chave com hífen (`argument-hint:`, campo real do Claude Code) não casa, então a
captura engolia a linha seguinte e o cheque respondia `False` para uma description idêntica — medido no
retrofit do `ticket` v1.6.1 (511 chars capturados × 456 reais). O padrão passa a `\n[A-Za-z0-9_-]+:`,
provado nos dois estados contra o mesmo arquivo antes da troca.

## [0.6.1] — 2026-09-29

### O repo do marketplace se chama `skills`

O repositório `j0ruge/skills_commands_manager` foi renomeado para `j0ruge/skills`, e a pasta
local também. A busca do repo no modo completo tentava primeiro `../skills_commands_manager` e
passaria a cair na busca por nome parecido. Agora ela tenta `../skills` e, depois, o nome antigo,
para clones que ainda não foram renomeados.

## [0.6.0] — 2026-09-29

### A skill-quality-audit vira a régua do retrofit; a skill-creator passa a ser condicional

**A skill-creator era carregada em toda execução e não fazia nada nela.** São 485 linhas e
~33 mil chars (~8k tokens) por retrofit. O que ela tem de próprio (o loop de evals com
subagentes, o viewer, o benchmark e o otimizador de description) nunca rodava num retrofit. O
que ela ensina de escrita já estava na seção de formato da spec e na família
`skill-quality-audit`. No Cursor ela nem existe. Agora o retrofit só a chama quando a lição muda
a `description` e o usuário quer medir o gatilho.

**O gate da 0.5.0 nunca rodou.** Ele apontava para `~/.hermes/skills/devops/skill-quality-audit/`,
que não existia, e o plugin também não estava instalado. O `CLAUDE.md` do repo tinha o mesmo
caminho morto. A nova seção *Localizar o auditor* procura primeiro no marketplace, depois no
cache de plugins (a versão mais alta, porque o cache guarda uma pasta por versão), em
`~/.claude/skills` e no Hermes. Se não achar, registra `[SKIP]`, que nunca conta como aprovação.

**O gate compara com um baseline, não com zero.** Rodado contra o `codereview`, o auditor acusou
3 avisos C2 que já existiam e um B5 (CHANGELOG ausente) que é falso positivo no marketplace, onde
o CHANGELOG fica no nível do plugin. Um gate "cru" bloquearia todo retrofit. Agora o baseline é
gravado antes da edição e, depois dela, só achado `NOVO` bloqueia; a dívida antiga vai para o
resumo. Os claims que o `--claims` acha nas linhas acrescentadas recebem veredito (sensor,
derivar, datar, remover), com teto de 2 ciclos de correção.

**Medido no ensaio**, numa cópia descartável do `codereview` (acrescentei uma reference citada e
ausente, uma reference órfã e dois números sem fonte):
- `FLAGS="--desc-budget 0 --no-changelog-required"` como string saiu com `rc=2` no zsh, que não
  divide `$FLAGS` em palavras. Por isso o comando usa array e `"${FLAGS[@]}"`.
- O gate marcou os dois B1 como `NOVO` e os três C2 como dívida, e listou o claim da reference
  nova. Não pegou "600 segundos" no `SKILL.md`, porque a heurística do `--claims` deixa passar
  prosa. Por isso o gate também imprime `LER` com a contagem de linhas novas por arquivo.

**Nada ou melhor, nunca pior.** Um sensor mais verde não prova uma skill melhor. Na
`codereview`, os 3 avisos C2 vêm das instruções que os subagentes leem por caminho absoluto, e
"corrigi-los" quebra os agentes. No ensaio, apagar essas citações deixou o auditor com `rc=0` e
um aviso a menos, e a skill ficou pior. Por isso o comando ganhou a seção *Princípio*:
- achado é sinal, não ordem;
- dívida antiga não se conserta dentro do retrofit;
- lição existente só sai com prova (obsoleta, movida ou fundida);
- lição que não cabe sem piorar não é aplicada.

O gate passou a imprimir `SUMIU` (achado que desapareceu, que precisa de motivo) e `-N` linhas
removidas por arquivo. O mesmo ensaio saiu assim: `SUMIU` nos dois C2 e `-1` em cada contrato. O
`NOVO` ganhou uma saída para a exceção legítima (declarada e registrada no CHANGELOG), para que o
gate não force a distorcer a skill até ele passar.

Também corrige o drift: o `metadata.version` do comando estava em 0.4.0 com o plugin em 0.5.0.

**Como reverter:** `git revert` do commit; a 0.5.0 continua funcional (sem gate efetivo).

## [0.5.0] — 2026-09-28

### Retrofit mantém a skill no formato da spec agentskills.io

Retrofit só soma texto. Na auditoria de 2026-09-28 contra a spec aberta
(https://agentskills.io/specification) e as boas práticas do mesmo site, o marketplace tinha
cinco `SKILL.md` acima de 500 linhas (o maior com 970), um de 110 mil chars (~27k tokens, 5x
o orçamento recomendado do corpo) e um `name` fora da spec (`coderabbit_pr`). Nenhum passo do
retrofit media isso.

Nova seção **"Mantenha a skill no formato da spec"**: frontmatter só com os seis campos da
spec (autor e versão em `metadata`), orçamento de 500 linhas / ~20 mil chars, lição entra na
seção de gotchas, references a um nível e com condição de leitura. Gate nos dois modos:
`validate-versions.py` (check 7, novo) no marketplace e a `skill-quality-audit` quando
instalada.

**Como reverter:** `git revert` do commit; a 0.4.0 continua funcional.

## [0.4.0] — 2026-09-11

Dois acréscimos, e os dois vêm do mesmo incidente: um retrofit que **danificou o
repositório que estava melhorando**.

### 🔴 `~/.claude/skills/<nome>` costuma ser SYMLINK — e o `ls -la` esconde isso

A pasta instalada e a do marketplace parecem dois diretórios com os mesmos
arquivos: `ls -la` lista arquivos reais (`-rw-rw-r--`), `md5sum` bate, e a
conclusão natural é "são duas cópias, ressincronizo no fim". O `ls -la` está
listando o conteúdo **através** do link.

O dano não é perder tempo: o `cp` de "ressincronização" escreve **de volta no
marketplace**, e com caminhos que não correspondem exatamente ele sobrescreve o
arquivo errado. Aconteceu — `plugins/<skill>/CHANGELOG.md` (versionado) por cima
de `plugins/<skill>/skills/<skill>/CHANGELOG.md` (registro por sessão), apagando
91 linhas. Os dois são distintos de propósito e cada um diz isso no cabeçalho.

O PASSO 0 ganhou a checagem certa (`ls -ld`, `readlink -f`, comparação de inode —
o `-d` é a diferença) e a conclusão: sendo symlink, **não há cópia para
sincronizar**, e qualquer passo de "ressincronizar" só pode causar dano.

### Ler o `--stat` antes do commit, e responder por cada arquivo

O que pegou o clobber não foi nenhum dos gates da skill. O `validate-versions`
passou limpo; a releitura da description passou. Eles olham o que você mudou **de
propósito** — nenhum olha o que você mudou sem querer. O que denunciou foi o
`--stat`: `CHANGELOG.md | 567 ++++----` num arquivo que o retrofit não tinha
motivo para tocar.

Novo passo antes do commit: `git add -A && git diff --cached --stat`, com a regra
de que **arquivo inesperado é sinal, não ruído**. É barato e é a última chance
antes de o erro virar histórico.

## [0.3.2] — 2026-09-09

### Fixed

- **O cheque de confirmação assumia que todo plugin tem exatamente um
  `SKILL.md`, com o nome do plugin.** Lia
  `plugins/<nome>/skills/<nome>/SKILL.md` direto, e dois casos reais do
  marketplace quebram isso. Um plugin **só de comandos** — o próprio
  `retrofit-skill` — não tem `skills/`, e o bloco estourava em
  `FileNotFoundError`: um cheque que não roda é pior que um que reprova, porque
  o erro se lê como problema de ambiente e não como resultado. E um plugin
  **multi-skill** (`dotnet-wpf` tem quatro, com nomes próprios) tem uma
  `description` por skill, que legitimamente difere da do `plugin.json` — o
  booleano `igual nos 3` reprovaria o estado correto. Agora o bloco usa `glob`:
  compara `plugin.json` × `marketplace.json` sempre, e depois imprime uma linha
  por `SKILL.md` encontrado; sem nenhum, diz que o canônico é o `plugin.json`.
- **E o filtro de linha do README só reconhecia uma das duas formas.** A tabela
  mistura `| **nome** |` e `| [**nome**](#ancora) |` (linha com link para a
  seção detalhada), e o `startswith` casava só a primeira. O sintoma foi honesto,
  não silencioso — `versao na linha do README: []` contra `esperado: ['1.7.0']`,
  visivelmente errado, que é a propriedade que o booleano da v0.3.0 não tinha —,
  mas é falso alarme. Agora a comparação normaliza a primeira célula (tira o
  link e os asteriscos) e imprime **quantas linhas** casaram, para distinguir
  "não achei" de "achei e diverge". Achado rodando o próprio bloco contra os
  três formatos de plugin do repo, em vez de o declarar correto.

## [0.3.1] — 2026-09-09

### Fixed

- **O cheque de confirmação do README era ele próprio um sensor cego.** A
  v0.3.0 introduziu um bloco `python3` para confirmar que os quatro lugares
  batem — e a linha do README perguntava `f"| {pj['version']} |" in rd`, isto é,
  se a string existe em *algum lugar* do arquivo. Ela responde `True` quando
  **outro** plugin está naquela versão. Medido nesta data: um script de edição
  morreu numa `AssertionError` sem escrever o README, e o cheque seguinte
  imprimiu `versao no README: True` — exatamente o falso verde que a v0.3.0
  existia para impedir, um nível acima. Agora o bloco extrai a versão da **linha
  do plugin** (o README tem duas tabelas com uma linha cada: compatibilidade,
  onde o campo é `✓`, e versões) e **imprime o valor encontrado** ao lado do
  esperado, em vez de devolver um booleano. Cheque que não consegue reprovar não
  é cheque; e imprimir o valor deixa o erro visível mesmo quando a comparação
  está errada.

## [0.3.0] — 2026-08-26

O fluxo já mandava rodar `validate-versions.py` — e mesmo assim um retrofit
passou deixando dois resíduos: a `description` do `cicd` entrou em 2 dos 3
arquivos e o README ficou uma versão atrás. O erro só apareceu na sessão
seguinte, quando outra pessoa rodou o validador.

Ou seja: o problema não era a ausência da instrução. Era o que ela não dizia —
**quando** rodar, **o que fazer com os warnings**, e que ter editado não é prova
de que o arquivo mudou.

### Added

- **Passo de verificação antes do commit**, com o validador movido para posição
  de gate e não de formalidade final, mais um snippet que confere os quatro
  lugares (`SKILL.md`, `plugin.json`, `marketplace.json`, README) e reporta se a
  description bate nos três e se a versão chegou ao README.
- **WARNINGS passam a ser bloqueantes para a skill que está sendo tocada.** Eles
  não reprovam o gate, e é por isso que passam despercebidos: aviso que nunca
  reprova vira ruído. Encurtar uma description no ato é barato; deixar acumular
  virou um mutirão de 7 plugins (até 871 chars).
- **Aviso sobre `git checkout -- .claude-plugin/marketplace.json`**: o arquivo é
  único e compartilhado, então usá-lo para desfazer uma sondagem leva junto as
  edições reais da sessão. A recuperação é ressincronizar a partir do
  `plugin.json`, que é canônico por plugin.

### Changed

- **A atualização do README deixou de ser condicional.** O texto dizia "*se* a
  mudança afeta como a skill é descrita/versionada" — mas um bump **sempre**
  muda a versão na tabela. Foi por esse "se" que o `2.20.0` sobreviveu.

## [0.2.3] — 2026-07-25

### Corrigido

- **Commits deste fluxo não levam mais o trailer `Co-Authored-By: Claude`.** Os dois
  modos (completo e enxuto) mandavam explicitamente assinar com coautoria do Claude.
  O usuário quer que o histórico do repositório dele mostre só o nome dele.
- A regra ficou numa seção própria (*Autoria dos commits*) e é **afirmativa**, não
  uma omissão: o prompt padrão do Claude Code instrui a terminar mensagens de commit
  com esse trailer, então apenas apagar a menção deixaria o default vencer. Dizer
  "sem `Co-Authored-By`" é o que efetivamente muda o comportamento.

Editado: `commands/retrofit-skill.md` (modo completo, modo enxuto e nova seção).
Sem mudança na superfície de triggering — descrição inalterada.

## [0.2.2] — 2026-06-06

### Adicionado

- **Seção "Mantenha a descrição ENXUTA (triggering)"** — orienta o retrofit a não deixar a `description` (superfície de triggering) inchar: não anexar a lição de cada versão, alvo ~350–500 chars, enxugar em vez de só somar (uma frase do que faz + 1–2 diferenciais + `Triggers —` compacto ≤8 itens), espelhada nos três lugares (SKILL.md, plugin.json, marketplace.json); detalhe vai para references/README.
- **Seção "Editando `marketplace.json` com segurança"** — ao editar programaticamente, escopar ao bloco do plugin alvo (`"name": "$ARGUMENTS"`); um match ingênuo em `"description":` ou `sed` global sobrescreve as descrições de TODOS os plugins.

### Motivação

- Nesta sessão, a descrição da skill `wsl-windows-onboarding` inchou para ~1.100 chars ao longo de v0.1.0→v0.2.0 (cada retrofit anexando) e precisou ser enxugada para ~720 — exatamente o anti-padrão que esta diretriz previne. E uma edição programática do `marketplace.json` por prefixo `"description":` chegou a sobrescrever as 14 outras descrições (revertida do git) — daí a regra de escopar ao bloco do alvo. Meta-retrofit: o `retrofit-skill` aplicado a si mesmo.

## [0.2.1] — 2026-06-06

### Adicionado

- **Passo "ANTES DE EDITAR — atualize o repo local"** no fluxo do comando: antes
  de tocar em arquivos, fazer `git fetch` e trazer a branch alvo para o estado do
  remoto (fast-forward ou rebase). Inclui o cuidado de, num clone recém-migrado
  Windows→WSL, limpar o ruído de CRLF/filemode (`git diff --ignore-cr-at-eol`
  vazio → `core.fileMode=false` + `git checkout -- .`) antes do rebase.

### Motivação

- Nesta sessão (publicação da skill `wsl-windows-onboarding`) o clone local estava
  **atrás do `origin/main`** — outra origem havia empurrado 4 commits. O `git push`
  foi **rejeitado** e foi preciso `git fetch` + `git rebase origin/main` com o
  commit já feito sobre uma base defasada (ainda por cima com a árvore "suja" só
  por CRLF, o que travava o rebase até um `git checkout -- .`). Sincronizar o repo
  ANTES de editar elimina esse retrabalho e faz o push final passar de primeira.

## [0.2.0] — 2026-06-05

### Adicionado

- **Modo enxuto (lean)** para skills locais. Passo 0 do fluxo agora escolhe entre **completo**
  (skill publicada no marketplace: bump de versão + `marketplace.json` + README + push) e
  **enxuto** (skill local de outro repo, ex.: `<outro-repo>/.claude/skills/<nome>/`: edita os
  arquivos + registra a lição num `CHANGELOG.md` na pasta da skill e commita no repo onde ela
  vive, **sem** bump, `marketplace.json`, README do marketplace ou push aqui).
- Critério explícito para não confundir os dois modos (está versionada no marketplace? → completo;
  é local/correção de cobertura? → enxuto).

### Motivação

- Nesta sessão o retrofit foi aplicado à skill `abnt-academico`, que é **local** (vive em
  `aula_veiga/.claude/skills/abnt-academico/`, fora do marketplace). O fluxo original assumia
  `<REPO>/plugins/$ARGUMENTS/`, bump em `marketplace.json` e push para o `origin/main` do repo de
  skills — passos inválidos para uma skill local. Faltava distinguir os dois cenários, o que gerava
  confusão entre "retrofit enxuto" e "retrofit completo".

## 0.1.0 — 2026-04-18

- Initial release: packaged the personal `/retrofit-skill` command as a marketplace plugin.
