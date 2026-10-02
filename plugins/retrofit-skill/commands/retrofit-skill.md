---
description: Apply non-obvious session lessons to a target skill in two modes — full (marketplace skill: bumps version, updates CHANGELOG/marketplace.json/README, commits and pushes) or lean (local skill in another repo: edits files + CHANGELOG and commits there, no bump or marketplace changes). Triggers — retrofit, skill-maintenance, session-lessons, lean-retrofit, local-skill.
metadata:
  version: 0.7.1
---

A régua deste retrofit é a família `skill-quality-audit`: um baseline antes de
editar e um gate por regressão depois (seção *Localizar o auditor* e passo 4).
A skill `skill-creator` **não** abre o fluxo. Ela só entra no caso do passo 3,
quando a lição muda a `description`.

Analise as lições aprendidas nesta sessão e aplique as relevantes à skill
`$ARGUMENTS`.

## Princípio: nada ou melhor, nunca pior

Um retrofit termina de dois jeitos: a skill ficou melhor, ou ficou **igual**
(nenhuma lição se aplica, ou nenhuma cabe sem estragar algo). Pior, nunca. Os
sensores deste fluxo servem ao princípio, e o princípio vem antes deles:

- **Achado da auditoria é sinal, não ordem.** Zerar um aviso pode piorar a
  skill. Na `codereview`, os avisos C2 vêm das instruções que os subagentes
  leem por caminho absoluto: "corrigir" o C2 derruba o aviso e quebra os
  agentes. Antes de mudar algo por causa de um achado, pergunte se a skill
  fica melhor para quem a usa, e não se o sensor fica verde.
- **Dívida antiga não se conserta dentro do retrofit.** O escopo é a lição da
  sessão. A dívida vai para o resumo como sugestão, e o conserto vira uma
  tarefa própria, com a autorização de reparo da `skill-quality-audit`.
- **Lição existente não sai sem prova.** Linha removida precisa de motivo
  escrito na proposta: está obsoleta (com o comando que mostra isso), foi
  movida (para onde) ou foi fundida (com qual). "Enxugar" sem provar não é
  motivo.
- **Se a lição não cabe sem piorar, não aplique.** Diga isso e pare, como no
  passo 2.

## PASSO 0 — escolher o MODO (enxuto vs completo)

Antes de tudo, localize a skill alvo e decida o modo. Os dois melhoram a
skill; diferem em **quais artefatos são tocados**:

- **COMPLETO** — a skill é publicada NESTE marketplace, em
  `<REPO>/plugins/$ARGUMENTS/`. Faz o ciclo versionado completo (bump de
  versão, `marketplace.json`, README, push).
- **ENXUTO** — a skill é LOCAL de outro repositório (ex.:
  `<outro-repo>/.claude/skills/$ARGUMENTS/`), fora deste marketplace. Edita
  os arquivos da skill e registra a lição num CHANGELOG dentro da própria
  pasta da skill, commitando NO REPO onde ela vive. NÃO mexe em
  `marketplace.json`, no README do marketplace, nem faz bump/push aqui.

Critério para não confundir: a skill está versionada/publicada no
marketplace? → **completo**. É local, normalmente uma correção de
cobertura/documentação? → **enxuto**. Na dúvida, pergunte ao usuário.

PARA LOCALIZAR O REPO DO MARKETPLACE (só no modo completo):
- Primeiro tente `../skills` (sibling do repo atual) e, se não existir, o nome
  antigo `../skills_commands_manager` (o repo foi renomeado em 2026-09-29).
- Se não existir, procure siblings com nome contendo "skills" ou "commands".
- Se ainda não achar, me pergunte o caminho. Não adivinhe.
- Confirme o caminho encontrado antes de seguir.

No modo completo a skill alvo fica em `<REPO>/plugins/$ARGUMENTS/`.

### 🔴 `~/.claude/skills/<nome>` costuma ser um SYMLINK, não uma cópia

`ls -la` lista o conteúdo *através* do link e `md5sum` dá igual, então parece
haver duas cópias. Um `cp` de "ressincronização" escreve através do link, de volta
no marketplace, e já apagou histórico assim (o caso: *Armadilhas*, §1). Confira o
link, não o conteúdo — `-d` faz toda a diferença:

```bash
ls -ld ~/.claude/skills/<nome>          # `l` no início = symlink; `-la` NÃO mostra isso
readlink -f ~/.claude/skills/<nome>     # para onde aponta
stat -c '%i' <local>/SKILL.md <marketplace>/SKILL.md   # mesmo inode = mesmo arquivo
```

Se for symlink: **não existe cópia para sincronizar**, e editar a fonte já
atualiza a instalação. Pule qualquer passo de "ressincronizar" — ele só pode
causar dano.

## Localizar o auditor e os scripts deste comando

O `audit_skill_quality.py` (da `skill-quality-audit`) é somente leitura, usa só a
stdlib e roda em ~0,1 s. Os scripts e a reference deste comando moram na pasta
do plugin `retrofit-skill` (`$RS`). Procure os dois nesta ordem:

```bash
# modo completo: o marketplace traz os dois
SQA=<REPO>/plugins/skill-quality-audit/skills/skill-quality-audit/scripts/audit_skill_quality.py
RS=<REPO>/plugins/retrofit-skill
# qualquer modo: plugin instalado, skill local ou harness Hermes (o cache guarda uma pasta por versão)
[ -f "$SQA" ] || SQA=$(find ~/.claude/plugins/cache ~/.claude/skills "${HERMES_HOME:-$HOME/.hermes}/skills" \
  -path '*skill-quality-audit/scripts/audit_skill_quality.py' 2>/dev/null | sort -V | tail -1)
[ -f "$RS/scripts/audit_gate.py" ] || RS=$(dirname "$(dirname "$(find ~/.claude/plugins/cache \
  -path '*retrofit-skill/*scripts/audit_gate.py' 2>/dev/null | sort -V | tail -1)")")
[ -f "$RS/scripts/audit_gate.py" ] || RS=AUSENTE
echo "SQA=${SQA:-AUSENTE} RS=$RS"
```

`RS=AUSENTE` (plugin não instalado nem marketplace à mão) é SKIP do gate, como o auditor ausente.

*Armadilhas*, nas seções abaixo, é `$RS/references/armadilhas-medidas.md`: o caso
medido por trás de cada regra. Leia a seção citada antes de afrouxar a regra.

- **Se não achar, é `[SKIP] auditor ausente`,** e isso vai escrito na proposta e
  no resumo final. SKIP é um gate que não rodou, **nunca** uma aprovação. A versão
  0.5.0 deste comando apontava para um caminho `~/.hermes/...` que não existia, e
  o gate nunca rodou sem que nada avisasse.
- **O alvo precisa ter `SKILL.md`.** Um plugin só de comandos (como este
  `retrofit-skill`) também vira SKIP explícito, e o gate dele fica sendo o
  `validate-versions.py`.
- **Flags:** `FLAGS=(--desc-budget 0)`, porque o Claude Code não corta a
  description em 60 chars como o Hermes. No modo completo, use
  `FLAGS=(--desc-budget 0 --no-changelog-required)`: no marketplace o CHANGELOG
  versionado fica no nível do plugin, e sem essa flag o check B5 acusa um falso
  erro. **Use array e `"${FLAGS[@]}"`, não string:** o zsh não divide `$FLAGS`
  em palavras, o script recebe as flags como um argumento só e sai com `rc=2`.
  Isso foi medido no ensaio desta versão.
- **`rc=2` é uso inválido, não resultado.** Nesse caso o JSON sai vazio. Corrija
  a chamada antes de seguir.

## ANTES DE EDITAR — atualize o repo local

Sincronize o repo alvo com o remoto **antes de tocar em qualquer arquivo**: com
o clone atrás do `origin/main`, o push é rejeitado com o commit já feito sobre
base defasada (*Armadilhas*, §2).

No repo onde o commit vai cair (o marketplace no modo completo; o repo da skill
no modo enxuto):

```bash
git fetch origin
git status -sb                      # veja se aparece "behind N"
# Se a árvore estiver "suja" só por artefatos de migração Windows→WSL
# (working tree CRLF vs blobs LF; /mnt/c entrega arquivos 0777), confirme que
# NÃO há mudança real antes de limpar:
git diff --ignore-cr-at-eol --stat  # vazio = só line-ending, seguro
git config core.fileMode false      # silencia o ruído de permissão 0777
git checkout -- .                   # restaura os blobs LF (só se o diff acima for vazio)
git merge --ff-only origin/<branch> || git rebase origin/<branch>
```

Só comece a editar depois de estar em dia (fast-forward limpo ou rebase). Assim
o commit nasce sobre o estado atual do remoto e o push final passa de primeira,
em vez de rebasear com a edição já feita.

**Árvore suja com arquivos que não são seus = outra sessão viva no mesmo
checkout.** O índice do git é **um só** para todas as sessões: o que você pôs nele
com `git add` sai no commit de **quem commitar primeiro**, e `marketplace.json` e
`README.md` misturam os dois trabalhos no mesmo arquivo (*Armadilhas*, §3). Nesse
caso, edite e commite num worktree próprio, e não toque no checkout compartilhado:

```bash
git worktree add -b retrofit-<skill> <scratchpad>/wt origin/main   # edite, valide e commite lá
git -C <scratchpad>/wt push origin HEAD:main                       # push; se rejeitar, rebase lá
git worktree remove <scratchpad>/wt && git branch -D retrofit-<skill>
```

Mesmo com a árvore limpa, só ponha arquivo no índice **no mesmo comando do
commit**, nunca antes de pedir confirmação.

**Depois, grave o baseline** de cada skill (diretório com `SKILL.md`) que o
retrofit vai tocar. Isso é a fase 1 da `skill-quality-audit`:

```bash
B=$(mktemp -d); ALVO=<dir-da-skill>
python3 "$SQA" "$ALVO" --format json --claims "${FLAGS[@]}" > "$B/antes.json"; echo "rc=$?"
wc -lc "$ALVO/SKILL.md"
```

Sem o baseline não há como separar a dívida antiga da regressão nova. Uma skill
real do marketplace já chega com avisos antigos (3 C2 no `codereview`), e um gate
"cru" bloquearia qualquer retrofit por eles.

## Fluxo

1. Liste as lições NÃO-ÓBVIAS da sessão: erros corrigidos, comportamentos
   surpreendentes, edge cases, padrões que funcionaram. Ignore trivialidades.

2. Filtre pelas que se aplicam ao escopo da skill `$ARGUMENTS`. Se nenhuma
   se aplicar, me diga e pare — não force.

3. Antes de editar, mostre: **o modo escolhido (enxuto/completo)** + arquivos
   a mudar + resumo do diff + tipo de bump (patch/minor/major — só no modo
   completo) + justificativa. Espere minha confirmação.

   A proposta também traz o **baseline resumido**: linhas e chars do
   `SKILL.md`, os ERRO/AVISO que já existiam e o `SQA` usado (ou o SKIP e o
   motivo). Se a lição levar o `SKILL.md` para perto do teto da spec (500
   linhas, ~20 mil chars), diga já na proposta para qual `references/` o
   detalhe vai. A decisão entre extrair e comprimir é da skill
   `skill-refactoring`; carregue-a só nesse caso.

   **`skill-creator`, só quando a lição muda a `description`.** Nesse caso,
   pergunte se quero medir o gatilho. Se eu disser que sim, use o otimizador de
   description dela com o eval set de gatilho da skill (`assets/trigger-evals.json`
   ou `evals/`, no formato dela) antes do commit. Fora desse caso ela não é
   invocada: o loop dela (evals com subagentes, viewer, benchmark) não faz parte
   de um retrofit, e carregá-la custa ~8k tokens por execução.

4. Após eu confirmar:

   **Modo completo (skill no marketplace):**
   - Edite os arquivos da skill (`commands/*.md`, `skills/**`, `references/**`).
   - Bump de versão em `plugin.json` e no `metadata.version` do comando/skill.
   - Entrada em `CHANGELOG.md` da skill com a data de hoje, explicando O QUÊ
     e POR QUÊ (a lição que motivou).
   - Atualize `<REPO>/.claude-plugin/marketplace.json` (versão espelhada +
     descrição/keywords se relevante).
   - Atualize `<REPO>/README.md`: a **versão na tabela de plugins sempre** muda
     junto com o bump — não é condicional. Se a linha da skill descreve o que
     cada versão trouxe, acrescente uma frase; não um parágrafo.
   - Rode o **gate da auditoria** (seção abaixo) em cada skill tocada.
   - **Verifique por releitura, não por ter editado.** Ter rodado o `sed` não
     prova que o arquivo mudou: um padrão que não casou falha em silêncio, e a
     description é a superfície de triggering — com os arquivos fora de sincronia,
     se a skill dispara passa a depender de qual deles o harness leu.

     ```bash
     python scripts/validate-versions.py     # ANTES do commit, não depois
     ```

     **Trate os WARNINGS como bloqueantes para a skill que você está tocando.**
     Eles não reprovam o gate, e é exatamente por isso que passam: aviso que nunca
     reprova vira ruído de fundo. Se a sua edição empurrou a description acima do
     cap, encurte agora — depois vira mutirão.

     Confirmação independente de que os quatro lugares batem (na raiz do marketplace):

     ```bash
     python3 "$RS/scripts/check_release_sync.py" <nome-do-plugin>
     ```

     Ele **imprime os valores** encontrados, não só booleanos: leia as versões e o
     tamanho da description, não apenas os `True`. Plugin só de comandos não tem
     `SKILL.md` (o canônico é o `plugin.json`); plugin multi-skill imprime uma linha
     por skill, cuja description pode diferir de propósito, e você julga. Os
     falsos verdes que o cheque já teve, e por que ele é assim, estão em
     *Armadilhas*, §4.
   - **Antes do commit, leia o `--stat` e responda por cada arquivo.**

     ```bash
     git add -A && git diff --cached --stat
     ```

     O `-A` só vale num worktree próprio ou numa árvore que estava limpa antes
     de você editar (ver *ANTES DE EDITAR*). Num checkout que outra sessão usa,
     ele leva o trabalho dela no seu commit.

     Um arquivo que você não pretendia tocar é **sinal, não ruído**: os gates olham
     o que você mudou de propósito, e só o `--stat` olha o que mudou sem querer. Já
     foi o único sensor a pegar um clobber (*Armadilhas*, §5).

   - Commit: `feat|fix($ARGUMENTS): vX.Y.Z — <resumo>`. **Sem trailer
     `Co-Authored-By`** — ver *Autoria dos commits* abaixo. Push pra origin/main.

   **Modo enxuto (skill local de outro repo):**
   - Edite os arquivos da skill na pasta local (`SKILL.md`, `references/**`).
   - Adicione/atualize um `CHANGELOG.md` dentro da pasta da skill com a data
     de hoje, explicando O QUÊ e POR QUÊ. Se a skill não tem versionamento,
     não invente `plugin.json`/bump — só registre a lição.
   - Rode o **gate da auditoria** (seção abaixo) em cada skill tocada.
   - Commit NO REPO onde a skill vive: `feat|fix($ARGUMENTS): <resumo>`. **Sem
     trailer `Co-Authored-By`** — ver *Autoria dos commits* abaixo. Push só se o
     usuário pedir.
   - NÃO toque em `marketplace.json`, no README do marketplace, nem em versões
     do marketplace.

## Gate da auditoria (depois de editar, antes do commit)

Vale para os dois modos, em cada skill com `SKILL.md` que o retrofit tocou. Com
`[SKIP] auditor ausente`, diga isso no resumo e siga só com os outros gates.

```bash
python3 "$SQA" "$ALVO" --format json --claims "${FLAGS[@]}" > "$B/depois.json"; echo "rc=$?"
git -C "$ALVO" add -N .                          # arquivo novo (reference) entra no diff
git -C "$ALVO" diff -U0 -- . > "$B/diff.txt"     # linhas acrescentadas e removidas
python3 "$RS/scripts/audit_gate.py" "$B"           # NOVO / dívida / SUMIU / LER / CLAIM
```

- **`NOVO` bloqueia,** com uma saída: a exceção legítima. Se a própria lição
  exige o que o check acusa (um contrato novo de subagente lido por caminho
  absoluto, um campo de topo que o harness só lê ali; a tabela *Erros comuns*
  da `skill-quality-audit` lista esses casos), não deforme a skill para o gate
  passar. Declare a exceção na proposta, com o motivo, e registre-a no
  CHANGELOG. Sem exceção declarada, corrija antes do commit. Uma mensagem com
  contagem que mudou (ex.: o `SKILL.md` cresceu de novo) aparece como `NOVO` e
  o `SUMIU` correspondente: o retrofit piorou algo que já estava fora.
- **`dívida` não bloqueia e não se conserta aqui:** vai para o resumo e para o
  CHANGELOG como dívida pré-existente (ver *Princípio*).
- **`SUMIU` precisa de motivo.** Um achado que desapareceu só é melhora se a
  causa foi resolvida. Se ele sumiu porque a reference, a citação ou a lição
  que o gerava foi apagada, a skill pode ter piorado com o sensor mais verde.
- **O `-N` do `LER` é a outra metade.** Cada linha removida tem que estar
  justificada na proposta (obsoleta com prova, movida ou fundida). Se não
  estiver, restaure.
- **Cada `CLAIM` recebe um veredito:** `tem sensor` (comando, `arquivo:símbolo`
  ou URL), `derivar` (a fórmula no lugar do valor), `datar` (data e comando de
  medição) ou `remover`. Um retrofit escreve "medido em 11/09/2026" e "91 linhas"
  o tempo todo, e é exatamente isso que apodrece. A régua é a da skill
  `skill-claim-check`; carregue-a se algum claim ficar sem veredito óbvio. A
  lista é heurística e deixa passar afirmação em prosa (no ensaio, "600 segundos"
  não apareceu). Por isso o gate imprime `LER` com as linhas novas de cada
  arquivo: leia todas elas.
- **Teto de 2 ciclos** (corrigir e rodar o gate de novo). Se ainda sobrar `NOVO`,
  pare e relate em vez de insistir.

## Autoria dos commits

Os commits deste fluxo saem **apenas com a autoria do usuário**. Não acrescente o
trailer `Co-Authored-By: Claude ...` — nem aqui, nem no corpo de PRs abertos por
este fluxo.

Dito explicitamente porque o prompt padrão do Claude Code **instrui** a pôr o
trailer, e o silêncio deixaria o default vencer. A instrução do usuário vence.

## Mantenha a descrição ENXUTA (triggering)

A `description` (frontmatter do SKILL.md, `plugin.json`, `marketplace.json`) é a **superfície
de triggering**: é por ela e pelo nome que o Claude decide invocar a skill.

- **Não anexe a lição de cada versão** nela: detalhe vai para `references/**` e para a linha do
  README. Descrição longa dilui o sinal e pode ser **cortada em silêncio** na lista `/skills`.
- **Alvo ~350–500 chars** (teto ~700 só para skill genuinamente complexa). Passou? Enxugue em vez
  de somar: UMA frase do que faz, 1–2 diferenciais e um `Triggers —` com ≤8 termos.
- **A MESMA descrição** nos três lugares.

## Mantenha a skill no formato da spec (agentskills.io)

Retrofit só soma texto, e é assim que uma skill passa do orçamento (*Armadilhas*, §6). A régua
é a spec aberta (https://agentskills.io/specification) e as boas práticas do mesmo site:

- **Frontmatter:** no topo só `name`, `description`, `license`, `compatibility`, `metadata` e
  `allowed-tools`. `name` com a-z, 0-9 e hífen, igual ao diretório. Autor e versão vão em
  `metadata` (`metadata.author`, `metadata.version`, em texto). Listas em bloco, nunca `[a, b]`.
- **Orçamento:** `SKILL.md` abaixo de 500 linhas e de ~20 mil chars (~5 mil tokens). Se a lição
  empurrar para cima disso, mova detalhe para `references/`, não comprima a lição até sumir.
- **Onde a lição entra:** na seção de gotchas/armadilhas do `SKILL.md`, uma linha por correção.
  Detalhe longo vai para uma reference.
- **References a um nível:** o `SKILL.md` roteia cada uma e diz **quando** ler ("leia
  `references/x.md` se a API devolver não-200", não "veja references/"). Reference acima de
  300 linhas ganha sumário no topo.

Gate, nos dois modos:

```bash
# modo completo (marketplace): o check 7 do validate-versions cobre a spec
python scripts/validate-versions.py
# qualquer modo: baseline + gate da auditoria (seções "Localizar o auditor" e "Gate da auditoria")
```

## Editando `marketplace.json` com segurança

Ele lista TODOS os plugins, cada um com seu próprio `"description"`/`"version"`. Ao editar programaticamente, **escope ao bloco do plugin alvo** — um match ingênuo em `"description":` (ou `sed` global) atinge as descrições de todos os plugins e as sobrescreve. Localize o bloco pelo `"name": "$ARGUMENTS"` e só então troque `version`/`description` dentro dele; depois confirme que as demais entradas ficaram intactas (ex.: contar descrições distintas) e rode `python -m json.tool` antes de commitar.

⚠️ **Não use `git checkout -- .claude-plugin/marketplace.json` para desfazer um teste** se você já editou esse arquivo nesta sessão. Ele é único e compartilhado por todos os plugins: o checkout leva junto as suas alterações reais, e o sintoma aparece depois, como divergência entre `plugin.json` e `marketplace.json`. Se precisar reverter uma sondagem, restaure só o valor que você mexeu — ou ressincronize a partir do `plugin.json`, que é a fonte canônica por plugin.

Não invente lições pra justificar uma mudança.
