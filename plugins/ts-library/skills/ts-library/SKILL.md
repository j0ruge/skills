---
name: ts-library
description: "Build and ship a TypeScript/Node library the 2026 way: ESM-only package, sensors on the packed tarball (publint, attw, API report), reproducible release, and vendored-tarball distribution when there is no registry or CI. Triggers — TypeScript library, npm package, extract lib, package.json exports, publint, attw, vendored tarball, library release"
license: MIT
metadata:
  author: Chewiesoft
  version: 0.2.0
---

# Biblioteca TypeScript/Node em 2026

Guia para criar, extrair de um workspace, revisar, versionar e distribuir uma biblioteca
TypeScript para Node. O ponto de partida é um caso real: uma lib de storage extraída de um monorepo
para servir mais de um sistema, numa organização com repositório privado, **sem GitHub Actions e sem
registro de pacotes**. As regras do pacote valem para qualquer lib; as de distribuição dizem quando
valem.

Cada afirmação desta skill tem uma de três marcas, e a diferença importa:

| Marca | Significa |
|---|---|
| **medido** | reproduzido em sessão, com o comando ao lado |
| **fonte** | fato externo com data de leitura; a fonte está em `references/fontes.md` |
| **desenho** | decidido e ainda não executado de ponta a ponta. Trate como proposta e prove antes de confiar |

Ao repassar um fato **medido** desta skill, diga que a medição é da skill e a data dela. Não escreva
como se você tivesse medido agora: quem lê decide diferente quando sabe que o número é de outra
máquina e de outra versão. Se o fato decide algo importante, meça de novo e cite o comando.

**Parta das restrições de quem pede.** O caso medido (repositório privado, sem CI, sem registro, imagem
`alpine` sem `git`, `npm ci --ignore-scripts`) é exemplo, não premissa. Se o pedido não diz como a lib
é instalada, pergunte, ou escreva a hipótese como hipótese. Uma recomendação justificada por uma
restrição que o usuário nunca citou é uma recomendação para outro projeto.

## Quando usar

- Criar uma lib nova, ou extrair código de um workspace para pacote que outro repositório instala.
- Revisar o `package.json`, o `tsconfig` ou o conteúdo de um pacote de biblioteca.
- Decidir como a lib chega ao consumidor: registro, dependência git, tarball versionado.
- Fazer uma release, ou atualizar a versão da lib num consumidor.

Antes de extrair, confira se há **um segundo consumidor de verdade**. Lib com um consumidor só é
acoplamento com cerimônia: o workspace já resolve, e cada ajuste de API vira release.

## O fluxo

### 1. A forma do pacote

O detalhe, com um `package.json` e um `tsconfig` anotados, está em `references/pacote.md`. Leia antes
de escrever ou revisar o manifesto. O resumo:

| Campo | Valor | O que evita |
|---|---|---|
| `type` | `module`, só ESM | o build CJS paralelo, que nenhum consumidor em Node 22+ precisa (**fonte**: `require(esm)` estável) |
| `exports` | aponta para `dist/`, com `types` **antes** de `default` em cada bloco | o TypeScript usa a primeira condição que casa; `types` depois de `default` resolve tipos errados |
| `exports` para `./src/*.ts` | nunca fora do workspace | o Node recusa remover tipos dentro de `node_modules` (**fonte**): só funciona no monorepo, com `tsx` |
| `files` | lista de permissão: `dist`, `src` sem testes, `README.md`, `AGENTS.md`, `CHANGELOG.md` | teste, `.env` e tarball velho dentro do pacote |
| `private` | `true` quando a lib não vai a registro público | o `npm publish` por engano para em `EPRIVATE` antes da rede, e o `npm pack` continua funcionando (**medido**) |
| `license` | `UNLICENSED` para código proprietário | o aviso do npm, e a dúvida sobre se o código pode ser usado |
| `engines.node` | o menor Node que a suíte prova | instalação silenciosa num Node que ninguém testou |
| `isolatedDeclarations` | `true` | export sem tipo explícito: a API pública passa a ser escrita, não inferida |

### 2. Os sensores

O gate da lib mede **o pacote como o consumidor o recebe**, e não o `src`. Um `exports` ou um `files`
errado passa em todos os testes do código-fonte. Comandos, ordem e casos sabotados estão em
`references/sensores.md`. Leia ao montar o gate ou quando um deles reprovar.

1. **Pacote instalado num consumidor vazio**: `npm pack`, instalar o `.tgz` num diretório novo,
   importar cada entrada com `node`, compilar um uso com `tsc` e conferir o conteúdo do pacote. Em
   cada Node suportado; o que falta na estação roda por container.
2. **`publint --strict`** e **`attw --pack --profile esm-only`**: os sensores usuais de `exports` e de
   resolução de tipos (**fonte**).
3. **Relatório da API pública** (API Extractor), versionado. O gate reprova quando o relatório gerado
   difere do versionado, e então toda mudança de API aparece no diff do PR (**desenho**).
4. **Contrato exportado**: se a lib define um port, exporte a suíte de contrato (`./testing`) para o
   consumidor provar o próprio adapter.
5. **Formato gravado**: se a lib persiste dados, um teste lê um objeto no formato da versão publicada.
   Mudar o formato não quebra tipo nenhum e deixa os dados de produção ilegíveis.
6. **Documentação que compila**: os blocos `typescript` do README passam na `typecheck`.

### 3. A versão

Semver estrito a partir da primeira release que um sistema em produção usa: lib que já guarda dado
de produção não é `0.x`. **Incompatível é o que exige mudar o consumidor ou os dados**: o port, as
classes e os códigos de erro, os nomes das variáveis de ambiente e o formato gravado. Versão
publicada nunca é republicada: um conserto vira patch novo.

### 4. A distribuição

Leia `references/distribuicao.md` antes de escolher: ele tem a tabela das quatro formas, a mecânica do
tarball versionado e o desenho da release reconstruível. A decisão em uma linha:

| Situação | Forma |
|---|---|
| há registro (npmjs, GitHub Packages, Verdaccio) e CI para publicar | registro, com token granular e provenance |
| repositório privado, sem CI, sem registro, e não se quer token novo em imagem nem em servidor | **tarball versionado**: o `.tgz` da release em `vendor/` do consumidor, declarado com `file:` |
| dependência git por tag | só se toda imagem de build tiver `git` e credencial de clone |

### 5. A documentação para agentes

O agente que trabalha no consumidor precisa da documentação **da versão instalada**. Ela vai dentro do
pacote (`README.md` e `AGENTS.md` no `files`), e o `CLAUDE.md` do consumidor aponta o caminho em
`node_modules/`. Leia `references/docs-para-agentes.md` ao escrever o `README.md`, o `AGENTS.md` ou o
ponteiro no consumidor.

### 6. A extração de um workspace

Histórico, cópia congelada, ADRs e a ordem dos passos estão em `references/extracao.md`. Leia antes de
tirar código de um monorepo que está em produção.

## Revisão rápida de um `package.json` de lib

Ao revisar, confira cada linha e diga o que ela evita, não só que falta:

- [ ] `exports` aponta para JavaScript compilado, nunca para `.ts`
- [ ] o build roda no `prepack`, e não no `prepublishOnly`, que o `npm pack` não chama (**medido**)
- [ ] `types` vem antes de `default` em cada bloco de `exports`
- [ ] `files` existe e é lista de permissão
- [ ] `private: true` e `license: UNLICENSED` quando o código é proprietário
- [ ] `type: module` e nenhum build CJS sem consumidor que o peça
- [ ] `engines.node` igual ao menor Node que a suíte prova
- [ ] o `tsconfig` tem `declaration`, `declarationMap` e `isolatedDeclarations`; os mapas resolvem porque o `src` vai no pacote
- [ ] o gate roda `publint` e `attw` sobre o tarball, não sobre a pasta

## Armadilhas medidas

- **`npm publish --dry-run` não respeita `private`.** Com `"private": true`, o dry-run imprime
  `+ pacote@versão` e sai 0. Só o publish real para em `EPRIVATE`. Para provar a proteção sem
  publicar, aponte para um registro inexistente com um token falso:
  `npm publish --registry=http://127.0.0.1:9/ --//127.0.0.1:9/:_authToken=falso` dá `EPRIVATE` com o
  campo e `ECONNREFUSED` sem ele. Sem o token, os dois casos param antes em `ENEEDAUTH`, e o teste não
  distingue nada (**medido**, npm 12.0.2).
- **O cache do npm engole o tarball trocado.** Num consumidor com `file:vendor/x.tgz`, trocar o `.tgz`
  sem rodar `npm install` passa no `npm ci` da estação com rc=0 e instala o conteúdo **antigo**: o npm
  serve os bytes do cache global pelo `integrity` do lockfile. Com cache vazio, que é o caso do
  `docker build` e do CI, o mesmo `npm ci` reprova com `EINTEGRITY` (**medido**, npm 12.0.2). Daí o
  sensor que compara o `sha512` do `.tgz` com o `integrity` do lockfile, e daí o caso sabotado rodar
  com `npm ci --cache "$(mktemp -d)"`.
- **`*.tgz` no `.gitignore` tira o tarball do commit sem aviso.** Num consumidor com `vendor/`, o
  `git add -A` sai com rc=0 e o commit fica sem o `.tgz`; só o `git add` explícito do arquivo recusa e
  avisa (**medido**, git, 2026-10-16). Confira no ponto de entrega, e não na cópia local:
  `git check-ignore -v vendor/*.tgz` vazio, `git ls-files vendor/` com o arquivo, e
  `git show HEAD:vendor/<arquivo>.tgz | sha256sum` igual ao publicado. Um `*.tgz` no `.dockerignore`
  tira o arquivo da imagem do mesmo jeito, e aí o `npm ci` do build quebra no servidor.
- **`declarationMap` e `sourceMap` apontam para o `src` ao lado do `dist`.** Se o `src` não vai no pacote, os mapas
  quebram e o "ir para a definição" cai no `.d.ts`. Ou o `src` vai junto, ou os mapas saem.
- **TypeScript 7.0 não tem API programática estável até a 7.1** (**fonte**). Ferramenta que usa a API
  (API Extractor, typescript-eslint) não acompanha o compilador novo. Fixe o TypeScript da lib na
  versão dos consumidores e migre como tarefa própria.
- **`npm pack` é reproduzível**: dois builds seguidos com o mesmo lockfile deram o mesmo sha256
  (**medido**, `tsc` 5.9 e npm 12.0.2). É o que torna possível provar que o publicado é o testado
  reconstruindo a tag.

## O que não fazer, e por quê

| Prática | Por que não aqui |
|---|---|
| Build CJS ao lado do ESM | nenhum consumidor em Node 22+ precisa; é o dobro de saída para testar |
| Bundler (tsdown, tsup) numa lib de vários pontos de entrada | o `tsc` arquivo a arquivo é a recomendação para esse caso (**fonte**); bundler serve a entrada única |
| `llms.txt` dentro do pacote | o `llms.txt` é convenção de site; no pacote, o padrão é `AGENTS.md` e documentação apontada pelo consumidor (**fonte**) |
| Changesets com um pacote só | é o padrão de fato em monorepo e aceita pacote privado, mas com um pacote o script de release é menos maquinário. Revisite no segundo pacote |
| Provenance do npm sem CI | exige OIDC de um CI; sem ele, a reconstrução da tag é a prova |
| `sideEffects: false` em lib de servidor | só bundler lê |
| Skill que ensina a **API** da lib | é uma segunda cópia da documentação, presa à versão da skill e não à instalada. A API mora no `AGENTS.md` do pacote |

## Referências

| Arquivo | Leia quando |
|---|---|
| `references/pacote.md` | for escrever ou revisar o `package.json` e o `tsconfig` |
| `references/sensores.md` | for montar o gate, ou um sensor reprovar |
| `references/distribuicao.md` | for escolher como a lib chega ao consumidor, fazer uma release ou atualizar a lib num consumidor |
| `references/docs-para-agentes.md` | for escrever o `README.md`, o `AGENTS.md` ou o ponteiro no consumidor |
| `references/extracao.md` | for tirar uma lib de um workspace |
| `references/fontes.md` | for conferir se um fato externo (calendário do Node, versão do TypeScript) ainda vale |
