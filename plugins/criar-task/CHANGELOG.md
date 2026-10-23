# Changelog

## [0.1.1] — 2026-10-22

Distribuição individual no catálogo Codex após instalação isolada, descoberta e smoke seguro de entrada dos workflows. Conteúdo canônico compartilhado com Claude Code/Cursor. Comando adaptado por geração, com nome preservado, comandos legados desativados e templates locais ao pacote. Requisitos e limites em `docs/codex/compatibility.md` na raiz do marketplace.

## [0.1.0] — 2026-09-04

- Initial release: packaged the personal `/criar-task` command as a marketplace plugin.
- Ships `templates/tasks-template.md` and `templates/task-template.md`, resolved via
  `${CLAUDE_PLUGIN_ROOT}`, with project-local templates taking precedence.
- Feature slug validated as a single kebab-case segment before it reaches any path.
