# Changelog: skill-refactoring

## [0.4.0] - 2026-09-29 - entra no marketplace

**Motivação:** a família de auditoria de skills vira o plugin `skill-quality-audit` do
marketplace, que passa a ser a fonte oficial.

**O que foi feito:**

- Descrição no padrão do marketplace: função e gatilho nos primeiros 60 chars, linha `Triggers —`.
  `metadata.version` alinhada à do plugin.
- Passo 6: a auditoria simples da `skill-quality-audit` no lugar do gate do harness de origem.
- Casos reais contados pelo mecanismo, com exemplos generalizados; a reference do estudo de caso
  passou a se chamar `references/estudo-de-caso-monitoramento.md`.
- As duas references citadas com o momento de ler (achado F1 do auditor); evals de gatilho em
  `assets/trigger-evals.json` (achado F4); "Relação com outras skills" diz como as quatro se acham.

**Como reverter:** `git revert` do commit que traz esta entrada.

## Histórico anterior (harness de origem, antes do marketplace)

- 2026-09-29: `metadata.author`.
- 2026-09-23: gatilho por família; caso de monitoramento movido para reference; limites
  rotulados (500 linhas pela spec; 20K e 15K chars e 400 linhas como heurística local); CLI
  inexistente corrigida na reference do Teste 0; vínculos com as irmãs.
- 2026-08-19: início do CHANGELOG (histórico anterior não registrado).
