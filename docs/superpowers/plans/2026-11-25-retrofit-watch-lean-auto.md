# retrofit-watch 0.5.0: modo autônomo nas skills locais — plano de construção

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for
> tracking. **No Codex:** siga as tarefas na ordem, um commit por tarefa, num worktree desta loja feito do
> `origin/main`; leia antes o `CLAUDE.md` da raiz (seção Git) e a spec abaixo inteira.

**Goal:** a skill local de um repo privado listado na config passa pelo fluxo autônomo da v1 e publica
direto na `main` desse repo, pelo pre-push dele, com a cópia em uso vinda de um clone dedicado que só segue a
`main`.

**Architecture:** o hook classifica a skill lean pelo `dono/repo` do `origin` e a deixa seguir no fluxo da v1
quando o repo está em `lean_auto`. O lote nasce de um worktree do clone dedicado, o executor roda o
`/retrofit-skill` enxuto com `--auto`, e a porta roda uma tabela de guardas própria do repo privado: sem as
camadas de nome, com o gate do repo rodado pelo próprio pre-push. O modo efetivo fica em `auto-dry` até uma
janela do critério da v2 se cumprir.

**Tech Stack:** Python 3 só com a biblioteca padrão; git (worktree, `extensions.worktreeConfig`); `gh api`
para o status; `unittest` com as fixtures de `tests/`.

**Spec:** `docs/superpowers/specs/2026-11-25-retrofit-watch-lean-auto-design.md`, que estende
`docs/superpowers/specs/2026-11-23-retrofit-watch-modo-autonomo-design.md` (a spec da v1). Os dois vão
junto com este plano.

Caminhos relativos à raiz da loja. `RW` = `plugins/retrofit-watch/skills/retrofit-watch`;
`RS` = `plugins/retrofit-skill`.

## Global Constraints

- Hook e scripts só com a biblioteca padrão; o hook tem 10 s; Windows: sem `fcntl`, stdout em ASCII.
- Nenhum commit da loja leva `Co-Authored-By` nem a linha `Generated with`. Sensor:
  `git log -1 --format='%(trailers:key=Co-authored-by,valueonly)'` vazio.
- A loja é pública: nenhum nome de repo privado, empresa, pessoa ou caminho com usuário, nem nos testes. Os
  testes usam a fixture `fixture/kb-libs`. Antes de cada push: `python3 scripts/check-private-names.py` e
  `python3 scripts/anonymity-gate.py --camada1 --base origin/main` com rc 0.
- Config nova: `lean_auto` (lista de `dono/repo`, padrão `[]`) e `live_dir` (padrão `~/.local/share/skills-live`).
- O modo efetivo do repo privado: `manual` → `manual`; `auto-dry` → `auto-dry`; `auto` → `auto` só com a janela
  cumprida, senão `auto-dry`. A janela: 10 publicados e 14 dias (`V2_MIN_PUBLISHED`, `V2_MIN_DAYS`), sem revert
  nem nome vazado, contados desde o último revert de um commit autônomo, na loja ou num repo da lista.
- Nunca `--no-verify`; nunca escrever no checkout de desenvolvimento do repo privado; nunca commitar no clone
  dedicado; nunca criar tag.
- No repo privado, `segredo` nunca se aprova; `caminho` (caminho com usuário) se aprova pelo `approve`.
- Versões: `retrofit-watch` 0.5.0 e `retrofit-skill` 0.12.0, com `CHANGELOG.md`, `.claude-plugin/marketplace.json`
  e `README.md` no mesmo incremento (Tarefa 10).
- Cada guarda nova tem um caso que a sabota (o teste fica vermelho com a guarda tirada) e um que passa.

## Review Focus

1. **Um plugin da loja e uma skill local com o mesmo nome na mesma retro.** Nunca viram um lote só: o segundo
   fica `segurado` com `fora-do-pedido` e o detalhe `lote duplicado` (teste na Tarefa 4).
2. **O dono deixou o clone dedicado num ramo, ou com arquivo não rastreado.** O avanço não mexe nele e o aviso
   diz `fora da main` ou `suja` (teste na Tarefa 3).
3. **Repo listado sem pre-push** (nem `core.hooksPath` com `pre-push`, nem `.git/hooks/pre-push`). A porta segura
   com `gate` e o detalhe `sem pre-push`, e nunca faz push sem gate (teste na Tarefa 6).
4. **Aprovação seguida de emenda do executor.** O `patch` do lote muda e a aprovação do lote privado se anula:
   o lote volta a segurar pelo motivo de antes (teste na Tarefa 6).
5. **Startup sem rede.** O avanço destacado falha, o hook volta dentro do prazo, e o aviso seguinte mostra
   a falha (teste na Tarefa 7).

---

### Task 1: A fixture do repo privado

**Files:**
- Create: `RW/tests/fixture_private.py`
- Test: `RW/tests/test_fixture_private.py`

**Interfaces:**
- Consumes: `World` e `GIT_ENV` de `RW/tests/test_retrofit_watch.py`; `StoreWorld` de `RW/tests/fixture_store.py`.
- Produces: `class PrivateWorld(StoreWorld)` com:
  - `self.remote: Path`: o bare em `<tmp>/remotes/fixture/kb-libs.git`, para o slug sair `fixture/kb-libs`;
  - `self.dev: Path`: um clone de desenvolvimento em `<home>/repos/kb-libs`;
  - `SLUG = "fixture/kb-libs"`; `SKILL = "kb-demo"`; `PASTA = ".claude/skills/kb-demo"`;
  - na `main` do bare: `PASTA/SKILL.md`, `PASTA/CHANGELOG.md` e `.githooks/pre-push`, um `#!/bin/sh` que roda
    `python3 scripts/gate_stub.py`. O stub lê `RW_FAKE_GATE_RC` (padrão `0`), imprime
    `gate: <rc> passo(s) reprovado(s)` e sai com esse rc;
  - `config(**extra)`: grava o `retrofit-watch.json` do HOME fixture com `owners` contendo `fixture`, `store` e
    `lean_auto: [SLUG]`, mais `extra`;
  - `commit_on_origin(files: dict[str, str], message: str) -> str`: commita no bare e devolve o sha.

- [ ] **Step 1:** Escreva `test_fixture_private.py` com `test_slug_parses_from_the_bare_url` (o
  `remote get-url origin` do `dev` termina em `fixture/kb-libs.git`), `test_prepush_stub_passes_and_fails` (um
  push de um commit novo com `RW_FAKE_GATE_RC=0` sobe; com `RW_FAKE_GATE_RC=2`, o rc do push é diferente de 0 e a
  saída tem `gate: 2 passo(s) reprovado(s)`) e `test_never_touches_real_home` (`assert_fixture_origin` de cada
  caminho).
- [ ] **Step 2:** Rode `cd RW && python3 -m unittest discover -s tests -p 'test_fixture_private.py' -v`. Esperado:
  FAIL (`ModuleNotFoundError: fixture_private`).
- [ ] **Step 3:** Implemente `PrivateWorld`. O `.githooks` entra pelo `git config core.hooksPath .githooks` no
  clone, como o `npm ci` faria no repo real.
- [ ] **Step 4:** Rode de novo. Esperado: PASS.
- [ ] **Step 5:** `git commit -m "test(retrofit-watch): a fixture do repo privado com pre-push"`

### Task 2: A config, a classificação e o `why_manual`

**Files:**
- Modify: `RW/scripts/retrofit_watch.py` (`Context`, `_lean`, `_owned`, `classify_path`)
- Modify: `RW/scripts/rw_auto.py` (`REASONS`, `REASON_TEXT`, `why_manual`, `open_request`, `auto_text`, `PEDIDO_SKILL_SPEC`)
- Test: `RW/tests/test_lean_auto.py`

**Interfaces:**
- Produces, em `retrofit_watch.py`:
  - `origin_slug(url: str) -> str | None`: o `dono/repo` em minúsculas, sem `.git`; o `_owned` passa a usá-la;
  - `Context.lean_auto -> frozenset[str]`, os slugs em minúsculas;
  - `Context.live_dir -> Path`, com o padrão `~/.local/share/skills-live`, expandido pelo `_home_path`;
  - `_lean(name, repo, origin=None)`: a entrada ganha `"origin": <slug | None>`.
- Produces, em `rw_auto.py`:
  - `REASONS = ("modo", "kit-ou-lean", "lista-manual", "permissao", "entrypoint", "sem-loja", "sem-clone", "teto")`;
  - `REASON_TEXT["sem-clone"]`: `"falta o clone dedicado do repo (retrofit_watch.py live-setup <dono/repo>)"`;
  - no `pedido.json`, cada skill ganha `"repo": <slug | None>`; `PEDIDO_SKILL_SPEC["repo"] = _opt_text`.
- Consumes: `rw_store.live_clone(ctx, slug)` (Tarefa 3). Nesta tarefa, use um stub que devolve `None`; a Tarefa 3
  o substitui.

- [ ] **Step 1:** Escreva os testes:
  - `test_lean_of_listed_repo_goes_auto`: entrada lean com `origin` em `lean_auto`, bypass, `cli`, loja e clone
    presentes → `why_manual(...) is None`;
  - `test_lean_not_listed_stays_kit_ou_lean` → `"kit-ou-lean"`;
  - `test_kit_stays_kit_ou_lean` → `"kit-ou-lean"`;
  - `test_listed_lean_without_store_is_sem_loja`, e `test_listed_lean_without_clone_is_sem_clone`, nessa ordem;
  - `test_pedido_carries_repo` (o `repo` é o slug na skill lean e `None` na full);
  - `test_origin_slug_forms`: `https://github.com/A/B.git`, a forma scp do SSH (usuário `git`, host `github.com`, caminho `A/B.git`),
    `.../fixture/kb-libs.git`,
    e `None` para uma string sem barra.
- [ ] **Step 2:** Rode `python3 -m unittest discover -s tests -p 'test_lean_auto.py' -v`. Esperado: FAIL.
- [ ] **Step 3:** Implemente a ordem nova do `why_manual`:
  1. `modo`;
  2. `full` segue; `lean` com `origin` em `lean_auto` segue; o resto sai `kit-ou-lean`;
  3. `lista-manual`, `permissao`, `entrypoint`;
  4. `sem-loja`, que vale para as duas, porque a auditoria da porta roda da loja;
  5. `sem-clone`, só para a lean;
  6. `teto`, contado por `entry["arg"]` como hoje.

  O `live_clone` do hook só lê arquivo, sem git, como o `Context.store`. No `auto_text`, a skill lean leva
  ` (repo <slug>)` depois do rótulo.
- [ ] **Step 4:** Rode a suíte inteira do plugin: `python3 -m unittest discover -s tests -v`. Esperado: PASS, sem
  regressão nos `test_auto_*`.
- [ ] **Step 5:** `git commit -m "feat(retrofit-watch): a skill local de repo listado entra no modo autônomo"`

### Task 3: O clone dedicado

**Files:**
- Modify: `RW/scripts/rw_store.py`; `RW/scripts/retrofit_watch.py` (`cli`: verbos `live-setup` e `live-advance`)
- Test: `RW/tests/test_lean_live.py`

**Interfaces:**
- Produces, em `rw_store.py`:
  - `live_path(ctx, slug: str) -> Path`: `ctx.live_dir / <repo do slug>`;
  - `live_clone(ctx, slug: str) -> Path | None`: o caminho, quando `<path>/.git/config` tem o `[remote "origin"]`
    com `url` de `origin_slug == slug`. Lê o arquivo e não chama o git;
  - `live_setup(ctx, slug: str, url: str | None = None) -> Path`. Ele:
    - levanta `StoreError` quando o caminho já existe;
    - clona com o `remote_env`, sendo o `url` padrão `https://github.com/<slug>.git`, e fica na `main`;
    - roda `git config extensions.worktreeConfig true` e
      `git config --worktree core.hooksPath <path>/.git/rw-live-hooks`;
    - grava `<path>/.git/rw-live-hooks/pre-commit`, com mode 755, que sai 1 com
      `retrofit-watch: este clone so segue a main; commite num worktree do lote`;
  - `live_advance(ctx, slug: str) -> dict`:
    - devolve as chaves `repo`, `resultado`, `antes`, `depois`, `detalhe` e `ts`, com o `resultado` em `ok`,
      `fora-da-main`, `suja` ou `erro`;
    - grava o resultado em `<dados>/live/<repo>.json`;
    - antes do `fetch`, confere o `symbolic-ref --short HEAD == "main"` e o `status --porcelain` vazio (o ignorado
      não conta). Depois roda o `merge --ff-only origin/main`.
- Produces, em `retrofit_watch.py`: `live-setup <dono/repo> [--url URL]` (rc 0 com o caminho; 1 com o
  `StoreError`; 2 com uso errado) e `live-advance [<dono/repo>]` (sem argumento, todos os da `lean_auto`; rc 0
  quando todos saem `ok`).

- [ ] **Step 1:** Escreva os testes, com a `PrivateWorld`:
  - `test_setup_clones_main_with_worktree_lock`: depois do `live_setup`, um `git commit --allow-empty` no clone
    sai 1 com a frase da trava;
  - `test_lote_worktree_is_not_locked`: um `git worktree add` a partir do clone, seguido de
    `git config core.hooksPath .githooks` e de um commit no worktree, sai 0;
  - `test_setup_refuses_existing_path`: o `StoreError` vem, e o conteúdo fica intacto;
  - `test_advance_fast_forwards`: o `commit_on_origin` e depois `live_advance` dão `ok`, com o `depois` igual ao
    sha novo;
  - `test_advance_leaves_branch_alone`: o clone num ramo dá `fora-da-main` e o HEAD não muda;
  - `test_advance_leaves_dirty_alone`: um arquivo não rastreado dá `suja`; um arquivo ignorado pelo
    `.gitignore` dá `ok`;
  - `test_live_clone_rejects_other_origin`: um clone de outro remoto no caminho dá `None`.
- [ ] **Step 2:** Rode `python3 -m unittest discover -s tests -p 'test_lean_live.py' -v`. Esperado: FAIL.
- [ ] **Step 3:** Implemente as funções e os verbos, e tire o stub da Tarefa 2.
- [ ] **Step 4:** Rode de novo e a suíte inteira. Esperado: PASS.
- [ ] **Step 5:** `git commit -m "feat(retrofit-watch): o clone dedicado que só segue a main"`

### Task 4: A lição, a triagem, o `prepare` e o selo do lote privado

**Files:**
- Modify: `RW/scripts/rw_auto.py` (`LICAO_SPEC`, `RETROFIT_SPEC`, `in_request`, `_plan`)
- Modify: `RW/scripts/rw_store.py` (`prepare`, `seal`)
- Test: `RW/tests/test_lean_auto.py`

**Interfaces:**
- Produces:
  - `LICAO_SPEC["repo"] = _opt_text`: o slug na lição de skill local, `null` na da loja;
  - `RETROFIT_SPEC` ganha `"repo": _opt_text` e `"pasta": _opt_text`. A `pasta` é o caminho da skill relativo à
    raiz do repo, achado pelo `realpath` da skill no clone;
  - o lote privado se chama pelo nome da skill;
  - `in_request` casa `plugin` e `repo` com uma skill do pedido;
  - `prepare` de lote com `repo`: o `fetch` e o `worktree add` saem do `live_clone(ctx, repo)`, e nunca do
    `store_clone`. Sem clone, levanta `StoreError("sem clone dedicado: <slug>")`;
  - o `seal` de lote com `repo` roda, da camada 1, só o segredo e o caminho com usuário
    (`anonymity-gate.py --camada1`, filtrado pelos tipos `segredo` e `caminho`). O nome e o e-mail não reprovam.

- [ ] **Step 1:** Escreva os testes:
  - `test_lean_lesson_needs_repo_in_request`: uma lição com `repo` de outro slug fica `fora-do-pedido`;
  - `test_same_name_store_and_lean_never_merge` (Review Focus 1): uma retro com o plugin `kb-demo` da loja e a
    skill `kb-demo` do repo dá um lote e uma linha `segurado` com `fora-do-pedido` e o detalhe `lote duplicado`;
  - `test_prepare_private_uses_live_clone`: o `retrofit.json` tem `repo`, `pasta == ".claude/skills/kb-demo"` e
    um `worktree` cujo `git rev-parse --git-common-dir` é o do clone;
  - `test_prepare_private_never_touches_dev`: o `git status`, os ramos e o `worktree list` do `dev` ficam iguais;
  - `test_seal_private_ignores_company_name`: um nome da lista de hashes no diff não reprova o selo, e um
    `/home/<usuário>` reprova.
- [ ] **Step 2:** Rode os testes. Esperado: FAIL.
- [ ] **Step 3:** Implemente. O `_plan` guarda o `repo` de cada lote, e uma segunda entrada com o mesmo nome e
  outro `repo` vai para `segurar`.
- [ ] **Step 4:** Rode os testes e a suíte inteira. Esperado: PASS.
- [ ] **Step 5:** `git commit -m "feat(retrofit-watch): o lote da skill local nasce do clone dedicado"`

### Task 5: A janela do critério e o modo efetivo

**Files:**
- Modify: `RW/scripts/rw_store.py`
- Test: `RW/tests/test_lean_window.py`

**Interfaces:**
- Produces:
  - `_reverts(repo: Path, head: str, marker_shas: list[str]) -> list[list]`: devolve `[sha, ts]` dos commits que
    trazem `This reverts commit <sha>` de um dos `marker_shas` (o `REVERTS` de hoje);
  - `lean_window(ctx, now: float | None = None) -> dict | None`:
    - devolve `publicados`, `dias`, `desde`, `ultimo_revert` e `cumprido`, ou `None` sem loja;
    - conta os commits autônomos da loja (`_autonomous`) com `ts` maior que o último revert. O revert vem da loja
      e do `origin/main` local de cada `live_clone` listado;
    - os `dias` contam do último revert quando há um, senão do primeiro commit contado;
    - os vazados saem do `_leaks` da loja, só quando os pisos passam;
    - o cache fica em `<dados>/lean-janela.json`, pelos heads;
  - `lean_mode(ctx, now: float | None = None) -> str`: `"manual"`, `"auto-dry"` ou `"auto"`, pela tabela das
    Global Constraints.

- [ ] **Step 1:** Escreva os testes, com a `PrivateWorld` e o `advance_origin` da loja fixture:
  - `test_window_like_v2_without_revert`: 10 commits autônomos com 15 dias dão `cumprido: True`;
  - `test_store_revert_restarts_window`: depois de um revert, 10 commits novos mas só 3 dias dão
    `cumprido: False`, com `ultimo_revert` preenchido;
  - `test_private_revert_restarts_window`: o mesmo, com o revert num commit marcado do repo privado;
  - `test_mode_table`: os quatro casos da tabela;
  - `test_window_never_fetches`: nenhum `fetch` roda (o dublê de `run` registra as chamadas).
- [ ] **Step 2:** Rode os testes. Esperado: FAIL.
- [ ] **Step 3:** Implemente. O `criterion` da v1 não muda.
- [ ] **Step 4:** Rode os testes e a suíte inteira. Esperado: PASS.
- [ ] **Step 5:** `git commit -m "feat(retrofit-watch): a janela do critério que recomeça no revert"`

### Task 6: A porta do repo privado

**Files:**
- Modify: `RW/scripts/rw_gate.py`; `RW/scripts/rw_auto.py` (`APROVADO_SPEC`, `approve`, e o novo `DIFF_SPEC` com
  `load_diff`)
- Test: `RW/tests/test_lean_gate.py`

**Interfaces:**
- Consumes: `retrofit.json` com `repo` e `pasta` (Tarefa 4); `lean_mode` (Tarefa 5); `live_advance` (Tarefa 3).
- Produces:
  - `GATE_REASONS` ganha `"sem-changelog"`, `"segredo"`, `"caminho"` e `"gate"`;
  - `OVERRIDABLE_PRIVATE = OVERRIDABLE + ("caminho",)`;
  - `GUARDS_PRIVATE`, nesta ordem:
    1. `escopo` (o lugar), `arvore-suja`, `fetch` e `rebase`;
    2. `escopo` (os arquivos só sob a `pasta`) e `escopo` (o opaco);
    3. `coautoria`, `sem-marca` e `sem-changelog` (o `<pasta>/CHANGELOG.md` mudou e tem uma linha com a data do
       commit, `AAAA-MM-DD`);
    4. `sem-veredito`, `fora-do-pedido`, `nao-publicavel` e `muda-description`;
    5. `segredo` e `caminho`;
    6. `revisao-desatualizada`, `regra-repetida` e `diff-alem-das-licoes`, os três lidos do `diff.json`;
    7. `auditoria`, que roda o auditor do `store_clone` sobre a `pasta` da cópia do commit;
    8. `teto` e `arvore-suja` (o HEAD que mudou);
    9. `gate`: com `package-lock.json` na raiz do worktree, roda `npm ci`; depois roda o pre-push do repo como
       o git rodaria, com o stdin `HEAD <sha> refs/heads/main <sha do origin/main>`;
    10. `auto-dry`, que segura quando o `lean_mode(ctx) != "auto"`, com o resumo do gate no detalhe;
  - `_Porta.repo: str | None` (do `retrofit.json`); a porta escolhe `GUARDS_PRIVATE` quando ele não é `None`;
  - `DIFF_SPEC = {"patch": _text, "regra_repetida": _opt_text, "fora_das_licoes": _opt_text}`. O arquivo é
    `<lote>/diff.json`, gravado pelo revisor na segunda passada do lote privado;
  - `APROVADO_SPEC["patch"] = _opt_text`: o `approve` grava o `patch` do `retrofit.json`. No lote privado,
    uma aprovação cujo `patch` difere do atual é ignorada, com a nota `aprovacao anulada: o patch mudou`;
  - `Effects.status(slug, sha, descricao) -> (bool, str)`:
    `gh api -X POST repos/<slug>/statuses/<sha> -f state=success -f context=local/ci -f description=<descricao>`;
  - no `_publish` do lote privado, nesta ordem: `push`, `status`, a linha `publicado` com `repo`,
    `live_advance`, e o `mark_done`. Não há `refresh_install`. A falha do `status` ou do avanço vai em
    `instalacao` (`status-falhou`, `clone-atras`), e o rc é 4;
  - `phrase`: `retrofit-watch: <skill> (<slug>) publicada sozinha (<sha>)`.

- [ ] **Step 1:** Escreva os testes. Cada guarda nova tem o caso que reprova e o que passa:
  - `test_gate_red_holds_with_summary`: com `RW_FAKE_GATE_RC=2`, o lote fica `segurado` por `gate`, e o detalhe
    tem `gate: 2 passo(s)`;
  - `test_no_prepush_holds` (Review Focus 3);
  - `test_dry_runs_gate_before_holding`: com `mode: auto`, a janela não cumprida e o gate verde, o lote fica
    `segurado` por `auto-dry`, e o detalhe tem `gate: 0 passo(s)`;
  - `test_live_mode_pushes_and_advances`: com a janela cumprida (um dublê de `lean_mode`), o lote fica
    `publicado`, o `origin/main` do bare é o sha, o `Effects.status` é chamado uma vez e o clone avança;
  - `test_company_name_passes_secret_fails`: um nome da lista no diff passa, e um `ghp_` mais 36 caracteres
    segura por `segredo`;
  - `test_userpath_holds_then_approve_releases`: um `/home/<u>` segura por `caminho`, e `approve` mais
    `publish` publica;
  - `test_secret_never_overridable`: o `approve` sobre `segredo` não libera;
  - `test_approval_voided_by_new_patch` (Review Focus 4);
  - `test_changelog_required`: o diff sem a entrada no CHANGELOG segura por `sem-changelog`;
  - `test_scope_outside_pasta`: um arquivo fora da `pasta` segura por `escopo`;
  - `test_never_no_verify`: `"--no-verify"` não aparece em nenhum argumento de `run`.
- [ ] **Step 2:** Rode `python3 -m unittest discover -s tests -p 'test_lean_gate.py' -v`. Esperado: FAIL.
- [ ] **Step 3:** Implemente. As guardas que já existem são reaproveitadas pela função, e não copiadas.
- [ ] **Step 4:** Rode os testes e a suíte inteira, inclusive o `test_auto_gate.py`. Esperado: PASS, com a porta
  da loja sem mudança de comportamento.
- [ ] **Step 5:** `git commit -m "feat(retrofit-watch): a porta do repo privado, pelo pre-push dele"`

### Task 7: O startup

**Files:**
- Modify: `RW/scripts/retrofit_watch.py` (`cmd_pending`, `NOTICES`); `RW/scripts/rw_store.py`; `RW/scripts/rw_auto.py`
- Test: `RW/tests/test_lean_live.py`

**Interfaces:**
- Produces:
  - `rw_store.spawn_live_advance(ctx) -> bool`: com a `lean_auto` não vazia, lança o
    `retrofit_watch.py live-advance` destacado e devolve sem esperar:
    - no POSIX, `subprocess.Popen(..., start_new_session=True)`;
    - no Windows, `creationflags=DETACHED_PROCESS`;
    - em todos, com o stdin, o stdout e o stderr em `DEVNULL`;
  - `rw_auto.live_notice(ctx) -> str | None`, que lê `<dados>/live/*.json`:
    - `cópia em uso de <repo> fora da main` (`fora-da-main` ou `suja`);
    - `avanço de <repo> falhou: <detalhe>` (`erro`);
    - nada, com `ok`;
  - `rw_auto.lean_mode_notice(ctx) -> str | None`: compara o `lean_mode` com `<dados>/lean-modo.json` e, na
    mudança, grava e devolve `repos privados fora do ensaio: o push agora é sozinho` ou
    `repos privados de volta ao ensaio (revert de <data>)`;
  - `cmd_pending` chama o `spawn_live_advance` antes dos avisos; os dois avisos novos entram em `NOTICES`.

- [ ] **Step 1:** Escreva os testes:
  - `test_startup_spawns_and_returns_fast`: com um dublê de `Popen` que dorme, o `cmd_pending` volta em menos
    de 1 s;
  - `test_offline_failure_shows_next_startup` (Review Focus 5): um `live/<repo>.json` com `erro` gera a frase;
  - `test_mode_notice_only_on_change`: duas chamadas seguidas dão a frase e depois `None`;
  - `test_no_lean_auto_no_spawn`.
- [ ] **Step 2:** Rode os testes. Esperado: FAIL.
- [ ] **Step 3:** Implemente.
- [ ] **Step 4:** Rode os testes e a suíte inteira. Esperado: PASS.
- [ ] **Step 5:** `git commit -m "feat(retrofit-watch): o startup avança o clone e avisa o modo"`

### Task 8: O `retrofit-skill` no lote privado e no repo listado

**Files:**
- Modify: `RS/commands/retrofit-skill.md` (seções "Modo autônomo" e "Modo enxuto"); `RS/references/modo-autonomo.md`
- Test: `RS/tests/test_modo_autonomo.py`

**Interfaces:**
- Consumes: `retrofit.json` com `repo` e `pasta` (Tarefa 4); `live-advance` (Tarefa 3); `diff.json` (Tarefa 6).
- Produces, em prosa:
  - **o `--auto` aceita o lote privado.** Com `repo` no `retrofit.json`, o executor faz o seguinte:
    - edita só a `pasta`;
    - escreve a entrada no `<pasta>/CHANGELOG.md` com a data de hoje, sem bump e sem `marketplace.json`;
    - commita com `Retrofit-Mode: autonomous` e sem coautoria;
    - roda o `seal`;
  - **o modo enxuto de um repo listado.** Quando o `origin` da skill está na `lean_auto`, o retrofit manual
    segue estes passos:
    - abre um worktree do clone dedicado e nunca commita nele;
    - edita, escreve o CHANGELOG e pede o "sim" do dono;
    - faz `git push origin HEAD:main`, pelo pre-push;
    - publica o `local/ci` no sha;
    - roda o `retrofit_watch.py live-advance <dono/repo>`.

- [ ] **Step 1:** Acrescente os testes de contrato de prosa no estilo dos que já existem:
  - `test_auto_accepts_private_lote`: a reference cita `pasta`, `CHANGELOG.md`, `sem bump` e `seal`;
  - `test_lean_listed_pushes_through_prepush`: o comando cita `HEAD:main`, `local/ci` e `live-advance`, e não
    cita `--no-verify`;
  - `test_never_commits_in_live_clone`: a frase de que nada se commita no clone dedicado está nos dois arquivos.
- [ ] **Step 2:** Rode `cd RS && python3 -m unittest discover -s tests -v`. Esperado: FAIL nos três.
- [ ] **Step 3:** Escreva a prosa. O `retrofit-skill.md` ganha só o roteamento, e o detalhe vai para a reference.
- [ ] **Step 4:** Rode de novo. Esperado: PASS, inclusive o `test_the_four_places_agree_at_0_11_0_or_later`.
- [ ] **Step 5:** `git commit -m "feat(retrofit-skill): o executor e o modo enxuto do repo listado"`

### Task 9: O revisor e a documentação da `retrofit-watch`

**Files:**
- Modify: `plugins/retrofit-watch/agents/retrofit-reviewer.md` (na primeira passada, a lição com `repo` se
  confere contra a skill no `origin/main` do clone dedicado, `git -C <clone> show origin/main:<pasta>/SKILL.md`,
  e não contra a loja; a segunda passada do lote privado grava o `diff.json`, e não o `anonimato.json`); `RW/references/modo-autonomo.md` (o lote privado: o `prepare` do clone, o
  despacho, o `diff.json`, o `publish`, a tabela de motivos com os quatro novos); `RW/SKILL.md` (a tabela de
  Controle com `lean_auto` e `live_dir`, e o Gotcha "o modo autônomo só vale…" estendido ao repo listado)
- Test: `RW/tests/test_auto_docs.py`

- [ ] **Step 1:** Estenda os testes de documentação que já existem. Todo motivo de `GATE_REASONS` e de `REASONS`
  aparece na tabela de motivos da reference, e o revisor cita `diff.json` com as chaves do `DIFF_SPEC`.
- [ ] **Step 2:** Rode `cd RW && python3 -m unittest discover -s tests -p 'test_auto_docs.py' -v`. Esperado: FAIL.
- [ ] **Step 3:** Escreva a prosa.
- [ ] **Step 4:** Rode a suíte inteira do plugin. Esperado: PASS.
- [ ] **Step 5:** `git commit -m "docs(retrofit-watch): o fluxo e o revisor do repo privado"`

### Task 10: A versão, o TODO e a publicação

**Files:**
- Modify:
  - `plugins/retrofit-watch/.claude-plugin/plugin.json`, `RW/SKILL.md` (`metadata.version`) e
    `plugins/retrofit-watch/CHANGELOG.md`: 0.5.0;
  - `plugins/retrofit-skill/.claude-plugin/plugin.json`, `RS/commands/retrofit-skill.md` (`metadata.version`) e
    `plugins/retrofit-skill/CHANGELOG.md`: 0.12.0;
  - `.claude-plugin/marketplace.json` e a tabela do `README.md`;
  - `TODO.md`, onde entra um item novo na seção "O que o uso da retrofit-watch 0.4.0 mostrou": *A aprovação da
    loja não fica presa ao patch*, ancorado em `RW/scripts/rw_gate.py` (`OVERRIDABLE`). A Fonte é a seção 9 da
    spec deste plano.

- [ ] **Step 1:** Escreva os CHANGELOGs, com o quê e por quê, citando a spec. Faça os bumps.
- [ ] **Step 2:** Rode os sensores, cada um com o rc lido sem pipe. Esperado: rc 0 em todos.
  - `python3 scripts/validate-versions.py`;
  - `python3 plugins/retrofit-skill/scripts/check_release_sync.py retrofit-watch`;
  - `python3 plugins/retrofit-skill/scripts/check_release_sync.py retrofit-skill`;
  - `claude plugin validate plugins/retrofit-watch` e `claude plugin validate plugins/retrofit-skill`, quando o
    cliente existe;
  - `python3 -m unittest discover -s tests`, na raiz;
  - as duas suítes dos plugins;
  - `python3 scripts/check-private-names.py`;
  - `python3 scripts/anonymity-gate.py --camada1 --base origin/main`;
  - `bash <kit sdd>/tests/check-todo.sh --check TODO.md`: nenhuma violação nova além das 4 que o
    `origin/main` já tem.
- [ ] **Step 3:** Confira o trailer em cada commit do ramo:
  `git log origin/main..HEAD --format='%h %(trailers:key=Co-authored-by,valueonly)'`, que deve sair sem nome.
- [ ] **Step 4:** `git fetch origin && git rebase origin/main`, rode o Step 2 de novo e faça
  `git push origin HEAD:main`.
- [ ] **Step 5:** Feche a issue deste plano com o sha.

**Fora deste plano:** os gestos no repo privado, que pedem o OK do dono:
- o estado da skill fora da pasta;
- a `lean_auto` na config;
- o `live-setup`;
- a troca dos links.

Eles moram num plano do próprio repo privado, porque esta loja é pública.
