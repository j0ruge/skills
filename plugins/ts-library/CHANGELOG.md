# Changelog — `ts-library`

Formato: [Semantic Versioning](https://semver.org/)

## [0.3.0] — 2026-10-16

### O que a extração real mostrou

A receita de extração da 0.1.0 tinha sido medida num repositório de prova. Na mesma data ela rodou de
verdade: a `@jrc/object-storage` saiu de `JRC-Brasil/sales_quote` (`a1ad4b74`) para
`JRC-Brasil/jrc-libs` (`21df76f`). Quatro lições, todas medidas nessa extração, entraram na
`references/extracao.md`:

- **A regex só pegava `(#N)`.** Duas das quatro referências estavam fora de parênteses ("review do PR
  #175", "no PR #178"). Com a receita antiga, elas teriam virado links para issues do repositório novo,
  sem erro nenhum. A regex nova é `(?<![\w/])#([0-9]+)`: pega `#N` em qualquer posição e deixa em paz
  a referência já qualificada e o `#` de URL (conferido com o `re` do Python, o motor do
  `--replace-message`). Entrou também como armadilha no `SKILL.md`.
- **Um clone sem rede.** `git clone --no-local` a partir do checkout local é aceito pelo `filter-repo`
  como clone novo. O `filter-repo` apaga o `origin`, então o push vai para um remoto acrescentado à
  mão, e um push de volta à origem fica impossível por engano.
- **Os checks antes do push.** A receita parava no `git log`. Agora são cinco: a contagem de commits
  dos dois lados, nenhuma referência solta, o hash da árvore igual ao da origem, a varredura de
  credencial em cada commit e a lib instalada e testada sozinha a partir de um `git archive`. A
  varredura achou 28 pares de commit e arquivo, todos marcadores falsos de teste. Daí a regra: o
  achado se classifica lendo a linha, nunca pela contagem.
- **O commit de entrada fora da pasta da lib.** Com um `README.md` na raiz, `git log --
  packages/<lib>` continua contando só os commits da origem, e a contagem serve de check.

## [0.2.0] — 2026-10-16

### O que a primeira avaliação mostrou

A avaliação da 0.1.0 (três casos, com e sem a skill) deu 100% contra 94%, e o avaliador apontou quatro
falhas que os critérios não pegavam:

- **Recomendação para outro projeto.** Na revisão de um `package.json` em que o usuário não disse como
  a lib é instalada, a resposta com a skill justificou a escolha com imagem `alpine` e
  `npm ci --ignore-scripts`, que vinham do caso medido da skill. O `SKILL.md` agora manda partir das
  restrições de quem pede, e perguntar, ou escrever a hipótese como hipótese.
- **Medição atribuída a quem não mediu.** Uma resposta escreveu "medido com o npm 12.0.2" sobre um
  fato que a skill mediu. Agora, quem repassa um fato *medido* diz que a medição é da skill e a data.
- **O tarball fora do commit.** A resposta sem a skill conferiu o arquivo commitado, e a com skill não.
  Medido em 2026-10-16: com `*.tgz` no `.gitignore`, o `git add -A` sai com rc=0 e o commit fica sem o
  tarball; só o `git add` explícito recusa e avisa. Entrou como armadilha e como passo da atualização
  (`git check-ignore -v`, `git show HEAD:vendor/… | sha256sum`).
- **A cópia congelada só com README.** A resposta sem a skill propôs um sensor, e ele entrou na
  `extracao.md`: `git log <sha-da-extração>..origin/<branch> -- <pasta>` tem de sair vazio antes de
  cada release (medido num repositório de prova).

E a segunda avaliação achou um defeito no próprio desenho da release:

- **O gate rodava antes do bump.** O número da versão está dentro do `package.json` do tarball, então o
  gate testava um arquivo e a release publicava outro, com outro sha256. A `distribuicao.md` passou a
  fazer bump e commit local primeiro, `npm pack` uma vez só, e o gate sobre esse commit e esse `.tgz`.
  Achado pela execução com a skill no caso do plano de extração.

Na segunda avaliação, a skill ficou com 24 de 25 critérios, contra 22 de 25 sem ela. A reprovação que
sobrou foi a mesma do primeiro item: a `distribuicao.md` descrevia o `docker build` como algo que
"costuma partir de `node:*-alpine` … com `--ignore-scripts`", e o modelo leu isso como fato do projeto
de quem pedia. O trecho virou condição ("vale **se**…"). Entraram também dois cuidados que a resposta
sem a skill teve e a skill não tinha: procurar script de instalação novo dentro do tarball antes do
`npm install`, e rodar o gate num `git worktree` limpo, onde um `.tgz` fora do commit não passa.

Os critérios da avaliação foram de 18 para 25, com os que o modelo base tende a errar: afirmação falsa
sobre o npm, restrição inventada, medição atribuída, arquivo commitado e janela de congelamento.

## [0.1.0] — 2026-10-16

### A skill nasce do planejamento de uma lib real

Origem: o planejamento da `@jrc/object-storage` como biblioteca da JRC (repositório privado, sem
GitHub Actions, sem registro de pacotes), com a conferência do desenho contra as práticas de 2026.

- **O fluxo em seis passos** no `SKILL.md`: forma do pacote, sensores, versão, distribuição,
  documentação para agentes e extração de um workspace. Cada um roteia a sua reference.
- **Três marcas para cada afirmação**: *medido* (com o comando), *fonte* (fato externo com data, em
  `references/fontes.md`) e *desenho* (decidido e ainda não executado). O script de release e a regra
  do relatório da API são *desenho*: a lib de origem ainda não fez a primeira release. Prove antes de
  confiar.
- **Armadilhas medidas em 2026-10-16** (npm 12.0.2, Node 22.22): o `npm publish --dry-run` ignora o
  `private`, e só o publish real para em `EPRIVATE` (sem token, os dois casos param antes em
  `ENEEDAUTH`); o cache global do npm instala o tarball antigo quando o `.tgz` em `vendor/` é trocado
  sem `npm install`, e só o cache vazio dá `EINTEGRITY`; o `npm pack` é reproduzível; no npm 12 o
  `npm pack --json` é um objeto, não uma lista; a negação no `files` funciona; o `prepublishOnly` não
  roda no `npm pack`, e o `prepack` sim; e a extração com `git filter-repo` numa execução só (`--path`
  + `--path-rename` + `--replace-message`).
- **Avaliação** em `evals/evals.json`: três casos (revisar um `package.json`, planejar a extração de
  uma lib, atualizar a lib num consumidor), com e sem a skill. A execução com a skill no primeiro caso
  achou a lição do `prepack`, conferida antes de entrar.
