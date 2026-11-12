# Changelog — rust (experimental)

Skill sem versão: fica em `experimental/`, fora dos catálogos (ver `../README.md`).
Cada entrada leva a data e o motivo.

## 2026-11-12 — entrada no repositório

A skill nasceu como skill pessoal do Codex em `~/.codex/skills/rust`, fora do git. Ela veio para
`experimental/rust/` sem nenhuma mudança de conteúdo (`diff -r` vazio contra a origem), e
`~/.codex/skills/rust` passou a ser um symlink para esta pasta. A única novidade é este arquivo.

**Por que é experimental:** a skill foi escrita e conferida numa aplicação só, um app desktop de
tarefas com GPUI 0.2.2, Rust 1.97.0 e Ubuntu 24.04 x86_64. Nenhum outro projeto Rust a usou ainda.

Dívida que veio da origem, registrada pelo auditor da `skill-quality-audit` (`--claims --desc-budget 0`)
e não corrigida nesta entrada:

- F2: o `SKILL.md` não tem seção de armadilhas.
- F4: não há evals de gatilho nem de comportamento.
- A `description` começa com "Use when…" e por isso fica fora do padrão de `plugins/` (ver
  `CLAUDE.md`, *Skill description guidelines*). Isso precisa mudar antes de uma promoção.
