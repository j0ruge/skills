# Changelog — skill-quality-audit

## [0.4.0] — 2026-09-29

Entrada no marketplace. O plugin reúne a família de auditoria de skills, que vivia no harness
Hermes do autor: `skill-quality-audit` (porta de entrada) e as irmãs `skill-self-containment`,
`skill-claim-check` e `skill-refactoring`. Esta cópia passa a ser a oficial; o Hermes a lê por
`skills.external_dirs`.

### Por que um plugin só

As quatro vêm juntas porque se ajudam: a porta de entrada fixa a ordem das fases (estrutura,
claims, progressive disclosure, integração, verificação final) e cada irmã decide uma fase. O
`--family` do auditor acha as irmãs como pastas vizinhas; em plugins separados, cada uma iria
para um diretório diferente e as irmãs sairiam como SKIP. No Cursor, o `install.py` copia as
quatro para `skills/` lado a lado quando as quatro são marcadas, e a família continua se achando.

### Changed

- Descrições no padrão do marketplace: função e gatilho nos primeiros 60 chars (o que o índice do
  Hermes mostra), linha `Triggers —`, até 350 chars. A da `skill-claim-check` tinha 677 e abria
  com "Use SEMPRE".
- As irmãs mandavam rodar um gate estrutural que ficava no harness de origem, fora da skill. O
  gate passa a ser a auditoria simples da `skill-quality-audit`, que vem no mesmo plugin.
- E1 (vínculo da família): sem bloco `metadata`, que o instalador do Cursor remove, vínculo
  ausente vira INFO em vez de AVISO, e `--family --strict` deixa de reprovar a instalação do
  Cursor.

### Added

- Evals de gatilho (`assets/trigger-evals.json`) nas três irmãs, com quase-acertos entre elas.
- Seções "Erros comuns" na `skill-claim-check` e "Relação com outras skills" nas três irmãs, que
  dizem como as quatro se acham e em que ponto cada uma ajuda.
- Testes `TestFamiliaNoPlugin` (38 no total).

### Changed (exemplos)

- Casos reais contados pelo mecanismo, com exemplos generalizados; a reference do estudo de caso
  da `skill-refactoring` passou a se chamar `estudo-de-caso-monitoramento.md`.

Histórico anterior de cada skill: `skills/<skill>/CHANGELOG.md`.
