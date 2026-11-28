# ADR 0001 — Publicação de retrofits de skills locais

- **Status**: proposed (—, 2026-11-27)
- **Spec**: docs/handoffs/20261127-retrofit-watch-050/00-missao.md

## Contexto

A `retrofit-watch` precisa preparar lotes de skills locais enquanto o mantenedor trabalha
em outra branch. A [spec de 25/11](../superpowers/specs/2026-11-25-retrofit-watch-lean-auto-design.md)
define a janela de observação que autoriza a passagem de `auto-dry` para `auto`.

## Decisão

- Identificar cada repositório pela origem e exigir sua presença em `lean_auto`. Manter um
  clone dedicado da `main` e um worktree por lote.
- Preservar `auto-dry` enquanto a janela da v2 estiver incompleta ou ilegível. O ensaio roda
  o pre-push efetivo com os argumentos e a entrada que o Git entregaria. A aprovação
  acompanha o patch validado e o Git repete o hook no push autorizado.
- Recalcular o modo após um revert conforme a spec e registrar as transições. A entrega da
  loja entra por PR para `main`, sob a delegação do worker. A adoção nos repositórios
  privados usa seu fluxo próprio de autorização.

## Consequências

O ensaio e o push validam o mesmo contrato do repositório. O clone dedicado mantém a
operação independente do checkout de trabalho do mantenedor. A implementação reaproveita
a porta existente e paga o custo de manter o clone e repetir a validação no push.
