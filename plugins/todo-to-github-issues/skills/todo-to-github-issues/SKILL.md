---
name: todo-to-github-issues
description: "Mirror an sdd-style TODO.md (`<!-- sdd:open -->` / `<!-- sdd:decided -->`) as GitHub issues, idempotently, re-syncing as the file changes; also audits and fixes an off-standard TODO.md and routes an `ACHADOS-*.md` report to the tracker. Triggers — TODO.md para issues, sincronizar issues do TODO, auditar TODO.md, relatório de achados, ACHADOS, gh issue create em lote."
metadata:
  version: 2.8.3
  user_invocable: "true"
  argument_description: "plan (padrão) | apply | apply --close-orphans | audit | fix | fix --write"
---

# TODO.md → GitHub issues

O `TODO.md` continua sendo **a fonte da verdade**; cada issue é um espelho dele. O script é
idempotente: pode rodar quantas vezes quiser, e só cria ou edita o que mudou.

O formato é o do **kit sdd**, não desta skill: `templates/todo.md` (uma variante por
`OUTPUT_LANG`, ex. `todo.pt-BR.md`). Duas seções `##`, cada uma com seu marcador na linha de baixo:
`<!-- sdd:open -->` (os achados, espelhados como issues) e `<!-- sdd:decided -->` (registros do que
foi refutado ou decidido; **não** viram issue). O texto do heading segue o idioma do repo; o
marcador e o `RESOLVED by <hash>` são o contrato, em inglês. Só a seção aberta é lida, até o
próximo `##`, e as `###` dentro dela viram as labels de seção.

## Requisitos (conferidos a cada execução — o script recusa, nunca degrada)

| Requisito | Vale para | Se faltar |
|---|---|---|
| Python ≥ 3.8, `git`, `bash` | tudo | instalar; o script lista **todas** as faltas de uma vez e sai com rc 3 |
| `gh` instalado e autenticado | espelho e relatório | https://cli.github.com e `gh auth login` |
| **o kit sdd** | espelho, `--audit`, `--fix` | `git clone https://github.com/j0ruge/sdd_agents ~/repos/sdd_agents`, ou `export SDD_HOME=<clone>` |
| kit com `--count` no sensor | idem | kit anterior ao esqueleto: `git -C "$SDD_HOME" pull` |
| kit com `WIDTH_CAP` no sensor | `--audit`, `--fix` | kit anterior à regra de largura (2026-09-25): `git -C "$SDD_HOME" pull` |
| `TODO.md` com `<!-- sdd:open -->` | espelho | `--audit` mostra o que falta e `--fix` acrescenta (seção abaixo) |

O kit é achado por `SDD_HOME` e, sem ele, pelo `sdd` no `PATH` ou por `~/repos/sdd_agents`. Um
`SDD_HOME` errado é **erro**, nunca motivo para usar outro kit: medir o arquivo contra o sensor
errado seria pior que não medir. Esta skill **não carrega cópia** do formato nem do sensor.

## Comando

```bash
S={SKILL_DIR}/scripts/todo_issues.py      # {SKILL_DIR} = o diretório que contém este SKILL.md
python3 $S                              # 1. PLANO: só lê, não toca no GitHub
python3 $S --apply --limit 1            # 2. canário: 1 criação (os UPDATE saem todos); confira a renderização
python3 $S --apply                      # 3. o resto (~2,5 s por issue, com ritmo contra rate limit)
python3 $S --apply --close-orphans      # só depois de ler as linhas ORPHAN do plano
```

Opções: `--file` (padrão `TODO.md`), `--repo OWNER/NAME` (padrão: o repo do arquivo, via `gh`;
obrigatório num clone cujo `origin` é um caminho local), `--dump DIR` (grava os corpos
renderizados em disco, sem rede) e `--allow-empty` (backlog esvaziado de propósito; *Erros comuns*). Mexeu no script? Rode `python3 scripts/test_todo_issues.py
<TODO.md de um repo real, já no esqueleto, com 5+ itens>`, que não usa a rede. Com menos itens o
primeiro caso reprova de propósito: o teste apaga 4 itens e precisa que sobre um. Casos de
gatilho (deve e não deve disparar): `assets/trigger-evals.json`, no formato do `skill-creator`.

## Scripts disponíveis

Só `todo_issues.py` se executa (`--help` lista todas as opções). Os outros três são módulos que ele
importa conforme o modo: abra-os só para depurar ou alterar esse modo.

| Arquivo | O que é | Quando abrir |
|---|---|---|
| `scripts/todo_issues.py` | ponto de entrada: plano, `--apply`, `--audit`/`--fix`, modo relatório | sempre: é o `$S` dos comandos acima |
| `scripts/kit.py` | acha o kit sdd, confere os requisitos (rc 3) e chama o sensor `check-todo.sh` | ao depurar um requisito recusado ou o kit errado |
| `scripts/todo_format.py` | `--audit`/`--fix`: as regras `AUTO` e `MANUAL`, e a recusa rc 6 do `--write` | ao depurar ou alterar uma regra de formato |
| `scripts/report.py` | modo relatório (`ACHADOS-*.md`): `CREATE closed`, `LINK?`, `COMMENT`, `CLOSE` | ao depurar ou alterar o modo relatório |
| `scripts/test_todo_issues.py` | testes sem rede do espelho e do modo relatório | depois de mexer em `todo_issues.py` ou `report.py` |
| `scripts/test_todo_format.py` | testes sem rede do `--audit`/`--fix` (precisa do kit e do git) | depois de mexer em `todo_format.py` ou `kit.py` |

## Como ler o plano

| Linha | Significa | O que fazer |
|---|---|---|
| `CREATE` | item sem issue | `--apply` cria a issue, com as labels `todo` e `todo: <seção>` |
| `UPDATE (anchor)` | só mudou o número de linha de uma referência `` `arquivo:N` `` (a âncora ou outra no texto): um PR que desloca linhas do arquivo ancorado gera dezenas | `--apply` sem mais prova: o script comparou o corpo vivo sem permalink, sem marcadores e sem esses números |
| `UPDATE (text)` | texto, título ou seção mudou de verdade | leia o item antes do `--apply`; é o único `UPDATE` que pede olho |
| `REF?` | um `#N` solto num corpo que esta rodada escreve (`CREATE`, `UPDATE (text)`), com o destino que o GitHub dará ao link | confira; se o texto quis dizer outra coisa, corrija a fonte (`dono/repo#N`, "item N") antes do `--apply` |
| `SKIP` | o corpo traz `RESOLVED by <hash>` e não existe issue | nada: não se abre card para achado já fechado; com o hash já na branch padrão, o `--fix` apaga o item |
| `ORPHAN` | a issue está aberta, mas o item saiu do arquivo. A linha diz em que commit ele saiu e, se o último texto trazia `RESOLVED by`, quem o consertou (`fixed by …`) — lido no commit da remoção, nunca no `HEAD` | **`fixed by`:** `--close-orphans` fecha como concluída, citando o conserto e a remoção. **`no RESOLVED by`**: `--close-orphans` pula (`SKIP`); feche à mão. Consertado sem o marcador (a missão do kit sdd apaga o item assim): `gh issue close N --reason completed --comment "<commit e PR>"`; decidido, refutado ou adiado: `--reason "not planned" --comment "<para onde foi>"`. **`last text unknown`** (`removal not found`): a chave nunca saiu do histórico deste checkout — clone raso, arquivo renomeado, branch não mergeada (a de um PR aberto sai como `PENDING`). Desconhecido não é ausente: leia o último texto antes de escolher `completed` ou `not planned` |
| `PENDING` | a remoção não está no histórico, mas o item está na cabeça de um PR aberto: a issue nasceu de um `--apply` na branch do PR. Só a órfã sem remoção é procurada, com um `gh pr list` e o arquivo em cada cabeça (do git local, ou da API de conteúdo) | nada: deixe aberta, e `--close-orphans` a pula. Depois do merge, vira `OK` ou `UPDATE`. Limite: PR de fork (cabeça em outro repositório) não foi medido; se a cabeça não for lida, a issue segue `ORPHAN` |
| `RENAME?` | par `ORPHAN` + `CREATE` com ≥ 85% do mesmo texto: o título mudou | confirme com o humano; se for o mesmo achado, rode o comando impresso **antes** do `--apply`, e a issue antiga vira `UPDATE` |
| `CLOSED` | a issue foi fechada à mão, mas o item continua no arquivo | decisão humana: reabrir a issue ou apagar o item |
| `DUP` | duas issues com a mesma chave | feche à mão todas menos a de menor número |

Depois do `--apply`, uma nova rodada do plano **tem de** mostrar `create=0 update=0`.

Antes de qualquer plano, o script passa o arquivo pelo sensor do kit
(`check-todo.sh --check <arquivo> --allow-empty`) e confere a contagem dele (`--count`) contra a
própria. Sem marcador: rc 4, e o recado manda rodar `--audit`. Arquivo fora de forma: rc 4, com as
violações. Contagens diferentes: rc 5 (*parser drift*) — pare, não espelhe nenhum dos dois números.

## Auditar e acertar o formato (`--audit`, `--fix`)

```bash
python3 $S --audit                        # o que está fora do padrão; não toca em nada
python3 $S --fix                          # idem + o diff das correções mecânicas; não toca em nada
python3 $S --fix --write                  # grava o diff e roda o sensor de novo
python3 $S --fix --open-heading "Pendências"   # quando o --audit não sabe qual `##` guarda os achados
python3 $S --fix --lang pt-BR             # repo sem OUTPUT_LANG em .sdd/config.sh
```

`AUTO` é o que o script corrige sozinho, porque é determinístico e não perde nada:

- a semente antiga do `sdd install`, **intocada** (mesmo blob), trocada pela variante do idioma;
  com um byte a mais ela é trabalho de alguém — só o preâmbulo dela é trocado;
- o marcador `<!-- sdd:open -->` sob o **único** `##` candidato (`Aberto`, `Open`, `Achados…`,
  `Findings`); `## Open` da semente antiga vira o heading da variante;
- a seção decidida acrescentada no fim; um `## Resolved` vazio removido;
- `RESOLVIDO por <hash>` → `RESOLVED by <hash>`, só dentro da seção aberta;
- item de uma linha sem negrito: o texto antes do primeiro ` — ` vira o `**título**` (só se
  couber num título de issue, ≤ `TITLE_MAX` caracteres, `todo_format.py`);
- linha física acima do `WIDTH_CAP` do sensor do kit (120 caracteres em 2026-10-16) quebrada nessa largura,
  com recuo de 2 espaços, sem mudar uma palavra — o que costuma **revelar** um item acima do teto
  de linhas que passava por estar numa linha só. A largura é **lida do kit** a cada execução: uma
  cópia daqui (100) sobreviveu à regra do kit e fez o `--audit` inventar 6 itens acima do teto num
  arquivo que o sensor chamava de limpo;
- `- [x]` apagado **só** quando todo commit que ele declara (`RESOLVED by`/`RESOLVIDO por|em`)
  já está na branch padrão, provado por `git merge-base --is-ancestor`; o mesmo vale para o item
  **aberto** (`- [ ] … RESOLVED by <hash>`), que o sensor aceita e o plano lê `SKIP` para sempre.

`MANUAL` é o resto, agrupado por regra, com a linha (no arquivo **depois** do `AUTO`) e a ação.
Resolva-os **com o humano, um grupo por vez**, e nunca em silêncio:

| MANUAL | O que fazer |
|---|---|
| nenhum/mais de um `##` candidato | perguntar qual guarda os achados e rodar `--open-heading`; cada `##` já é um item: `references/migrar-a-mao.md` |
| item acima do teto | a análise vai para `docs/` (ou o handoff da missão) e o item aponta para lá; fica ~6 linhas |
| `##` sem marcador | narrativa → `docs/`; categoria → `###` dentro da seção aberta; assunto encerrado → uma linha na seção decidida |
| `[x]` sem hash, ou com hash não mergeado | consertado: citar o commit e rodar de novo; refutado/decidido: uma linha na seção decidida; não mergeado: `- [ ] … RESOLVED by <hash>` até mergear |
| sem âncora, sem data, sem autor | completar com o humano — o script não inventa `arquivo:linha` nem quem achou |
| âncora que não aponta arquivo do repo (ADR 0011 do kit), sem o símbolo designado logo depois — `` `arq:N` (`símbolo`) ``, fechado pelo `)` — ou cujo símbolo não está perto da linha ancorada (ADR 0015 §2; tamanho mínimo e distância são os do cabeçalho do `check-todo.sh`, nunca uma cópia daqui) | antes, conferir se o achado ainda vale: âncora sem alvo às vezes é achado já consertado, que sai do arquivo citando o commit (reancorado, vira issue no `--apply`); valendo, reancorar no código atual, designando o símbolo que a linha contém — `tests/check-todo.sh --anchors TODO.md` do kit lista só essas, e a mensagem diz o que falta (`designates no symbol`) ou onde está o símbolo (`nearest … is at line N`) |

`--fix --write` recusa (rc 6) arquivo versionado com mudança não commitada, para a correção chegar
como um diff próprio; arquivo não versionado é escrito com aviso. Branch e commit ficam com você.
Antes de commitar o `--write` de uma migração, leia `references/conferir-o-fix.md`: provar que a
quebra não mudou palavra, salvar o plano condicional de um item apagado e o sensor do repo que lia
os headings antigos.

A cópia que o sensor mede é escrita **ao lado** do arquivo checado (oculta, apagada em seguida), não
em `/tmp`: desde o ADR 0011 a âncora é resolvida contra o repositório do arquivo, e uma cópia fora
dele fazia toda âncora falhar — o `--audit` do sales_quote acusava 188 violações onde o kit vê 97.

## Relatório de achados (`ACHADOS-*.md`)

Um arquivo com seções `### N. <título>` entra no **modo relatório** sozinho (`--format` força); um
`TODO*.md` é sempre o backlog. Antes do primeiro plano de um relatório, leia
`references/modo-relatorio.md`: a unidade é a seção, o status sai da tabela de roteamento, e o plano
tem linhas próprias (`CREATE closed`, `LINK?`, `COMMENT`, `CLOSE`).

## Identidade: por que o script faz assim

- **A chave é só o título** (`<!-- todo-key -->` no corpo). Âncora `arquivo:linha` fica de fora
  porque o número da linha muda a toda hora, e cada mudança viraria uma issue nova. O preço disso:
  **renomear o título cria uma issue nova e deixa a antiga órfã**. O plano marca o par como
  `RENAME?` e imprime o comando que copia a chave nova para a issue antiga.
- **As issues existentes vêm de `gh issue list`, nunca de `--search`.** O índice de busca do
  GitHub pode atrasar (não medido aqui), e uma segunda rodada logo depois de uma queda criaria duplicatas.
- **O `todo-hash` cobre título, seção e texto, e deixa os links de fora.** Assim um commit novo em
  `HEAD` não reescreve 98 issues só porque o sha do permalink mudou.
- **Cada issue sabe de que arquivo veio** (`<!-- todo-src -->`, ou o link do rodapé nas antigas).
  Sem isso, rodar com `--file` num segundo arquivo lia **todo** o espelho do primeiro como órfão,
  e um `--close-orphans` o fecharia inteiro.
- **O corpo sai literal**: o texto do item, desquebrado em parágrafos, porque numa issue cada
  quebra simples vira `<br>`. A âncora e todo link relativo viram links para o sha em `HEAD`, e
  todo `@nome` fora de bloco de código ganha um espaço de largura zero depois da arroba: sem isso,
  `` `@codex review` `` citado num achado fez o conector do Codex responder na issue (crase não
  protege: bot lê o texto cru). Com o arquivo sujo ou com `HEAD` fora do remoto, o script avisa e gera
  links sem número de linha. O símbolo que a âncora designa (`` `arq:N` (`símbolo`) ``) fica na linha
  **Âncora:**; até a 2.5.0 ele abria o parágrafo seguinte (kit sdd #255, 2026-10-15), e o
  `update_kind` lê esse corpo antigo como o de hoje, ou cada issue dele voltaria `UPDATE (text)`.

## Erros comuns

- **Tratar `RESOLVED by` solto como fechado.** Um item pode falar da convenção sem ter sido
  fechado (`` o ciclo de vida do `RESOLVED by` ``). Só conta `RESOLVED by <hash>`. O antigo
  `RESOLVIDO por` não é lido pelo espelho: `--fix` o converte.
- **Espelhar antes de acertar o formato.** Num arquivo sem marcador o espelho recusa (rc 4). A
  ordem é `--audit` → `--fix` → `--fix --write` → os `MANUAL` com o humano → commit → plano.
- **Deixar as órfãs esperando a migração do formato.** Um `TODO.md` anterior a uma regra nova do
  sensor recusa o plano (rc 4) até ser migrado — no sales_quote, em 2026-10-09, `--audit` deu
  `manual=206`, quase todas `designates no symbol` (ADR 0015 §2 do kit) — e o espelho para: lá, 8
  órfãs abertas desde a última sincronização. Feche-as sem esperar: `git log --format='%h %ad %s'
  --date=short -S"<começo do título>" -- TODO.md` acha o commit que removeu o item; consertado,
  `gh issue close N --reason completed --comment "<commit ou PR>"`; por decisão, `not planned` com o
  destino. Item consertado que **ainda** está no arquivo sai por PR, com o que o repo exigir junto
  (no sales_quote, o doc da `Fonte:`), e a issue fecha depois do merge: fechada antes, o próximo
  plano a lê `CLOSED`.
- **Ler o `MANUAL` como tarefa do script.** Tudo ali exige julgamento: o que é decidido, para onde
  vai uma análise, qual heading guarda os achados. Pergunte; não escolha pelo humano.
- **Fechar órfã sem ler.** `--close-orphans` nunca é o primeiro comando. Primeiro o plano, depois
  confira cada `ORPHAN`.
- **Esperar que o `--close-orphans` feche o item que saiu por decisão.** Ele só fecha a órfã cujo
  último texto trazia `RESOLVED by <hash>`, e pula as outras com `SKIP`: item refutado, adiado ou
  levado para outro lugar (cabeçalho de sensor, YAGNI) fica aberto até alguém fechá-lo à mão como
  `not planned`, com o destino. Até a 2.2.0 ele fechava todas como *concluídas*, sem citar conserto.
  Para conferir o motivo depois: `gh api repos/<dono>/<repo>/issues/N --jq .state_reason` (o
  `gh issue view --json stateReason` não existe no gh 2.45, medido em 2026-10-25).
- **Ler `removal not found` como "saiu por decisão".** Até a 2.3.0 a remoção era procurada pelo
  texto do título, que o parser normaliza: o kit sdd fechou quase como `not planned` um item
  consertado (#113, título com `` `^  ok    ` ``). Desde a 2.3.1 ela é achada pela chave.
- **Contar com o canário para uma issue só.** O `--limit` limita só as criações. No espelho, todo
  `UPDATE` do plano já sai no canário (kit sdd, 2026-10-16: `created #277` e `updated #271` no mesmo
  `--limit 1`): leia cada `UPDATE (text)` antes dele. No relatório, com `--link`, todo comentário.
- **Traduzir ou resumir o item na issue.** O espelho que se afasta da fonte deixa de ser espelho.
  Corrija o texto no `TODO.md` e sincronize.
- **Deixar um `#N` solto no item.** Na issue, o GitHub liga todo `#N` fora de crase ao `#N` **deste**
  repo, queira o texto o item N do arquivo ou o PR de outro repo: "Liga com o #1" (o item 1) virou
  link para o PR #1 do magic_tutor (2026-10-20). Cada `REF?` do plano mostra o destino; o conserto é
  na fonte, com `dono/repo#N` ou "item N". Rode o plano (sem `--apply`) na branch do PR, antes do
  merge: o `REF?` cobre os itens que o PR escreve, e o conserto vai no mesmo PR. Depois do merge, ele
  pede outro PR (magic_tutor #114 → #115, 2026-10-26).
- **Espelhar a partir de uma branch de trabalho.** O script lê o `TODO.md` do diretório atual: numa
  branch, o `--apply` leva o texto dela (`RESOLVED by` ainda não mergeado, permalink no sha da
  branch) a toda issue que difere da branch padrão — no kit sdd, em 2026-10-07, 15 `UPDATE` onde só
  uma issue tinha mudado. Espelhe da branch padrão, ou de um `HEAD` contido nela e sem diff para ela. Quem já criou a issue da branch de um PR
  publicado a vê como `PENDING` até o merge, não como órfã (kit sdd #249, do PR #248, 2026-10-13).
  Para mudar UMA issue antes do merge, pegue o corpo dela no `--dump`, tire o `# título` que o dump
  põe no topo e aplique com `gh issue edit N --body-file`; o plano depois do merge a lê como em dia.
  Com o checkout da branch padrão ocupado ou atrás do remoto, espelhe de um worktree destacado,
  `git worktree add --detach <dir> origin/<padrão>` (magic_tutor, 2026-10-25: `permalinks at 8d1eaab`,
  e o plano final em `create=0 update=0 orphans=0`).
- **Editar o corpo à mão sem o link da âncora.** O `UPDATE (anchor)` (`update_kind`) compara os
  corpos sem o alvo dos links, mas com os colchetes: uma âncora escrita `` `arq:N` `` no lugar de
  `` [`arq:N`](…) `` nunca mais é `(anchor)`, e cada linha deslocada volta como `UPDATE (text)` (kit
  sdd, #239 e #236 em 2026-10-07). Edite partindo do corpo do `--dump`, que já traz o link.
- **Vírgula no `###` da seção.** O GitHub recusa vírgula em nome de label (422 `Label.name is
  invalid`, sem dizer qual caractere; medido em 2026-09-24, `_label_safe`) e a primeira issue nunca sai. O script troca `, ` por ` · `
  na label (o texto da seção no arquivo não muda). O teto de 50 é de **caracteres**, não bytes:
  acento não encurta nada.
- **Rodar com o arquivo vazio ou fora do lugar.** O script recusa um arquivo sem nenhum item
  (rc 2), porque nesse caso toda issue viraria órfã. Backlog esvaziado de propósito (marcador
  presente, o sensor do kit aceitou e contou 0) passa com `--allow-empty`: plano primeiro, depois
  `--apply --close-orphans --allow-empty`. Sem a flag, o kit sdd fechou à mão as 4 últimas issues
  (2026-10-09).
