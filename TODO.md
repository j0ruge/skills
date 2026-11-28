# TODO

Achados que não cabem no trabalho em curso: registrados, nunca perdidos. Formato e ciclo de vida: o
`templates/todo.pt-BR.md` do kit sdd. A forma se mede com o `tests/check-todo.sh --check TODO.md` do kit. Um
item consertado ganha `RESOLVED by <hash>` e sai depois do merge; um item decidido vira registro na segunda
seção. Análise longa mora em `docs/`, e o item aponta com `Fonte:`.

## Aberto
<!-- sdd:open -->

### Curadoria de terceiros

- [ ] **Criar uma área de skills de terceiros e incorporar o par de QA** —
  `CLAUDE.md:5` (`developed exclusively`) — distinguir as skills curadas das autorais na loja.
  Direção: começar por `qa-report` e `qa-execution`, de Pedro Nauck, comparando o upstream com as cópias locais.
  Preservar o retrofit de `qa-execution` sobre evidência sintética, homologação e falhas preexistentes.
  Registrar autoria, revisão de origem, licença e diferenças locais. Validar as referências entre as duas skills.
  Fonte: [pedronauck/skills](https://github.com/pedronauck/skills) — descoberto por `mantenedor` (2026-11-24)

- [ ] **Incorporar a skill `handoff`, de Matt Pocock (@mattpocock)** —
  `CLAUDE.md:5` (`developed exclusively`) — incluir na área de terceiros, com crédito visível ao criador
  e link para o upstream.
  Direção: fixar a revisão de origem, preservar o aviso da licença MIT e documentar as adaptações locais
  para referências que resolvem fora da pasta temporária e retomada de revisão com escopo Git explícito.
  Fonte: [mattpocock/skills — handoff](https://github.com/mattpocock/skills/tree/main/skills/productivity/handoff)
  — registrado por `mantenedor` (2026-11-25)

### Rulings do merge da retrofit-watch 0.4.0

- [ ] **O commit autônomo sem guarda de autor** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:1015` (`_mark_approved`) — nenhuma guarda
  lê o autor nem o committer, e o `--amend` mantém autor e data do HEAD, não os do `reviewed`. Um `includeIf`
  com outro e-mail passa. Anterior ao plano: a spec 5.6 só nomeia o diff e a mensagem (Ruling FR-1).
  Direção: uma guarda que confere autor e committer, ou o `commit-tree` com o autor explícito.
  Fonte: `docs/retrofit-watch/2026-11-24-pendencias-0.4.0.md` (T8-1) — descoberto por `revisor final` (2026-11-24)
- [ ] **Os hooks globais no amend da aprovação** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:1033` (`--amend`) — o `commit --amend` do
  `_mark_approved` roda os hooks do `core.hooksPath` global. Um `commit-msg` global mudaria a mensagem depois
  da camada 1. Nesta máquina nenhuma config global ou de sistema tem a chave (Ruling FR-2).
  Direção: `-c core.hooksPath=<devnull>` no amend, ou o `commit-tree`, com o par.
  Fonte: Ruling FR-2 da revisão final — descoberto por `revisor final` (2026-11-24)
- [ ] **Mensagem de commit fora do UTF-8 lida com replace** — `scripts/anonymity-gate.py:101` (`'replace'`) —
  as camadas leem a mensagem do commit com `replace`, e um nome em bytes inválidos na mensagem passa. A guarda
  5b (item 12 do plano) só cobre arquivos (Ruling FR-3).
  Direção: segurar com `escopo` a mensagem fora do UTF-8, como o blob, com o par.
  Fonte: Ruling FR-3 da revisão final — descoberto por `revisor final` (2026-11-24)
- [ ] **NFD contra NFC na camada 1** — `scripts/check-private-names.py:38` (`chave`) — a camada 1 não
  normaliza Unicode: um diretório colhido em NFD tem uma forma, a menção em NFC tem outra, e o nome privado
  passa. Anterior ao plano (Ruling FR-4).
  Direção: normalizar em NFC na `chave` e no `candidatos`, com o par; abrir antes de usar o `auto` num macOS.
  Fonte: `docs/retrofit-watch/2026-11-24-pendencias-0.4.0.md` (T12-4) — descoberto por `revisor final` (2026-11-24)
- [ ] **A busca do .git do projeto da sessão ignora o teto do git** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:275` (`_session_project`) — ignora o
  `GIT_CEILING_DIRECTORIES` e o `GIT_DISCOVERY_ACROSS_FILESYSTEM`. Falha fechada: um `~/.git` de dotfiles com
  o teto no `$HOME` seguraria as sessões fora de repo (R3, codereview r1 #14).
  Direção: respeitar as duas variáveis na subida pelos pais.
  Fonte: resíduo R3 da revisão final — descoberto por `revisor final` (2026-11-24)
- [ ] **O expected_ssh da fixture não segue o include.path** —
  `plugins/retrofit-watch/skills/retrofit-watch/tests/fixture_store.py:85` (`expected_ssh`) — lê só a
  config `--system`, e o código lê a config inteira. Caso teórico, só do teste (R4, codereview r1 #23).
  Direção: ler sem `--system`, como o código.
  Fonte: resíduo R4 da revisão final — descoberto por `revisor final` (2026-11-24)
- [ ] **Os nomes NTFS do .gitattributes** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:310` (`_attributes_name`) — o nome curto
  `gi7d29~N` não é reconhecido. Exige o 8.3 ligado e os `~1` a `~4` ocupados (R5, codereview r1 #6). O
  fluxo `.gitattributes::$DATA` também não é (falta reproduzir no NTFS; r1 #5).
  Direção: reconhecer o prefixo do `is_ntfs_dotgitattributes` do git e cortar o sufixo `:`, com o par.
  Fonte: resíduo R5 da revisão final e codereview r1 #5 — descoberto por `revisor final` (2026-11-24)

### Passos do dono antes de ligar o modo auto

- [ ] **O ensaio auto-dry e ligar o auto** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:96` (`AUTO_MODES`) — os passos 2
  e 3: `"mode": "auto-dry"` e `"store"` na config, uma sessão com `bypassPermissions` e uma skill da loja
  com atrito. Esperado: o ramo pronto e a linha `segurado — auto-dry`. Depois, `"mode": "auto"`.
  Fonte: `docs/superpowers/plans/2026-11-23-retrofit-watch-modo-autonomo.md` — descoberto por `plano` (2026-11-24)
- [ ] **A suíte do plugin no Windows** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:39` (`RUN_TIMEOUT`) — o passo 4: rodar a
  suíte com o `python3` do PATH antes de ligar o `auto` lá. O Git Credential Manager pode abrir uma janela, e
  o `RUN_TIMEOUT` de 900 s dá `erro` (falha fechada). Aceito: 15 min por lote numa máquina assim (FR-5).
  Fonte: Ruling FR-5 da revisão final — descoberto por `revisor final` (2026-11-24)
- [ ] **O MAX_PATH da cópia do commit no Windows** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:504` (`TREE_PREFIX`) — a cópia
  `.porta-*` sob a pasta de dados tem cerca de 60 caracteres de margem no `MAX_PATH`, não medida. Passar dá
  `interno` (falha fechada) (Ruling FR-6). Direção: o passo 4 do dono mede a margem.
  Fonte: Ruling FR-6 da revisão final — descoberto por `revisor final` (2026-11-24)

### O que o uso da retrofit-watch 0.4.0 mostrou

- [ ] **A skill de fora carregada na mesma mensagem apaga a atribuição da vigiada** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:567` (`_watch`) —
  uma mensagem carregou `zitadel-idp` e uma externa juntas. A monitorada ficou com `work: 0` e sem pedido de retro.
  Direção: preservar o par no mesmo `message.id` e testar que a externa posterior ainda encerra a atribuição.
  Corrigido no patch 0.4.1. RESOLVED by 682cd3d
  Fonte: relato observado em transcript interativo. A reprodução sintética está em
  `docs/handoffs/20261125-retrofit-watch-atribuicao/00-missao.md` —
  descoberto por `investigação do modo auto` (2026-11-25)

### LOW da codereview da retrofit-watch 0.4.0

- [ ] **A guarda 5b lista a árvore inteira** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:318` (`_g_opaque`) — o `ls-tree` lista a
  árvore inteira para conferir poucos caminhos (r1 #9).
  Direção: `ls-tree -z -- <paths>`.
  Fonte: codereview r1 #9 — descoberto por `codereview r1` (2026-11-24)
- [ ] **O _extract_base deixa passar TarError e OSError** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:667` (`_extract_base`) — o `clean_tree`
  embrulha os dois em StoreError, e o `_extract_base` não. O `publish` os pega (D25) (r1 #7).
  Direção: embrulhar dentro do `untar`.
  Fonte: codereview r1 #7 — descoberto por `codereview r1` (2026-11-24)
- [ ] **O alias network_env só serve a um teste** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:225` (`network_env`) — o alias não tem uso
  no `rw_gate.py`, só no `test_network_env_keeps_the_owner_ssh` (r1 #8; também o minor T7-2).
  Direção: o teste chama o `rw_store.network_env`, e o alias sai; ou o comentário diz para quê.
  Fonte: codereview r1 #8 — descoberto por `codereview r1` (2026-11-24)
- [ ] **O seal roda o portão do próprio ramo** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:623` (`seal`) — o portão do `seal` sai
  do commit do ramo. Rebaixado de MEDIUM: a porta segura com `escopo` todo caminho fora de
  `plugins/<plugin>/` antes da camada 1 (r1 #10). Direção, opcional: o portão do `seal` do `origin/main`.
  Fonte: codereview r1 #10 — descoberto por `codereview r1` (2026-11-24)
- [ ] **O estouro do critério apaga o cache dos commits** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:686` (`_startup_git`) — o `criterion`
  grava `{sha, estouro}` por cima dos commits: por 24 h, "desconhecido" parece "não cumprido" (r1 #11).
  Depois do `-c`, a mensagem do `_startup_git` (`args[:2]`) não nomeia o `archive` (r1 #12).
  Direção: o estouro numa chave à parte; o rótulo pula o par `-c k=v`.
  Fonte: codereview r1 #11 e #12 — descoberto por `codereview r1` (2026-11-24)
- [ ] **As pastas .porta- que sobram** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:534` (`ignore_errors=True`) — um SIGKILL
  deixa `.porta-*` na pasta de dados (r1 #13), e o `rmtree` falha em silêncio: no Windows sobram cerca de
  7,6 MB por porta (minor T10-4). Direção: limpar as pastas velhas no início, ou avisar.
  Fonte: codereview r1 #13 — descoberto por `codereview r1` (2026-11-24)
- [ ] **As mensagens de erro do projeto da sessão** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:300` (`run(command, env=env)`) — o rc da
  1ª chamada sai com a saída da 2ª (r2 #3). Um `PermissionError` no `isdir` dá "nao deu uma pasta" (r2 #4).
  Nenhum teste confere que o texto da 2ª chamada chega à mensagem (r3).
  Direção: o rc da chamada que deu o texto; o `os.stat` no lugar do `isdir`; o subteste do texto.
  Fonte: codereview r2 #3, #4 e r3 — descoberto por `codereview r2` (2026-11-24)
- [ ] **As docstrings do _session_project e do run_bytes** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:77` (`run_bytes`) — a do `run_bytes`
  não cita o `stderr=`, e a do `_session_project` não cita o caminho físico nem o caminho só do stdout.
  Direção: uma frase em cada uma.
  Fonte: codereview r2, forma — descoberto por `codereview r2` (2026-11-24)
- [ ] **A saída do escopo ambígua na referência** —
  `plugins/retrofit-watch/skills/retrofit-watch/references/modo-autonomo.md:241` (`escopo`) — a "Saída" junta
  a do executor e a do dono numa célula, e a frase "também o que o ramo tira" não diz de quem é a saída.
  Direção: duas frases, uma por saída, com o sensor do `test_auto_docs.py` verde.
  Fonte: codereview r2, forma — descoberto por `codereview r2` (2026-11-24)
- [ ] **O discard_retro conta no teto da sessão** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_auto.py:942` (`discard_retro`) — as linhas
  `descartado` dele contam no `used` e no teto da sessão (r1 #15). A função é longa, o `_own` não tem
  docstring e o acento é desigual nas mensagens (r1 #17).
  Direção: dizer na docstring, ou marcar as linhas; extrair dois helpers.
  Fonte: codereview r1 #15 e #17 — descoberto por `codereview r1` (2026-11-24)
- [ ] **A regra da palavra do dono não cita o discard** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_auto.py:30` (`OWNER_WORD_RULE`) — o agente pode
  fechar uma retro inteira sem a palavra do dono (r1 #16).
  Direção: pôr o `discard` na regra.
  Fonte: codereview r1 #16 — descoberto por `codereview r1` (2026-11-24)
- [ ] **A linha corrompida do registro some em silêncio** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_auto.py:80` (`read_registry`) — a linha ilegível é
  pulada sem aviso e pode reabrir um fluxo fechado. Anterior ao plano (r1 #18).
  Direção: contar as linhas puladas e avisar.
  Fonte: codereview r1 #18 — descoberto por `codereview r1` (2026-11-24)
- [ ] **Os sensores do CHANGELOG no test_auto_docs** —
  `plugins/retrofit-watch/skills/retrofit-watch/tests/test_auto_docs.py:440` (`flat(read(CHANGELOG))`) — a
  asserção lê o CHANGELOG inteiro, não a entrada `[0.4.0]` (r1 #19). O `assertNotIn` da frase antiga só barra
  o texto exato (r1 #20). Direção: ler só a primeira entrada; manter ou tirar o `assertNotIn`.
  Fonte: codereview r1 #19 e #20 — descoberto por `codereview r1` (2026-11-24)
- [ ] **Os sensores da referência no test_auto_docs** —
  `plugins/retrofit-watch/skills/retrofit-watch/tests/test_auto_docs.py:421` (`REASON_CAUSES`) — as
  subcadeias são curtas (r1 #22), e o `--retro` da referência não está ligado ao `CLI_USAGE` (r1 #21).
  Direção: `rows.get` com mensagem; `assertIn("--retro", rw.CLI_USAGE["discard"][0])`.
  Fonte: codereview r1 #21 e #22 — descoberto por `codereview r1` (2026-11-24)
- [ ] **O CHANGELOG 0.4.0 cita só o fetch e o push** —
  `plugins/retrofit-watch/CHANGELOG.md:113` (`push`) — o ponto da config de sistema cita só o `fetch` e o
  `push` da porta, e o `prepare` também usa o `remote_env` (r1 #24).
  Direção: "todo git que fala com o `origin`".
  Fonte: codereview r1 #24 — descoberto por `codereview r1` (2026-11-24)
- [ ] **A cópia da porta não confere o info/attributes** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:508` (`info/attributes`) — a C2 do plano
  deixa fora o `info/attributes` do `.git` comum, e um `export-ignore` ali tiraria um arquivo da cópia
  (r1 #25). Direção, opcional: comparar a lista da cópia com o `ls-tree` do commit.
  Fonte: codereview r1 #25 — descoberto por `codereview r1` (2026-11-24)

### Minors adiados (triagem)

- [ ] **Os minors adiados da retrofit-watch 0.4.0** —
  `docs/retrofit-watch/2026-11-24-pendencias-0.4.0.md:1` (`Abertos`) — 50 minors das revisões por tarefa
  ainda valem no `main`, uma linha cada, com o arquivo e o símbolo. A revisão final os julgou "podem esperar".
  Direção: tratar por arquivo, junto com o item vizinho deste TODO; tirar da lista o que for corrigido.
  Fonte: `docs/retrofit-watch/2026-11-24-pendencias-0.4.0.md` — descoberto por `revisor final` (2026-11-24)

### Revisão da atribuição da retrofit-watch

- [ ] **O registro da missão mistura a medição histórica com o estado atual** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/00-missao.md:76` (`I1 estava vermelha`) —
  a frase usa HEAD para a medição anterior à correção e lista uma aprovação que já consta do aceite.
  Direção: ancorar o Red no commit anterior e separar aprovação de merge. RESOLVED by 9e79cb6
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r1.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-25)
- [ ] **A publicação do patch desloca uma âncora do backlog da retrofit-watch** —
  `plugins/retrofit-watch/CHANGELOG.md:113` (`push`) — a entrada 0.4.1 deslocou a âncora original da linha 66.
  O linter sem baseline detecta o desvio. Direção: atualizar a referência do item sobre fetch e push.
  A primeira correção ficou em `9e79cb6`. RESOLVED by 9e79cb6
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r1.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-25)

- [ ] **ID de chamada reaproveitado entre mensagens passa por vínculo novo** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:681` (`_skill_origin`) —
  após trocar a mensagem ativa, o ID consumido antes ainda pode preservar a monitorada diante de uma carga externa.
  Direção: medir a janela de ambiguidade antes de ampliar a detecção além da mensagem ativa.
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r2.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-25)

- [ ] **Metadado externo antigo encerra a atribuição de uma carga posterior** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:725` (`unlinked = False`) —
  após confirmar a carga posterior, o metadado externo antigo encerra o crédito futuro. O caso já falha na base.
  Direção: diferenciar ID comprovadamente obsoleto de metadado sem origem conhecida. RESOLVED by fcbd6cb
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r3.md` — descoberto por
  `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-25)

- [ ] **O handoff de R3 não distingue de qual mensagem é a chamada pendente** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r4.md:64` (`outra chamada pendente`) —
  a frase estende a garantia a uma chamada de outra mensagem, mas a sonda de R4 devolve o alvo errado nesse caso.
  Direção: distinguir vínculo restante na mesma mensagem de pendência em outra. RESOLVED by 893c9c6
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r4.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-26)

- [ ] **Medições históricas da atribuição sem saída preservada** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r6.md:225` (`58 degradações`) —
  totais de mutações e a prova nativa foram resumidos sem as saídas nos artefatos de revisão.
  Direção: guardar os resultados junto do commit e do comando que os produziu.
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r5.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)

- [ ] **A receita histórica de suíte do plano herda o Git privado do runner** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/01-plano.md:121` (`TEST_CMD`)
  — As variáveis do Git do runner desviam os comandos Git das fixtures. O handoff de execução já isola as duas.
  Direção: na triagem da prosa histórica, apontar para a receita isolada e manter a evidência da execução.
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r7.md` — descoberto por
  `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)

- [ ] **A migração perde a ordem de cargas anteriores ao offset** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:433` (`attribution_closed`) —
  a 0.4.0 não distingue os dois cortes, com perda de retro nova e falso pedido quando só houve nome externo.
  Direção: recuperar só a ordem sem recontar trabalho. RESOLVED by 8fa5c7d
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r9.md` — descoberto por
  `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)

- [ ] **Três âncoras da atribuição apontam para linhas vizinhas** —
  `TODO.md:91` (`_watch`) — as referências a `_watch`, `_skill_origin` e `unlinked = False`
  passam a tolerância de dez linhas, mas abrem trechos vizinhos em vez dos símbolos citados.
  Direção: alinhar as três linhas à próxima alteração do backlog. RESOLVED by e58f9fc
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r10.md` — descoberto por
  `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)

- [ ] **A nota de release torna exclusiva a proteção por ID aposentado** —
  `plugins/retrofit-watch/CHANGELOG.md:21` (`prova de ID aposentado`) —
  a sonda de r23 também preserva a monitorada com metadado externo atrasado e vínculo da mesma mensagem.
  Direção: distinguir as duas provas de preservação. RESOLVED by 5459e8c
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r23.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)

- [ ] **Estado intermediário inverte a precedência do slash** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:430` (`slash_prior_calls`) —
  um slash anterior volta a valer após a externa no snapshot de c2c0c8c. O estado real da 0.4.0 passa.
  Direção: decidir se snapshots intermediários precisam recuperar a ordem antes de ampliar a migração.
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r24.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)

- [ ] **O resumo de EXEC mantém o estado de R19 após a validação de R20** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/20-handoff-exec.md:7` (`TEST_CMD`) —
  o gate aponta 41f2952 e 134 testes do hook, mas o resumo e o estado do repo ainda orientam por R19.
  Direção: identificar os SHAs e as provas no host. RESOLVED by ac6c96f
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r30.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-28)

- [ ] **Handoff de EXEC não explicita a condição da delegação de merge** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/00-missao.md:34` (`Campanha e delegação`) —
  a condição de vigência e a fonte da autorização não aparecem no handoff, que antes apontava para o mantenedor.
  Direção: explicitar a vigência e vincular a decisão. RESOLVED by b6b1d3c
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r31.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-28)

- [ ] **Missão registra duas autoridades para o merge** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/00-missao.md:85` (`pr-ready`) —
  a pendência preserva a regra do piloto, mas a seção de campanha descreve o merge delegado.
  Direção: centralizar as condições vigentes na missão. RESOLVED by 02fe0ac
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r32.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-28)

- [ ] **Inventário de EXEC não inclui o Check de R24** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint.md:35` (`possível dono rejeitado`) —
  a tabela termina em R23, mas o checkpoint inclui R24 e o boot manda repetir 26 Checks.
  O inventário remete à tabela canônica sem repetir o intervalo. RESOLVED by 149086f
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r37.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-28)

- [ ] **A cópia histórica do Check da retrofit-watch diverge do resultado canônico** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r37.md:91` (`skill_externa`) —
  a grafia não coincide com o stdout da sonda, embora a célula do checkpoint passe.
  A expectativa histórica foi alinhada à célula canônica, sem alterar o comando. RESOLVED by 0bd4efa
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r38.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-28)

- [ ] **Resumo de EXEC confunde o alvo da retro na retomada legada** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/20-handoff-exec.md:18` (`pedem retro para a externa antiga`) —
  o metadado externo antigo é ignorado, mas o resumo diz que a retro vai para a externa.
  Direção: distinguir a carga externa ignorada da monitorada `codereview`, que recebe a retro.
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r39.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-28)

### Documentação da loja

- [ ] **Separar o histórico de releases da tabela de plugins no README** —
  `README.md:147` (`Available Plugins`) — a tabela repete notas de várias versões e dificulta comparar plugins.
  Direção: manter nome, versão, descrição curta e links na tabela. Preservar detalhes nos changelogs e referências.
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/45-docs.md` —
  descoberto por `sdd-docs` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)

- [ ] **A fonte do incidente da atribuição leva à reprodução sintética** —
  `TODO.md:95` (`transcript interativo`) — a missão citada registra o caso sintético, não o incidente descrito.
  Direção: distinguir a origem do relato da reprodução no handoff. RESOLVED by 1b6b72f
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r14.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)

- [ ] **Marcador RESOLVED by fora da linha do corpo no backlog** — `TODO.md:268` (`RESOLVED by`) —
  O marcador em linha própria consome uma das oito linhas do item.
  Direção: colocar o marcador ao fim do corpo ou junto da fonte. RESOLVED by 42905fc
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r15.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)

- [ ] **Pré-scan manual da revisão pode passar sem analisar linhas** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r15.md:117` (`scan_secrets.sh`) —
  `3b8ef98` cobriu cor e prefixos. `261bff5` cobriu comparadores e conversores.
  `f41ad63` corrigiu Markdown binário. Na r19, o bloco da r15 ainda saiu com rc 0 após a contagem rejeitada.
  Direção: propagar a falha do pré-scan ao bloco inteiro. RESOLVED by 26feade
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r16.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)

- [ ] **Controle negativo da r16 perde a receita original** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r16.md:152` (`recipe=`) —
  A extração lê a r15 atual e o bloco termina antes de chamar o scanner.
  Direção: extrair a receita do blob histórico. RESOLVED by 261bff5
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r17.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)

- [ ] **A reprodução do limite do backlog perde o caminho do kit** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r15.md:132` (`SDD_KIT`) —
  Bash e Zsh retornam rc 127 ao reproduzir o limite de linhas após o bloco estrito.
  Direção: localizar o kit no bloco da amostra temporária. RESOLVED by 41a6ca5
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r20.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)

- [ ] **A reprodução do limite do backlog não fixa a versão da amostra** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r15.md:129` (`item do incidente`) —
  Com o item atual, as três inserções dão oito linhas e rc 0 em vez da rejeição esperada.
  Direção: copiar a amostra do blob histórico indicado na r20. RESOLVED by a664c98
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r21.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)

- [ ] **Receitas de pré-scan da r24 à r27 não isolam o Git** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r24.md:159` (`scan_secrets.sh`) —
  com o Git da fixture, a revisão é inválida, mas as quatro receitas retornam rc 0 e analisam zero linhas.
  Direção: isolar a seleção do Git e propagar falha ou contagem divergente nas quatro receitas. RESOLVED by 1863fc2
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r34.md` — descoberto por
  `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-28)

- [ ] **Sonda de r34 não existe no commit revisado** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r34.md:122` (`--expect`) —
  a extração falha no SHA indicado, mas o Python recebe código vazio e retorna rc 0.
  Direção: exigir o blob publicado e rejeitar extração sem código.
  RESOLVED by f82e1d5
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r35.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-28)

## Decidido — não reabrir
<!-- sdd:decided -->

- **As frases do plano de correções (r1 #26 e #27)** — o plano já rodou, e plano executado não se edita: o "Final-F1" sem definição (r1 #26) e o "em qualquer versão do Python" não medido no 3.11 (r1 #27) ficam como estão; decisão do dono na triagem do TODO.md — `docs/superpowers/plans/2026-11-24-retrofit-watch-auto-correcoes.md` (2026-11-24)
