# Changelog — todo-to-github-issues

Changelog **versionado** do plugin. O registro por sessão da skill fica em
`skills/todo-to-github-issues/CHANGELOG.md`.

## [2.1.0] — 2026-09-28

Conformidade com a spec do agentskills.io, apontada pelo `skill-quality-audit` v0.2.0: 6 avisos → 3,
e os 3 que ficam são falso positivo (ver B7 abaixo). Minor porque o frontmatter muda; nenhum script
muda.

### Changed

- **A4, `user_invocable` e `argument_description` saem do topo do frontmatter e vão para
  `metadata`, em texto.** A doc do Claude Code (code.claude.com/docs/en/skills, "Frontmatter
  reference") só reconhece os campos com hífen (`user-invocable`, `argument-hint`) e diz que um
  campo que não casa com a tabela, hífen incluído, é ignorado sem erro. Os dois nunca tiveram
  efeito: `user_invocable: true` repetia o default de `user-invocable` (`true`), e o
  `argument_description` nunca apareceu no autocomplete. Converter para `argument-hint` ligaria um
  hint que a skill nunca teve, com um campo fora da spec: o `skills-ref` reprova, e o upload para
  claude.ai ou a Skills API falha com "Unexpected key(s)". Em `metadata` o texto continua no
  arquivo para quem o lê, e o comportamento é o mesmo de antes.

### Fixed

- **B2, quatro scripts contados como órfãos.** O `SKILL.md` invoca o espelho como
  `{SKILL_DIR}/scripts/todo_issues.py`, forma que o auditor não reconhece (o normalizador dele trata
  `<x>/`, `{{x}}/` e `MAIUSCULA/`, não `{x}/`); `kit.py`, `report.py` e `todo_format.py` são módulos
  importados por ele e não eram citados em lugar nenhum. Nova seção `## Scripts disponíveis`: os
  seis arquivos de `scripts/`, o que cada um é e quando abrir. O bloco `## Comando` não muda.
- **B6, `scripts/__pycache__`.** Não era versionado (o `.gitignore` da raiz já ignora
  `__pycache__/`); era lixo local, movido para a lixeira.

### Mantido

- **B7, `kit.py`, `report.py` e `todo_format.py` sem shebang.** São módulos (sem `__main__`, sem
  argparse, modo 644) que `todo_issues.py` importa conforme o modo. Um shebang anunciaria uma
  execução direta que não existe; o B7 e o F3 do auditor sobre eles são falso positivo.
- Números: `SKILL.md` 186 → 200 linhas (13.110 → 14.238 chars).
- Como reverter: `git revert` do commit que traz esta entrada.

## [2.0.2] — 2026-09-26

### Fixed

- **`--audit` / `--fix` quebravam linha numa largura que o kit não tem.** O `todo_format.py`
  guardava um `WRAP = 100` próprio, de antes de o kit ter regra de largura. A regra 5 do sensor do
  kit chegou em 2026-09-25 com `WIDTH_CAP=120`, e desde então a skill dava uma segunda opinião:
  no `TODO.md` do próprio kit, que o sensor chama de limpo (82 achados, âncoras no alvo), o
  `--audit` acusava 42 linhas longas e **6 itens acima do teto de 8 linhas** que só existiam na
  quebra em 100. A largura agora é **lida do sensor** (`kit.width_cap`, `^WIDTH_CAP=N` na coluna
  0); com ela o mesmo `--audit` dá `auto=0 manual=0`. Kit sem `WIDTH_CAP` (anterior à regra):
  `--audit`/`--fix` recusam com rc 3 e o `git pull` que resolve, como o resto do preflight. O
  espelho não usa a largura e não muda.
- **`test_todo_issues.py` reprovava `body edit -> 1 update` no `TODO.md` real do kit** sem defeito
  no espelho: a sonda editava o item 3 pela **última linha**, uma atribuição (`— descoberto por …`)
  que se repete em 7 itens, e o `replace(…, 1)` editava o primeiro deles (#102). Agora edita o
  bloco inteiro do item, que é único.

### Added

- Testes da largura em `test_todo_format.py`: a largura usada é a do kit; uma linha entre 100 e o
  `WIDTH_CAP` **não** é quebrada (a regressão); `width_cap` ignora o nome citado num comentário; um
  kit sem `WIDTH_CAP` é recusado com rc 3. Cada regra foi sabotada numa cópia e o teste ficou
  vermelho (o probe do comentário só passou a morder depois de a fixture perder o texto depois do
  número).
- `SKILL.md`: o requisito do kit com `WIDTH_CAP`, e a nota de que o número da âncora é texto — um
  PR que desloca linhas gera `UPDATE` em massa, que se prova com `--dump` antes do `--apply`.

## [2.0.1] — 2026-09-26

A skill entra no marketplace. Até aqui ela vivia só em `~/.claude/skills/`, fora de qualquer
repositório; a 2.0.0 é o estado em que ela rodava local, e esta versão traz a primeira correção
publicada.

### Fixed

- **`--audit` / `--fix` contavam toda âncora como inválida.** O ADR 0011 do kit sdd (2026-09-25)
  passou a resolver a âncora `arquivo:linha` contra o repositório **do arquivo checado**, e a skill
  media uma cópia gravada em `/tmp` — fora de qualquer repositório. Resultado medido no `TODO.md`
  do `sales_quote`: 188 violações acusadas onde o sensor do kit vê 97. A cópia agora é gravada ao
  lado do arquivo (oculta, apagada no `finally`), como o `with_decided` do próprio kit faz.
- **5 casos de `test_todo_format.py` vermelhos** pelo mesmo motivo: as fixtures ancoravam em
  arquivos que não existiam (`bin/x:1`, `a:1`). Ganharam um repositório temporário com os arquivos
  citados, e cada item cita um símbolo presente no arquivo ancorado. Sensor provado por sabotagem:
  devolver a cópia a `/tmp` traz de volta exatamente as 5 falhas.

### Changed

- `SKILL.md`: linha nova na tabela de MANUAL para âncora que não aponta arquivo do repo (com o
  `check-todo.sh --anchors` do kit), e o porquê da cópia ao lado do arquivo.
- `description` encurtada de 839 para 369 caracteres (cap do marketplace: 500).
- O comando do `SKILL.md` apontava `~/.claude/skills/todo-to-github-issues/scripts/`, caminho que só
  existe na instalação local por symlink — instalado pelo marketplace (cache de plugins) ou no Cursor,
  o primeiro comando quebraria. Passa a `{SKILL_DIR}/scripts/`, a convenção da skill `codereview`.
- Entrada no `CURSOR_SKILL_MAP` do `install.py` (a pasta `scripts/` é copiada inteira).

## [2.0.0] — antes de 2026-09-26

Estado local, não publicado: espelho idempotente `TODO.md` → issues (`plan` / `apply` /
`--close-orphans`), `--audit` / `--fix` contra o sensor do kit sdd, e o relatório `ACHADOS-*.md`.
