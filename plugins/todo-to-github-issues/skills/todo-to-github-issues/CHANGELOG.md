# Changelog — skill `todo-to-github-issues`

Registro por sessão da skill; o changelog **versionado** é `plugins/todo-to-github-issues/CHANGELOG.md`.
Cada entrada registra **o que mudou e por quê** — a lição que a motivou, não só o diff.

## 2026-10-07 — a regra de âncora que a skill ainda ensinava, e o espelho feito da branch

Publicado como **v2.3.2**.

- Chore pós-merge do lote 5 do kit sdd. A linha 124 do `SKILL.md` descrevia a regra de âncora da
  ADR 0011 (qualquer símbolo entre crases perto da linha), e o kit mede outra desde a ADR 0015 §2: o
  símbolo designado `` `arq:N` (`símbolo`) `` logo depois da âncora. A defasagem não era só de
  prosa: o `test_todo_format.py` estava vermelho em 5 casos, todos "o sensor do kit aceita o
  fixture". Sondado direto no sensor: a forma antiga dá `designates no symbol`, a nova passa. Com
  os fixtures corrigidos, 39 `ok` (antes 34). É a mesma classe da v2.0.1: a skill não carrega o
  sensor, mas os testes e a tabela dela descrevem a regra, e a regra andou.
- Mudar só a #240 antes do merge: rodado na branch, o plano queria 15 `UPDATE`, 14 deles com o
  texto da branch (`RESOLVED by` ainda não mergeado). O script não filtra por issue. Saída: corpo do
  `--dump`, `gh issue edit`, e o plano pós-merge leu a #240 como em dia.
- O re-sync pós-merge trouxe a #239 e a #236 como `UPDATE (text)` com só a âncora mudada. Causa no
  `update_kind`: ele tira o alvo do link e deixa os colchetes, e os corpos dessas issues tinham sido
  escritos à mão com a âncora sem link. Lição de uso, não de código: editar partindo do `--dump`.
- Visto e não consertado: o `fixed by` cita só o primeiro hash de `RESOLVED by A e B` (#227).

## 2026-10-04 — a órfã consertada que quase saiu como "not planned"

Publicado como **v2.3.1**.

- Re-sync do `TODO.md` do kit depois do lote 3 (PRs #219 e #220): 35 órfãs, 12 com `fixed by`.
  Quatro saíram como `removal not found`, e o `--close-orphans` sugeriu `--reason "not planned"` para
  todas. Uma delas, a #113, estava consertada (`RESOLVED by 0521972`); fechei como `completed` à mão
  porque sabia do conserto, não porque a ferramenta disse.
- Causa, provada com o histórico: o título da #113 tem `` `^  ok    ` ``, o parser normaliza para
  `` `^ ok ` ``, e o `git log -S` com esse trecho acha 0 ocorrência no arquivo. As outras três
  (#143, #154, #158) foram movidas para a seção decidida com o mesmo título, e a contagem 1/1 esconde
  o commit do `-S`.
- Protótipo antes do código: percorrer os commits do arquivo com o teste da chave achou as quatro e
  concordou com o `-S` onde ele já achava. Teste vermelho escrito antes do conserto (título com
  espaços repetidos), sabotagem nos dois sentidos depois.

## 2026-10-02 — a órfã que fechava sem dizer quem a consertou

Publicado como **v2.3.0**.

- Re-sync do `TODO.md` do kit depois dos PRs #196/#197: o plano deu 8 `ORPHAN`, todas de itens
  consertados (`RESOLVED by` no último texto). O `--close-orphans` as fecharia com "O item saiu de
  `TODO.md` em `<HEAD>`" — sem o conserto. Fechei as 8 à mão para citar cada hash; a memória já
  registrava o mesmo trabalho manual com 14 órfãs em 2026-09-25, e o caso inverso (4 órfãs por
  decisão que o `--close-orphans` chamaria de concluídas) em 2026-10-01.
- O script tinha o dado: o commit que removeu o item guarda o texto dele no pai. `last_text()` o lê
  e o plano passa a dizer `fixed by <hash>` ou `no RESOLVED by`; o `--close-orphans` fecha só o que
  foi consertado. Protótipo antes do código: 13/13 casos conhecidos em 1,3 s.
- A sabotagem achou uma regra sem probe (casar pelo título em vez da chave): ganhou o mundo dos
  títulos gêmeos antes do commit.

## 2026-10-01 — a receita de prova que mentia

Publicado como **v2.2.0**.

- O humano pediu para sincronizar o `TODO.md` do kit depois da varredura D15. O plano deu 24
  `UPDATE` e 4 `ORPHAN`. A prova "é só número" pela receita da skill acusou as 24; descontada a
  linha `# título` do `--dump`, sobrou uma (#156) — prova feita à mão, por tentativa. Medida depois
  num espelho já sincronizado, a receita tinha quatro camadas de falso positivo (86 → 59 → 59 → 16
  de 86). A prova saiu da skill e entrou no script: `UPDATE (anchor)` / `UPDATE (text)`.
- As 4 órfãs tinham saído por decisão (`7ee1c3e`), não por conserto. O `--close-orphans` as
  fecharia como concluídas, com o texto "achado fechado". Foram fechadas à mão como `not planned`, cada uma
  com o destino. A tabela passou a dizer isso.
- A sabotagem achou dois probes cegos na primeira versão: o teste roda sem sha (o permalink não
  mudava) e o número "trocado" era acrescentado, não trocado. Os dois foram reescritos e agora mordem.

## 2026-09-26 — a largura que a skill guardava sozinha

Publicado como **v2.0.2**.

- O humano pediu para mergear um PR do kit com o `TODO.md` "em harmonia com a skill". O sensor do
  kit dizia limpo; o `--audit` dizia 42 linhas longas e 6 itens acima do teto. O mesmo `--audit`
  sobre a `main` do kit dava o mesmo — não era o PR. Era a skill: `WRAP = 100` no `todo_format.py`,
  contra `WIDTH_CAP=120` no `check-todo.sh`. Os 100 são mais velhos que a regra do kit; quando o
  kit ganhou a regra, a cópia virou segunda opinião, e o teste da skill (`len(p) <= f.WRAP`)
  concordava consigo mesmo. A skill jurava não carregar cópia do formato e carregava um número.
- A largura passa a ser lida do sensor a cada execução; kit sem ela é recusado, nunca adivinhado.
  Medido: o `--audit` do `TODO.md` do kit foi de `auto=1 manual=6` para `auto=0 manual=0`.
- A sabotagem achou um probe cego: "o nome num comentário não é declaração" passava com a regex
  sem âncora, porque a fixture tinha texto depois do número e nenhuma das duas formas casava.
  Fixture sem esse texto, e o probe morde.
- De carona, um vermelho antigo do `test_todo_issues.py` (`body edit -> 1 update`): a sonda
  editava pela última linha do item, e atribuição se repete. Vermelho pelo motivo errado — o
  espelho estava certo; agora a sonda edita o bloco, que é único.
- Lição de uso, não de código: depois de um PR que desloca linhas de um arquivo ancorado, o plano
  traz `UPDATE` em massa (14 no #170 do kit), e todos eram número de âncora. Normalizar os dígitos
  do `--dump` contra o corpo vivo provou isso antes do `--apply`.

## 2026-09-26 — a regra de âncora do kit, e a cópia que morava fora do repo

Publicado como **v2.0.1**.

- O `test_todo_format.py` tinha 5 casos vermelhos. A hipótese do usuário — "o kit está mudando
  neste momento" — estava certa na causa e errada no tempo: a mudança (ADR 0011, `fb6fb78` +
  `2cf432d`) já estava na `main` do kit, e o `check-todo.sh` do checkout era idêntico ao da
  `origin/main`. Não era trabalho em voo; era a skill defasada.
- O defeito não era só de fixture. `sensor_violations` escrevia o texto em `/tmp`, e a âncora passou
  a ser resolvida contra o repositório do arquivo checado — toda âncora de um `TODO.md` real virava
  "names no file". Sensor que mede uma cópia em outro lugar mede outro arquivo.
- A regra, medida: arquivo **não rastreado** serve (o sensor olha o disco, não o índice); a âncora
  precisa ter forma de caminho (`a:1` não é lida como âncora); e um span entre crases da cabeça do
  item precisa ocorrer no arquivo até 10 linhas da linha ancorada.
