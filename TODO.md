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
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:1280` (`_mark_approved`) — nenhuma guarda
  lê o autor nem o committer, e o `--amend` mantém autor e data do HEAD, não os do `reviewed`. Um `includeIf`
  com outro e-mail passa. Anterior ao plano: a spec 5.6 só nomeia o diff e a mensagem (Ruling FR-1).
  Direção: uma guarda que confere autor e committer, ou o `commit-tree` com o autor explícito.
  Fonte: `docs/retrofit-watch/2026-11-24-pendencias-0.4.0.md` (T8-1) — descoberto por `revisor final` (2026-11-24)
- [ ] **Os hooks globais no amend da aprovação** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:1298` (`--amend`) — o `commit --amend` do
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
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:276` (`_session_project`) — ignora o
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
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:342` (`_attributes_name`) — o nome curto
  `gi7d29~N` não é reconhecido. Exige o 8.3 ligado e os `~1` a `~4` ocupados (R5, codereview r1 #6). O
  fluxo `.gitattributes::$DATA` também não é (falta reproduzir no NTFS; r1 #5).
  Direção: reconhecer o prefixo do `is_ntfs_dotgitattributes` do git e cortar o sufixo `:`, com o par.
  Fonte: resíduo R5 da revisão final e codereview r1 #5 — descoberto por `revisor final` (2026-11-24)

- [ ] **A aprovação pública não fica vinculada ao patch revisto** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:30` (`OVERRIDABLE`) —
  a autorização da loja não identifica o patch que o dono aprovou.
  Direção: persistir a identidade do patch e conferir no gate público antes de aceitar a aprovação.
  Fonte: `docs/superpowers/specs/2026-11-25-retrofit-watch-lean-auto-design.md:269` (§9) —
  descoberto por `sdd-executor` na missão `20261127-retrofit-watch-050` (2026-11-28)

### Passos do dono antes de ligar o modo auto

- [ ] **O ensaio auto-dry e ligar o auto** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:100` (`AUTO_MODES`) — os passos 2
  e 3: `"mode": "auto-dry"` e `"store"` na config, uma sessão com `bypassPermissions` e uma skill da loja
  com atrito. Esperado: o ramo pronto e a linha `segurado — auto-dry`. Depois, `"mode": "auto"`.
  Fonte: `docs/superpowers/plans/2026-11-23-retrofit-watch-modo-autonomo.md` — descoberto por `plano` (2026-11-24)
- [ ] **A suíte do plugin no Windows** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:40` (`RUN_TIMEOUT`) — o passo 4: rodar a
  suíte com o `python3` do PATH antes de ligar o `auto` lá. O Git Credential Manager pode abrir uma janela, e
  o `RUN_TIMEOUT` de 900 s dá `erro` (falha fechada). Aceito: 15 min por lote numa máquina assim (FR-5).
  Fonte: Ruling FR-5 da revisão final — descoberto por `revisor final` (2026-11-24)
- [ ] **O MAX_PATH da cópia do commit no Windows** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:552` (`TREE_PREFIX`) — a cópia
  `.porta-*` sob a pasta de dados tem cerca de 60 caracteres de margem no `MAX_PATH`, não medida. Passar dá
  `interno` (falha fechada) (Ruling FR-6). Direção: o passo 4 do dono mede a margem.
  Fonte: Ruling FR-6 da revisão final — descoberto por `revisor final` (2026-11-24)

### LOW da codereview da retrofit-watch 0.4.0

- [ ] **A guarda 5b lista a árvore inteira** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:350` (`_g_opaque`) — o `ls-tree` lista a
  árvore inteira para conferir poucos caminhos (r1 #9).
  Direção: `ls-tree -z -- <paths>`.
  Fonte: codereview r1 #9 — descoberto por `codereview r1` (2026-11-24)
- [ ] **O _extract_base deixa passar TarError e OSError** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:709` (`_extract_base`) — o `clean_tree`
  embrulha os dois em StoreError, e o `_extract_base` não. O `publish` os pega (D25) (r1 #7).
  Direção: embrulhar dentro do `untar`.
  Fonte: codereview r1 #7 — descoberto por `codereview r1` (2026-11-24)
- [ ] **O alias network_env só serve a um teste** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_gate.py:257` (`network_env`) — o alias não tem uso
  no `rw_gate.py`, só no `test_network_env_keeps_the_owner_ssh` (r1 #8; também o minor T7-2).
  Direção: o teste chama o `rw_store.network_env`, e o alias sai; ou o comentário diz para quê.
  Fonte: codereview r1 #8 — descoberto por `codereview r1` (2026-11-24)
- [ ] **O seal roda o portão do próprio ramo** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:677` (`seal`) — o portão do `seal` sai
  do commit do ramo. Rebaixado de MEDIUM: a porta segura com `escopo` todo caminho fora de
  `plugins/<plugin>/` antes da camada 1 (r1 #10). Direção, opcional: o portão do `seal` do `origin/main`.
  Fonte: codereview r1 #10 — descoberto por `codereview r1` (2026-11-24)
- [ ] **O estouro do critério apaga o cache dos commits** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:748` (`_startup_git`) — o `criterion`
  grava `{sha, estouro}` por cima dos commits: por 24 h, "desconhecido" parece "não cumprido" (r1 #11).
  Depois do `-c`, a mensagem do `_startup_git` (`args[:2]`) não nomeia o `archive` (r1 #12).
  Direção: o estouro numa chave à parte; o rótulo pula o par `-c k=v`.
  Fonte: codereview r1 #11 e #12 — descoberto por `codereview r1` (2026-11-24)
- [ ] **As pastas .porta- que sobram** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:582` (`ignore_errors=True`) — um SIGKILL
  deixa `.porta-*` na pasta de dados (r1 #13), e o `rmtree` falha em silêncio: no Windows sobram cerca de
  7,6 MB por porta (minor T10-4). Direção: limpar as pastas velhas no início, ou avisar.
  Fonte: codereview r1 #13 — descoberto por `codereview r1` (2026-11-24)
- [ ] **As mensagens de erro do projeto da sessão** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:303` (`run(command, env=env)`) — o rc da
  1ª chamada sai com a saída da 2ª (r2 #3). Um `PermissionError` no `isdir` dá "nao deu uma pasta" (r2 #4).
  Nenhum teste confere que o texto da 2ª chamada chega à mensagem (r3).
  Direção: o rc da chamada que deu o texto; o `os.stat` no lugar do `isdir`; o subteste do texto.
  Fonte: codereview r2 #3, #4 e r3 — descoberto por `codereview r2` (2026-11-24)
- [ ] **As docstrings do _session_project e do run_bytes** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:78` (`run_bytes`) — a do `run_bytes`
  não cita o `stderr=`, e a do `_session_project` não cita o caminho físico nem o caminho só do stdout.
  Direção: uma frase em cada uma.
  Fonte: codereview r2, forma — descoberto por `codereview r2` (2026-11-24)
- [ ] **A saída do escopo ambígua na referência** —
  `plugins/retrofit-watch/skills/retrofit-watch/references/modo-autonomo.md:280` (`escopo`) — a "Saída" junta
  a do executor e a do dono numa célula, e a frase "também o que o ramo tira" não diz de quem é a saída.
  Direção: duas frases, uma por saída, com o sensor do `test_auto_docs.py` verde.
  Fonte: codereview r2, forma — descoberto por `codereview r2` (2026-11-24)
- [ ] **O discard_retro conta no teto da sessão** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_auto.py:1114` (`discard_retro`) — as linhas
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
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_auto.py:81` (`read_registry`) — a linha ilegível é
  pulada sem aviso e pode reabrir um fluxo fechado. Anterior ao plano (r1 #18).
  Direção: contar as linhas puladas e avisar.
  Fonte: codereview r1 #18 — descoberto por `codereview r1` (2026-11-24)
- [ ] **Os sensores do CHANGELOG no test_auto_docs** —
  `plugins/retrofit-watch/skills/retrofit-watch/tests/test_auto_docs.py:494` (`flat(read(CHANGELOG))`) — a
  asserção lê o CHANGELOG inteiro, não a entrada `[0.4.0]` (r1 #19). O `assertNotIn` da frase antiga só barra
  o texto exato (r1 #20). Direção: ler só a primeira entrada; manter ou tirar o `assertNotIn`.
  Fonte: codereview r1 #19 e #20 — descoberto por `codereview r1` (2026-11-24)
- [ ] **Os sensores da referência no test_auto_docs** —
  `plugins/retrofit-watch/skills/retrofit-watch/tests/test_auto_docs.py:475` (`REASON_CAUSES`) — as
  subcadeias são curtas (r1 #22), e o `--retro` da referência não está ligado ao `CLI_USAGE` (r1 #21).
  Direção: `rows.get` com mensagem; `assertIn("--retro", rw.CLI_USAGE["discard"][0])`.
  Fonte: codereview r1 #21 e #22 — descoberto por `codereview r1` (2026-11-24)
- [ ] **O CHANGELOG 0.4.0 cita só o fetch e o push** —
  `plugins/retrofit-watch/CHANGELOG.md:134` (`push`) — o ponto da config de sistema cita só o `fetch` e o
  `push` da porta, e o `prepare` também usa o `remote_env` (r1 #24).
  Direção: "todo git que fala com o `origin`".
  Fonte: codereview r1 #24 — descoberto por `codereview r1` (2026-11-24)
- [ ] **A cópia da porta não confere o info/attributes** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:556` (`info/attributes`) — a C2 do plano
  deixa fora o `info/attributes` do `.git` comum, e um `export-ignore` ali tiraria um arquivo da cópia
  (r1 #25). Direção, opcional: comparar a lista da cópia com o `ls-tree` do commit.
  Fonte: codereview r1 #25 — descoberto por `codereview r1` (2026-11-24)

### Minors adiados (triagem)

- [ ] **Os minors adiados da retrofit-watch 0.4.0** —
  `docs/retrofit-watch/2026-11-24-pendencias-0.4.0.md:1` (`Abertos`) — 50 minors das revisões por tarefa
  ainda valem no `main`, uma linha cada, com o arquivo e o símbolo. A revisão final os julgou "podem esperar".
  Direção: tratar por arquivo, junto com o item vizinho deste TODO; tirar da lista o que for corrigido.
  Fonte: `docs/retrofit-watch/2026-11-24-pendencias-0.4.0.md` — descoberto por `revisor final` (2026-11-24)

- [ ] **A camada 1 sinaliza evidência sintética da entrega local** —
  `scripts/anonymity-gate.py:187` (`_segredos`) — a comparação com `origin/main` acusa
  uma impressão digital pública do plano e duas URLs SSH de fixture, sem credenciais.
  Direção: tratar as formas públicas comprovadas sem reduzir a detecção de segredos reais. RESOLVED by b5512cb
  Fonte: `docs/handoffs/20261127-retrofit-watch-050/20-handoff-exec.md` — descoberto por
  `sdd-executor` na missão `20261127-retrofit-watch-050` (2026-11-28)
  RECURRED 1: 20261127-retrofit-watch-050/R7 (2026-11-28)

### Revisão da atribuição da retrofit-watch

- [ ] **ID de chamada reaproveitado entre mensagens passa por vínculo novo** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:755` (`_skill_origin`) —
  após trocar a mensagem ativa, o ID consumido antes ainda pode preservar a monitorada diante de uma carga externa.
  Direção: medir a janela de ambiguidade antes de ampliar a detecção além da mensagem ativa.
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r2.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-25)

- [ ] **Medições históricas da atribuição sem saída preservada** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r6.md:225` (`58 degradações`) —
  totais de mutações e a prova nativa foram resumidos sem as saídas nos artefatos de revisão.
  Direção: guardar os resultados junto do commit e do comando que os produziu.
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r5.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)
  RECURRED 1: chewiesoft-marketplace/20261127-retrofit-watch-050 (2026-11-28)

- [ ] **A receita histórica de suíte do plano herda o Git privado do runner** —
  `docs/handoffs/20261125-retrofit-watch-atribuicao/01-plano.md:121` (`TEST_CMD`)
  — As variáveis do Git do runner desviam os comandos Git das fixtures. O handoff de execução já isola as duas.
  Direção: na triagem da prosa histórica, apontar para a receita isolada e manter a evidência da execução.
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r7.md` — descoberto por
  `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)
  RECURRED 2: 20261127-retrofit-watch-050 (2026-11-28); 20261127-retrofit-watch-050/R11 (2026-11-28)

- [ ] **A fixture de duas skills full do mesmo plugin já falha na base** —
  `plugins/retrofit-watch/skills/retrofit-watch/tests/test_auto_mode.py:203`
  (`test_second_skill_of_the_same_plugin_is_recorded`) — a segunda skill não entra no estado em `6d72029`.
  Direção: verificar se os IDs das duas cargas na fixture representam chamadas distintas no Stop da 0.4.1.
  Fonte: `docs/handoffs/20261127-retrofit-watch-050/checkpoint-notas.md` — descoberto por
  `sdd-executor` na missão `20261127-retrofit-watch-050` (2026-11-28)
  RECURRED 3: 20261127-retrofit-watch-050/I2 (2026-11-28); 20261127-retrofit-watch-050/I3 (2026-11-28); 20261127-retrofit-watch-050/I4 (2026-11-28)

- [ ] **Estado intermediário inverte a precedência do slash** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:510` (`slash_prior_calls`) —
  um slash anterior volta a valer após a externa no snapshot de c2c0c8c. O estado real da 0.4.0 passa.
  Direção: decidir se snapshots intermediários precisam recuperar a ordem antes de ampliar a migração.
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/40-review-r24.md` —
  descoberto por `sdd-reviewer` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)

### Documentação da loja

- [ ] **Separar o histórico de releases da tabela de plugins no README** —
  `README.md:147` (`Available Plugins`) — a tabela repete notas de várias versões e dificulta comparar plugins.
  Direção: manter nome, versão, descrição curta e links na tabela. Preservar detalhes nos changelogs e referências.
  Fonte: `docs/handoffs/20261125-retrofit-watch-atribuicao/45-docs.md` —
  descoberto por `sdd-docs` na missão `20261125-retrofit-watch-atribuicao` (2026-11-27)

- [ ] **O executor privado herda caminhos de auditoria da loja no worktree errado** —
  `plugins/retrofit-skill/references/modo-autonomo.md:13` (`skill-quality-audit/skills`) —
  o diretório nominal do worktree não contém o auditor da loja.
  Direção: declarar a origem de Q, SQA e RS para lote privado e manter o alvo na pasta da skill. RESOLVED by 3162507
  Fonte: `docs/handoffs/20261127-retrofit-watch-050/40-review-r1.md` —
  descoberto por `sdd-reviewer` na missão `20261127-retrofit-watch-050` (2026-11-28)

- [ ] **As receitas dos handoffs preservam escapes indevidos ao copiar** —
  `docs/handoffs/20261127-retrofit-watch-050/40-review-r3.md:47` (`--repo`) —
  o caminho do scanner recebe aspas literais e o comando da suíte falha antes de rodar.
  Direção: usar aspas de shell nas receitas Markdown e conservar os escapes necessários no YAML. RESOLVED by 2c63f1a
  Fonte: `docs/handoffs/20261127-retrofit-watch-050/40-review-r3.md` —
  descoberto por `sdd-reviewer` na missão `20261127-retrofit-watch-050` (2026-11-28)

- [ ] **O status manual não preserva a porta HTTPS explícita** —
  `plugins/retrofit-skill/references/modo-autonomo.md:49` (`--hostname`) —
  o endpoint relativo usa a porta padrão. O cliente recusa passar a porta no hostname.
  Direção: descrever a URL absoluta para esse caso e manter o hostname sem porta. RESOLVED by 84a0b0e
  Fonte: `docs/handoffs/20261127-retrofit-watch-050/40-review-r4.md` —
  descoberto por `sdd-reviewer` na missão `20261127-retrofit-watch-050` (2026-11-28)

### Clone dedicado da retrofit-watch

- [ ] **O avanço pode mover outro ramo depois da última conferência** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:1170` (`merge-base`) —
  uma troca de ramo limpo após a prova de ancestralidade move esse ramo, deixa a main parada e grava sucesso.
  Direção: vincular a atualização da cópia ao ramo conferido, sem depender só de uma checagem separada.
  Fonte: `docs/handoffs/20261127-retrofit-watch-050/40-review-r2.md` — descoberto por
  `sdd-reviewer` na missão `20261127-retrofit-watch-050` (2026-11-28)

- [ ] **A remoção do marcador do setup no Windows ainda depende do caminho** —
  `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:1021` (`_finish_live_setup`) —
  As duas checagens de identidade sinalizam a troca, mas não ancoram a remoção entre elas.
  Direção: testar a remoção pelo identificador do arquivo numa fixture Windows nativa.
  Fonte: `docs/handoffs/20261127-retrofit-watch-050/20-handoff-exec.md` — descoberto por
  `sdd-executor` na missão `20261127-retrofit-watch-050` (2026-11-28)

## Decidido — não reabrir
<!-- sdd:decided -->

- **As frases do plano de correções (r1 #26 e #27)** — o plano já rodou, e plano executado não se edita: o "Final-F1" sem definição (r1 #26) e o "em qualquer versão do Python" não medido no 3.11 (r1 #27) ficam como estão; decisão do dono na triagem do TODO.md — `docs/superpowers/plans/2026-11-24-retrofit-watch-auto-correcoes.md` (2026-11-24)
