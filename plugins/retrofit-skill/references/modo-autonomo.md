# Modo autônomo: o executor do retrofit-watch

Leia esta página inteira antes de editar, quando o comando vier como
`/retrofit-skill <plugin> --auto <dir do lote>`. Quem a lê é o executor que a `retrofit-watch` despacha.
O dono não está nesta conversa. Ninguém responde pergunta: o que o veredito não decide fica fora do commit.

Estes nomes valem em toda a página e no comando:

- `<dir do lote>` é o diretório do argumento. Lá está o `retrofit.json`. O `licoes.json` e o
  `veredito.json` estão na pasta-mãe.
- `<worktree>` é a chave `worktree` do `retrofit.json`.
- `<REPO>` do comando é o `<worktree>`. O PASSO 0 não procura o repo nem pergunta.
- `$Q` é `<worktree>/plugins/skill-quality-audit/skills`, a família da auditoria no worktree.
- `SQA=$Q/skill-quality-audit/scripts/audit_skill_quality.py`, o auditor que a porta roda.
- `RS=<worktree>/plugins/retrofit-skill`, a pasta deste comando no worktree.

O modo autônomo da loja segue as seções 1–8. Quando `retrofit.json` traz `repo`, siga a
variante privada abaixo no lugar dos passos exclusivos da loja.

## Lote privado com `--auto`

Trabalhe no `worktree` preparado e edite só a `pasta` do lote. Para o baseline e o gate
da seção 4, `<loja>` é o caminho `store` de `~/.claude/retrofit-watch.json`. Use
`Q=<loja>/plugins/skill-quality-audit/skills`, `SQA=$Q/skill-quality-audit/scripts/audit_skill_quality.py`
e `RS=<loja>/plugins/retrofit-skill`. O alvo da auditoria continua sendo `<worktree>/<pasta>`.
Confira o veredito e as lições como na seção 1. Se o lote muda a descrição, mude somente a
`description` do próprio SKILL.md. Faça os testes da mudança e acrescente uma entrada sob
um título com a data do commit em `<pasta>/CHANGELOG.md`, sem bump e sem mudar catálogo
ou README da loja. Faça um commit com `Retrofit-Mode: autonomous`, sem coautoria, e use
o `seal` da seção 6. Nunca commite no clone dedicado. Não faça push, nem publique status:
a publicação autônoma é da porta.

## Retro manual de repo listado

1. Confirme `origin`, a inscrição em `lean_auto`, o clone dedicado e a pasta rastreada.
   O servidor e o caminho efetivo de fetch e push precisam corresponder aos do clone.
   Fora do GitHub público, confira o caminho exato, não só o slug normalizado.
   Use `live_dir` da config ou `~/.local/share/skills-live` e nunca commite no clone dedicado.
   Busque `origin/main` nesse clone e crie um worktree num ramo próprio a partir dessa ref.
   Não mude o checkout de desenvolvimento.
2. Edite só a skill e seu CHANGELOG. Rode a auditoria e apresente o diff e o destino.
   Sem o sim do dono, não faça commit, push, status ou avanço.
3. Com o sim, faça o commit no worktree. Se houver `package-lock.json`, rode `npm ci` ali.
   Confirme que o Git resolve um pre-push executável (`git rev-parse --git-path hooks/pre-push`).
   Se faltar ou não executar, pare. Confira o SHA do commit e publique com
   `git -C <worktree> push --no-follow-tags origin HEAD:main`. Se o pre-push ou o remoto recusar,
   não publique status nem faça avanço. Mostre o resultado e conserve o worktree.
4. Confirme o SHA recebido na main. Registre o resultado do gate com
   `gh api --hostname <servidor-validado> -X POST repos/<dono/repo>/statuses/<sha> -f state=success -f context=local/ci -f description=<resumo>`.
   Rode `retrofit_watch.py live-advance <dono/repo>` e confira o HEAD do clone dedicado.
   Se um desses dois passos falhar, diga qual e preserve o SHA já publicado.

## 1. Antes de editar

1. Leia o `<dir do lote>/retrofit.json`. Dele saem o `id`, o `lote`, o `plugin`, o `worktree`, o `ramo` e
   as `licoes` do lote.
2. Leia o `veredito.json` e o `licoes.json` da pasta-mãe. O `licoes.json` dá o texto de cada lição. O
   `veredito.json` dá o parecer do revisor e faz o papel da confirmação do passo 3 do comando.
3. Sem o `retrofit.json` ou sem o `veredito.json`, pare: não edite, não faça commit e não rode o `seal`.
   Diga isso no relatório.
4. No lote do tipo `description`, a lição muda a `description`. Faça a mudança nos três lugares, como no
   modo completo, e sele igual. A porta segura o ramo pronto com `muda-description`, e o dono decide.
   Não carregue a `skill-creator`: a pergunta sobre o gatilho fica para o dono.

## 2. O escopo

- As lições são as do lote, e nenhuma outra entra no commit. Uma lição que você notou nesta execução
  fica fora. O revisor confere o diff contra as lições declaradas, na segunda passada.
- O worktree é o do `retrofit.json`. Não crie outro worktree nem outro ramo. Nunca escreva no checkout
  compartilhado da loja. O `prepare` já fez o `git fetch` e criou o worktree sobre o `origin/main`: da
  seção *ANTES DE EDITAR* do comando, só o baseline vale aqui.
- Corrija a frase que errou em vez de acrescentar uma regra. Antes de escrever, procure a regra já
  escrita: `grep -rn '<termo da lição>' <worktree>/plugins/<plugin>`. Se ela existe, mude essa frase. O
  revisor confere isso também, e uma regra repetida segura o lote com `regra-repetida`.

## 3. Os testes

Numa skill com `tests/` (`plugins/<plugin>/tests` ou `plugins/<plugin>/skills/<skill>/tests`):

1. Escreva o teste que falha antes da correção. Rode-o e veja-o falhar.
2. Aplique a correção.
3. Rode o teste e veja-o passar.
4. Mate os mutantes da correção: desfaça cada parte dela, rode o teste, veja-o falhar e restaure.

A porta roda os testes do plugin e a suíte `tests/` da raiz. Rode os dois antes do commit, com
`python3 -m unittest discover -s <pasta> -p 'test_*.py'`.

## 4. A auditoria

A família da auditoria fica em `$Q`. O baseline vai para uma pasta fora do worktree, como o
comando manda (`mktemp -d -p ~/.wt`): um arquivo novo no worktree deixa a árvore suja.

| Quando | O que roda | Nome em `--fases` |
|---|---|---|
| sempre | o baseline e o gate do script da fase 1, como hoje. ERRO ou AVISO novo segura | — |
| a lição põe ou muda um número, limite, caminho, flag ou versão (a linha `version:` do frontmatter não conta: o bump é mecânico, e o `validate-versions.py` o confere) | `skill-claim-check`: leia o `SKILL.md` dela no worktree e dê veredito a cada `CLAIM` | `claim-check` |
| a lição põe um caminho, uma reference ou uma dependência de fora da skill | `skill-self-containment`: leia o `SKILL.md` dela no worktree e siga-o na skill tocada | `self-containment` |
| o `SKILL.md` cruza ~400 linhas ou ~16 mil caracteres com a mudança (antes no teto ou abaixo, depois acima); um `SKILL.md` que já estava acima não dispara a fase | `skill-refactoring`: leia o `SKILL.md` dela no worktree; a escolha entre extrair e comprimir é dela | `refactoring` |

A porta confere três gatilhos mecânicos e recusa com `fase-de-auditoria` quando a fase exigida não está
no selo:

- `claim-check`: o gate da auditoria imprime um `CLAIM` fora da linha `version:` do frontmatter.
- `self-containment`: o commit cria um arquivo em `references/`, `scripts/` ou `assets/` de uma skill.
- `refactoring`: o `SKILL.md` cruza o teto, como diz a tabela.

Rodar a fase e não a declarar segura o retrofit. No `--fases`, ponha cada fase que rodou, e só elas.
Com a fase `refactoring` declarada, a segunda passada do revisor aceita o diff da refatoração.

Um plugin só de comandos não tem `SKILL.md`. A fase 1 é SKIP, como no comando, e o gate dele é o
`validate-versions.py`.

## 5. O commit

- Bump, `CHANGELOG`, `marketplace.json` e README como no modo completo (passo 4 do comando), com o
  `validate-versions.py` em rc 0 e o `check_release_sync.py` lido valor por valor.
- Antes do commit, `git -C <worktree> add -A && git -C <worktree> diff --cached --stat`. Responda por
  cada arquivo.
- Um commit só, com `--trailer "Retrofit-Mode: autonomous"`:
  `git -C <worktree> commit -m "<feat|fix>(<plugin>): vX.Y.Z — <resumo>" --trailer "Retrofit-Mode: autonomous"`.
  Ponha um trailer `Retrofit-Mode`, uma vez: a porta recusa dois valores com `sem-marca`.
- Sem `Co-Authored-By` e sem "Generated with". A porta segura com `coautoria` o commit que traz o
  primeiro.
- A mensagem passa pela camada 1, como o diff: nenhum nome de projeto, pessoa, empresa, máquina ou
  usuário nela.
- Depois do commit, `git -C <worktree> status --porcelain` sai vazio. Mudança fora do commit segura o lote
  com `arvore-suja`.
- Não faça nenhum push e não rode nenhum comando `claude plugin`. O push, a atualização da cópia
  instalada e o pedido de `/reload-plugins` são da porta e da sessão do dono.
- Não rode `approve`, `--publico-add` nem `--add`: os três pedem a palavra do dono.

## 6. O selo

O último passo é `seal <id> <lote> --licoes <n,…> --fases <fases>`, com o comando que o prompt do executor
dá. O `--licoes` leva as lições que entraram no commit. O `--fases` leva as fases da seção 4 que rodaram.
Sem fase, tire o `--fases`.

Com achado da camada 1, o `seal` sai 1 e lista os achados em `camada1`. Então:

1. Troque o termo por um genérico (`um projeto`, `<repo>`), no diff e na mensagem.
2. Emende o commit (`git -C <worktree> commit --amend`), com o mesmo trailer.
3. Sele de novo.

Faça isso no máximo 2 ciclos. Se ainda sobrar achado, pare e diga isso no relatório: a porta segura o
lote com `nome-privado`, e o dono decide.

## 7. A lição que não cabe

A lição que não cabe sem piorar a skill fica fora do commit e fora do `--licoes`. Cite-a no relatório,
com o motivo. O `seal` grava sozinho a linha `segurado` com `executor-recusou` para ela. Não rode `hold`.

Se nenhuma lição do lote cabe, não faça commit e não rode o `seal`. Diga isso no relatório: a sessão do
dono segura o lote.

## 8. O relatório

Responda em até 5 linhas:

1. o commit (sha curto e assunto) e a versão;
2. as lições incluídas;
3. as lições deixadas de fora, com o motivo;
4. as fases rodadas;
5. o resultado do `seal` (rc e `camada1`).
