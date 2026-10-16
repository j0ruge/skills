# Distribuição e release

## As quatro formas

O que cada uma exige de **cada consumidor**: a estação de quem desenvolve, o CI ou gate que roda
`npm ci`, e o `docker build` das imagens. Pergunte como cada um instala antes de escolher. A coluna
"armadilha" vale **se** a imagem parte de `node:*-alpine`, sem `git`, e instala com
`npm ci --ignore-scripts`, como no caso medido; não atribua isso a um projeto que não o disse.

| Forma | Exige | Armadilha |
|---|---|---|
| Registro (npmjs, GitHub Packages) | token de leitura na estação, no CI e como secret de build (`--mount=type=secret`, nunca `ARG` nem `.npmrc` copiado para a imagem) | no GitHub Packages o escopo é a conta dona (`@dono/pacote`), e a documentação pede token clássico com `read:packages`; repositório privado consome a cota de cobrança da conta |
| Dependência git por tag (`github:dono/repo#vX.Y.Z`) | o `dist` commitado na tag, porque o `--ignore-scripts` impede o `prepare`; `git` e credencial de clone em toda imagem de build | o CI com `git` passa e a imagem sem `git` falha |
| Tarball anexado à release, baixado por URL | download autenticado do asset em cada consumidor | como o `npm ci` autenticaria esse download não está resolvido |
| **Tarball versionado no consumidor** | o `.tgz` em `vendor/` na raiz do consumidor e uma dependência `file:` com o caminho relativo do `package.json` que a declara até esse `.tgz` | atualizar é um gesto (um script), e não há `npm outdated` |

Quando a organização não tem registro, nem CI para publicar, nem quer credencial nova em imagem e em
servidor, o tarball versionado é a forma que não pede nada. Migrar dele para um registro é trocar uma
linha por consumidor.

## A mecânica do tarball versionado (medido, npm 12.0.2)

- O lockfile grava `"resolved": "file:vendor/x.tgz"`, relativo à raiz mesmo quando quem declara é um
  pacote de workspace, e o `integrity` em `sha512`. Quem fixa os bytes é o lockfile.
- **Cache frio** (o `docker build`, o CI, um clone novo): um `.tgz` trocado sem atualizar o lockfile
  reprova o `npm ci` com `EINTEGRITY`.
- **Cache quente** (a estação): o mesmo `.tgz` trocado passa com rc=0, e o npm instala os bytes do
  cache pelo `integrity`, sem ler o arquivo. A troca fica invisível na estação e reprova no build.

Dois sensores fecham isso no consumidor:

1. o `sha512` de cada `.tgz` em `vendor/` é igual ao `integrity` do lockfile
   (`openssl dgst -sha512 -binary x.tgz | base64 -w0`, prefixado com `sha512-`);
2. todo pacote do escopo da organização no lockfile resolve para `file:vendor/`. Isso fecha a confusão
   de dependência por construção: ninguém instala um homônimo do registro público.

E um terceiro, sobre o commit e não sobre o disco: `*.tgz` no `.gitignore` faz o `git add -A` deixar o
tarball de fora com rc=0 (medido em 2026-10-16), e o `.dockerignore` faz o mesmo com a imagem. Confira
`git check-ignore -v vendor/*.tgz` (tem de sair vazio) e o sha256 do arquivo **commitado**
(`git show HEAD:vendor/<arquivo>.tgz | sha256sum`), não o da cópia local.

O `vendor/README.md` do consumidor diz o que é a pasta, por que um binário no git, como atualizar e
qual ADR decidiu isso.

## Atualizar a lib num consumidor

Um script **do consumidor** (no repositório dele, por exemplo `atualizar-lib.sh <pacote> <versão>`) faz, nesta ordem:

1. `gh release download <tag> --repo <dono>/<repo-das-libs> --pattern '*.tgz' --dir vendor/`;
2. confere o sha256 contra o publicado nas notas da release;
3. roda a verificação por reconstrução (abaixo), se quiser a prova completa;
4. abre o `package.json` de dentro do tarball novo e procura script de instalação (`preinstall`,
   `install`, `postinstall`) que a versão anterior não tinha: o `npm install` da estação o executaria,
   e quem instala no servidor pode estar rodando como root;
5. troca o `file:` no `package.json` e roda **`npm install`**, que atualiza o lockfile. Copiar o `.tgz`
   sem esse passo é exatamente o caso do cache quente;
6. apaga o `.tgz` da versão anterior e roda a suíte, mais um `npm ci --cache "$(mktemp -d)"`;
7. depois do commit, confere o arquivo no commit: `git ls-files vendor/` com só a versão nova e
   `git show HEAD:vendor/<arquivo>.tgz | sha256sum` igual ao publicado;
8. roda o gate num `git worktree` limpo, no sha do commit e com `npm ci` de verdade. No checkout de
   trabalho, o `node_modules` e o cache já têm a versão nova, e um `.tgz` que ficou fora do commit
   passa.

## A release reconstruível (desenho)

Sem CI, a release sai da estação por script, e a prova de que o publicado é o testado é
**reconstruir**:

- **`release.sh <pacote> <versão> [--dry-run]`** recusa fora da branch principal, árvore suja, tag que
  já existe no remoto, `CHANGELOG.md` sem a seção da versão e bump patch quando o relatório da API
  mudou desde a última tag do pacote. Depois, nesta ordem: bump e commit **local** da versão; build e
  `npm pack` **uma vez só**; o gate sobre esse commit e sobre esse `.tgz` (o teste do pacote instalado
  usa exatamente o arquivo que vai subir); tag anotada `<pacote>-v<versão>`; push; `gh release create`
  com o mesmo `.tgz` e o sha256 nas notas; e o status `local/ci` no sha da tag. O `--dry-run` para
  antes do push e roda primeiro: publicar é irreversível. Se o gate reprovar, o commit local é desfeito
  e nada saiu da máquina.
- **O gate vem depois do bump, e não antes.** O número da versão está dentro do `package.json` do
  tarball: um gate rodado antes do bump testa outro arquivo, com outro sha256, e a prova de que o
  publicado é o testado deixa de valer. Achado na avaliação da skill em 2026-10-16.
- **`verificar-release.sh <tag>`** clona a tag num diretório vazio, reconstrói, baixa o asset publicado
  e compara os dois sha256.
- **Versão publicada nunca é republicada.** Quem já baixou tem o sha256 antigo, e retaguear quebra a
  verificação dele.

A reconstrução depende de o build ser determinístico. Dois builds seguidos com `tsc` e `npm pack` deram
o mesmo sha256 (medido em 2026-10-16), mas uma versão diferente do `tsc` muda o `dist`: fixe o
ferramental no lockfile da lib.

Com mais de um pacote no repositório, tag e release vão por pacote (`<pacote>-vX.Y.Z`), e o script de
release recebe o pacote como argumento. O Changesets resolve bump, changelog e tag por pacote, inclusive
privado (`privatePackages: { version: true, tag: true }`); com um pacote só, o script é menos
maquinário.
