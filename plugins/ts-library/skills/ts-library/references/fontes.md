# Fatos externos, com data e fonte

Lidos em 2026-10-16. Confira de novo quando a data ficar velha: calendário de runtime e versão de
compilador são os fatos que mais apodrecem.

| Fato | Fonte |
|---|---|
| O Node recusa remover tipos de arquivo `.ts` dentro de `node_modules` | [Node.js — TypeScript](https://nodejs.org/download/nightly/v26.0.0-nightly20251019481b9b11b3/docs/api/typescript.html) |
| `require(esm)` estável no Node 22+; a recomendação de 2026 para lib nova é só ESM, com `types` primeiro no `exports` | [guia de publicação 2026](https://www.pkgpulse.com/guides/publishing-npm-package-complete-guide-2026), [ts-packaging](https://claudskills.com/skills/ts-packaging/SKILL.md) |
| TypeScript 7.0 (compilador em Go) saiu em 2026-07-08; a API programática estável só vem na 7.1 | [InfoQ](https://infoq.com/news/2026/08/typescript-7-released/), [Visual Studio Magazine](https://visualstudiomagazine.com/articles/2026/07/08/typescript-7-arrives-to-rock-vs-code-with-go-powered-speed.aspx) |
| Node 22: fim da vida em 2027-04-30. Node 24: sai do Active LTS em 2026-10-20. Node 26: LTS em 2026-10-28. A partir do 27, um release por ano | [endoflife — Node.js 22](https://endoflife.ai/nodejs/22), [um release por ano](https://ecorpit.com/nodejs-one-release-per-year-node-27-lts-upgrade-cadence-2026/) |
| `publint` e `attw` são os sensores usuais de `exports` e tipos; `attw --profile esm-only` para lib só ESM | [tsdown — lint](https://tsdown.dev/options/lint), [README do attw](https://cdn.jsdelivr.net/npm/@arethetypeswrong/cli@0.18.2/README.md), [exemplo de gate](https://github.com/callstack/agent-device/pull/1578) |
| `tsc` arquivo a arquivo para lib de vários pontos de entrada; bundler (tsdown) para entrada única; o tsup recomenda o tsdown como sucessor | [ts-packaging](https://claudskills.com/skills/ts-packaging/SKILL.md), [supabase-js #1961](https://github.com/supabase/supabase-js/pull/1961) |
| Relatório de API (API Extractor) e gate de breaking change sem bump major | [API Extractor](https://api-extractor.com/), [`@clerk/break-check`](https://socket.dev/npm/package/@clerk/break-check) |
| Documentação para agentes dentro do pacote; `llms.txt` é para site | [Next.js — AI agents](https://nextjs.org/docs/app/guides/ai-agents), [Mysten — LLM docs](https://sdk.mystenlabs.com/sui/llm-docs.md), [Documentation stack for AI agents](https://ravichaganti.com/blog/documentation-stack-for-ai-agents/) |
| Changesets versiona e tagueia pacote privado com `privatePackages` | [Changesets is a game changer](https://levelup.gitconnected.com/changesets-is-a-game-changer-fe752af6a8cc) |
| GitHub Packages: escopo é a conta dona; token clássico com `read:packages` | [GitHub Docs — npm registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-npm-registry) (lido em 2026-10-16) |
