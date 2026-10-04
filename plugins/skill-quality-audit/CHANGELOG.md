# Changelog — skill-quality-audit

## [0.5.0] — 2026-10-04

### `skill-quality-audit` 0.5.0: campo de topo do Claude Code é custo aceito em plugin só `claude-code`

O `ticket` saía com ERRO G2 e AVISO A4 pelo `argument-hint` no topo do frontmatter, e a correção
que o aviso sugeria ("mover para metadata") pioraria a skill: a doc do Claude Code
(code.claude.com/docs/en/skills, "Frontmatter reference") diz que o `argument-hint` é a dica do
autocomplete e que `metadata` é para ferramenta própria — o Claude Code não age sobre o conteúdo.
Movido, o `/ticket` perde a dica `start (open) | split | close | status`. O custo de mantê-lo é o
upload para claude.ai/API falhar, que não alcança um plugin declarado só para o Claude Code.

- **A4:** `CLAUDE_CODE_TOP_FIELDS` (os 14 campos da tabela da doc fora da spec) vira INFO "custo
  aceito" quando o `<plugin>/.claude-plugin/plugin.json` declara `platforms: ["claude-code"]`.
  Sem manifesto, ou com outra plataforma (`cursor`), segue AVISO.
- **G2:** reprovação do `skills-ref` cuja **toda** linha de erro é `Unexpected fields` com campos
  aceitos vira INFO. Antes nem os campos do Hermes (`platforms`), já INFO no A4, escapavam do ERRO.
  Outro erro na saída, ou um campo fora da lista, mantém o ERRO.
- **Seis testes novos** (`TestCamposClaudeCodeNoTopo`), três RED antes do código; três sabotagens
  (ignorar `platforms`, aceitar com outra linha de erro, não checar o subconjunto) deixam testes
  vermelhos. Caso real: `ticket` 1.8.0 passou de 1 ERRO + 1 AVISO para 0 + 0 com o `skills-ref`
  0.1.1 de verdade.
- `scripts/validate-versions.py` do marketplace aplica a mesma regra ao warning do check 7 (lista
  duplicada lá; o comentário pede para manter as duas iguais). Sondado: com `cursor` no `platforms`
  do `ticket` o warning volta.
- `references/checks.md` (A4, G2) e a tabela de erros comuns do `SKILL.md`.

## [0.4.1] — 2026-10-04

### `skill-quality-audit` 0.4.1: o B5 acha o CHANGELOG do plugin

O B5 só olhava `<skill>/CHANGELOG.md`. Toda skill de plugin de marketplace (`<plugin>/skills/<skill>/`)
saía com `CHANGELOG.md ausente`, ERRO sem `--no-changelog-required` e INFO com ela, embora o CHANGELOG
versionado do plugin estivesse em `<plugin>/CHANGELOG.md`. O falso positivo apareceu na auditoria da
`coderabbit-pr` (plugin `codereview`), e o único jeito de calá-lo pela skill era um segundo CHANGELOG
dentro dela, que partiria o histórico em dois.

- **Agora o B5 aceita o CHANGELOG do plugin** quando `<plugin>/.claude-plugin/plugin.json` existe ao
  lado dele, e diz o caminho num OK. Sem o manifesto, um CHANGELOG solto dois níveis acima não conta.
- **Três testes novos** em `tests/test_audit_skill_quality.py`: o caso do plugin (RED antes:
  `[ERRO] B5 CHANGELOG.md ausente`) e dois controles negativos (sem manifesto; plugin sem CHANGELOG).
  Sabotagem: tirar a exigência do manifesto deixa o primeiro controle vermelho, e tirar a do arquivo
  deixa o segundo. A condição `d.parent.name == "skills"` do primeiro rascunho saiu: nenhum probe a
  distinguia, e skill em outro subdiretório do plugin continua sendo do plugin.
- `references/checks.md`: a linha do B5 diz as duas origens.

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
