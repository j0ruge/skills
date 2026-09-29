# Changelog: skill-claim-check

## [0.4.0] - 2026-09-29 - entra no marketplace

**Motivação:** a família de auditoria de skills vira o plugin `skill-quality-audit` do
marketplace, que passa a ser a fonte oficial.

**O que foi feito:**

- Descrição de 677 para menos de 350 chars, sem "Use SEMPRE", função primeiro e linha
  `Triggers —`. `metadata.version` alinhada à do plugin.
- Tabela de vizinhas, regra 4, regra 6 e checklist: o gate estrutural passa a ser a auditoria
  simples da `skill-quality-audit`, no lugar de um script do harness de origem.
- Seções novas: "Erros comuns" (achado F2 do auditor) e "Relação com outras skills".
  `assets/trigger-evals.json` com casos de gatilho (achado F4).
- Ferramenta: `<dir-da-skill>` como uso principal; `<cat>/<skill>` fica para o layout do Hermes.
  Registrado que a `skill-quality-audit` tem o mesmo scanner, com paridade testada.

**Como reverter:** `git revert` do commit que traz esta entrada.

## Histórico anterior (harness de origem, antes do marketplace)

- 2026-09-29: `metadata.author`; exemplos didáticos viraram placeholder.
- 2026-09-23: vínculo com a `skill-quality-audit`; `listar-afirmacoes.sh` aceita diretório de
  skill e `--help`, e ignora blocos `~~~` (paridade com o auditor).
- 2026-09-12: regra 6, "script funcional" exige execução segura (caso válido e inválido, `rc`,
  artefato observado).
- 2026-08-28: criação, a partir de dois erros do mesmo dia. (1) Uma reference afirmava "cada
  arquivo de contexto é limitado a 20.000 caracteres", mas o código deriva o limite e 20 mil é
  só o piso. (2) Um `.gitignore` com padrão sem âncora (`hermes-agent/`) engolia também a skill
  de mesmo nome, e nenhuma edição nela era commitada.
