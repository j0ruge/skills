---
campaign: 20261125-loja-skills
title: Validar o fluxo SDD da loja com uma correção pequena e comprovável
date: 2026-11-25
harness: codex
plan_model: gpt-6.2-astra
exec_model: gpt-6.2-sol
---

# Campanha — Piloto SDD da loja de skills

## Lotes

| Lot | Título | Ceiling | Itens |
|---|---|---|---|
| L1 | Preservar a atribuição da retrofit-watch na mesma mensagem | plan | 1 |

### L1 — Preservar a atribuição da retrofit-watch na mesma mensagem

- [ ] A skill de fora carregada na mesma mensagem apaga a atribuição da vigiada

O resultado esperado está no [TODO.md](../../../TODO.md). A carga de skill externa na mesma
mensagem não deve apagar a atribuição da vigiada. A carga externa numa mensagem posterior ainda
deve encerrar a atribuição. O plano e os testes do lote devem provar os dois casos.
Em transcript sintético na revisão `ba3da3c`, não houve pedido de retro em nenhum dos casos.

## Como operar

- Use o kit [sdd_agents](https://github.com/j0ruge/sdd_agents) para planejar, verificar e publicar
  em worktree próprio, a partir de `origin/main`. Rode `sdd-link-agents` no worktree antes do preflight.
- O `TEST_CMD` roda a suíte da loja e `test_retrofit_watch.py`, que cobre atribuição. Os testes
  do modo autônomo e de publicação da retrofit-watch não fazem parte deste gate.
  Para a suíte completa do plugin, use um `TMPDIR` sem ancestral com marcador `.git`.
- As três provas reais em `test_codex_distribution.py` precisam criar um namespace Bubblewrap.
  Rode-as no host com `python3 -m unittest discover -s tests -p 'test_codex_distribution.py'`.
  O sandbox do Codex não permite o Bubblewrap aninhado.
- Sem delegação assinada, o worker fica em `assisted`. A execução delegada no Codex exige os termos
  assinados no checkout principal, incluindo o aceite de sessões sem valor faturado informado.
  A aprovação do plano e o merge continuam com o mantenedor. O teto `plan` do lote não os delega.
- Faça o primeiro espelho com `todo-to-github-issues` a partir de `origin/main`. Confira o plano
  sem escrita antes de usar `--apply --limit 1`.
