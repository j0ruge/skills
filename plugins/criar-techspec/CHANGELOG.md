# Changelog

## [0.1.1] — 2026-10-22

Distribuição individual no catálogo Codex após instalação isolada, descoberta e smoke seguro de entrada dos workflows. Conteúdo canônico compartilhado com Claude Code/Cursor. Comando adaptado por geração, com nome preservado, comandos legados desativados e templates locais ao pacote. Requisitos e limites em `docs/codex/compatibility.md` na raiz do marketplace.

## [0.1.0] — 2026-09-04

- Initial release: packaged the personal `/criar-techspec` command as a marketplace plugin.
- Ships its own `templates/techspec-template.md`, resolved via `${CLAUDE_PLUGIN_ROOT}`, with
  a project-local template taking precedence. The missing-template hard stop is gone; a
  missing PRD still stops the command, since there is nothing to specify without one.
- Decoupled from the origin project: the fixed `.agents/rules/*.md` list, the `graphify`
  CLI, `docs/stack_tec.md` and the Vite-specific env rule became a discovery step over
  whatever conventions the target project actually has.
- Feature slug validated as a single kebab-case segment before it reaches any path.
- Section-retention contract stated once: the command omits only what the template marks
  optional, and the template marks exactly one section (Observabilidade) as such.
