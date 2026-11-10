# Fechar à mão a órfã sem `RESOLVED by`

Leia antes de fechar uma issue que o plano mostra como `ORPHAN … no RESOLVED by — close by hand`. A
linha diz em que commit o item saiu, e não para onde ele foi. Num projeto, em 2026-11-10, depois de um
PR de 17 commits, as quatro órfãs da rodada tinham quatro destinos, e o plano dava a mesma linha para
todas. Fechar sem saber o destino erra o motivo: `not planned` num conserto, ou `completed` numa
issue que ainda tem metade aberta.

| O item… | Como se descobre | Como fecha |
| --- | --- | --- |
| foi para a seção decidida | o `+` do diff da remoção traz a linha sob `<!-- sdd:decided -->` | `--reason "not planned"`, citando a decisão e o commit |
| ganhou título novo e texto reescrito | o `+` do diff da remoção traz o item novo, que o plano lista como `CREATE`. O `RENAME?` só aparece com ≥ 85% do texto igual (`guess_renames`) | a mesma escolha do `RENAME?`, com o humano (abaixo) |
| foi dividido | uma parte saiu e a outra é um `CREATE`, que pode ter nascido em outro commit e não aparecer no diff da remoção | `completed` só se a parte que saiu foi consertada, citando o conserto e a issue da parte que fica |
| foi consertado antes de sair | o diff da remoção só tem `-`, e o conserto está no arquivo que a âncora nomeia | `completed`, citando o commit do conserto e o da remoção |

```bash
# o que saiu e o que entrou no mesmo commit
git show <commit-da-remoção> -- TODO.md | grep -E '^[-+]' | grep -vE '^(\+\+\+|---)'
# o conserto: procure o que a Direção do item pede que exista, no arquivo que ela nomeia
git log --format='%h %ad %s' --date=short -S'<trecho que o conserto escreveria>' -- <arquivo da âncora>
```

- **O `-S` com o título acha a remoção, não o conserto.** No caso medido, o conserto veio 27 dias
  antes da remoção, num commit que não tocou o `TODO.md`. Ele só apareceu pelo trecho que a Direção
  pedia, procurado no arquivo da âncora.
- **Commit em comum não prova sucessão.** O mesmo commit que mandou um item para a seção decidida
  acrescentou outro, sem relação com ele. Leia o texto dos dois antes de ligar uma órfã a um `CREATE`.
- **Item retitulado: manter a issue ou abrir outra é decisão do humano.** Para manter, refaça a chave
  **antes** do `--apply`, com o mesmo comando que o `RENAME?` imprime (`todo_issues.py`, `RENAME?`).
  A chave nova é o fim do nome do arquivo do `--dump`, `L<linha>-<chave>.md`, que é a `todo-key` que a
  issue receberia. Para abrir outra, rode o `--apply` e feche a antiga como `not planned`, apontando a
  nova pelo número.
- **O `gh issue close --reason` só aceita `completed` e `not planned`.** Não há "duplicada" (gh 2.85.0,
  `gh issue close --help`, 2026-11-10). Depois de fechar, releia o motivo com
  `gh api repos/<dono>/<repo>/issues/N --jq .state_reason`.
