# Changelog — todo-to-github-issues

Changelog **versionado** do plugin. O registro por sessão da skill fica em
`skills/todo-to-github-issues/CHANGELOG.md`.

## [2.3.1] — 2026-10-04

Patch: o contrato do `--close-orphans` não muda (fecha só a órfã cujo último texto trazia
`RESOLVED by`); a busca da remoção deixa de perder commits, e a órfã sem remoção achada deixa de
ser empurrada para `not planned`.

### Fixed

- **A remoção é achada pela chave quando o título não acha.** O `last_text()` procurava candidatos só
  pelo `git log -S` dos 40 primeiros caracteres do título, e esse filtro é cego duas vezes: o parser
  normaliza espaços repetidos (`re.sub(r"\s+", " ")`), então um título com `` `^  ok    ` `` nunca
  aparece no arquivo como a issue o escreve; e o commit que apaga o item e cita o título na seção
  decidida não muda a contagem. Agora, quando nenhum candidato do `-S` serve, o script percorre todo
  commit que tocou o arquivo, do mais novo ao mais antigo, com o mesmo teste da chave (o pai tem o
  item, o commit não tem). Cada leitura do arquivo fica em cache durante a execução: 3 ms por versão,
  ~1,2 s para os 352 commits do `TODO.md` do kit, medido em 2026-10-04.
- **`removal not found` deixa de virar "not planned".** O plano dizia `no RESOLVED by — close by hand`
  também quando não achava a remoção, e o `--close-orphans` sugeria `--reason "not planned"`. Agora a
  linha diz `last text unknown — read it before closing`, e o `SKIP` manda ler o último texto antes de
  escolher o motivo.

Medido no re-sync do kit em 2026-10-04: a #113 (consertada, `RESOLVED by 0521972`) saiu como
`removal not found` e só não foi fechada como `not planned` porque o operador sabia do conserto; as
#143, #154 e #158 (decididas, movidas para a seção decidida com o mesmo título) também saíram sem
commit. Com a 2.3.1, as quatro saem com a remoção certa (`8a45e71 · fixed by 0521972`, `8577df6`,
`db2eee1`, `db2eee1`), e as que o `-S` já achava respondem igual (#216, #63). Testes: 71 → 73 `ok`;
o teste `q3` mantém "o commit que só citou o título nunca é a remoção" e passa a esperar a remoção
verdadeira em vez de `None`. Sabotado numa cópia: sem o percurso, os dois testes novos ficam
vermelhos; sem a 2ª metade do teste da chave, o `q3` fica vermelho.

## [2.3.0] — 2026-10-02

Minor porque a saída do plano e o comportamento do `--close-orphans` mudam.

### Changed

- **A órfã é julgada pelo ÚLTIMO texto do item, lido no commit que o removeu.** `last_text()` acha
  esse commit pelo `git log -S` do título, lê o `TODO.md` do pai com o mesmo `parse()` e casa o item
  pela `todo-key` da issue (nunca pelo título: dois títulos com os mesmos 40 caracteres se
  confundiriam). O commit só vale como remoção se o pai tem o item **e** ele mesmo não tem; na dúvida
  responde `None`, nunca um commit errado. Custo medido: ~0,1 s por órfã no histórico do kit.
- **`ORPHAN` diz onde e por quê:** `left the file in 156ebf9 · fixed by 813f808`, ou
  `no RESOLVED by — close by hand`, ou `removal not found in history`; o resumo ganha
  `orphans=N (fixed M)`.
- **`--close-orphans` fecha só a órfã consertada**, como `completed`, com comentário que cita o
  conserto e a remoção. A que saiu sem `RESOLVED by` (decidida, refutada, adiada) é pulada com
  `SKIP` e o comando para fechá-la à mão como `not planned`. Antes ele fechava **todas** como
  concluídas, com "O item saiu de `TODO.md` em `<HEAD>`" — um sha onde o item já não existe, sem
  conserto nenhum citado.

Medido em 13 issues de resposta conhecida do kit: as 8 órfãs do PR #197 (remoção `156ebf9`, cada
conserto certo), as 4 que saíram por decisão na varredura D15 (`7ee1c3e`, nenhum `RESOLVED by`) e a
#62 (`121a696`, removida em `3c01b88`): **13/13**. Testes sem rede: cinco mundos num repo git
temporário, e cada regra nova sabotada numa cópia ficou vermelha (sem a 2ª metade da remoção,
`RESOLVED_RE` sem grupo, `HEAD` no lugar da remoção, título no lugar da chave).

## [2.2.0] — 2026-10-01

Minor porque a saída do plano muda: cada `UPDATE` vem marcado e o resumo ganha a contagem.

### Added

- **`UPDATE (anchor)` × `UPDATE (text)` no plano, e `update=N (anchor M)` no resumo.** A skill
  mandava provar à mão que um `UPDATE` em massa era só número de linha ("`--dump` contra o corpo
  vivo, dígitos normalizados"). Medido num espelho recém-sincronizado (`update=0`), essa receita
  acusava diferença em **86 de 86** issues cruas, 59 sem a linha `# título` do dump, 59 com o sha do
  permalink normalizado e **16** ainda com dígitos normalizados (issues antigas sem `todo-src`). Cada
  camada só aparece por tentativa. Agora `update_kind()` compara o corpo vivo com o novo sem destino
  de link e sem marcadores, e normaliza só o número depois de `:` dentro de crases. Um número solto
  (`90 → 85`), o título e a seção continuam sendo `text`. Medido em duas versões antigas do `TODO.md`
  do kit contra as issues vivas: 25 de 25 e 23 de 24 `anchor`; o único `text` é o #156, que de fato
  ganhou uma frase.

### Changed

- **`ORPHAN`: o item que saiu por decisão se fecha à mão, como `not planned`.** O `--close-orphans`
  fecha como concluída, com o comentário fixo "achado fechado". Na varredura D15 do kit
  (`7ee1c3e`), quatro itens saíram por decisão (cabeçalho de sensor, refutação, YAGNI) e teriam ficado
  registrados como consertados. A linha da tabela e "Erros comuns" mandam achar o commit que removeu o
  item (`git log -S`) e fechar esses com `gh issue close --reason "not planned"`, antes do
  `--close-orphans`.

### Limites

- Cinco probes novos no `test_todo_issues.py`, e a sabotagem de cada regra da classificação (sem tirar
  os marcadores, sem tirar os links, sem normalizar a referência, normalizando todo dígito, sem olhar o
  título, sempre `anchor`) deixa a suíte vermelha. Dois desses sabotadores sobreviviam à primeira
  versão dos probes e ganharam probe próprio. **Sobrevive** apagar o marcador da linha impressa: o
  `main()` precisa do `gh`, e nenhum teste offline passa pela saída do plano, como antes.

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
