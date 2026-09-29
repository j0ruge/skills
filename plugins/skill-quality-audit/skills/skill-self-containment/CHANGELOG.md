# Changelog: skill-self-containment

## [0.4.0] - 2026-09-29 - entra no marketplace

**Motivação:** a família de auditoria de skills vira o plugin `skill-quality-audit` do
marketplace, que passa a ser a fonte oficial. A skill mandava rodar um gate que vivia no harness
de origem e não vinha junto com ela, justamente o tipo de dependência que ela ensina a caçar.

**O que foi feito:**

- Descrição no padrão do marketplace: função e gatilho nos primeiros 60 chars, linha `Triggers —`.
  `metadata.version` alinhada à do plugin.
- Passo 7: o gate estrutural passa a ser a auditoria simples da `skill-quality-audit`, que vem no
  mesmo plugin; gate próprio do harness vira opcional (ela o roda como G1).
- Poka-yoke reescrito sem script do harness: hook `pre-commit`, cron no delta e varredura
  completa só para medir baseline.
- Greps dos Passos 2 e 7 procuram a home de qualquer harness (`~/.` seguido de letra) e `/Users/`.
- Caso real da seção de abrangência com exemplo generalizado. Vínculo com `skill-script-organization` removido
  (não vem no plugin); a regra "script de uso vive em `scripts/` da skill" foi para o Passo 4.
- "Relação com outras skills" diz como as quatro se acham e em que ponto cada uma ajuda.

**Como reverter:** `git revert` do commit que traz esta entrada.

## Histórico anterior (harness de origem, antes do marketplace)

- 2026-09-29: `metadata.author`; exemplos didáticos viraram placeholder (o auditor os lia como
  arquivo ausente).
- 2026-09-27: documentado o watcher diário do harness (arquivo morto fora do escopo, varredura
  completa com caminhos relativos).
- 2026-09-23: frontmatter na spec (tags e vínculos em `metadata.hermes`, lista de bloco),
  validador `skills-ref`/`agentskills` no Passo 7, baseline medido, vínculo com a
  `skill-quality-audit`.
- 2026-09-06: poka-yoke do padrão (sensor automático no delta) e correção do falso positivo de
  reticências no gate.
- 2026-09-04: seção de abrangência (skill por família de tarefa, não por instância).
- 2026-08-31: citar reference de outra skill deixou de reprovar o gate.
- 2026-08-20: criação, com o workflow de 7 passos e o checklist final.
