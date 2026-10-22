# Changelog

## [0.1.1] — 2026-10-22

Distribuição individual no catálogo Codex após instalação isolada, descoberta e smoke seguro de entrada dos workflows. Conteúdo canônico compartilhado com Claude Code/Cursor. Comando adaptado por geração, com nome preservado, comandos legados desativados e templates locais ao pacote. Requisitos e limites em `docs/codex/compatibility.md` na raiz do marketplace.

## [0.1.0] — 2026-09-04

- Initial release: packaged the personal `/executar-task` command as a marketplace plugin.
- Decoupled from the origin project: the fixed `.agents/rules/*.md` list, the `graphify`
  CLI, the hardcoded `yarn test` / `npx playwright test` / `yarn qa` commands, the
  `docs/notas/…` and `docs/stack_tec.md` paths, the JSDoc-in-pt-BR requirement and the
  Vite env rule now resolve against whatever the target project actually uses — the test
  command is discovered from the build manifest instead of assumed.
- Feature slug validated as a single kebab-case segment, and the task number as an integer,
  before either reaches a path.
