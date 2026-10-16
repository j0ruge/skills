# Changelog — `ts-library`

Formato: [Semantic Versioning](https://semver.org/)

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
