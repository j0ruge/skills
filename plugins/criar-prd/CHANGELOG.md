# Changelog

## [0.1.1] — 2026-10-22

Distribuição individual no catálogo Codex após instalação isolada, descoberta e smoke seguro de entrada dos workflows. Conteúdo canônico compartilhado com Claude Code/Cursor. Comando adaptado por geração, com nome preservado, comandos legados desativados e templates locais ao pacote. Requisitos e limites em `docs/codex/compatibility.md` na raiz do marketplace.

## [0.1.0] — 2026-09-04

- Initial release: packaged the personal `/criar-prd` command as a marketplace plugin.
- Ships its own `templates/prd-template.md`, resolved via `${CLAUDE_PLUGIN_ROOT}` — a
  project-local `templates/prd-template.md` still wins when present. Without this the
  command referenced a template no consumer had.
- Feature slug validated as a single kebab-case segment before it reaches any path.
