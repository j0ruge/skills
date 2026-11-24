# retrofit-watch 0.4.0: as correções que faltam para o modo `auto` — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fechar os 15 defeitos que impedem o modo `auto` de funcionar na prática, ou que deixam um nome privado ou uma mudança sem revisão chegar ao `origin/main` público.

**Architecture:** Nenhuma peça nova. A porta (`publish`) passa a rodar o portão, os testes, o `validate-versions.py` e a auditoria de uma cópia do commit conferido, tirada com `git archive`, e não do disco do worktree. Ela guarda o HEAD depois do rebase e segura o lote se ele mudar. O registro, a colheita e o critério deixam de ler erro como vazio. Duas guardas novas e três apertadas entram na porta, todas com motivos que já existem.

**Tech Stack:** Python 3 só com biblioteca padrão (`unittest`, `subprocess`, `json`, `tarfile`, `py_compile`), git, Markdown dos contratos da skill.

**Spec:** `docs/superpowers/specs/2026-11-23-retrofit-watch-modo-autonomo-design.md`. Plano anterior, para as decisões O1 a O9 e D1 a D25: `docs/superpowers/plans/2026-11-23-retrofit-watch-modo-autonomo.md`.

**Base:** HEAD `1313ba5`, 46 commits sobre `f099db4`. Nada foi empurrado. A 0.4.0 da `retrofit-watch` e a 0.11.0 da `retrofit-skill` ainda não saíram: este plano entra nelas, **sem bump**.

## Global Constraints

Copiadas do plano anterior, palavra por palavra, as que ainda valem. "Tarefa 6" e "Tarefa 13" nelas são tarefas do plano anterior.

- Trabalhar no worktree `~/.wt/retrofit-watch-autonomo`, ramo `feat/retrofit-watch-autonomo`. Nunca no checkout `~/repos/skills`. Nenhum `git push`, PR ou merge: são do dono.
- A loja é pública. Nenhum nome de projeto, empresa, pessoa, máquina ou usuário em arquivo nem em mensagem de commit. Caminho com `~`, nunca com o nome do usuário. `python3 scripts/check-private-names.py` sai 0 antes de cada commit. A mensagem ninguém varre: releia.
- Commit sem `Co-Authored-By` e sem "Generated with". Conferir: `git log -1 --format='%(trailers:key=Co-authored-by,valueonly)'` imprime nada.
- Só biblioteca padrão. Código novo não importa `fcntl`: a trava é o `_lock`/`_unlock` de `retrofit_watch.py`. Toda saída para stdout é `json.dumps` com ASCII (o stdout do Windows é cp1252). Caminho comparado passa pelo `_slashed`.
- Script Python se chama com `sys.executable`, nunca com `python3` fixo. Binário externo se acha com `shutil.which` (no Windows o `claude` é `claude.cmd`).
- O hook (`stop`, `baseline`, `pending`) tem 10 s de timeout: no caminho dele, nenhuma chamada de rede e nenhum `git fetch`. O hook nunca lança subagente. Nada estoura dentro do hook: uma falha no caminho autônomo cai no texto manual e vai ao `errors.log`.
- O padrão de `mode` é `manual`. Sem a config, a saída do hook é byte a byte a de hoje. `RETROFIT_WATCH=off` continua desligando tudo.
- Nenhum teste toca a rede, o `claude` real ou o `origin` real. A loja dos testes é a fixture da Tarefa 6: um repo `--bare` como `origin` e um clone, os dois sob o diretório temporário. `publish()` recebe os efeitos (`push`, `refresh_install`, `cache_matches`) por parâmetro obrigatório. Só o `main()` constrói os efeitos reais.
- **Toda guarda nova tem um caso sabotado e um mutante morto.** Caso sabotado: a entrada que viola a guarda, com a asserção do motivo exato. Mutante: desligue a guarda no código, rode o teste nomeado na tabela da tarefa, veja-o falhar, restaure. O relatório da tarefa lista cada par mutante → teste que morreu. Teste que não falha com o mutante se corrige antes do commit.
- Texto de sabotagem (e-mail, caminho com usuário, forma de segredo, nome inventado) se monta em tempo de execução no teste, como o canário de `tests/test_private_names.py`. Literal no arquivo faria a camada 1 reprovar o próprio ramo (Tarefa 13).
- Leia o `rc` de cada comando sem pipe: saída para arquivo, `echo "rc=$?"`, depois leia o arquivo.
- Texto com barra invertida (regex, caminho Windows) entra por `Write` ou `Edit`, nunca por heredoc do shell.
- Contratos em português, como o resto dos dois plugins. A `description` do agente e a seção do README em inglês, como as vizinhas. Nomes de teste: em inglês nos testes do plugin, em português em `tests/` da raiz, como os existentes.
- Limites da spec, seção 5.10: no máximo 2 retrofits autônomos por skill por sessão e 3 por sessão. Critério da v2, seção 5.9: pelo menos 10 publicados e 14 dias.
- Abreviações: `W=plugins/retrofit-watch/skills/retrofit-watch`, `R=plugins/retrofit-skill`, `Q=plugins/skill-quality-audit/skills`, `<dados>` = `ctx.data_dir`.
- Suítes: `python3 $W/tests/<arquivo>.py` para um arquivo; `python3 -m unittest discover -s $W/tests -p 'test_*.py'` para o plugin; `python3 -m unittest discover -s tests -p 'test_*.py'` para a raiz.

Novas, deste plano:

- **Sem bump de versão.** `plugin.json`, `metadata.version`, `marketplace.json` e a linha do README ficam em 0.4.0 e 0.11.0. O texto novo entra na entrada `[0.4.0]` do `CHANGELOG` que já existe.
- **Nenhum motivo novo.** Toda recusa nova usa um motivo de `GATE_REASONS` que já existe. `OVERRIDABLE` e `ERRORS` não mudam. O `auto-dry` continua a última guarda de `GUARDS`.
- A regra do par vale também para guarda **mudada** e para leitura que passa a falhar fechada.
- Teste que sabota o que a porta roda escreve a sabotagem num commit ou no `origin` da fixture. Depois da Tarefa 10, um arquivo fora do commit não chega às guardas.
- As decisões que valem não se reabrem: O1 a O9, D1 a D25 e as rulings do ledger do plano anterior.

## Decisões deste plano

| # | Decisão | Por quê |
|---|---|---|
| C1 | Item 1: a porta e o `seal` rodam o que é da loja de uma cópia do commit, tirada com `git archive <sha>`. Não basta `PYTHONPYCACHEPREFIX`. | O prefixo só fecha o bytecode. Um `.py` ignorado por `.git/info/exclude` ou por um `.gitignore` do plugin ainda trocaria um módulo do portão ou um teste. A cópia do commit não tem arquivo ignorado nenhum. Medido: na cópia de `1313ba5`, fora de um repo git, a suíte da raiz dá 154 OK (3 pulados), o `validate-versions.py` dá rc 0, e as 6 pastas de teste dos outros plugins dão OK. |
| C2 | Item 1: quem escreve dentro de `.git/` (`config`, hooks, `info/attributes`) fica fora. | Quem escreve ali já controla o git da porta. Não é a classe do arquivo ignorado. |
| C3 | Item 10: o HEAD que mudou durante as guardas segura com `arvore-suja`, e não com um motivo novo. | O sentido é o mesmo: o worktree não ficou parado. Um motivo novo mudaria a tabela da referência, o README e o CHANGELOG sem ganho. |
| C4 | Item 12: arquivo que as camadas não leem segura com `escopo`, não substituível. | "O que um retrofit pode tocar" já é o `escopo`. Uma lição é texto. A saída é o `/retrofit-skill` manual. |
| C5 | Item 12: a guarda recusa qualquer mudança num `.gitattributes`, e não só `filter=`. | Uma lição nunca precisa de atributo. A recusa também fecha `export-ignore` e `export-subst`, que mudariam a cópia da C1. |
| C6 | Item 4: a guarda recusa zero testes. Não compara o número com o do `origin/main`. | Comparar pede rodar as suítes duas vezes, e a guarda já leva minutos. Tirar a pasta de testes já é recusado. Tirar parte dos testes fica com o revisor (O8). |
| C7 | Item 14: o fecho é uma forma do verbo que já existe, `discard <id> --retro`, e não um verbo novo. | A spec 5.11 dá ao dono dois atos: liberar e descartar. Fechar a retro inteira é descartar. |
| C8 | Item 8: fonte da colheita que existe e não lê é `StoreError`. Fonte ausente continua sem erro. | A camada 1 "limpa" com menos nomes é o anti-objetivo 1. Um aviso contado na porta ninguém lê. Os testes de hoje fixam que raiz ausente e `private_sources` ausente não são erro. |
| C9 | Item 9: o cache negativo vale 24 h por sha. | Sem prazo, um estouro por carga passageira calaria o critério até o `origin/main` andar. |
| C10 | Item 7: a conferência do `id` mora em três leitores novos de `rw_auto`, e todo chamador que lê da pasta da retro os usa. | O defeito está na triagem, mas a porta lê os mesmos três arquivos. |

## Itens do escopo

| Item | Reproduz? | Tarefa |
|---|---|---|
| 1 (CR1) | Sim. Medido: um `.pyc` de hash não conferido em `__pycache__/` troca o `candidatos` do `check-private-names.py` (5 candidatos viram 0). | 10 |
| 2 (CR2) | Sim. `rw_gate.py:54` só casa `co-authored-by`. | 11 |
| 3 (CR3) | Sim. `references/modo-autonomo.md:201` e `:205` dizem o que a re-revisão cita. | 13 |
| 4 (CR4) | Sim. `rw_gate.py:502-506` lê só o rc. Medido no Python 3.12: zero testes dá rc 5. O rc 0 do 3.11 vem do relatório; não há 3.11 nesta máquina. | 11 |
| 5 (CR5) | Sim. `rw_auto.py:83-86`: `except OSError: return []`. | 2 |
| 6 (CR6) | Sim. `rw_auto.py:106-107` e `:633-636` gravam `json + "\n"` sem olhar o fim do arquivo. | 2 |
| 7 (CR7) | Sim. `rw_auto.py:600-606` não compara `id`. Os leitores da porta também não. | 3 |
| 8 (CR8) | Sim. `rw_store.py:196-230`. Medido: `git remote get-url origin` sem remoto dá rc 2, e `git config --get` de chave ausente dá rc 1. Os outros rc hoje viram "sem nome". | 5 |
| 9 (CR9) | Sim. `rw_store.py`, `criterion`: o `StoreError` do estouro sobe antes do `_write_json`. | 6 |
| 10 | Sim. `rw_gate.py:923`: o `_plan` lê o HEAD depois de todas as guardas. | 8 |
| 11 (FR Minor 3) | Sim. `rw_gate.py:113`, `:750` e `:969` usam `nosystem=True`. O `prepare` (`rw_store.py:365`) não usa. | 7 |
| 12 (FR Minor 4) | Sim. Nenhuma guarda lê o conteúdo do blob. As duas camadas decodificam com `replace`. | 9 |
| 13 (FR Minor 5) | Sim, e é mais largo que o relatório diz. `rw_gate.py:249` compara `"<termo>"` com o `detalhe` letra por letra. A camada 1 imprime o trecho em minúsculas e com `ascii()`. Um nome com maiúscula também nunca fica "citado". | 12 |
| 14 (FR Minor 6) | Sim. O `discard` exige linha em aberto. O `hold_item` chama a triagem, que exige o `veredito.json` válido. | 4 |
| 15 (CR18) | **Não, pela CLI. Sai do plano.** Medido: com a pasta de dados ausente, `retrofit_watch.py harvest` sai rc 2 pela `data_dir_problem` de `retrofit_watch.py`, com a mensagem que manda definir a pasta, antes de chegar ao `write_harvest`. Essa recusa é deliberada. O `FileNotFoundError` só aparece na chamada direta da função. O `seal` passa pela mesma recusa. | — |
| 16a (F10 sem sensor) | Sim. Nenhum teste lê as duas frases. | 13 |
| 16b (`_show`) | Sim. `rw_gate.py:276-279` devolve None para qualquer rc ≠ 0. | 11 |

Nenhum LOW a mais do `CR` entra. O 19 foi medido: o git do Windows (2.56) aceita `GIT_CONFIG_GLOBAL` apontado para o dispositivo nulo.

## Formatos que mudam

Nenhum motivo entra nos conjuntos da tabela *Formatos e motivos* do plano anterior. Mudam duas linhas de arquivo:

| Arquivo | Quem grava | O que muda |
|---|---|---|
| linha de `autonomo.jsonl` | o `discard --retro` | Um terceiro formato de `item`: `<id>#retro`, com `lote: null`, `plugin: null` e `licoes: []`. Fecha uma retro cujo `licoes.json` não se lê. Tem `#`, então não conta no teto. |
| `criterio.json` | `criterion` | Uma segunda forma, a do estouro: `{"sha", "estouro"}`, com o instante em segundos. A forma de hoje fica igual. |

## Review Focus

1. **O worktree com `__pycache__/` do próprio executor.** É o caso normal: o executor roda os testes antes do selo. O dono espera que a porta passe e que o bytecode do disco não entre em nada. Teste na Tarefa 10.
2. **Uma pasta sob `harvest_roots` que some durante a colheita.** Um clone apagado no meio da varredura não pode virar `StoreError`: só o que existe e não lê. Teste na Tarefa 5.
3. **Um arquivo de texto com acento no nome, e um arquivo apagado pelo lote.** A guarda de conteúdo tem de deixar os dois passar e não pode estourar no nome. Teste na Tarefa 9.
4. **A pasta de dados com espaço e acento no caminho.** A cópia do commit nasce lá. O dono do Windows espera que a porta rode. Teste na Tarefa 10.
5. **O `discard --retro` na retro que a sessão ainda tem aberta.** O dono espera que o hook volte a contar no próximo Stop, sem esperar as 6 h. Teste na Tarefa 4.

---

### Task 1: Conferir a base

**Files:** nenhum. Não há commit.

- [ ] **Step 1:** `git status --short` imprime nada, e `git rev-parse --short HEAD` imprime `1313ba5`. Outro resultado para o plano.
- [ ] **Step 2:** Rode as linhas de base e anote os números no relatório.

| Comando | Esperado em 2026-11-24 |
|---|---|
| `python3 -m unittest discover -s $W/tests -p 'test_*.py'` | `Ran 333 tests`, `OK` |
| `python3 $R/tests/test_modo_autonomo.py` | `Ran 9 tests`, `OK` |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | `Ran 154 tests`, `OK (skipped=3)` |
| `python3 scripts/validate-versions.py` | rc 0, `All checks passed.` |
| `python3 scripts/check-private-names.py` | rc 0 |

---

### Task 2: O registro falha fechado e não cola linha (itens 5 e 6)

**Files:**
- Modify: `$W/scripts/rw_auto.py:78-110` (`read_registry`, `append_registry`) e `:626-637` (`_append_new`)
- Test: `$W/tests/test_auto_mode.py`

**Interfaces:**
- Produces:
  - `read_registry(ctx) -> list[dict]`: arquivo ausente dá `[]`. Qualquer outro `OSError` levanta `Malformed`, com o caminho e "registro ilegivel" na mensagem.
  - `_append(ctx, entries) -> None`: a única função que escreve no registro. Sob a trava, se o arquivo existe, não está vazio e o último byte não é `\n`, ela grava `\n` antes das linhas. `append_registry` e `_append_new` a usam.

- [ ] **Step 1: Escreva os testes que falham.**

| Teste | Entrada sabotada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_unreadable_registry_is_malformed_not_empty` | o registro é uma pasta; em outro subteste, `Path.read_bytes` levanta `PermissionError` só para o caminho do registro | `read_registry` levanta `rw_auto.Malformed` com "registro ilegivel"; sem o arquivo, devolve `[]` | voltar ao `except OSError: return []` |
| `test_unreadable_registry_keeps_the_hook_manual` | config `auto`, uma entrada pronta, o registro ilegível | a saída do `stop` é a do modo manual (sem `[modo autônomo`), e o `errors.log` ganha uma linha com `Malformed` | o mesmo: com o mutante, o hook abre um pedido autônomo |
| `test_line_after_a_torn_line_is_kept` | o registro termina em `{"item": "x", "resul`, sem `\n`; depois, um `append_registry` e um `triage` que grava linha | `read_registry` devolve as duas linhas novas; a linha cortada é pulada | tirar o `\n` de conserto de `_append` |

- [ ] **Step 2:** `python3 $W/tests/test_auto_mode.py`. Esperado: os três falham.
- [ ] **Step 3:** Implemente. `flow_finished` já devolve False num `Malformed`: não mude.
- [ ] **Step 4:** O arquivo de teste e a suíte do plugin. Esperado: `OK`. O `test_unwritable_registry_never_raises` de `test_auto_gate.py` continua a dar linha `erro`, `interno`.
- [ ] **Step 5:** Mate os dois mutantes da tabela, um por vez.
- [ ] **Step 6:** `python3 scripts/check-private-names.py` (rc 0) e commit: `fix(retrofit-watch): o registro ilegivel nao vira registro vazio, e a linha nova nao cola na cortada`.

---

### Task 3: O `id` dos arquivos da retro (item 7)

**Files:**
- Modify: `$W/scripts/rw_auto.py` (seção *formatos* e `_plan`), `$W/scripts/rw_gate.py:138-139`, `:320-321`, `:333-336`, `:716`, `:882`, `:920`, `$W/scripts/rw_store.py:449`
- Test: `$W/tests/test_auto_formats.py`, `$W/tests/test_auto_gate.py`

**Interfaces:**
- Produces, em `rw_auto`:
  - `retro_pedido(ctx, rid) -> dict`, `retro_licoes(ctx, rid) -> dict[str, dict]`, `retro_veredito(ctx, rid) -> dict[str, dict]`: leem o arquivo de `retro_dir(ctx, rid)` com o `load_*` de hoje e levantam `Malformed` quando o `id` do arquivo difere de `rid`. A mensagem traz o caminho e "e de outra retro".
  - Os `load_*` ficam como estão: o `_started` e os testes os usam.
- Todo chamador que hoje faz `load_x(retro_dir(ctx, rid) / "x.json")` passa a usar o leitor novo. Os sete lugares estão em *Files*.

- [ ] **Step 1: Escreva os testes que falham.** Cada caso grava uma retro válida e troca só o `id` de um arquivo pelo de outra retro válida.

| Teste | Entrada sabotada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_triage_refuses_a_file_of_another_retro` | um subteste por arquivo: `pedido.json`, `licoes.json`, `veredito.json` | `triage` levanta `Malformed` com "outra retro"; nenhuma linha no registro; pela CLI, rc 2 | tirar a comparação de um dos três leitores (cada subteste mata o seu) |
| `test_gate_refuses_a_verdict_of_another_retro` | retrofit limpo; o `veredito.json` copiado de outra retro, com todos os pareceres `procede` | `refuse` dá `sem-veredito` | `_veredito` da porta de volta ao `load_veredito` |
| `test_gate_stops_on_lessons_of_another_retro` | retrofit limpo; o `licoes.json` com outro `id` | `publish` dá linha `erro`, `interno`, rc 3, com "outra retro" no `detalhe`; o `origin/main` não muda | `_lessons` da porta de volta ao `load_licoes` |

- [ ] **Step 2:** Rode os dois arquivos. Esperado: falham.
- [ ] **Step 3:** Implemente os três leitores e troque os chamadores.
- [ ] **Step 4:** Os dois arquivos e a suíte do plugin. Esperado: `OK`.
- [ ] **Step 5:** Mate os mutantes.
- [ ] **Step 6:** Commit: `fix(retrofit-watch): pedido, licoes e veredito de outra retro sao recusados pelo id`.

---

### Task 4: `discard <id> --retro` fecha a retro sem fim (item 14)

**Files:**
- Modify: `$W/scripts/rw_auto.py` (`flow_finished`, verbos do registro), `$W/scripts/retrofit_watch.py:988-1043` (`CLI_USAGE` e `cli`), `$W/references/modo-autonomo.md` (seção *O aviso de startup*, o item "sem registro de fim")
- Test: `$W/tests/test_auto_notice.py`, `$W/tests/test_auto_formats.py`, `$W/tests/test_auto_docs.py`

**Interfaces:**
- Produces, em `rw_auto`:
  - `RETRO_ITEM = "{rid}#retro"`.
  - `discard_retro(ctx, rid, motivo="descartado-pelo-dono") -> list[dict]`: as linhas gravadas. `Malformed` com a pasta da retro ausente, com o motivo fora de `OWNER_REASONS` e quando não há nada a fechar. Ele grava uma linha `descartado` para cada coisa da retro sem registro de fim, e só para elas:
    1. cada lote com `retrofit.json` e sem linha própria: item `<id>/<lote>`, com o `lote`, o plugin tirado do nome do lote e as `licoes` do `retrofit.json` (`[]` se ele não se lê);
    2. com o `licoes.json` válido, cada lição sem linha: item `<id>/<plugin>#<n>`, `licoes: [n]`;
    3. com o `licoes.json` presente e inválido: uma linha só, item `RETRO_ITEM`.
    A `sessao` vem do `pedido.json`; com ele ilegível, `null`.
  - `flow_finished` devolve True quando o registro tem uma linha da retro com o item `RETRO_ITEM`, antes de ler o `licoes.json`.
- CLI: `discard <id> --retro [--motivo M]`. `CLI_USAGE["discard"]` passa a `("discard <id> <item>|--retro [--motivo M]", 2)`. rc 0 com as linhas em JSON ASCII; rc 2 no `Malformed`.
- O item em aberto com linha `segurado` ou `erro` não muda: continua a sair pelo `discard <id> <item>`.

- [ ] **Step 1: Escreva os testes que falham.**

| Teste | Entrada sabotada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_discard_retro_closes_lessons_without_a_verdict` | retro de 2 lições, sem `veredito.json`, com 2 h; uma lição já com linha | antes, `orphans` tem a retro; depois, uma linha `descartado` só para a lição sem linha, `orphans == []`, `held == []` | gravar linha também para a lição que já tem |
| `test_discard_retro_closes_an_unreadable_lessons_file` | `licoes.json` com `{` | uma linha com o item `<id>#retro`; `orphans == []`; `used` da sessão igual ao de antes | tirar a leitura do `RETRO_ITEM` de `flow_finished` (a retro continua órfã); gravar o item sem `#` (o `used` sobe) |
| `test_discard_retro_closes_a_lote_without_a_line` | lote preparado, sem selo e sem linha | uma linha `descartado` com o item `<id>/<lote>` e o `lote`; `orphans == []` | pular os lotes |
| `test_discard_retro_refuses_when_nothing_is_open` | retro com toda lição já com linha; id sem pasta; motivo `teto` | `Malformed` nos três; nenhuma linha nova | tirar a recusa do "nada a fechar" |
| `test_discard_retro_reopens_the_hook_count` | o estado da sessão com `auto_open` desta retro; depois, o `discard_retro` | `flow_finished(ctx, pedido)` é True, e o `stop` seguinte tira o `auto_open` do estado | o mesmo de `flow_finished` |
| `test_cli_discard_retro` | `discard <id> --retro --motivo resolvido-manual`; depois, de novo | rc 0 e JSON ASCII; na segunda, rc 2 | — |
| `test_reference_names_the_retro_discard` (em `test_auto_docs.py`) | — | a seção *O aviso de startup* cita `retrofit_watch.py discard <id> --retro` e a palavra do dono | apagar a frase da referência |

- [ ] **Step 2:** Rode os três arquivos. Esperado: falham.
- [ ] **Step 3:** Implemente. Na referência, o item "sem registro de fim" ganha a frase: quando o fluxo não tem conserto, por exemplo o revisor falha de novo, o fecho é `retrofit_watch.py discard <id> --retro`, só com a palavra do dono; o ramo e o worktree ficam.
- [ ] **Step 4:** Os três arquivos e a suíte do plugin. Esperado: `OK`. O `--help` lista a forma nova (`test_help_lists_every_subcommand`).
- [ ] **Step 5:** Mate os mutantes.
- [ ] **Step 6:** Commit: `fix(retrofit-watch): o discard --retro fecha a retro sem registro de fim`.

---

### Task 5: A colheita não encolhe em silêncio (item 8)

**Files:**
- Modify: `$W/scripts/rw_store.py:196-230` (`_origin_of`, `_repos`, `_git_config`, `_source_lines`)
- Test: `$W/tests/test_auto_store.py`

**Interfaces:**
- Produces (as assinaturas ficam; muda o erro):
  - `_repos(root)`: `FileNotFoundError` e `NotADirectoryError` numa pasta continuam a ser "nada ali" (a raiz ausente, a raiz que é arquivo, a pasta que sumiu no meio). Outro `OSError` é `StoreError` com a pasta.
  - `_source_lines(path)`: arquivo ausente dá `[]`. Outro `OSError` é `StoreError` com o caminho.
  - `_origin_of(repo, env)`: rc 0 dá os termos; rc 2 (sem remoto `origin`) dá `[]`; outro rc é `StoreError`.
  - `_git_config(key, env, cwd)`: rc 0 dá o valor; rc 1 (chave ausente) dá `""`; outro rc é `StoreError`.
- O `cwd` do pedido que não é repo continua sem erro (O5 e `test_harvest_includes_the_session_project`).
- Na porta, o `StoreError` da colheita vira `interno` pelo `refuse`, como os outros.

- [ ] **Step 1: Escreva os testes que falham.**

| Teste | Entrada sabotada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_harvest_fails_closed_on_an_unreadable_source` | um subteste por fonte: `private_sources` aponta uma pasta; `Path.iterdir` levanta `PermissionError` numa pasta sob a raiz; o git do `remote get-url` sai 128; o git do `config --get user.name` sai 128 (os dois por `mock` em `rw_store.run`) | `harvest` levanta `StoreError` que nomeia a fonte | em cada função, voltar a engolir o erro (cada subteste mata o seu) |
| `test_harvest_skips_what_is_absent` | repo sem `origin`; `user.email` ausente; `private_sources` ausente; `Path.iterdir` levanta `FileNotFoundError` numa pasta filha | sem exceção; os outros nomes estão na colheita | tratar todo rc ≠ 0 ou todo `OSError` como `StoreError` |
| `test_gate_reports_a_shrunk_harvest_as_internal` | retrofit limpo; `private_sources` aponta uma pasta | `refuse` dá `interno`, com o caminho no `detalhe` | — |

- [ ] **Step 2:** `python3 $W/tests/test_auto_store.py`. Esperado: os novos falham.
- [ ] **Step 3:** Implemente.
- [ ] **Step 4:** O arquivo e a suíte do plugin. `test_harvest_respects_depth_and_survives_bad_roots` e `test_harvest_collects_every_source` continuam verdes sem mudança.
- [ ] **Step 5:** Mate os mutantes.
- [ ] **Step 6:** Commit: `fix(retrofit-watch): a colheita falha quando uma fonte existe e nao le`.

---

### Task 6: O critério da v2 com cache negativo (item 9)

**Files:**
- Modify: `$W/scripts/rw_store.py` (seção *o critério da v2*: `_startup_git`, `criterion`)
- Test: `$W/tests/test_auto_notice.py`

**Interfaces:**
- Produces:
  - `class StartupTimeout(StoreError)`: o `_startup_git` a levanta quando o rc é 124.
  - `CRITERION_RETRY = 86400`.
  - `criterion(ctx, now=None)`: com `criterio.json` igual a `{"sha": <o origin/main>, "estouro": <ts>}` e `now - estouro < CRITERION_RETRY`, devolve None sem chamar `git log`. Num `StartupTimeout` do `_autonomous` ou do `_leaks`, grava essa forma com o `now` e deixa a exceção subir. O estouro do `rev-parse` não grava nada: ainda não há sha.
  - `criterion_notice` já devolve None com `criterion` None.

- [ ] **Step 1: Escreva o teste que falha.** `test_criterion_timeout_is_cached_by_sha`: `run_bytes` embrulhado devolve `(124, b"")` para o comando com `log`.

| Passo do teste | Asserção | Mutante que ele mata |
|---|---|---|
| primeira chamada | levanta `StartupTimeout`; `criterio.json` tem as chaves `sha` e `estouro` | — |
| segunda chamada, mesmo sha, 60 s depois | devolve None; nenhuma chamada com `log` | não gravar o cache negativo |
| chamada com `now` 24 h e 1 s depois | uma chamada com `log` | ignorar o prazo |
| o `origin/main` anda, sem estouro | devolve o dicionário do critério | ignorar o sha |
| pelo `pending`, com o cache negativo válido | a linha do aviso sai sem o segmento do critério, e o `errors.log` não cresce | — |

- [ ] **Step 2:** Rode. Esperado: falha.
- [ ] **Step 3:** Implemente. O `_cached` não muda: a forma do estouro tem outras chaves e continua a não ser cache positivo.
- [ ] **Step 4:** O arquivo e a suíte do plugin. `test_criterion_is_cached_by_origin_main_sha` continua verde.
- [ ] **Step 5:** Mate os três mutantes.
- [ ] **Step 6:** Commit: `fix(retrofit-watch): o estouro do criterio fica em cache por sha, por 24 h`.

---

### Task 7: O fetch e o push leem a config de sistema do git (item 11)

**Files:**
- Modify: `$W/scripts/rw_store.py` (junto do `network_env`, e o `prepare`), `$W/scripts/rw_gate.py:203-206` (`_g_fetch`), `:745-755` (`Effects.push`), `:969-972` (o fetch do `_publish`)
- Test: `$W/tests/test_auto_gate.py`, `$W/tests/test_auto_store.py`

**Interfaces:**
- Produces: `rw_store.remote_env(ctx, worktree) -> dict`, igual a `network_env(git_env(home=ctx.home), worktree)`. É o único ambiente de um git que fala com o `origin`. O `prepare`, a guarda do fetch, o fetch do `_publish` e o `Effects.push` o usam.
- O `p.env` das outras guardas continua com `nosystem=True`, e o `neutral` não muda.

- [ ] **Step 1: Escreva os testes que falham.**

| Teste | Entrada sabotada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_network_git_reads_the_system_config` | um `publish` limpo, com `rw_store.run` embrulhado | em toda chamada com `fetch` ou `push`, `GIT_CONFIG_NOSYSTEM` não está no `env`, `GIT_TERMINAL_PROMPT` é `0` e o HOME é o do Context; na chamada com `rebase`, `GIT_CONFIG_NOSYSTEM` é `1` | pôr `nosystem=True` em `remote_env` |
| `test_prepare_and_gate_share_the_remote_env` (em `test_auto_store.py`) | o `prepare`, com `rw_store.run` embrulhado | o `env` do fetch é igual a `remote_env(ctx, store)` | o `prepare` montar o ambiente por conta própria |

- [ ] **Step 2:** Rode. Esperado: falham.
- [ ] **Step 3:** Implemente.
- [ ] **Step 4:** Os dois arquivos e a suíte do plugin. `test_network_git_runs_in_batch_mode`, `test_network_env_keeps_the_owner_ssh` e `test_prepare_fetch_runs_in_batch_mode` continuam verdes.
- [ ] **Step 5:** Mate os mutantes.
- [ ] **Step 6:** Commit: `fix(retrofit-watch): o fetch e o push da porta leem a config de sistema do git`.

---

### Task 8: A porta publica o HEAD que ela conferiu (item 10)

**Files:**
- Modify: `$W/scripts/rw_gate.py`: `_Porta`, `_g_rebase`, `GUARDS`, `refuse`, `_mark_approved`, `_plan` (o da porta, `:916-926`), `_publish`
- Test: `$W/tests/test_auto_gate.py`

**Interfaces:**
- Produces:
  - `_Porta.head`: None até o rebase; a guarda do rebase, quando passa, grava o sha de `rev-parse HEAD`.
  - `_g_still(p)`: devolve `("arvore-suja", "o HEAD mudou durante as guardas: <a> -> <b>")` quando `rev-parse HEAD` difere de `p.head`. Entra em `GUARDS` como `("arvore-suja", _g_still)`, logo antes de `("auto-dry", _g_dry)`.
  - `_check(ctx, rid, lote, notes) -> tuple`: `(recusa ou None, head)`. `refuse(ctx, rid, lote, notes)` continua com a assinatura e o retorno de hoje, e devolve o primeiro elemento.
  - `_plan(ctx, rid, lote, retrofit, worktree, aprovado, detalhe, commit)`: o `commit` da linha vem do parâmetro. No ramo "já publicado", quem chama passa `_head(worktree)`.
  - `_mark_approved(ctx, worktree, env, reviewed) -> str`: lê a mensagem de `reviewed`, nunca do HEAD. Depois da emenda, confere que a árvore do HEAD é a de `reviewed` e que o pai do HEAD é o pai de `reviewed`. Outra coisa é `StoreError`. Devolve o sha novo.
  - `_publish` usa `_check`, e o push sobe o `head` dele, ou o sha que o `_mark_approved` devolveu.
- O que este plano não fecha: um HEAD que sai e volta ao mesmo sha durante as guardas. O sha é o mesmo, e o que sobe é ele.

- [ ] **Step 1: Escreva os testes que falham.** O commit "durante as guardas" entra por um `mock.patch.object(rg, "GUARDS", ...)` com uma guarda a mais, antes de `_g_still`, que emenda o commit do worktree e devolve None. O commit "depois das guardas" entra por um embrulho de `rg._check`.

| Teste | Entrada sabotada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_commit_made_during_the_guards_is_held` | a emenda acrescenta uma linha ao `SKILL.md` do plugin | `publish` dá rc 1, `segurado`, `arvore-suja`, com "HEAD mudou" no `detalhe`; o `origin/main` não muda; `fx.calls == []` | tirar `_g_still` de `GUARDS` |
| `test_plan_records_the_checked_sha` | sem aprovação; depois do `_check`, um commit novo no worktree | rc 0; `line["commit"]` e o `origin/main` são o sha conferido | o `_plan` voltar a ler o `_head(worktree)` |
| `test_approval_amends_the_reviewed_message` | lote aprovado; depois do `_check`, a mensagem do HEAD ganha uma linha com um nome inventado | a mensagem no `origin/main` não tem o nome e tem o trailer `autonomous-approved` | ler a mensagem do HEAD no `_mark_approved` |
| `test_approval_refuses_a_commit_on_top` | lote aprovado; depois do `_check`, `commit --allow-empty` | linha `erro`, `interno`, rc 3; o `origin/main` não muda; o ramo volta ao commit revisado | tirar a conferência do pai |

- [ ] **Step 2:** Rode. Esperado: falham.
- [ ] **Step 3:** Implemente.
- [ ] **Step 4:** O arquivo e a suíte do plugin. `test_push_sends_the_checked_sha_not_the_head`, `test_amend_that_changes_the_tree_or_drops_the_marker_is_an_error` e `test_readme_names_the_modes_and_the_held_verb` (o `auto-dry` por último) continuam verdes.
- [ ] **Step 5:** Mate os quatro mutantes.
- [ ] **Step 6:** Commit: `fix(retrofit-watch): a porta segura o lote quando o HEAD muda durante as guardas`.

---

### Task 9: O arquivo que as camadas não leem (item 12)

**Files:**
- Modify: `$W/scripts/rw_gate.py` (guarda nova depois de `_g_scope`; `GUARDS`)
- Test: `$W/tests/test_auto_gate.py`

**Interfaces:**
- Consumes: `p.head` (Tarefa 8), `p.names()`.
- Produces: `_g_opaque(p)`, em `GUARDS` como `("escopo", _g_opaque)`, logo depois de `("escopo", _g_scope)`. Ela devolve `("escopo", <detalhe com o caminho>)` quando:
  1. um caminho que o ramo muda, acrescenta ou tira tem o nome `.gitattributes`, em qualquer pasta;
  2. um caminho presente no `p.head` não é arquivo regular: o modo do `ls-tree` fora de `100644` e `100755` (link simbólico, submódulo);
  3. o blob de um caminho presente no `p.head` tem um byte NUL;
  4. esse blob não decodifica em UTF-8 estrito.
  Caminho que o ramo só tira não tem blob: fora a regra 1, a guarda o pula. O blob se lê em bytes, pelo `_git_bytes`, no ambiente neutro.

- [ ] **Step 1: Escreva os testes que falham.** `test_content_the_layers_cannot_read_is_held`, um subteste por linha. Os bytes se montam em tempo de execução. O nome colhido vem de um repo sob `harvest_roots`.

| Subteste | Entrada sabotada (no commit do lote) | Asserção | Mutante que ele mata |
|---|---|---|---|
| NUL | arquivo novo do plugin, UTF-8 válido com um `\x00` no meio | `escopo`, com o caminho | tirar a regra 3 |
| UTF-16 | arquivo novo em UTF-16 com BOM, com o nome colhido dentro | `escopo`, com o caminho | tirar as regras 3 e 4 juntas: o `refuse` passa pela camada 1 sem `nome-privado`, e o subteste morre |
| Latin-1 | arquivo novo com uma palavra acentuada em Latin-1 | `escopo` | tirar a regra 4 |
| atributo | `plugins/demo/.gitattributes` novo, com `*.md filter=x` | `escopo`, com o caminho | tirar a regra 1 |
| link | um link simbólico novo no plugin (sem permissão de link, o subteste se pula) | `escopo` | tirar a regra 2 |

`test_plain_text_passes_the_content_guard`: um arquivo novo com acento no nome e no conteúdo, em UTF-8, e um arquivo do plugin apagado pelo lote. Asserção: `_g_opaque` devolve None para os dois, e o `refuse` não dá `escopo`.

- [ ] **Step 2:** Rode. Esperado: falham.
- [ ] **Step 3:** Implemente.
- [ ] **Step 4:** O arquivo e a suíte do plugin. `test_diff_keeps_accented_names_for_the_audit_gate` continua verde.
- [ ] **Step 5:** Mate os mutantes.
- [ ] **Step 6:** Commit: `fix(retrofit-watch): a porta segura arquivo binario, fora do UTF-8, link e mudanca de .gitattributes`.

---

### Task 10: A porta roda a loja de uma cópia do commit (item 1)

**Files:**
- Modify: `$W/scripts/rw_store.py` (`_gate`, `layer1`, `new_terms`, `seal`, função nova), `$W/scripts/rw_gate.py` (`_Porta`, `refuse`/`_check`, `_g_layer1`, `_g_terms`, `_g_tests`, `_g_versions`, `_audit_json`, `_extract_base`, `_g_audit`)
- Test: `$W/tests/test_auto_gate.py`, `$W/tests/test_auto_store.py`

**Interfaces:**
- Consumes: `p.head` (Tarefa 8). A guarda `_g_opaque` (Tarefa 9) roda antes da primeira cópia: os atributos da árvore copiada são os do `origin/main`.
- Produces, em `rw_store`:
  - `clean_tree(ctx, worktree, ref)`: gerenciador de contexto. Entrega um `Path` com a árvore de `ref`, tirada com `git archive --format=tar <ref>` no ambiente neutro e extraída com `filter="data"` numa pasta temporária nova sob `<dados>`. A pasta sai no fim. Falha do git ou da extração é `StoreError` ("arvore limpa: …"). O `TypeError` do Python sem o filtro sobe, como no `_extract_base` (D25).
  - `_gate(tools, worktree, *args)`: roda `tools / GATE` com `--repo worktree`, com `PYTHONDONTWRITEBYTECODE=1` no ambiente neutro.
  - `layer1(ctx, rid, worktree, tools)` e `new_terms(worktree, tools)`: `tools` é obrigatório.
  - `seal` abre um `clean_tree` do commit que ele sela e passa a pasta aos dois.
- Produces, em `rw_gate`:
  - `_Porta.tree() -> Path`: a cópia de `p.head`, criada na primeira chamada e reusada. `_check` a fecha num `finally`, com ou sem recusa.
  - As guardas da camada 1 e dos termos passam `p.tree()` como `tools`. As guardas dos testes, do `validate-versions.py` e da auditoria rodam com `cwd=p.tree()` e leem dele os scripts, a lista de `SKILL.md`, o texto de cada `SKILL.md` e a presença do auditor. O que é pergunta ao git (`p.diff`, `p.names`, `ls-tree`) continua no worktree.
- O `cache_matches` continua a ler o worktree: ele roda depois do push e já pula o bytecode.

- [ ] **Step 1: Escreva os testes que falham.** Cada caso planta um arquivo **ignorado** no worktree e confere antes que `git status --porcelain --untracked-files=all` imprime nada. O que não é `__pycache__/` fica ignorado por uma linha em `info/exclude` do repo.

| Teste | Entrada sabotada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_planted_bytecode_does_not_blind_layer1` | o commit traz um nome colhido; em `scripts/__pycache__/` do worktree, um `.pyc` do `check-private-names.py` com o `candidatos` vazio, compilado no teste com `py_compile` e `PycInvalidationMode.UNCHECKED_HASH`, no caminho de `importlib.util.cache_from_source` | `refuse` dá `nome-privado` | `_g_layer1` passar o worktree como `tools` |
| `test_planted_module_does_not_pass_the_versions_guard` | o commit deixa a versão do `marketplace.json` para trás; `scripts/json.py` ignorado com `raise SystemExit(0)` | `refuse` dá `validate-versions` | `_g_versions` rodar do worktree |
| `test_planted_module_does_not_pass_the_audit` | o commit traz o campo a mais do `extra_field`; ao lado do auditor, um `json.py` ignorado que imprime o JSON vazio do auditor e sai 0 | `refuse` dá `auditoria` | `_audit_json` rodar do worktree |
| `test_tests_come_from_the_commit` | retrofit limpo; um `test_ignorado.py` que falha, ignorado, na pasta de testes do plugin | `refuse` devolve None | `_g_tests` rodar do worktree (dá `testes`) |
| `test_gate_passes_with_the_executor_bytecode` | retrofit limpo; a suíte do plugin rodada no worktree sem `PYTHONDONTWRITEBYTECODE` | há `__pycache__/` no worktree; `refuse` devolve None; nenhuma pasta `.porta-*` sobra em `<dados>` | não fechar a cópia no `finally` |
| `test_clean_tree_is_the_commit_and_leaves_nothing` (em `test_auto_store.py`) | a pasta de dados com espaço e acento no nome; um arquivo solto e não rastreado no worktree | a cópia tem os arquivos do commit e não tem o solto; depois do `with`, a pasta não existe; com um `ref` que não existe, `StoreError` | — |
| `test_seal_runs_the_gate_from_the_commit` (em `test_auto_store.py`) | o `.pyc` do primeiro caso, antes do `seal` | `seal` devolve o achado em `camada1` | o `seal` passar o worktree como `tools` |

- [ ] **Step 2:** Rode os dois arquivos. Esperado: os novos falham.
- [ ] **Step 3:** Implemente. O `_extract_base` e o `clean_tree` dividem a extração do tar.
- [ ] **Step 4:** Acerte os testes que sabotam pelo disco. O `gate_stub` de `test_auto_store.py` passa a montar o portão falso numa pasta do teste e a entregá-la como `tools`. Depois, os dois arquivos e a suíte do plugin. `test_clean_retrofit_passes_every_guard` e `test_missing_auditor_refuses` continuam verdes.
- [ ] **Step 5:** Mate os mutantes da tabela, um por vez.
- [ ] **Step 6:** Commit: `fix(retrofit-watch): a porta roda o portao, os testes e a auditoria de uma copia do commit`.

---

### Task 11: Três guardas apertadas (itens 2, 4 e 16b)

**Files:**
- Modify: `$W/scripts/rw_gate.py`: `CO_AUTHOR` e `_g_coauthor` (`:54`, `:261-263`), `_g_tests`, `_show` (`:276-279`)
- Test: `$W/tests/test_auto_gate.py`

**Interfaces:**
- Produces:
  - `GENERATED = re.compile(r"(?i)generated with[^\n]*claude")`. `_g_coauthor` devolve `("coautoria", "o commit tem a linha Generated with")` quando ela casa na mensagem inteira (`%B`).
  - `RAN = re.compile(r"(?m)^Ran (\d+) tests? in ")`. Em `_g_tests`, com rc 0, a última ocorrência na saída diz quantos testes rodaram. Sem ocorrência, ou com zero, a guarda devolve `("testes", "<pasta>: nenhum teste rodou")`.
  - `_show(p, ref, path)`: primeiro `ls-tree -z --name-only <ref> -- <path>` pelo `rw_store._git`. A saída vazia dá None. Depois, `show <ref>:<path>` pelo `rw_store._git`. Falha do git é `StoreError`, que o `refuse` grava como `interno`.

- [ ] **Step 1: Escreva os testes que falham.**

| Teste | Entrada sabotada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_generated_with_line_refuses` | a mensagem do commit com a linha de rodapé do Claude Code, montada em tempo de execução, em dois subtestes de caixa | `coautoria`, com "Generated with" no `detalhe`; uma mensagem com "generated with care" passa | tirar o `GENERATED` |
| `test_zero_tests_refuse` | `rw_store.run` embrulhado devolve `(0, "Ran 0 tests in 0.000s\n\nOK\n")` para o `discover` do plugin; em outro subteste, `(0, "")` | `testes`, com "nenhum teste rodou" e a pasta | tirar a leitura do `RAN` |
| `test_emptied_test_file_refuses` | o commit troca o arquivo de teste do plugin por `import unittest` | `testes`, em qualquer versão do Python | — (no 3.12 o rc 5 já segura; o par do mutante é o teste de cima) |
| `test_git_failure_is_not_a_new_plugin` | `rw_store.run` embrulhado devolve rc 128 para o `ls-tree` do `plugin.json` no `origin/main` | `refuse` dá `interno` | `_show` voltar a ler rc ≠ 0 como None (o `refuse` devolve None) |

- [ ] **Step 2:** Rode. Esperado: falham.
- [ ] **Step 3:** Implemente.
- [ ] **Step 4:** O arquivo e a suíte do plugin. `test_new_plugin_passes_the_bump_guard` e `test_plugin_without_tests_passes_with_a_note` continuam verdes.
- [ ] **Step 5:** Mate os três mutantes.
- [ ] **Step 6:** Commit: `fix(retrofit-watch): a porta recusa Generated with, zero testes e falha do git lida como plugin novo`.

---

### Task 12: O termo que o dono ensina conta por forma, não por letra (item 13)

**Files:**
- Modify: `$W/scripts/rw_gate.py:233-258` (`_g_scope`)
- Test: `$W/tests/test_auto_gate.py`

**Interfaces:**
- Produces:
  - `_form(text) -> str`: as palavras de `text.lower()` (sequências de `[^\W_]`), unidas sem separador.
  - `_cited(detail) -> set[str]`: a `_form` de cada trecho entre aspas duplas do `detalhe`, nas duas leituras: como está, e com os escapes `\x`, `\u` e `\U` do `ascii()` desfeitos. Um trecho que não se desfaz conta só como está.
  - Em `_g_scope`, um termo novo da lista de públicos está citado quando a `_form` dele está em `_cited(detail)`. A igualdade é da forma inteira, nunca de um pedaço.

- [ ] **Step 1: Escreva os testes que falham.** Com os verbos reais, como o `teaching` de hoje: `publish`, `--publico-add`, a emenda, `rw_auto.approve` e `publish`.

| Teste | Entrada sabotada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_teaching_a_harvested_name_with_capital_and_accent_publishes` | um repo sob `harvest_roots` com maiúscula e acento no nome, montado em tempo de execução; o commit cita o nome; o dono roda `--publico-add` com o nome como ele o escreve | o primeiro `publish` segura com `nome-privado`; depois do ensino e do `approve`, `publish` dá rc 0, e a lista publicada tem o nome | comparar letra por letra, como hoje (fica `escopo`) |
| `test_a_piece_of_a_cited_name_is_not_cited` | a recusa cita o nome inteiro; a lista ganha só a primeira metade dele | `escopo`, com o termo no `detalhe` | trocar a igualdade por "está contido" |
| `test_list_files_need_owner_approval` (o de hoje) | — | continua verde | tirar a conferência do citado |

- [ ] **Step 2:** Rode. Esperado: o primeiro e o segundo falham.
- [ ] **Step 3:** Implemente.
- [ ] **Step 4:** O arquivo e a suíte do plugin. Os três `test_teaching_the_gate_*` continuam verdes.
- [ ] **Step 5:** Mate os três mutantes.
- [ ] **Step 6:** Commit: `fix(retrofit-watch): o nome que o dono chama de publico conta como citado com maiuscula e acento`.

---

### Task 13: Os textos e os sensores (itens 3 e 16a)

**Files:**
- Modify: `$W/references/modo-autonomo.md` (o passo 6, `:205-206`; a tabela do passo 8), `$W/tests/test_auto_gate.py` (o docstring do módulo conta as guardas)
- Test: `$W/tests/test_auto_docs.py`, `$W/tests/test_auto_gate.py`

**Interfaces:**
- Consumes: os comportamentos das Tarefas 8, 9 e 11.
- Produces, em `test_auto_docs.py`: a constante `MISSING_REVIEW_RULE`, com a frase nova do passo 6.

- [ ] **Step 1: Escreva os testes que falham.**

| Teste | Asserção | O que o mata |
|---|---|---|
| `test_missing_review_runs_the_gate_before_the_owner_pair` | o passo 6, lido pelo `flat`, traz a `MISSING_REVIEW_RULE`; a frase antiga ("o revisor refaz antes a segunda passada") não está mais lá | voltar ao texto antigo |
| `test_approving_a_dry_batch_is_said_to_publish` | a seção do README, pelo `flat`, traz "the owner's `approve` on a batch held by `auto-dry` publishes it for real"; o `CHANGELOG` traz "aprovar um lote segurado por `auto-dry` o publica de verdade"; `"auto-dry"` está em `rw_gate.OVERRIDABLE` | apagar uma das duas frases |
| `test_reason_rows_name_the_new_causes` | na tabela do passo 8: a linha `escopo` cita `.gitattributes` e UTF-8; a `arvore-suja` cita o HEAD que mudou durante as guardas; a `coautoria` cita "Generated with"; a `testes` cita "nenhum teste" | apagar a causa de uma linha |
| `test_missing_review_path_publishes_without_an_early_approve` (em `test_auto_gate.py`) | o caminho do texto novo, com os verbos reais: `sem-anonimato` → a segunda passada com o termo em dúvida → `publish` (`termo-nao-publico`) → `--publico-add` e a emenda → `approve` → `publish` dá rc 0 | — (prende o caminho que a frase manda; nenhum `approve` vem antes do `termo-nao-publico`) |

- [ ] **Step 2:** Rode os dois arquivos. Esperado: os três primeiros falham; o quarto já passa, porque o código da Final-F1 cobre essa ordem.
- [ ] **Step 3:** Escreva os textos.
  - Passo 6, no lugar das linhas `:205-206`: "Com `sem-anonimato`, o revisor refaz a segunda passada e a porta roda (`publish`); se ela segurar por `termo-nao-publico`, vale o par acima."
  - Passo 8: acrescente a causa nova a cada uma das quatro linhas. A coluna "Substituível" não muda.
  - O docstring de `test_auto_gate.py` passa a dizer o número de `len(rg.GUARDS)` depois deste plano.
- [ ] **Step 4:** Os dois arquivos e a suíte do plugin. `test_every_reason_code_is_explained` continua verde: nenhum motivo entrou.
- [ ] **Step 5:** Para cada sensor de texto, apague a frase, veja o teste falhar, restaure.
- [ ] **Step 6:** Commit: `docs(retrofit-watch): o passo do sem-anonimato manda a porta rodar antes do par do dono, com sensores`.

---

### Task 14: Release — os números e as portas da loja

**Files:**
- Modify: `plugins/retrofit-watch/CHANGELOG.md` (a entrada `[0.4.0]`), `README.md` (a seção da `retrofit-watch`, o parágrafo *The gate*)
- Não muda: `plugin.json`, `metadata.version`, `marketplace.json`, a linha de versão do README, `plugins/retrofit-skill/`, `CLAUDE.md`, `docs/codex/compatibility.md`

**Interfaces:**
- Consumes: tudo das Tarefas 2 a 13.

- [ ] **Step 1:** Rode as três suítes com a saída em arquivo e anote os três números.
- [ ] **Step 2:** `plugins/retrofit-watch/CHANGELOG.md`, entrada `[0.4.0]`:
  - o item **Testes** (`:53-57`) troca os números pelos medidos no Step 1. É o único lugar que cita contagem. Medido em `1313ba5`: o README, o `CLAUDE.md` da loja, o `docs/codex/compatibility.md` e o `CHANGELOG` da `retrofit-skill` não citam contagem de testes; neles nada muda;
  - o item **As guardas da porta** ganha, na ordem de `GUARDS`: o arquivo que as camadas não leem (`escopo`), a linha "Generated with" (`coautoria`), o lote sem nenhum teste (`testes`) e o HEAD que muda durante as guardas (`arvore-suja`);
  - um item novo diz, em uma frase cada: a porta e o `seal` rodam o portão, os testes, o `validate-versions.py` e a auditoria de uma cópia do commit; o `discard <id> --retro`; o registro ilegível e a fonte da colheita ilegível falham fechado; o fetch e o push leem a config de sistema do git.
- [ ] **Step 3:** `README.md`, parágrafo *The gate*, em inglês: depois de "no `Co-Authored-By`", acrescente a linha "Generated with"; depois do item do commit único, o arquivo que não é texto UTF-8 e a mudança de `.gitattributes`; no fim da lista, o commit que muda enquanto a porta roda. Diga em uma frase que a porta roda os scripts e os testes da loja de uma cópia do commit.
- [ ] **Step 4: Conferência final.** Rode cada comando com a saída num arquivo e leia o `rc`.

| Comando | Esperado |
|---|---|
| `python3 -m unittest discover -s $W/tests -p 'test_*.py'` | `OK`; os 333 da base continuam ou foram adaptados, e o relatório lista os adaptados |
| `python3 $R/tests/test_modo_autonomo.py` | `Ran 9 tests`, `OK` |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | `Ran 154 tests`, `OK (skipped=3)` |
| `python3 scripts/validate-versions.py` | rc 0; `retrofit-watch: v0.4.0` e `retrofit-skill: v0.11.0`; nenhum WARNING novo |
| `python3 $R/scripts/check_release_sync.py retrofit-watch` | rc 0; `0.4.0` nos manifestos e no README |
| `python3 $R/scripts/check_release_sync.py retrofit-skill` | rc 0; `0.11.0` |
| `python3 scripts/check-private-names.py` | rc 0 |
| `python3 scripts/anonymity-gate.py --camada1 --base origin/main` | rc 0: o próprio ramo passa na camada 1 |
| `git log origin/main..HEAD --format='%(trailers:key=Co-authored-by,valueonly)'` | nada |
| `git log origin/main..HEAD -i --grep='generated with' --format=%H` | nada |
| `/usr/bin/grep -rn 'import fcntl' $W/scripts/rw_*.py` | nada |
| `/usr/bin/grep -rn '"python3"' $W/scripts/rw_*.py` | nada |
| `git diff 1313ba5 --stat -- '*plugin.json' .claude-plugin/marketplace.json` | nada: sem bump |

- [ ] **Step 5:** Achado da camada 1 no próprio ramo se corrige no arquivo que o causou, com o texto montado em tempo de execução. Nunca pela lista de públicos.
- [ ] **Step 6:** `git add -A && git diff --cached --stat`. Responda por cada arquivo. Commit: `docs(retrofit-watch): o CHANGELOG 0.4.0 e o README contam as correcoes do modo auto`.

---

## Passos do dono, depois deste plano

Fora do plano. Nenhum subagente os faz.

1. O `/codereview:codereview` com `base=1313ba5`, e o merge e o push, só com o sim do dono.
2. Os *Passos do dono* do plano anterior: `harvest` e `--arvore` com a classificação dos nomes; o ensaio `auto-dry`; ligar o `auto`; a suíte no Windows.
3. A Tarefa 5 muda o passo 1: se o `harvest` sair rc 2 com o nome de uma pasta, ela existe sob `harvest_roots` e não se lê. O dono acerta a permissão ou tira a raiz da config.

## Self-review

- **Cobertura do escopo:** item 1 (Tarefa 10); 2, 4 e 16b (11); 3 e 16a (13); 5 e 6 (2); 7 (3); 8 (5); 9 (6); 10 (8); 11 (7); 12 (9); 13 (12); 14 (4). O item 15 saiu, com a medida na tabela.
- **Spec:** 5.6 (Tarefas 5, 9, 10, 12); 5.7 (3, 7, 8, 9, 10, 11); 5.9 (2, 4, 6); 5.11 (4, 12, 13). Nenhum item da lista da 5.7 perde guarda. O conjunto do que a aprovação substitui não muda.
- **Pares:** cada linha de tabela com guarda nova ou mudada tem o caso sabotado e o mutante. As linhas com "—" são casos de borda de uma guarda cujo mutante outra linha da mesma tabela mata.
- **Nomes:** `remote_env`, `clean_tree`, `_gate(tools, …)`, `layer1(…, tools)`, `new_terms(…, tools)`, `_Porta.head`, `_Porta.tree()`, `_check`, `_g_still`, `_g_opaque`, `_form`, `_cited`, `retro_pedido`, `retro_licoes`, `retro_veredito`, `discard_retro`, `RETRO_ITEM`, `StartupTimeout` e `CRITERION_RETRY` são os mesmos em todas as tarefas que os citam.
- **Ordem:** as Tarefas 2 a 4 mexem em `rw_auto.py`; a 5 e a 6, em `rw_store.py`; a 7 abre `rw_gate.py`; da 8 à 12, a porta, uma por vez. A 9 vem antes da 10 porque a cópia do commit conta com a recusa do `.gitattributes`. A 13 e a 14 só escrevem texto.
- **Review Focus:** 1 e 4 na Tarefa 10; 2 na 5; 3 na 9; 5 na 4.
