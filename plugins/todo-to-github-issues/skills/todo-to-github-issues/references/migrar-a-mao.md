# Migrar à mão: quando cada `##` já é um item

O `--fix` migra o arquivo cujos achados moram **dentro** de um `##` (`Aberto`, `Findings`…). Há
outro formato comum: cada achado é o próprio `##` (`## 1. Título`, `## 2. Título`), em prosa. Aí o
`--audit` responde `no open marker … (candidates: none)`, e as duas saídas que ele sugere não
servem. O `--open-heading` não tem `##` que guarde os itens. E um `## Open` + `<!-- sdd:open -->`
acima do primeiro achado deixa a seção vazia, porque ela vai só até o próximo `##` (SKILL.md, início).

A migração é à mão, e o formato é **o do kit**, nunca uma cópia daqui: o template
`templates/todo.<OUTPUT_LANG>.md` e o sensor `tests/check-todo.sh` do `$SDD_HOME`. Os tetos de
linha e de largura, a distância da âncora e o campo `descoberto por` são lidos de lá. Medido no
`magic_tutor` em 2026-10-19 (6 itens `## N.`, o PR #9 do repo).

## 1. Rascunho dentro do repo, medido pelo kit antes de trocar o arquivo

1. **Escreva o rascunho na raiz do repo, sem rastrear** (ex.: `TODO.rascunho.md`). O sensor
   resolve a âncora contra o repositório do arquivo (ADR 0011 do kit). Um rascunho no `/tmp` ou no
   scratchpad faria toda âncora falhar, pelo mesmo motivo que o `--audit` escreve a cópia dele ao
   lado do arquivo checado.
2. **Cada `## N.` vira um item** do template. O que já foi resolvido vira uma linha na seção
   decidida, e a análise longa vai para `docs/` (a linha `Fonte:` aponta). A data é a do commit
   que trouxe o item, e a âncora é a linha atual do código, com o símbolo que ela contém:

   ```bash
   git log --reverse --format='%h %ad' --date=short -S'<trecho do título>' -- TODO.md | head -1
   ```

3. **Meça com o kit e veja o plano**, que só lê:

   ```bash
   bash "$SDD_HOME/tests/check-todo.sh" --check TODO.rascunho.md --allow-empty   # ok N finding(s)
   bash "$SDD_HOME/tests/check-todo.sh" --anchors TODO.rascunho.md               # 0 off target
   python3 $S --file TODO.rascunho.md --repo OWNER/NAME     # CREATE por item; avisa "no line permalinks"
   ```

   O aviso é esperado, porque o rascunho difere do `HEAD`. No caso medido, o sensor deu `ok 6
   finding(s) … every anchor on target` e o plano deu `create=6`.
4. **Só com o OK do humano** (os `MANUAL` são dele), troque o arquivo: `mv TODO.rascunho.md
   TODO.md`. O `--audit` tem de dar `auto=0 manual=0`. Depois vem o commit e, da branch padrão, o
   espelho.

## 2. A numeração que o repositório cita perde o alvo

No formato `## N.`, o resto do repo costuma citar o item pelo número (`TODO.md #6`). A migração
apaga esse número, e nenhum sensor lê essas citações: elas morrem em silêncio. Antes de migrar:

```bash
git grep -nE 'TODO\.md`? ?#[0-9]' -- ':!TODO.md'
```

No caso medido, deu 18 linhas: o `CLAUDE.md`, uma `SKILL.md`, CHANGELOGs, `docs/` e uma mensagem
no código (`monitor/replays.py:819`). Há duas saídas:

- **Manter o `N.` no começo do título em negrito.** Foi o que se fez. A chave da issue é o título,
  então o número fica estável. O template deixa o título livre, o sensor aceitou e a issue saiu
  "1. Ver a dica…". O preço é o mesmo de qualquer título: tirar o número depois é um `RENAME?`
  (SKILL.md, *Identidade*).
- **Citar a issue depois do espelho**, como o próprio kit cita os itens dele pelo número da issue
  (`#191 (este)` em `docs/handoffs/20261004-lote-4-a-catraca-zera/01-plano.md`, no kit). Isso
  reescreve cada citação, num commit próprio.
