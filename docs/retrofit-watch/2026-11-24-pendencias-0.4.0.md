# retrofit-watch 0.4.0 — triagem dos minors adiados

Os revisores de cada tarefa do plano `docs/superpowers/plans/2026-11-24-retrofit-watch-auto-correcoes.md`
deixaram 65 minors adiados. A revisão final os julgou "podem esperar". Esta triagem confere cada um no código
do `main` de 2026-11-24 (merge `3b3cd4c`), pelo símbolo e não pela linha, porque os números de linha dos
relatórios são de commits antigos.

Contagem: **50 abertos**, 10 corrigidos, 4 fundidos com um item do `TODO.md` e 1 que é só do relatório.

Os caminhos são relativos a `plugins/retrofit-watch/skills/retrofit-watch/`, menos os que começam por
`plugins/` ou `docs/`, e o `README.md` da raiz. O código de cada linha é `T<tarefa>-<n>`: a tarefa do plano
e a ordem do minor no registro da tarefa. O item `Minors adiados da 0.4.0` do `TODO.md` aponta para cá.

## Abertos

Cada linha: `arquivo` (`símbolo`) — o problema — o que fazer. "Conferir" quer dizer que a triagem não achou
prova de que o minor ainda vale nem de que já não vale.

### Tarefa 2 — o registro

- T2-2 `scripts/rw_auto.py` (`_append`) — aceita uma lista ou uma função e decide por `callable()` — um
  parâmetro nomeado à parte deixaria o contrato visível.
- T2-3 `scripts/rw_auto.py` (`_append`) — nenhum teste fixa que o registro que termina em `\n` não ganha um
  `\n` a mais; o mutante "sempre grava `\n`" sobrevive — um teste com o registro íntegro. Conferir.

### Tarefa 3 — os leitores da pasta da retro

- T3-2 `scripts/rw_auto.py` (`retro_licoes`, `retro_veredito`) — repetem três linhas, e o `_numbered(...)[1]`
  do `load_licoes` é um índice opaco — um helper com nome e um retorno com nome.

### Tarefa 6 — o critério da v2

- T6-1 `scripts/rw_store.py` (`_leaks`) — o estouro do teto dentro do `_leaks` não tem teste; o mutante que
  aperta o `try` do `criterion` só em volta do `_autonomous` sobrevive — o caso do `_leaks` lento.
- T6-3 `scripts/rw_store.py` (`_cached`, `_timed_out`) — a leitura do `criterio.json` está em duas cópias, e o
  `mkdir` com o `_write_json` em mais duas, no `criterion` — um leitor e um gravador só.
- T6-4 `scripts/rw_store.py` (docstring do módulo, linha `criterion`) — fala só do cache positivo — citar o
  cache do estouro, `{sha, estouro}`.
- T6-5 `scripts/rw_store.py` (`STARTUP_TIMEOUT`) — o teto de 3 s vale por chamada ao git, e o caminho tem até
  cinco; a soma pode passar dos 10 s do hook antes de gravar o estouro, e então o cache do estouro nunca
  grava — um prazo do caminho inteiro, ou gravar antes.

### Tarefa 4 — o `discard --retro`

- T4-1 `scripts/rw_auto.py` (`orphans`, `discard_retro`) — o critério "lote preparado sem linha" em duas
  cópias — um helper `_prepared_lotes(folder)`.
- T4-2 `scripts/rw_auto.py` (`orphans`) — a docstring diz que o `licoes.json` ilegível conta como aberto; com a
  linha `<id>#retro` do `RETRO_ITEM`, conta como fechado — corrigir a docstring.
- T4-3 `tests/test_auto_formats.py` (`test_cli_discard_retro`) — o `isascii()` passa com `ensure_ascii=False`,
  e a agulha `"r1"` é fraca — conferir o escape `\uXXXX` e uma agulha da mensagem.
- T4-4 `scripts/rw_auto.py` (`discard_retro`) — falta o caso da `sessao` null com o `pedido.json` de outra
  retro — um teste. Conferir.

### Tarefa 5 — a colheita

- T5-1 `tests/test_auto_store.py` (`"origin"`) — o subteste `origin` só asserta o texto fixo "origin"; o
  mutante que tira o `{repo}` da mensagem sobrevive — assertar o caminho do repo.
- T5-2 `scripts/rw_store.py` (`_source_lines`) — o `NotADirectoryError` é StoreError aqui e ausência no
  `_repos`; o critério é desigual, e falha fechado — escolher um critério.
- T5-3 `tests/test_auto_gate.py` (`clean_retrofit`) — um `wt` não usado num teste da guarda do veredito (era a
  linha 601 no commit da tarefa) — tirar. Conferir qual teste.
- T5-4 `scripts/rw_store.py` (`_origin_of`) — o `_gone(repo)` confere a pasta, não o `.git`; com a pasta
  presente e o `.git` já apagado (um `rm -rf` em curso), o rc 128 vira StoreError — `_gone(repo / ".git")`.
- T5-5 `scripts/rw_store.py` (`_repos`) — o `p.is_dir()` dos filhos: no Python 3.13, uma raiz `r--` pode
  encolher a colheita em silêncio — medir no 3.13.
- T5-6 `scripts/rw_store.py` (`_inside_repo`) — usa `(p / ".git").exists()`: no 3.12 levanta o
  `PermissionError` cru, no 3.13 pode dar `False`, e a guarda da pasta de dados passa — usar o `_gone`.

### Tarefa 7 — o ambiente do git de rede

- T7-1 `tests/test_auto_gate.py` (`test_git_of_the_gate_ignores_the_inherited_environment`) — o comentário do
  cabeçalho ainda diz "nem lê a config de fora do HOME do Context"; o git de rede lê a de sistema — corrigir.
- T7-3 `tests/test_auto_store.py` (`test_prepare_and_gate_share_the_remote_env`) — confere só o lado do
  `prepare`, por igualdade — conferir também o fetch da porta.
- T7-4 `tests/test_auto_gate.py` (`assertNotIn("GIT_DIR", env)`) — ao falhar, imprime o ambiente inteiro de
  quem roda — `assertFalse("GIT_DIR" in env)`.

### Tarefa 8 — o sha conferido

- T8-2 `scripts/rw_gate.py` (`_plan`) — a `versao` da linha vem do `plugin.json` no disco do worktree, não do
  sha conferido; uma edição depois do `_check` muda a `versao` e o `cache_matches` — ler do sha.
- T8-3 `tests/test_auto_gate.py` (`test_publish_without_anonimato_is_held_by_its_guard`) — este comentário e o
  de `test_amend_keeps_the_marker_before_another_trailer` dizem `refuse` onde o `publish` passa pelo `_check`
  — trocar. A docstring do módulo `rw_gate.py`, a outra metade do minor, foi corrigida em `8aba070`.
- T8-4 `tests/test_auto_gate.py` (`test_approval_refuses_a_commit_on_top`) — um `assertEqual` dentro do `then`,
  que roda dentro do `publish`; o D25 transforma a falha em `erro`, e a mensagem engana — guardar o valor e
  assertar depois.
- T8-5 `scripts/rw_gate.py` (`_mark_approved`) — um `--amend` estranho entre o da porta e a leitura de `new`,
  com a mesma árvore, o mesmo pai e o trailer, sobe a mensagem dele (classe "HEAD sai e volta", fora do
  plano) — conferir a mensagem também.

### Tarefa 9 — a guarda 5b

- T9-2 `tests/test_auto_gate.py` (`test_plain_text_passes_the_content_guard`) — nenhum caso que segura usa um
  nome acentuado, e o teste de passagem não prova que o arquivo com acento foi lido — um caso que segura.
- T9-3 `tests/test_auto_gate.py` (`got[0] != "escopo"`) — aceita `interno` — exigir `None` ou um motivo
  conhecido.
- T9-4 `tests/test_auto_gate.py` (`test_content_the_layers_cannot_read_is_held`) — o subteste UTF-16 não tem o
  controle em UTF-8 que dá `nome-privado` — acrescentar o controle.
- T9-5 `scripts/rw_gate.py` (`_g_opaque`) — um nome de caminho fora do UTF-8 chega às camadas como U+FFFD; a
  guarda lê o conteúdo, não o nome — segurar o nome também.
- T9-6 `scripts/rw_gate.py` (`meta.split(" ")`) — sem defesa: um aviso do git na listagem dá `ValueError`
  (falha fechada) — partir com limite e conferir a forma.

### Tarefa 10 — a cópia do commit

- T10-1 `scripts/rw_gate.py` (`_g_tests`) — os testes rodam na mesma cópia que o `validate-versions.py` e a
  auditoria leem depois; um teste que grava na árvore muda o que as guardas seguintes veem (já era assim no
  worktree) — uma cópia por guarda, ou conferir a cópia depois dos testes.
- T10-3 `tests/test_auto_gate.py` (`back_to_old`) — cópia literal em dois testes — um helper.
- T10-6 `scripts/rw_store.py` (`_version`) — o `seal` lê a `versao` do `plugin.json` do disco do worktree
  (dado rastreado, decisão do brief da tarefa) — junto com o T8-2, ler do commit selado.

### Tarefa 11 — as guardas da mensagem e dos testes

- T11-1 `scripts/rw_gate.py` (`_g_tests`) — a docstring não diz que recusa zero testes — acrescentar.
- T11-2 `scripts/rw_gate.py` (`GENERATED`) — sem fronteira de palavra, casa "regenerated with … claude" e
  "generated without claude", e o `coautoria` não é substituível (na loja, 1 em 709 commits, e é o rodapé
  real) — `\b` e a forma do rodapé.
- T11-3 `tests/test_auto_gate.py` (`test_printed_ran_line_does_not_count`) — a morte do mutante "sem
  `PYTHONUNBUFFERED`" depende do ambiente de quem roda; com a variável no shell, o teste passa sem ela no
  código — `mock.patch.dict(os.environ)` sem a variável.
- T11-4 `scripts/rw_gate.py` (`_g_tests`) — um módulo de teste que escreve um resumo falso e chama
  `os._exit(0)` no import passa a guarda (a classe do resíduo `atexit`) — conferir o rc e o resumo de outra
  fonte.

### Tarefa 12 — o termo citado

- T12-1 `scripts/rw_gate.py` (`ASCII_ESCAPE`) — não consome `\\`: `\\x41` vira `\A` e põe uma forma de lixo no
  conjunto (a forma certa continua lá) — consumir o `\\` antes.
- T12-2 `scripts/rw_gate.py` (`_cited`) — "um trecho que não se desfaz conta só como está" não tem teste; sem
  o `try`, o `OverflowError` de `\U99999999` escapa do `refuse`, que só pega StoreError — um caso.
- T12-3 `scripts/rw_gate.py` (`QUOTED`) — um `"` cru no `onde` ou num trecho `segredo` desalinha os pares;
  dá `escopo` (falha fechada) — ler os trechos pela forma que a camada 1 escreve.

### Tarefa 13 — a referência

- T13-2 `references/modo-autonomo.md` (`coautoria`) — a "Saída" diz "sem o trailer", e a linha `Generated with`
  não é trailer — "sem o trailer e sem a linha".
- T13-3 `scripts/rw_store.py` (`ARCHIVE`) — o "(C2)" do comentário colide com o "(C2)" de outro plano em
  `scripts/rw_gate.py` (`OWNER_ONLY`) — escrever "(item 1, C2)".
- T13-4 `tests/test_auto_gate.py` (`rg.GUARDS`) — o "25" da docstring do módulo não tem sensor —
  `len(rg.GUARDS)` num teste, ou tirar o número.
- T13-5 `scripts/rw_gate.py` (docstring do módulo, `rebaseiam`) — "o rebaseiam" refere-se a "o git", e a lista
  não cita a camada 2 (`--termos`), que também roda da cópia — reescrever a frase.
- T13-6 `tests/test_auto_gate.py` (`teaching`) — `without_review` e `missing_review` dizem quase o mesmo —
  um nome como `early_approve`.

### Tarefa 14 — o CHANGELOG e o README

- T14-1 `plugins/retrofit-watch/CHANGELOG.md` (`O que a porta lê e de onde`) — o rótulo não cobre o
  `discard --retro` nem a config de sistema nos testes — outro rótulo, ou dois pontos.
- T14-2 `plugins/retrofit-watch/CHANGELOG.md` (`falham fechado`) — duas frases num ponto que o Step 2 da
  tarefa pedia em uma — juntar.
- T14-3 `plugins/retrofit-watch/CHANGELOG.md` e `references/modo-autonomo.md` (`uma linha da retro inteira`) —
  dá a entender que a linha da retro substitui as de lote; o `discard_retro` grava as de lote nos dois casos
  — "cada lote sem linha e, conforme o `licoes.json`, cada lição ou a retro inteira".
- T14-4 `plugins/retrofit-watch/CHANGELOG.md` (`auto_limits`) — a linha 37 da entrada tem 154 caracteres e a
  35 é curta — refazer a quebra.
- T14-5 `README.md` (`a commit that changed while the gate ran`) — a referência diz "o HEAD mudou" —
  "the HEAD changed while the gate ran".
- T14-6 `plugins/retrofit-watch/CHANGELOG.md` (`o portão`) — "o portão" sem "de anonimização", ao lado de
  "a porta" — nomear o portão inteiro.

## Fora da lista

| Código | Classe | Onde ficou |
|---|---|---|
| T2-1 docstring "sem exceção" do `flow_finished` | corrigido | `58f12ed` (a docstring diz que o registro ilegível é Malformed) |
| T3-1 o `flow_finished` lê o `licoes.json` sem o `id` | corrigido | `58f12ed` (lê pelo `retro_licoes`) |
| T3-3 o relatório conta 7 chamadores e lista 8 | só do relatório | não há código: o erro é do texto do relatório |
| T6-2 o estouro do critério sem limite inferior | corrigido | `2676441` (`0 <= now - when` no `_timed_out`) |
| T7-2 o alias `rw_gate.network_env` só serve a um teste | fundido | item `O alias network_env só serve a um teste` do `TODO.md` (LOW r1 #8) |
| T8-1 o `--amend` do `_mark_approved` mantém o autor do HEAD | fundido | item `O commit autônomo sem guarda de autor` do `TODO.md` (Ruling FR-1) |
| T9-1 `.gitattributes` comparado com caixa exata | corrigido | `6963039` (`_attributes_name`, com `casefold().rstrip(". ")`) |
| T10-2 o `.pyc` do `plant_blind_name_check` fora do worktree | corrigido | `7f4a61a` (`pyc.is_relative_to(wt)` nos dois testes) |
| T10-4 `rmtree(ignore_errors=True)` do `clean_tree` | fundido | item `As pastas .porta- que sobram` do `TODO.md` (LOW r1 #13) |
| T10-5 a docstring do `rw_gate.py` não diz que as portas rodam da cópia | corrigido | `8aba070` |
| T10-7 o `git archive` do `_leaks` lê atributos de fora da árvore | corrigido | `1c84e35` (o `_leaks` usa `ARCHIVE` e `archive_env()`) |
| T10-8 o comentário do `ARCHIVE` sem a C2 | corrigido | `8aba070` (cita o `info/attributes` e a C2) |
| T11-5 a referência e o CHANGELOG sem a recusa `Generated with` e a de zero testes | corrigido | `8aba070` (referência) e `93156b0` (CHANGELOG) |
| T12-4 a camada 1 não normaliza Unicode (NFD contra NFC) | fundido | item `NFD contra NFC na camada 1` do `TODO.md` (Ruling FR-4) |
| T13-1 a "Saída" do `escopo` sem a saída manual | corrigido | `5087268` (codereview r1 #1) |
