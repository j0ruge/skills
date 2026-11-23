# retrofit-watch 0.4.0 e retrofit-skill 0.11.0: modo autônomo — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** No modo `auto`, uma lição de skill da loja que passa nas guardas é publicada sem nenhum "sim" do dono, e a que não passa fica segurada num ramo local.

**Architecture:** O Stop hook continua só pedindo a retro, agora com o caminho de um diretório de dados por retro. O agente da sessão grava as lições, despacha um revisor independente e um executor por lote, e chama subcomandos determinísticos do script do plugin: `triage`, `prepare`, `seal` e `publish`. A porta (`publish`) é o único caminho até o `origin/main`. Ela roda de novo todas as guardas sobre o commit final e registra cada resultado num arquivo só de acréscimo. As duas camadas mecânicas da anonimização moram num script novo da raiz da loja, que a porta chama dentro do worktree do lote.

**Tech Stack:** Python 3 só com biblioteca padrão (`unittest`, `subprocess`, `json`, `tarfile`), git, Markdown dos contratos da skill e do agente.

**Spec:** `docs/superpowers/specs/2026-11-23-retrofit-watch-modo-autonomo-design.md`

**Execução:** subagent-driven. Um subagente Opus com esforço `medium` implementa cada tarefa. Um Opus com esforço `xhigh` revisa cada uma. O plano passa por uma revisão do Fable antes da primeira tarefa (spec, seção 6).

## Global Constraints

- Trabalhar no worktree `~/.wt/retrofit-watch-autonomo`, ramo `feat/retrofit-watch-autonomo`. Nunca no checkout `~/repos/skills`. Nenhum `git push`, PR ou merge: são do dono.
- A loja é pública. Nenhum nome de projeto, empresa, pessoa, máquina ou usuário em arquivo nem em mensagem de commit. Caminho com `~`, nunca com o nome do usuário. `python3 scripts/check-private-names.py` sai 0 antes de cada commit. A mensagem ninguém varre: releia.
- Commit sem `Co-Authored-By` e sem "Generated with". Conferir: `git log -1 --format='%(trailers:key=Co-authored-by,valueonly)'` imprime nada.
- Só biblioteca padrão. Código novo não importa `fcntl`: a trava é o `_lock`/`_unlock` de `retrofit_watch.py`. Toda saída para stdout é `json.dumps` com ASCII (o stdout do Windows é cp1252). Caminho comparado passa pelo `_slashed`.
- O hook (`stop`, `baseline`, `pending`) tem 10 s de timeout: no caminho dele, nenhuma chamada de rede e nenhum `git fetch`. O hook nunca lança subagente.
- O padrão de `mode` é `manual`. Sem a config, a saída do hook é byte a byte a de hoje. `RETROFIT_WATCH=off` continua desligando tudo.
- Nenhum teste toca a rede, o `claude` real ou o `origin` real. A loja dos testes é a fixture da Tarefa 6: um repo `--bare` como `origin` e um clone. `publish()` recebe os efeitos (`push`, `refresh_install`, `cache_matches`) por parâmetro obrigatório. Só o `main()` constrói os efeitos reais.
- **Toda guarda nova tem um caso sabotado e um mutante morto.** Caso sabotado: a entrada que viola a guarda, com a asserção do motivo exato. Mutante: desligue a guarda no código, rode o teste nomeado na tabela da tarefa, veja-o falhar, restaure. O relatório da tarefa lista cada par mutante → teste que morreu.
- Texto de sabotagem (e-mail, caminho com usuário, forma de segredo, nome inventado) se monta em tempo de execução no teste, como o canário de `tests/test_private_names.py`. Literal no arquivo faria a camada 1 reprovar o próprio ramo (Tarefa 12).
- Leia o `rc` de cada comando sem pipe: saída para arquivo, `echo "rc=$?"`, depois leia o arquivo.
- Texto com barra invertida (regex, caminho Windows) entra por `Write` ou `Edit`, nunca por heredoc do shell.
- Versões: `retrofit-watch` 0.4.0 e `retrofit-skill` 0.11.0, com `CHANGELOG`, `plugin.json`, metadata do `SKILL.md` ou do comando, `marketplace.json` e README no mesmo incremento. Nenhum dos dois tem `codex` em `platforms` (`["claude-code"]` e `["claude-code", "cursor"]`): nenhum derivado Codex muda. A `description` e as `keywords` dos dois ficam como estão.
- Contratos em português, como o resto dos dois plugins. A `description` do agente e a seção do README em inglês, como as vizinhas. Nomes de teste: em inglês nos testes do plugin, em português em `tests/` da raiz, como os existentes.
- Limites da spec, seção 5.10: no máximo 2 retrofits autônomos por skill por sessão e 3 por sessão. Critério da v2, seção 5.9: pelo menos 10 publicados e 14 dias.
- Abreviações: `W=plugins/retrofit-watch/skills/retrofit-watch`, `R=plugins/retrofit-skill`, `<dados>` = `ctx.data_dir`.
- Suítes: `python3 $W/tests/<arquivo>.py` para um arquivo; `python3 -m unittest discover -s $W/tests -p 'test_*.py'` para o plugin; `python3 -m unittest discover -s tests -p 'test_*.py'` para a raiz.

## Decisões do planejador (spec, seção 8)

| # | Decisão |
|---|---|
| D1 | Sintaxe no `retrofit-skill`: `/retrofit-skill <plugin> --auto <dir do lote>`. |
| D2 | A unidade é o **lote**: `<plugin>` (tipo `auto`) ou `<plugin>__description` (tipo `description`). A porta vira `publish <id> <lote>`. Lotes do mesmo plugin rodam em sequência, o `auto` primeiro. |
| D3 | Arquivos por retro em `<dados>/auto/<id>/`: `pedido.json` (hook), `licoes.json` (sessão), `veredito.json` (revisor). Por lote, em `<dados>/auto/<id>/<lote>/`: `retrofit.json`, `termos-novos.json`, `anonimato.json`, `aprovado.json`. Chaves na Tarefa 5. |
| D4 | A camada 1 e a extração da camada 2 moram num script novo da raiz, `scripts/anonymity-gate.py`. A lista de públicos é `scripts/public-names.txt`, em texto puro. A colheita mora no plugin e entra por `--extra ARQUIVO`, de fora do repo. |
| D5 | `harvest_roots` padrão: `["~/repos"]`, profundidade 2. |
| D6 | A porta marca a retro como feita no estado da sessão. A sessão vem do `pedido.json` que o hook gravou. |
| D7 | A porta faz `fetch` e rebase **antes** das guardas, para que cada guarda leia o commit que sobe. A numeração dos motivos segue a spec. |
| D8 | Publicar é `git push origin HEAD:main` a partir do worktree do lote. O `main` local do checkout compartilhado não é tocado. |
| D9 | Guardas a mais na porta, nunca substituídas por aprovação: árvore limpa, um commit só, e caminhos dentro do escopo do retrofit. Os dois arquivos de lista só mudam com `aprovado.json`. |
| D10 | Auditoria na porta: a `skill-quality-audit` roda na base (extraída com `git archive`) e no commit. Qualquer linha `NOVO` do `audit_gate.py` segura. |
| D11 | A porta roda os testes do plugin (`plugins/<p>/tests` e `plugins/<p>/skills/*/tests`) e a suíte `tests/` da raiz. |
| D12 | O lote `description` também passa pela porta: ela recusa com `muda-description` e registra o ramo pronto. |
| D13 | Enquanto um pedido autônomo está aberto, o hook não conta trabalho nem atrito das skills dele. O pedido fecha quando toda lição tem linha no registro, ou em 6 h. |
| D14 | Órfão no aviso de startup: lote com `retrofit.json`, sem linha no registro, com pedido de mais de 1 h. |
| D15 | Os 14 dias do critério contam da primeira linha `publicado` sem aprovação. O startup não faz `fetch`: usa o `origin/main` local, que a porta atualiza. |
| D16 | A forma de segredo inclui sequência alfanumérica de 32 ou mais com letra e dígito. Um sha de 40 é achado; o sha curto passa. |
| D17 | A retro sob demanda (`/retrofit-watch:retrofit-watch <skill>`) continua manual: só o Stop hook abre um pedido autônomo. |
| D18 | A porta atualiza a cópia instalada só no escopo `user`. Outro escopo sai nomeado na linha. |

## Pendências do dono

A spec não decide estes três pontos, e a seção 8 dela não os deixa a quem constrói. O plano segue uma resposta provisória em cada um, isolada num lugar só.

| # | Pergunta | Provisório no plano | O que a resposta muda |
|---|---|---|---|
| P1 | De qual clone da loja saem os worktrees dos lotes? | Uma chave nova na config, `store`, com o caminho do clone. Sem ela, o modo `auto` não vale e o hook manda o texto manual com o motivo `sem-loja`. | `Context.store`, `rw_store.store_clone()` e dois testes (um na Tarefa 4, um na 6). |
| P2 | O anti-objetivo "regra nova embaixo de regra que já existe" ganha guarda mecânica? | Não. Só a instrução ao executor, na Tarefa 11. | Com guarda: uma pergunta a mais na tarefa *anonimato* do revisor, um campo no `anonimato.json` e uma guarda na porta (Tarefas 5, 7 e 10). |
| P3 | Lição com evidência não confirmada, ou na lista do que não capturar: segura ou descarta? | Segura, pela leitura literal da spec 5.4, que só lista três descartes. | Duas linhas da tabela de classificação da Tarefa 5. |

## Review Focus

1. **O fluxo atravessa vários turnos.** Subagente em segundo plano termina o turno, e o Stop hook dispara de novo no meio do fluxo, com erros de ferramenta no trecho novo. O dono espera silêncio, não outra retro. Teste na Tarefa 4.
2. **Duas portas ao mesmo tempo, de plugins diferentes.** As duas mexem no `marketplace.json` e no README. A segunda faz rebase sobre a primeira e publica, ou segura com `rebase`. Nunca um push forçado. Teste na Tarefa 8.
3. **JSON malformado escrito por um agente.** `veredito.json` com lição faltando, chave a mais, tipo errado, BOM ou cerca de código. O dono espera uma recusa com o campo nomeado, não um traceback. Teste na Tarefa 5.
4. **`origin` inalcançável.** `fetch` ou `push` falham. O dono espera uma linha `erro` com o motivo, rc diferente de 0 e o ramo intacto. Testes nas Tarefas 7 e 8.
5. **Saída com acento no stdio cp1252.** `held`, `triage` e `publish` imprimem motivo e caminho. O dono do Windows espera JSON válido. Teste nas Tarefas 5 e 8.

---

### Task 1: Conferir a base

**Files:** nenhum. Não há commit.

- [ ] **Step 1:** `git fetch origin` e `git rev-parse --short origin/main`. Esperado: `f099db4`.
- [ ] **Step 2:** Se o `origin/main` andou, `git rebase origin/main` no ramo. Com conflito, pare e relate.
- [ ] **Step 3:** Rode as linhas de base e anote os números no relatório.

| Comando | Esperado em 2026-11-23 |
|---|---|
| `python3 $W/tests/test_retrofit_watch.py` | `Ran 54 tests`, `OK` |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | `Ran 80 tests`, `OK (skipped=3)` |
| `python3 scripts/validate-versions.py` | rc 0, `All checks passed.` |
| `python3 scripts/check-private-names.py` | rc 0, `ok: nenhum dos 68 nomes na arvore` |

Número diferente depois de um rebase não é falha: anote o novo. Falha em qualquer linha para o plano.

---

### Task 2: `anonymity-gate.py` — a camada 1

**Files:**
- Create: `scripts/anonymity-gate.py`, `scripts/public-names.txt`
- Test: `tests/test_anonymity_gate.py`

**Interfaces:**
- Consumes: `scripts/check-private-names.py`, carregado por `importlib` como em `validate-versions.py`: `chave`, `_resumo`, `carregar`, `candidatos`, `arquivos`, `LISTA`.
- Produces:
  - `carregar_publicos(lista=PUBLICOS) -> set[str]`: cada linha normalizada por `cpn.chave`. Arquivo ausente dá conjunto vazio.
  - `linhas_novas(repo, base) -> list[tuple[str, int, str]]`: `(onde, linha, texto)` de cada linha acrescentada em `git diff -U0 --no-renames base...HEAD`, o caminho de cada arquivo novo como linha 0, e cada linha das mensagens de `base..HEAD` com `onde == "<mensagem>"`.
  - `camada1(repo, base, extras=frozenset(), hashes=None, publicos=None) -> list[tuple[str, int, str, str]]`: `(onde, linha, tipo, trecho)`, com `tipo` em `lista`, `colheita`, `email`, `caminho`, `segredo`.
  - CLI: `--camada1 --base REF [--repo DIR] [--extra ARQUIVO]`. rc 0 limpa, 1 com achados, 2 uso ou lista inutilizável. Uma linha por achado: `onde:linha: tipo "trecho"`, com o trecho em ASCII.
  - CLI: `--publico-add NOME`, `--publico-remove NOME`. `--publico-add` de um nome que está na lista de hashes sai 1.

**Regras que os testes fixam:**
- `lista`: forma candidata cujo hash está na lista da loja. `colheita`: forma candidata igual a `cpn.chave` de um termo de `--extra` (um por linha, `#` comenta).
- `email`: endereço com `@` e domínio com ponto.
- `caminho`: `/home/<u>`, `/Users/<u>`, `<letra>:\Users\<u>` e `/mnt/<x>/<pasta>`. O segmento capturado é isento quando começa com `<`, `$`, `%` ou `{`.
- `segredo`: os prefixos da seção 4 do `criteria.md` seguidos de 8 ou mais caracteres, e a sequência da D16. Depois de `Bearer` e de `Basic`, o que segue tem de ter 16 ou mais caracteres sem espaço e pelo menos um dígito. O arquivo `scripts/private-names.sha256` é isento só deste tipo.
- A lista de públicos isenta `lista`, `colheita`, `email` e o segmento de `caminho`. Nunca isenta `segredo`.
- `public-names.txt` nasce com os nomes da tabela *Identity* do `CLAUDE.md`: o dono no GitHub, a marca, o slug da loja e os dois nomes do repo.

- [ ] **Step 1: Escreva os testes que falham.** A fixture é um repo git temporário com um commit base e um commit novo. Modelo:

```python
def test_nome_da_colheita_na_mensagem_do_commit_e_achado(self):
    nome = 'cafe' + '_tutor'
    self.commit({'doc.md': 'limpo\n'}, mensagem=f'fix: medido no {nome}')
    achados = ag.camada1(self.repo, 'base', extras={nome})
    self.assertEqual([(a[0], a[2]) for a in achados], [('<mensagem>', 'colheita')])
```

| Teste | Entrada sabotada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_nome_da_lista_em_linha_nova_e_achado` | nome com hash na lista, numa linha acrescentada | um achado `lista` com caminho e linha certos | tirar a comparação de hash |
| `test_nome_da_colheita_na_mensagem_do_commit_e_achado` | acima | acima | não varrer a mensagem |
| `test_linha_antiga_nao_e_achado` | o nome já está no commit base, e o commit novo muda outra linha | `[]` | varrer o arquivo inteiro |
| `test_caminho_de_arquivo_novo_e_varrido` | arquivo novo com o nome no caminho | achado na linha 0 | pular a linha 0 |
| `test_email_e_achado` | endereço montado em tempo de execução | tipo `email` | tirar o padrão |
| `test_caminho_com_usuario_e_achado` | as quatro formas, uma por `subTest` | tipo `caminho` | tirar uma forma |
| `test_placeholder_de_caminho_passa` | `/home/<u>`, `/home/$USER` | `[]` | tirar a isenção |
| `test_forma_de_segredo_e_achado` | cada prefixo, e um sha de 40 | tipo `segredo` | tirar a sequência longa |
| `test_o_que_nao_e_segredo_passa` | sha de 7, caminho longo com data, `Basic authentication` | `[]` | tirar a exigência de letra e dígito |
| `test_publico_isenta_nome_e_nunca_segredo` | termo da colheita que está nos públicos; segredo que está nos públicos | `[]`; depois um achado `segredo` | isentar tudo |
| `test_a_lista_de_hashes_e_isenta_so_de_segredo` | hash novo em `private-names.sha256` | `[]` | isentar o arquivo de todos os tipos |
| `test_as_listas_reais_nao_se_cruzam` | os dois arquivos reais | nenhum público tem hash na lista | — |
| `test_publico_add_recusa_nome_privado` | `--publico-add` de nome da lista | rc 1, arquivo igual | tirar a recusa |
| `test_linha_de_comando` | repo limpo; repo com achado; lista ausente | rc 0; rc 1; rc 2 | — |

- [ ] **Step 2:** `python3 tests/test_anonymity_gate.py`. Esperado: falha por módulo ausente.
- [ ] **Step 3:** Implemente o script e a lista. O cabeçalho da lista diz como mudá-la.
- [ ] **Step 4:** Rode o arquivo de teste e a suíte da raiz. Esperado: `OK`.
- [ ] **Step 5:** Mate os mutantes da tabela, um por vez.
- [ ] **Step 6:** `python3 scripts/check-private-names.py` (rc 0) e commit: `feat(scripts): camada 1 do portão de anonimização`.

---

### Task 3: `anonymity-gate.py` — termos novos e varredura da árvore

**Files:**
- Modify: `scripts/anonymity-gate.py`, `CLAUDE.md` (parágrafo *Private names*)
- Test: `tests/test_anonymity_gate.py`

**Interfaces:**
- Consumes: `linhas_novas`, `carregar_publicos` (Tarefa 2).
- Produces:
  - `termos_novos(repo, base, publicos=None) -> list[dict]`: itens `{"termo", "onde", "contexto"}`, sem repetição de `termo`, na ordem de aparição. `onde` é `arquivo:linha` ou `<mensagem>`.
  - `varrer_arvore(raiz, extras, hashes=None, publicos=None) -> list[tuple[str, int, str, str]]`: só os tipos `lista` e `colheita`, sobre `cpn.arquivos(raiz)`.
  - CLI: `--termos --base REF [--repo DIR]` imprime a lista em JSON, rc 0. `--arvore [--extra ARQUIVO]` imprime os achados, rc 1 com achados.

**Regras que os testes fixam:**
- Candidato a termo: palavra com maiúscula fora do início da frase, CamelCase, palavra com dígito ou `_` dentro, caminho e URL.
- Fora dos candidatos: número, data, versão (`v1.2.3`, `0.4.0`) e sha em hexadecimal de 7 a 40.
- O termo é novo quando não existe na loja em `base` e não está nos públicos. A busca é uma chamada `git grep -F -i -w -q -e <termo> <base>` por termo distinto.

- [ ] **Step 1: Escreva os testes que falham.**

| Teste | Entrada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_nome_proprio_novo_e_termo` | linha nova com um nome inventado no meio da frase | o termo sai com `onde` e `contexto` | tirar a regra da maiúscula |
| `test_identificador_novo_e_termo` | CamelCase, `com_sublinhado`, `abc9def`, um caminho, uma URL | os cinco saem | tirar uma regra |
| `test_termo_que_a_loja_ja_tem_nao_sai` | o mesmo nome já num arquivo do commit base, em outra caixa | `[]` | tirar o `-i` ou a busca |
| `test_pedaco_de_palavra_da_loja_ainda_e_novo` | a loja tem `Acmecorp`, a linha nova tem `Acme` | `Acme` sai | tirar o `-w` |
| `test_publico_nao_sai` | termo dos públicos | `[]` | — |
| `test_numero_data_versao_e_sha_nao_saem` | `0.4.0`, `2026-11-23`, `v1.2.3`, sha de 7 | `[]` | tirar a exclusão |
| `test_termo_da_mensagem_sai` | nome novo só na mensagem | `onde == "<mensagem>"` | não ler a mensagem |
| `test_inicio_de_frase_nao_e_termo` | `Depois rode o teste.` | `[]` | — |
| `test_a_arvore_com_a_colheita` | arquivo antigo com um termo de `--extra` | achado `colheita`; com o termo nos públicos, `[]` | varrer só o diff |
| `test_a_arvore_nao_aplica_os_padroes` | arquivo antigo com caminho de usuário | `[]` | — |

- [ ] **Step 2:** Rode. Esperado: falha por função ausente.
- [ ] **Step 3:** Implemente as duas funções e os dois modos da CLI.
- [ ] **Step 4:** Acrescente duas frases ao parágrafo *Private names* do `CLAUDE.md`: o `anonymity-gate.py` varre as linhas novas e a mensagem do commit quando é chamado, e a lista de públicos muda por `--publico-add` e `--publico-remove`. A frase "nothing scans the commit message" passa a dizer que nenhum gate de commit manual a varre.
- [ ] **Step 5:** Rode a suíte da raiz e o `validate-versions.py`. Esperado: `OK` e rc 0.
- [ ] **Step 6:** Mate os mutantes. `check-private-names.py` rc 0. Commit: `feat(scripts): termos novos e varredura da árvore no portão de anonimização`.

---

### Task 4: O modo na config, o pedido e o texto do hook

**Files:**
- Create: `$W/scripts/rw_auto.py`, `$W/tests/test_auto_mode.py`
- Modify: `$W/scripts/retrofit_watch.py` (`Context`, `_full`, `Scanner._bump`, `build_output`, `cmd_stop`, o fim do arquivo), `$W/tests/test_retrofit_watch.py` (só a extração do arnês)

**Interfaces:**
- Produces, em `retrofit_watch.py`:
  - `Context.mode -> str`: `manual`, `auto` ou `auto-dry`. Valor inválido ou ausente dá `manual`.
  - `Context.manual -> set[str]`, `Context.auto_limits -> dict` (padrão `{"per_skill": 2, "per_session": 3}`, fundido com a config), `Context.store -> Path | None` (P1), `Context.harvest_roots -> list[Path]` (D5), `Context.private_sources -> list[Path]`.
  - `_full` acrescenta `"skill": skill` à entrada. Estado antigo sem a chave se lê com `.get`.
  - `build_output(entries, auto_text=None, reasons=None)`: sem os dois argumentos novos, a saída é a de hoje.
  - Última linha antes do `if __name__`: `sys.modules.setdefault("retrofit_watch", sys.modules[__name__])`, para o `import retrofit_watch` dos módulos novos não carregar uma segunda cópia.
  - `class HookHarness` em `test_retrofit_watch.py`, com `write`, `run_hook` e `context_of` tirados de `StopTest`. `StopTest(HookHarness, unittest.TestCase)` mantém os 54 testes.
- Produces, em `rw_auto.py`:
  - `AUTO_DIR = "auto"`, `REGISTRY = "autonomo.jsonl"`, `AUTO_OPEN_TTL = 6 * 3600`, `FINAL = {"publicado", "segurado", "descartado", "erro"}`.
  - `new_id(session_id, now=None) -> str`: `AAAAMMDD-HHMMSS-<8 caracteres seguros da sessão>`.
  - `retro_dir(ctx, rid) -> Path`, `lote_dir(ctx, rid, lote) -> Path`. Os dois recusam `rid` ou `lote` fora de `^[A-Za-z0-9][A-Za-z0-9_.-]*$` com `Malformed`.
  - `class Malformed(Exception)`.
  - `read_registry(ctx) -> list[dict]`, `append_registry(ctx, line: dict) -> dict` (acrescenta `ts`, sob `_lock` de `<dados>/autonomo.lock`).
  - `used(registry, session, plugin=None, skip=None) -> int`: pares `(id, plugin)` distintos das linhas de lote (item sem `#`) da sessão.
  - `why_manual(ctx, payload, entry, registry) -> str | None`. `None` quer dizer que o modo autônomo vale. Motivos, na ordem: `modo`, `kit-ou-lean`, `lista-manual`, `permissao`, `sem-loja`, `teto`.
  - `open_request(ctx, payload, entries) -> dict`: grava `pedido.json` com `id`, `sessao`, `ts`, `transcript`, `modo` e `skills` (`key`, `plugin`, `label`).
  - `auto_text(ctx, pedido, entries) -> str`.
  - `flow_finished(ctx, pedido) -> bool`: `licoes.json` ausente, ou toda lição dele aparece em `licoes` de alguma linha do registro com aquele `id`.

**Comportamento do `cmd_stop`:**
- `rw_auto` só é importado quando `ctx.mode != "manual"`.
- Para cada entrada pronta, `why_manual` decide. As autônomas entram num pedido só. As manuais saem com o texto de hoje, no mesmo `additionalContext`.
- Ao pedir, grava `st["auto_open"] = {"id", "keys", "ts"}`. Enquanto existe e tem menos de `AUTO_OPEN_TTL`, `_bump` não conta para as chaves dele.
- O fechamento é conferido **depois** da varredura do trecho. No Stop de continuação (`stop_hook_active`), `licoes.json` ausente fecha o pedido.
- `systemMessage` no modo autônomo: `retrofit-watch: retro de <nomes> pedida ao Claude, modo autônomo (<id>)`. Com `mode` diferente de `manual` e a entrada caindo no manual por `permissao`, `sem-loja` ou `teto`, a mensagem de hoje ganha ` — modo manual: <motivo por extenso>`. O texto de `permissao` cita `bypassPermissions`.

**O texto autônomo contém, e os testes conferem:** o caminho absoluto de `<dados>/auto/<id>/licoes.json`; o caminho absoluto de `$W/references/modo-autonomo.md` e de `retrofit_watch.py`; a ordem de fazer a retro pelas seções 1 a 4 do `criteria.md`; a resposta `retro <label>: sem lições novas` sem gravar nada; a proibição de perguntar ao dono, de rodar o `/retrofit-skill` nesta sessão e de citar valor de segredo; quantos retrofits restam na sessão.

- [ ] **Step 1: Extraia o `HookHarness`** e rode `test_retrofit_watch.py`. Esperado: `Ran 54 tests`, `OK`.
- [ ] **Step 2: Escreva os testes que falham** em `test_auto_mode.py`. Modelo:

```python
class AutoStopTest(HookHarness, unittest.TestCase):
    def config(self, **keys):
        (self.w.home / ".claude/retrofit-watch.json").write_text(json.dumps(keys))

    def test_auto_request_names_absolute_paths_and_writes_pedido(self):
        self.config(mode="auto", store=str(self.w.repo))
        self.write(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), *[tool()] * 6)
        out = self.run_hook(mode="bypassPermissions")
        pedido = next((self.w.data / "auto").glob("*/pedido.json"))
        text = self.context_of(out)
        self.assertIn(str(pedido.parent / "licoes.json"), text)
        self.assertIn("modo-autonomo.md", text)
        self.assertNotIn("Rodo /retrofit-skill", text)
        self.assertEqual(json.loads(pedido.read_text())["skills"][0]["plugin"], "codereview")
```

| Teste | Entrada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_default_mode_is_manual_and_text_is_unchanged` | sem config, `bypassPermissions` | texto com `/retrofit-skill:retrofit-skill codereview`; `<dados>/auto` não existe | padrão `auto` |
| `test_invalid_mode_is_manual` | `mode: "sempre"` | como acima | aceitar qualquer valor |
| `test_auto_needs_bypass_permissions` | `mode: auto`, modo `default` | texto manual; `systemMessage` com `bypassPermissions` | tirar o `permissao` |
| `test_auto_request_names_absolute_paths_and_writes_pedido` | acima | acima | — |
| `test_manual_list_kit_and_lean_stay_manual` | uma skill da loja, uma lean e uma em `manual`, no mesmo Stop | um pedido só com a da loja; o texto manual das outras duas presente | tirar `kit-ou-lean` ou `lista-manual` |
| `test_auto_dry_is_requested_like_auto` | `mode: auto-dry` | `pedido["modo"] == "auto-dry"` | — |
| `test_store_missing_or_not_the_marketplace_is_manual` | sem `store`; `store` num repo de terceiro | texto manual, motivo `sem-loja` | tirar a conferência do `marketplace.json` |
| `test_session_cap_reached_asks_manually` | 3 linhas de lote da sessão no registro | texto manual, motivo `teto` | trocar `>=` por `>` |
| `test_flow_in_progress_counts_no_work_or_friction` | depois do pedido: `licoes.json` gravado, 6 erros de ferramenta, Stop novo sem `stop_hook_active` | `None`; `work == friction == 0` no estado | tirar o silêncio do `_bump` |
| `test_flow_without_lessons_closes_at_the_continuation_stop` | Stop com `active=True`, sem `licoes.json` | `auto_open` sai do estado | — |
| `test_flow_closes_when_every_lesson_has_a_line` | linhas no registro para todas as lições; depois 2 erros | o segundo Stop fecha; o terceiro pede a 2ª retro | fechar antes de varrer |
| `test_stale_open_flow_expires` | `auto_open.ts` com 7 h | o atrito volta a contar | tirar o TTL |
| `test_auto_text_stays_ascii_on_cp1252_stdout` | `env=WINDOWS_STDIO` | a saída é JSON válido | — |
| `test_new_modules_do_not_import_fcntl` | o fonte de cada `rw_*.py` | `"fcntl"` ausente | — |

- [ ] **Step 3:** Rode. Esperado: falha por `rw_auto` ausente.
- [ ] **Step 4:** Implemente.
- [ ] **Step 5:** Rode os dois arquivos de teste. Esperado: `OK`, e os 54 antigos continuam.
- [ ] **Step 6:** Mate os mutantes. `check-private-names.py` rc 0. Commit: `feat(retrofit-watch): modo auto na config e pedido autônomo no Stop hook`.

---

### Task 5: Os formatos, a triagem e os verbos do registro

**Files:**
- Modify: `$W/scripts/rw_auto.py`, `$W/scripts/retrofit_watch.py` (`main`)
- Test: `$W/tests/test_auto_formats.py`

**Formatos (D3):**

| Arquivo | Conteúdo |
|---|---|
| `licoes.json` | `{"id", "licoes": [{"n", "plugin", "skill", "tipo", "evidencia": {"texto", "transcript", "entrada"}, "padrao", "resolveu", "muda_description"}]}`. `tipo` é `pitfall` ou `melhoria`. `resolveu: null` é "sem correção verificada". |
| `veredito.json` | `{"id", "base", "licoes": [{"n", "evidencia_confere", "coberta", "generica", "procede", "basta_o_transcript", "nao_capturar", "nota"}]}`. `procede` é `procede`, `nao-procede` ou `nao-reproduzivel`. `coberta` é `null` ou `arquivo:linha`. |
| `retrofit.json` | `{"id", "lote", "plugin", "tipo", "worktree", "ramo", "base", "licoes", "commit", "versao"}` |
| `termos-novos.json` | `{"commit", "termos": [{"termo", "onde", "contexto"}]}` |
| `anonimato.json` | `{"commit", "termos": [{"termo", "veredito", "nota"}]}`. `veredito` é `publico`, `privado` ou `duvida`. |
| `aprovado.json` | `{"id", "lote", "ts", "motivo"}` |
| linha de `autonomo.jsonl` | `{"ts", "sessao", "id", "lote", "plugin", "item", "licoes", "resultado", "motivo", "detalhe", "commit", "ramo", "worktree", "versao", "aprovado"}`. `item` é `<id>/<lote>` no lote e `<id>/<plugin>#<n>` na lição sem ramo. |

**A classificação (spec 5.4), a primeira condição que casar:**

| Condição | Destino | Motivo |
|---|---|---|
| lição sem parecer no veredito | `segurar` | `sem-veredito` |
| `coberta` preenchida | `descartar` | `coberta` |
| `generica` falso | `descartar` | `do-projeto` |
| `procede == "nao-procede"` | `descartar` | `nao-procede` |
| `evidencia_confere` falso | `segurar` | `sem-evidencia` |
| `nao_capturar` preenchido | `segurar` | `nao-capturar` |
| `nao-reproduzivel` e `basta_o_transcript` nulo | `segurar` | `nao-reproduzivel` |
| `resolveu` nulo | `segurar` | `sem-correcao` |
| `muda_description` verdadeiro | `ramo-pronto` | `muda-description` |
| o resto | `publicar` | — |

**Interfaces:**
- Consumes: `Malformed`, `retro_dir`, `lote_dir`, `read_registry`, `append_registry` (Tarefa 4).
- Produces, em `rw_auto.py`:
  - `LICAO_KEYS`, `EVIDENCIA_KEYS`, `PARECER_KEYS`, `TERMO_KEYS`, `ANONIMATO_KEYS`: conjuntos com as chaves da tabela.
  - `LESSON_REASONS`: os motivos da tabela de classificação e `descartado-pelo-dono`. `AGENT_REASONS = {"executor-falhou", "executor-recusou"}`.
  - `load_licoes(path) -> dict[str, dict]` e `load_veredito(path) -> dict[str, dict]`, por `n`. `Malformed` nomeia o arquivo e o campo.
  - `classify(licao, parecer) -> tuple[str, str | None]`.
  - `triage(ctx, rid) -> dict`: `{"lotes": [{"lote", "plugin", "tipo", "licoes"}], "segurar": [...], "descartar": [...]}`. Os lotes `auto` vêm antes dos `description`. Grava uma linha `segurado` ou `descartado` por lição sem ramo. Rodar de novo não repete linha.
  - `last_lines(registry) -> dict[str, dict]`: a última linha de cada `item`.
  - `held(ctx) -> list[dict]`: os itens cuja última linha é `segurado` ou `erro`.
  - `hold_item(ctx, rid, item, motivo, detalhe="") -> dict`: linha `segurado` para o que o agente da sessão segura. Motivo fora de `AGENT_REASONS` é `Malformed`.
  - `approve(ctx, rid, lote) -> Path`: grava `aprovado.json` com o `motivo` da última linha `segurado` do lote. Sem ela, `Malformed`.
  - `discard(ctx, rid, item) -> dict`: linha `descartado` com motivo `descartado-pelo-dono`.
- Produces, em `retrofit_watch.py`: `cli(argv, ctx) -> int` para os subcomandos de linha de comando (`queue` e os novos). rc 0 certo, 1 recusado, 2 uso ou `Malformed` (mensagem no stderr, sem traceback). Nesta tarefa: `triage <id>`, `held`, `hold <id> <item> <motivo>`, `approve <id> <lote>`, `discard <id> <item>`. Todos imprimem JSON em ASCII.

- [ ] **Step 1: Escreva os testes que falham.**

| Teste | Entrada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_classification_table` | uma linha da tabela por `subTest`, mudando um campo de uma lição publicável | o destino e o motivo da linha | tirar cada condição, uma por vez |
| `test_covered_wins_over_description` | `coberta` e `muda_description` juntos | `descartar` | trocar a ordem |
| `test_triage_splits_lotes_and_orders_auto_first` | plugin A com 2 publicáveis e 1 de `description`; plugin B com 1 publicável | lotes `A`, `B`, `A__description`, nessa ordem | juntar tudo num lote |
| `test_triage_writes_held_and_discarded_lines_once` | 1 `sem-correcao`, 1 `coberta`; duas chamadas | 2 linhas no registro, não 4 | tirar a idempotência |
| `test_malformed_verdict_is_a_refusal_not_a_traceback` | chave a mais; `procede` fora do domínio; BOM; cerca de código; lista no lugar de objeto | `Malformed` nomeando o campo; pela CLI, rc 2 e stderr sem `Traceback` | tirar a validação de domínio |
| `test_lesson_missing_from_verdict_is_held` | `veredito.json` sem a `L2` | `L2` em `segurar` com `sem-veredito` | tratar ausente como publicável |
| `test_path_traversal_in_id_or_lote_is_refused` | `../x` | `Malformed` | tirar o padrão |
| `test_held_lists_only_open_items` | um segurado, um segurado e depois publicado, um descartado | só o primeiro | ler a primeira linha em vez da última |
| `test_approve_needs_a_held_lote` | lote sem linha `segurado` | rc 2; `aprovado.json` ausente | — |
| `test_approve_copies_the_reason_that_held` | lote segurado por `teto` | `aprovado.json` com `motivo == "teto"` | — |
| `test_cli_output_is_valid_json_on_cp1252` | `held` com detalhe acentuado, `PYTHONIOENCODING=cp1252` | rc 0 e JSON válido | `ensure_ascii=False` |

- [ ] **Step 2:** Rode. Esperado: falha por função ausente.
- [ ] **Step 3:** Implemente.
- [ ] **Step 4:** Rode a suíte do plugin. Esperado: `OK`.
- [ ] **Step 5:** Mate os mutantes. `check-private-names.py` rc 0. Commit: `feat(retrofit-watch): formatos, triagem e registro do modo autônomo`.

---

### Task 6: A loja fixture, a colheita, `prepare` e `seal`

**Files:**
- Create: `$W/scripts/rw_store.py`, `$W/tests/fixture_store.py`, `$W/tests/test_auto_store.py`
- Modify: `$W/scripts/retrofit_watch.py` (`cli`)

**Interfaces:**
- Consumes: `Context.store`, `Context.harvest_roots`, `Context.private_sources` (Tarefa 4); `triage`, `classify`, `lote_dir` (Tarefa 5); a CLI do `scripts/anonymity-gate.py` (Tarefas 2 e 3).
- Produces, em `fixture_store.py`:
  - `class StoreWorld(World)`: `origin` (repo `--bare`), `store` (o clone, que faz o papel do checkout compartilhado), o plugin `demo` 1.0.0 com `SKILL.md`, `CHANGELOG.md`, `skills/demo/tests/test_demo.py`, bloco no `marketplace.json` e linha no README. A raiz traz as cópias de `scripts/` da loja real, o `install.py`, o auditor da `skill-quality-audit`, o `audit_gate.py` do `retrofit-skill` e um `tests/test_root.py` mínimo. A config do HOME fixture tem `mode: auto` e `store`.
  - `StoreWorld.retro(licoes, pareceres) -> str`: grava `pedido.json`, `licoes.json` e `veredito.json` e devolve o `id`.
  - `StoreWorld.retrofit(wt, files, message=None, version="1.0.1", trailer="Retrofit-Mode: autonomous") -> str`: faz no worktree um commit de retrofit completo (arquivos, `plugin.json`, metadata do `SKILL.md`, `CHANGELOG`, `marketplace.json`, README) e devolve o sha.
  - `StoreWorld.origin_main() -> str` e `StoreWorld.shared_state() -> tuple`: (HEAD, ramo atual, `status --porcelain`) do clone.
  - Os testes que usam a fixture pulam quando a raiz da loja real não está acima do arquivo (cópia instalada) ou quando falta o PyYAML.
- Produces, em `rw_store.py`:
  - `class StoreError(Exception)`.
  - `store_clone(ctx) -> Path` (P1): o `store` da config, quando é um clone cujo `marketplace.json` tem o nome da loja. Senão, `StoreError`.
  - `harvest(ctx) -> set[str]`: o nome da pasta de cada repo git sob `harvest_roots` até a profundidade 2, o dono e o nome de cada `origin`, o `user.name` e o e-mail do git, o nome da pasta do HOME, o hostname, e cada linha das `private_sources`.
  - `write_harvest(ctx) -> Path`: grava `<dados>/colheita.txt`, um termo por linha, com permissão `0o600`.
  - `prepare(ctx, rid, lote) -> dict`: `git fetch origin` no clone; `git worktree add -b retrofit-auto/<lote>-<rid> ~/.wt/retrofit-auto-<lote>-<rid> origin/main`; grava e devolve o `retrofit.json`. Chamado de novo para o mesmo lote, devolve o que já existe.
  - `layer1(ctx, worktree) -> list[str]` e `new_terms(worktree) -> list[dict]`: chamam `python3 <worktree>/scripts/anonymity-gate.py` com `--base origin/main`. O primeiro passa `--extra` com a colheita.
  - `seal(ctx, rid, lote, licoes: list[str]) -> dict`: confere que cada lição é do lote pela triagem; completa `retrofit.json` com `licoes`, `commit` e `versao`; grava `termos-novos.json`; roda a camada 1. Devolve `{"commit", "versao", "termos", "camada1"}`.
- Produces, na CLI: `prepare <id> <lote>` e `seal <id> <lote> --licoes L1,L2` (rc 1 com achado da camada 1), e `harvest`, que imprime só `{"termos": N, "arquivo": "<caminho>"}`.

- [ ] **Step 1: Escreva a fixture e os testes que falham.**

| Teste | Entrada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_fixture_store_passes_its_own_gates` | a loja fixture recém-criada | `validate-versions.py` rc 0; os testes do `demo` passam; o `origin` é um caminho sob o diretório temporário | — |
| `test_prepare_creates_a_linked_worktree_from_origin_main` | outro clone avança o `origin` antes | o worktree fica sob `<home>/.wt`; o ramo é `retrofit-auto/demo-<id>`; `base` é o sha novo do `origin/main` | tirar o `fetch` |
| `test_prepare_leaves_the_shared_checkout_untouched` | arquivo sujo no clone | `shared_state()` igual antes e depois | criar o ramo com `checkout -b` no clone |
| `test_prepare_is_idempotent` | duas chamadas | o mesmo `retrofit.json`; um worktree só | — |
| `test_store_missing_is_an_error_with_the_reason` | config sem `store`; `store` apontando para um repo de terceiro | `StoreError`; pela CLI, rc 2 | aceitar qualquer repo git |
| `test_harvest_collects_every_source` | HOME fixture com 2 repos, um não-repo, `.gitconfig` e uma `private_sources` | cada fonte da lista aparece; a pasta que não é repo não | tirar uma fonte |
| `test_harvest_respects_depth_and_survives_bad_roots` | repo no nível 3; raiz inexistente | o do nível 3 fica fora; nenhuma exceção | — |
| `test_harvest_cli_prints_no_name` | `harvest` pela CLI | stdout sem nenhum termo colhido; o arquivo existe fora de qualquer repo | imprimir a lista |
| `test_seal_writes_terms_and_reports_layer1` | commit com um nome colhido numa linha nova | rc 1; `camada1` nomeia arquivo e linha; `termos-novos.json` existe | não passar `--extra` |
| `test_seal_refuses_a_lesson_from_another_lote` | `--licoes` com a lição de `description` no lote `auto` | rc 2; `retrofit.json` sem `commit` | tirar a conferência |

- [ ] **Step 2:** Rode. Esperado: falha por módulo ausente.
- [ ] **Step 3:** Implemente.
- [ ] **Step 4:** Rode a suíte do plugin. Esperado: `OK`.
- [ ] **Step 5:** Mate os mutantes. `check-private-names.py` rc 0. Commit: `feat(retrofit-watch): colheita, worktree do lote e selo do executor`.

---

### Task 7: A porta — as recusas

**Files:**
- Create: `$W/scripts/rw_gate.py`, `$W/tests/test_auto_gate.py`

**Interfaces:**
- Consumes: `StoreWorld` (Tarefa 6); `load_licoes`, `load_veredito`, `classify`, `used`, `append_registry` (Tarefas 4 e 5); `layer1`, `new_terms` (Tarefa 6).
- Produces:
  - `OVERRIDABLE = {"sem-veredito", "nao-publicavel", "muda-description", "sem-anonimato", "termo-nao-publico", "teto", "auto-dry"}`.
  - `ERRORS = {"fetch", "push", "update", "cache-difere"}`. `GATE_REASONS`: os motivos da tabela abaixo e os de `ERRORS`.
  - `SCOPE` (prefixos e arquivos que um retrofit pode tocar: `plugins/<plugin>/`, `.claude-plugin/marketplace.json`, `README.md`, `.agents/plugins/marketplace.json`, `docs/codex/compatibility.md`, `docs/codex/smokes.json`) e `OWNER_ONLY = ("scripts/private-names.sha256", "scripts/public-names.txt")`.
  - `refuse(ctx, rid, lote) -> tuple[str, str] | None`: `(motivo, detalhe)` da primeira guarda que reprova, ou `None`.
  - `hold(ctx, rid, lote, motivo, detalhe) -> dict`: grava a linha `segurado`, ou `erro` quando o motivo está em `ERRORS`, e a devolve.

**A ordem das guardas em `refuse` (D7, D9):**

| Ordem | Guarda | Motivo | Item da spec 5.7 |
|---|---|---|---|
| 1 | o worktree é um clone da loja e o ramo é o do `retrofit.json`; `git status --porcelain` vazio | `escopo`, `arvore-suja` | D9 |
| 2 | `git fetch origin` | `fetch` | 6 |
| 3 | `git rebase origin/main`; com conflito, `git rebase --abort` | `rebase` | 6 |
| 4 | um commit só em `origin/main..HEAD`; cada caminho em `SCOPE`; `OWNER_ONLY` só com `aprovado.json` | `escopo` | D9 |
| 5 | o commit não tem `Co-authored-by` | `coautoria` | 5 |
| 6 | o trailer `Retrofit-Mode` é `autonomous`; com `aprovado.json`, também vale `autonomous-approved` | `sem-marca` | 5 |
| 7 | `veredito.json` existe e é válido | `sem-veredito` | 1 |
| 8 | cada lição do `retrofit.json` classifica como `publicar`; no lote `description`, `ramo-pronto` reprova com `muda-description` | `nao-publicavel`, `muda-description` | 1 |
| 9 | `layer1` vazia | `nome-privado` | 3 |
| 10 | `anonimato.json` existe | `sem-anonimato` | 2 |
| 11 | cada termo de `new_terms`, recalculado agora, está no `anonimato.json` como `publico` | `termo-nao-publico` | 2 |
| 12 | os testes do plugin e os da raiz passam (D11) | `testes` | 4 |
| 13 | `python3 scripts/validate-versions.py` rc 0 | `validate-versions` | 4 |
| 14 | nenhuma linha `NOVO` do `audit_gate.py`, para cada skill do plugin (D10) | `auditoria` | 4 |
| 15 | `used` abaixo de `auto_limits`, sem contar este lote | `teto` | 7 |
| 16 | `ctx.mode` não é `auto-dry` | `auto-dry` | 8 |

Com `aprovado.json`, a guarda cujo motivo é igual ao `aprovado["motivo"]` é pulada, e só quando o motivo está em `OVERRIDABLE`. Todas as outras rodam. `retrofit.json` ausente ou inválido é `Malformed` (rc 2), sem linha no registro.

- [ ] **Step 1: Escreva os testes que falham.** Cada teste parte de `clean_retrofit(**sabotagem) -> (rid, worktree)`, um auxiliar da classe de teste que monta um retrofit limpo do `demo` com veredito, selo e `anonimato.json`, e sabota uma coisa. Todos terminam conferindo que `origin_main()` não mudou. Modelo:

```python
def test_co_authored_by_refuses(self):
    rid, wt = self.clean_retrofit(message="fix(demo): v1.0.1\n\nCo-Authored-By: " + "x <x" + "@" + "x.dev>")
    self.assertEqual(rg.refuse(self.ctx, rid, "demo")[0], "coautoria")
    self.assertEqual(self.w.origin_main(), self.base)
```

| Teste | Sabotagem | Motivo esperado | Mutante que ele mata |
|---|---|---|---|
| `test_clean_retrofit_passes_every_guard` | nenhuma | `refuse` devolve `None` | — |
| `test_dirty_worktree_refuses` | arquivo sem commit no worktree | `arvore-suja` | guarda 1 |
| `test_branch_other_than_the_lote_refuses` | o worktree em outro ramo | `escopo` | tirar a conferência do ramo |
| `test_unreachable_origin_is_an_error_not_a_pass` | URL do `origin` trocada por um caminho que não existe | `fetch`; `hold` grava `erro` | tratar falha do `fetch` como "em dia" |
| `test_rebase_conflict_refuses_and_leaves_the_branch_intact` | outro clone muda a mesma linha no `origin` | `rebase`; o HEAD do worktree é o de antes; nenhum rebase em andamento | tirar o `--abort` |
| `test_rebase_over_unrelated_commits_passes` | outro clone muda outro arquivo | `None`; o HEAD do worktree tem o `origin/main` novo como pai | — |
| `test_two_commits_refuse` | segundo commit no ramo | `escopo` | guarda 4, contagem |
| `test_path_outside_scope_refuses` | o commit toca `scripts/check-private-names.py` | `escopo` | guarda 4, caminhos |
| `test_list_files_need_owner_approval` | o commit toca `scripts/public-names.txt` | `escopo`; com `aprovado.json`, passa desta guarda | `OWNER_ONLY` sempre permitido |
| `test_co_authored_by_refuses` | acima | `coautoria` | guarda 5 |
| `test_commit_without_marker_refuses` | `trailer=None` | `sem-marca` | guarda 6 |
| `test_missing_verdict_refuses` | sem `veredito.json` | `sem-veredito` | guarda 7 |
| `test_lesson_not_publishable_refuses` | lição com `resolveu` nulo no `retrofit.json` | `nao-publicavel` | guarda 8 |
| `test_description_lote_is_held_as_ready_branch` | lote `demo__description` | `muda-description`; a linha de `hold` tem o ramo | — |
| `test_private_name_in_diff_refuses` | nome inventado com hash acrescentado à lista da fixture | `nome-privado` | guarda 9 |
| `test_harvested_name_in_commit_message_refuses` | nome de um repo do HOME fixture na mensagem | `nome-privado` | passar a colheita vazia |
| `test_missing_anonimato_refuses` | sem `anonimato.json` | `sem-anonimato` | guarda 10 |
| `test_term_in_doubt_refuses` | um termo com `duvida` | `termo-nao-publico` | aceitar `duvida` |
| `test_term_added_after_the_review_refuses` | emenda o commit com um nome novo depois do `anonimato.json` | `termo-nao-publico` | ler `termos-novos.json` em vez de recalcular |
| `test_failing_plugin_test_refuses` | o commit quebra `test_demo.py` | `testes` | guarda 12 |
| `test_failing_root_test_refuses` | `tests/test_root.py` que falha, vindo do `origin` | `testes` | pular a suíte da raiz |
| `test_version_out_of_sync_refuses` | `plugin.json` em 1.0.1 e `marketplace.json` em 1.0.0 | `validate-versions` | guarda 13 |
| `test_new_audit_finding_refuses` | o commit põe um campo de topo fora da spec no `SKILL.md` | `auditoria` | guarda 14 |
| `test_old_audit_debt_does_not_refuse` | o mesmo defeito já no `origin/main` | `None` | comparar sem a base |
| `test_caps_refuse` | 2 linhas de outros ids do `demo` na sessão; 3 lotes de outros plugins; `auto_limits` na config mudando o teto | `teto`, `teto`, `None` | trocar `>=` por `>` |
| `test_auto_dry_refuses_last` | `mode: auto-dry` com um retrofit limpo; depois com um teste quebrado | `auto-dry`; depois `testes` | pôr a guarda 16 no começo |
| `test_approval_replaces_only_the_item_that_held` | `aprovado.json` com `muda-description` e um teste quebrado | `testes` | pular todas as guardas com aprovação |
| `test_approval_never_replaces_items_3_to_6` | `aprovado.json` com motivo `nome-privado`, e o nome ainda no diff | `nome-privado` | tirar a conferência de `OVERRIDABLE` |

- [ ] **Step 2:** Rode. Esperado: falha por módulo ausente.
- [ ] **Step 3:** Implemente `refuse` e `hold`. A base da auditoria sai de `git archive origin/main plugins/<plugin>`, lida com `tarfile`.
- [ ] **Step 4:** Rode a suíte do plugin. Esperado: `OK`. Anote o tempo do arquivo novo no relatório.
- [ ] **Step 5:** Mate os mutantes da tabela, um por vez.
- [ ] **Step 6:** `check-private-names.py` rc 0. Commit: `feat(retrofit-watch): as guardas da porta de publicação`.

---

### Task 8: A porta — publicar, liberar e registrar

**Files:**
- Modify: `$W/scripts/rw_gate.py`, `$W/scripts/retrofit_watch.py` (`cli`)
- Test: `$W/tests/test_auto_gate.py`

**Interfaces:**
- Consumes: `refuse`, `hold`, `OVERRIDABLE` (Tarefa 7); `State`, `_lock`, `_unlock`, `MAX_REVIEWS` de `retrofit_watch.py`.
- Produces:
  - `class Effects`, com `push(worktree) -> tuple[bool, str]` (`git push origin HEAD:main`, sem força), `refresh_install(plugin) -> tuple[bool, str]` (`claude plugin marketplace update <loja>` e `claude plugin update <plugin>@<loja> --scope user`; sem o `claude` no PATH, `(False, "claude ausente")`; plugin fora do escopo `user`, `(True, "nao-instalado")`) e `cache_matches(ctx, worktree, plugin, versao) -> tuple[bool, str]` (compara `plugins/<plugin>` do worktree com `~/.claude/plugins/cache/<loja>/<plugin>/<versao>`, fora o `.in_use`).
  - `publish(ctx, rid, lote, effects) -> dict`: a linha gravada no registro. `effects` é obrigatório.
  - `mark_done(ctx, session, key) -> None`: no estado da sessão, sob a trava dele, põe a chave em `done` e `reviews = MAX_REVIEWS`.
  - CLI: `publish <id> <lote>`. rc 0 `publicado`, 1 `segurado`, 3 `erro`, 2 uso. Imprime a linha em JSON e, na última linha do stdout, a frase da spec 5.1: `retrofit-watch: <plugin> vX.Y.Z publicada sozinha (<sha>)` ou `retrofit-watch: <plugin> segurada — <motivo> (ramo <ramo>)`, em ASCII com escape.

**A sequência de `publish`:**
1. Prende `<dados>/publish.lock` até o fim.
2. `refuse`. Com recusa, `hold` e fim.
3. Com `aprovado.json`: troca o trailer por `Retrofit-Mode: autonomous-approved` com `commit --amend`. A árvore do commit tem de ficar igual.
4. `effects.push`. Falha: linha `erro`, motivo `push`.
5. `effects.refresh_install`. Falha: linha `erro`, motivo `update`, com o `commit`.
6. `effects.cache_matches`, quando o plugin está instalado. Diferença: linha `erro`, motivo `cache-difere`, com o `commit`.
7. Linha `publicado`, com `commit`, `versao`, `ramo`, `licoes` e `aprovado`. `mark_done` para a sessão do `pedido.json`.

- [ ] **Step 1: Escreva os testes que falham.** `FixtureEffects(Effects)` herda o `push` real, que cai no `origin` da fixture, e troca `refresh_install` por uma cópia do plugin para o cache do HOME fixture, com as chamadas anotadas.

| Teste | Entrada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_publish_pushes_exactly_the_reviewed_commit` | retrofit limpo | `origin_main()` é o HEAD do worktree; um commit a mais; o trailer é `autonomous`; linha `publicado` com sha e versão | publicar outro ref |
| `test_refused_retrofit_never_reaches_the_effects` | retrofit sem veredito | nenhuma chamada anotada; `origin_main()` igual | chamar o `push` antes do `refuse` |
| `test_rejected_push_is_an_error_and_keeps_the_branch` | `push` que devolve `(False, …)` | linha `erro`, motivo `push`; o ramo existe; nenhum `refresh_install` | seguir depois do push falho |
| `test_failed_update_is_an_error_line_with_the_commit` | `refresh_install` que devolve falso | `erro`, `update`, `commit` preenchido | gravar `publicado` |
| `test_cache_mismatch_is_an_error_line` | o `refresh_install` copia uma versão alterada | `erro`, `cache-difere` | não comparar |
| `test_plugin_not_installed_is_still_published` | `refresh_install` devolve `nao-instalado` | `publicado`; `cache_matches` não é chamado | — |
| `test_published_skill_is_silenced_in_the_session_state` | publica; depois 3 erros de ferramenta e um Stop | o hook devolve `None` | tirar o `mark_done` |
| `test_second_gate_rebases_over_the_first_publication` | dois lotes de plugins diferentes da mesma base; publica um, depois o outro | os dois commits no `origin`; as duas versões no `marketplace.json` | tirar o rebase |
| `test_second_lote_of_the_same_plugin_conflicts_and_is_held` | dois lotes do mesmo plugin da mesma base | o segundo sai `segurado`, motivo `rebase` | — |
| `test_the_lock_is_held_during_the_push` | o `push` do teste tenta a trava sem espera | a tentativa falha (só onde há `fcntl`) | soltar a trava antes do push |
| `test_owner_approval_publishes_with_the_approved_marker` | lote `description` segurado; `approve`; `publish` de novo | trailer `autonomous-approved`; linha com `aprovado: true`; a árvore do commit é a mesma | não trocar o trailer |
| `test_shared_checkout_is_untouched_by_a_publication` | publicação completa | `shared_state()` igual antes e depois | — |
| `test_cli_publish_in_auto_dry_never_calls_effects` | `mode: auto-dry`, pela CLI | rc 1; `origin_main()` igual; a última linha do stdout tem `segurada` | — |
| `test_real_effects_without_claude_fail_closed` | `Effects().refresh_install` com um PATH sem `claude` | `(False, "claude ausente")`, sem exceção | — |
| `test_cli_lines_are_ascii_on_cp1252` | recusa com detalhe acentuado, `PYTHONIOENCODING=cp1252` | rc 1 e stdout decodificável | — |

- [ ] **Step 2:** Rode. Esperado: falha por `publish` ausente.
- [ ] **Step 3:** Implemente.
- [ ] **Step 4:** Rode a suíte do plugin. Esperado: `OK`.
- [ ] **Step 5:** Mate os mutantes. `check-private-names.py` rc 0. Commit: `feat(retrofit-watch): a porta publica, libera e registra`.

---

### Task 9: O aviso de startup e o critério da v2

**Files:**
- Modify: `$W/scripts/rw_auto.py`, `$W/scripts/rw_store.py`, `$W/scripts/retrofit_watch.py` (`cmd_pending`)
- Test: `$W/tests/test_auto_notice.py`

**Interfaces:**
- Consumes: `held`, `last_lines`, `read_registry` (Tarefa 5); `store_clone` (Tarefa 6); o `check-private-names.py` do clone, por `importlib`.
- Produces:
  - `rw_auto.ORPHAN_AGE = 3600` e `rw_auto.orphans(ctx, now=None) -> list[dict]` (D14).
  - `rw_store.V2_MIN_PUBLISHED = 10`, `rw_store.V2_MIN_DAYS = 14`.
  - `rw_store.criterion(ctx, now=None) -> dict`: `{"publicados", "dias", "revertidos", "vazados", "desde", "cumprido"}`. Conta as linhas `publicado` sem `aprovado`. Abaixo de 10 ou de 14 dias, devolve sem chamar o git. `revertidos`: commits do `origin/main` com `This reverts commit <sha>` de um publicado. `vazados`: achados da lista de hashes nos arquivos que os commits publicados tocaram. A lista e os arquivos se leem do `origin/main` com `git show`. O resultado fica em `<dados>/criterio.json`, por sha do `origin/main` e contagem.
  - `cmd_pending` junta os segmentos com ` · ` num `systemMessage` só: a fila de hoje; `N retrofit(s) segurado(s) (<plugin>: <ramo>, …) — /retrofit-watch:retrofit-watch segurados`; `N worktree(s) de retrofit autônomo sem registro de fim (<ramo>, …)`; e a frase do critério.
  - A frase do critério, da spec 5.9: `retrofit-watch: 10 retrofits autônomos, 0 revertidos, 0 nomes vazados desde <data> — o kit pode entrar (ver a spec do modo autônomo)`, com os números medidos.

- [ ] **Step 1: Escreva os testes que falham.**

| Teste | Entrada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_startup_without_auto_data_is_unchanged` | registro vazio, fila com 1 item | o `systemMessage` de hoje, byte a byte | — |
| `test_held_retrofit_is_announced_with_its_branch` | um segurado; um segurado e depois descartado | um só, com o ramo e o verbo `segurados` | ler a primeira linha |
| `test_orphan_worktree_is_announced_after_an_hour` | lote com `retrofit.json` e sem linha; pedido de 10 min, depois de 2 h | ausente; depois presente | tirar a idade |
| `test_criterion_needs_ten_and_fourteen_days` | 9 e 20 dias; 10 e 13 dias; 10 e 14 dias | falso, falso, verdadeiro com a frase exata | trocar `>=` por `>` em cada limite |
| `test_approved_and_held_do_not_count` | 9 publicados sozinhos e 3 aprovados | `publicados == 9` | contar toda linha `publicado` |
| `test_a_revert_on_origin_main_blocks_the_criterion` | 10 publicados; um commit no `origin` que reverte um deles | `revertidos == 1`, `cumprido` falso | não ler o `origin/main` |
| `test_a_leaked_name_in_a_touched_file_blocks_the_criterion` | um arquivo tocado ganha, no `origin`, um nome da lista da fixture | `vazados == 1` | varrer o worktree em vez do `origin/main` |
| `test_startup_makes_no_fetch` | `origin` inalcançável, 10 publicados e 14 dias | o aviso sai; nenhum erro em `errors.log` | chamar `fetch` |
| `test_below_the_floor_no_git_runs` | 3 publicados e `store` apontando para um caminho que não existe | `cumprido` falso, sem exceção | — |

- [ ] **Step 2:** Rode. Esperado: falha.
- [ ] **Step 3:** Implemente.
- [ ] **Step 4:** Rode a suíte do plugin. Esperado: `OK`.
- [ ] **Step 5:** Mate os mutantes. `check-private-names.py` rc 0. Commit: `feat(retrofit-watch): segurados, órfãos e critério da v2 no aviso de startup`.

---

### Task 10: O revisor, a `SKILL.md` e a referência do fluxo

**Files:**
- Create: `plugins/retrofit-watch/agents/retrofit-reviewer.md`, `$W/references/modo-autonomo.md`, `$W/tests/test_auto_docs.py`
- Modify: `$W/SKILL.md`, `$W/references/criteria.md` (seção 6: duas linhas dizendo que no modo autônomo não há "sim" e apontando a referência nova)

**Interfaces:**
- Consumes: os subcomandos da CLI (Tarefas 5, 6 e 8); as constantes `LICAO_KEYS`, `PARECER_KEYS`, `ANONIMATO_KEYS`, `LESSON_REASONS`, `AGENT_REASONS`, `GATE_REASONS` e `OVERRIDABLE`.
- Produces: o agente `retrofit-watch:retrofit-reviewer`; o verbo `/retrofit-watch:retrofit-watch segurados`.

**O agente (spec 5.4).** Frontmatter: `name: retrofit-reviewer`, `description` em inglês, `tools: Read, Grep, Glob, Bash`, `model: opus`. O corpo diz:
- o que ele recebe: o diretório da retro, o caminho do clone da loja e qual das duas tarefas fazer;
- tarefa *achado*: `git -C <loja> fetch origin`, ler a skill-alvo em `origin/main` **nesta revisão**, conferir a evidência no transcript, responder as cinco perguntas da tabela da spec 5.4 e gravar `veredito.json` no formato da Tarefa 5;
- tarefa *anonimato*: julgar cada termo de `termos-novos.json` como `publico`, `privado` ou `duvida`, com a linha de contexto e a colheita de `<dados>/colheita.txt` como referência, e gravar `anonimato.json`;
- nunca rodar o comando da evidência sobre o estado real: só numa cópia (`git archive` para dentro do diretório da retro) ou fixture. Sem cópia possível, `nao-reproduzivel`, e `basta_o_transcript` diz por que a evidência basta, ou fica nulo;
- gravar os dois arquivos pelo Bash, no diretório da retro, e não editar nenhum arquivo de repo. A resposta volta em até 10 linhas.

**A referência `modo-autonomo.md`**, para o agente da sessão, com os passos numerados:
1. As lições: o formato do `licoes.json` e as seções 1 a 4 do `criteria.md`.
2. O revisor: `subagent_type: "retrofit-watch:retrofit-reviewer"`, `model: "opus"`, `effort: "xhigh"`, sem o contexto da sessão no prompt.
3. `triage <id>`: o que fazer com `lotes`, `segurar` e `descartar`.
4. Por lote: `prepare`; o executor (`subagent_type: "general-purpose"`, `model: "opus"`, `effort: "medium"`, com o prompt-modelo que manda ler `plugins/retrofit-skill/commands/retrofit-skill.md` no worktree e rodar `<plugin> --auto <dir do lote>`); o revisor na tarefa *anonimato*; `publish`. Plugins diferentes em paralelo. Lotes do mesmo plugin em sequência.
5. A linha ao dono, nas duas formas da spec 5.1, e o pedido de `/reload-plugins` depois de uma publicação.
6. O verbo `segurados`: `held`; liberar (`approve`, depois `publish`); descartar (`discard`). Num segurado por nome: "privado" é `check-private-names.py --add` no worktree, o executor troca o termo por um genérico e emenda o commit; "público" é `anonymity-gate.py --publico-add` e emenda. Segurado sem ramo: o `/retrofit-skill` manual.
7. Executor que falha ou recusa a lição: `hold <id> <item> <motivo>`.
8. A tabela de motivos: cada código, o que quer dizer e se a aprovação do dono o substitui.
9. O que nunca fazer: push fora da porta, escrever no checkout compartilhado, apagar ramo ou worktree.

**A `SKILL.md`:** o parágrafo de abertura passa a citar os dois modos. Seção nova *Modo autônomo* com até 25 linhas, que diz **quando** ler a referência (ao receber um pedido autônomo do hook ou o verbo `segurados`). A tabela *Controle* ganha `mode`, `manual`, `private_sources`, `harvest_roots`, `auto_limits` e `store`. *Gotchas* ganha: só vale com `bypassPermissions`; a retro sob demanda continua manual (D17); o revert só é contado quando tem a linha `This reverts commit`. A tabela *Arquivos* ganha os arquivos novos. Teto: abaixo de 250 linhas e de 20.000 caracteres (hoje 150 e 10.218).

- [ ] **Step 1: Grave o baseline da auditoria** da skill, como manda o `retrofit-skill` (seção *ANTES DE EDITAR*): `antes.json` fora do repo.
- [ ] **Step 2: Escreva os testes de contrato que falham.**

| Teste | Asserção |
|---|---|
| `test_every_cited_subcommand_exists` | cada `retrofit_watch.py <sub>` citado em `SKILL.md`, `modo-autonomo.md`, `criteria.md`, no agente e, quando o arquivo existe, em `plugins/retrofit-skill/references/modo-autonomo.md` está na tabela da CLI |
| `test_every_subcommand_is_documented` | cada subcomando da CLI aparece em `modo-autonomo.md` |
| `test_format_keys_are_documented` | cada chave de `LICAO_KEYS` aparece em `modo-autonomo.md`; cada chave de `PARECER_KEYS` e de `ANONIMATO_KEYS` aparece no agente |
| `test_every_reason_code_is_explained` | cada código de `LESSON_REASONS`, `AGENT_REASONS` e `GATE_REASONS` aparece na tabela de motivos |
| `test_reviewer_frontmatter` | `name` igual ao nome do arquivo; `tools: Read, Grep, Glob, Bash` exato |
| `test_dispatch_names_model_and_effort` | o passo do revisor tem `opus` e `xhigh`; o do executor, `opus` e `medium` |
| `test_skill_budget_and_routing` | `SKILL.md` abaixo de 250 linhas e de 20.000 caracteres; a linha que cita `references/modo-autonomo.md` diz quando ler |
| `test_owner_lines_match_the_gate` | as duas frases ao dono da referência têm o mesmo começo das que a CLI imprime |

- [ ] **Step 3:** Rode. Esperado: falha por arquivo ausente.
- [ ] **Step 4:** Escreva o agente, a referência e as mudanças da `SKILL.md` e do `criteria.md`.
- [ ] **Step 5:** Rode a suíte do plugin. Esperado: `OK`.
- [ ] **Step 6:** Rode o gate da auditoria (`depois.json`, `diff.txt`, `audit_gate.py`). Esperado: nenhuma linha `NOVO`. Cada `CLAIM` recebe veredito no relatório da tarefa.
- [ ] **Step 7:** Se o `claude` estiver no PATH, `claude plugin validate plugins/retrofit-watch`. Esperado: nenhum erro em `agents`. Sem o `claude`, diga isso no relatório.
- [ ] **Step 8:** `check-private-names.py` rc 0. Commit: `feat(retrofit-watch): revisor independente e contrato do fluxo autônomo`.

---

### Task 11: `retrofit-skill` 0.11.0 — o modo autônomo do executor

**Files:**
- Create: `$R/references/modo-autonomo.md`, `$R/tests/test_modo_autonomo.py`
- Modify: `$R/commands/retrofit-skill.md`, `$R/CHANGELOG.md`, `$R/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (só o bloco do `retrofit-skill`), `README.md` (a linha da tabela e a seção de detalhes do plugin), `docs/codex/compatibility.md` (a contagem da linha do `retrofit-skill`: a previsão é de 3 para 4 arquivos; meça com `git ls-files` em `scripts/` e `references/`)

**Interfaces:**
- Consumes: `prepare` e `seal` (Tarefa 6); o formato do `retrofit.json` e do `veredito.json` (Tarefa 5).
- Produces: a sintaxe `/retrofit-skill <plugin> --auto <dir do lote>` (D1).

**O comando muda em quatro pontos, e só neles:**
1. A regra do argumento: `--auto <dir>` depois do nome escolhe o modo autônomo. O resto da regra fica.
2. Seção nova *Modo autônomo*, com até 20 linhas: só vale no modo completo; exige `<dir>/retrofit.json` e o `veredito.json` da retro; o veredito faz o papel da confirmação do passo 3; o fluxo para antes do push; manda ler `references/modo-autonomo.md` antes de editar.
3. Passo 3: depois de "Espere minha confirmação", a exceção do modo autônomo, numa frase.
4. Passo 4, no item do push e no item da loja: no modo autônomo, os dois são da porta.

**A referência cobre a spec 5.5, item por item:**
- as lições são as do lote, e nenhuma outra entra no commit;
- o worktree é o do `retrofit.json`: não criar outro, não tocar o checkout compartilhado;
- baseline e gate da `skill-quality-audit`, como hoje;
- corrigir a frase que errou em vez de acrescentar uma regra, procurando antes a regra já escrita (`grep -rn` na skill);
- skill com `tests/`: o teste que falha antes da correção, a correção, o teste passando, e os mutantes da correção;
- bump, `CHANGELOG`, `marketplace.json` e README como no modo completo;
- um commit só, com `--trailer "Retrofit-Mode: autonomous"`, sem `Co-Authored-By`;
- nenhum push e nenhum `claude plugin`;
- o último passo é `seal <id> <lote> --licoes …`. Com achado da camada 1: trocar o termo por um genérico, emendar o commit e selar de novo, no máximo 2 ciclos;
- a lição que não cabe sem piorar a skill fica fora do commit e sai no relatório;
- o relatório volta em até 5 linhas: commit, versão, lições incluídas, lições deixadas de fora e o resultado do `seal`.

- [ ] **Step 1: Escreva o teste de contrato que falha.**

| Teste | Asserção |
|---|---|
| `test_o_comando_roteia_para_a_referencia` | o comando cita `--auto` e `references/modo-autonomo.md`, e a frase diz quando ler |
| `test_o_passo_3_tem_a_excecao` | o parágrafo de "Espere minha confirmação" cita o modo autônomo |
| `test_a_referencia_tem_as_ancoras_da_spec` | a referência contém `retrofit.json`, `veredito.json`, `seal`, `Retrofit-Mode: autonomous` e a proibição do `Co-Authored-By` |
| `test_a_referencia_nao_manda_publicar` | nenhuma linha da referência tem `git push` ou `claude plugin` fora de uma frase de proibição |
| `test_os_quatro_lugares_estao_na_0_11_0` | `plugin.json`, o `metadata.version` do comando, o bloco do `marketplace.json` e a linha do README dizem `0.11.0`; o `CHANGELOG` tem a entrada |

- [ ] **Step 2:** `python3 $R/tests/test_modo_autonomo.py`. Esperado: falha.
- [ ] **Step 3:** Escreva a referência e as quatro mudanças do comando.
- [ ] **Step 4:** Faça o bump para 0.11.0 nos quatro lugares e escreva a entrada do `CHANGELOG` com o quê e o porquê. Edite o `marketplace.json` só dentro do bloco do plugin, sem passar o arquivo por um parser.
- [ ] **Step 5:** Rode `$R/tests/test_modo_autonomo.py` e `$W/tests/test_auto_docs.py`. Esperado: `OK` nos dois.
- [ ] **Step 6:** `python3 scripts/validate-versions.py` (rc 0) e `python3 $R/scripts/check_release_sync.py retrofit-skill`. Leia os valores impressos: `0.11.0` nos dois manifestos e na linha do README.
- [ ] **Step 7:** `git add -A && git diff --cached --stat`. Responda por cada arquivo. `check-private-names.py` rc 0. Commit: `feat(retrofit-skill): v0.11.0 — modo autônomo para o executor do retrofit-watch`.

---

### Task 12: `retrofit-watch` 0.4.0 — versão, catálogo e conferência final

**Files:**
- Modify: `plugins/retrofit-watch/.claude-plugin/plugin.json`, `$W/SKILL.md` (`metadata.version`), `plugins/retrofit-watch/CHANGELOG.md`, `.claude-plugin/marketplace.json` (só o bloco do `retrofit-watch`), `README.md` (a linha da tabela e a seção de detalhes), `docs/codex/compatibility.md` (a contagem da linha do `retrofit-watch`: a previsão é de 2 para 6 arquivos; meça do mesmo jeito), `$W/scripts/retrofit_watch.py` (a docstring do topo e o `--help`: as chaves novas da config e os subcomandos)
- Test: `$W/tests/test_auto_docs.py`

**Interfaces:**
- Consumes: tudo das Tarefas 2 a 11.

- [ ] **Step 1: Escreva os testes que falham**, em `test_auto_docs.py`.

| Teste | Asserção |
|---|---|
| `test_release_places_agree_on_0_4_0` | `plugin.json`, `metadata.version` do `SKILL.md`, o bloco do `marketplace.json` e a linha do README dizem `0.4.0`; o `CHANGELOG` tem a entrada |
| `test_help_lists_every_subcommand` | a saída de `retrofit_watch.py --help` cita cada subcomando da CLI |
| `test_readme_names_the_modes_and_the_held_verb` | a seção do README cita `manual`, `auto`, `auto-dry` e `segurados` |

- [ ] **Step 2:** Rode. Esperado: falha.
- [ ] **Step 3:** Faça o bump para 0.4.0 nos quatro lugares. A entrada do `CHANGELOG` diz o quê e o porquê, lista as guardas da porta e as chaves novas da config, e traz as contagens de teste medidas.
- [ ] **Step 4:** Reescreva a seção do README em inglês: os dois modos, o padrão `manual`, a porta, o verbo `segurados` e as chaves novas da config. A frase "one yes and the retrofit takes over" passa a valer só para o modo manual.
- [ ] **Step 5:** Atualize a docstring e o `--help` do script.
- [ ] **Step 6: Conferência final.** Rode cada comando com a saída num arquivo e leia o `rc`.

| Comando | Esperado |
|---|---|
| `python3 -m unittest discover -s $W/tests -p 'test_*.py'` | `OK`; os 54 testes da linha de base continuam |
| `python3 $R/tests/test_modo_autonomo.py` | `OK` |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | `OK`; os 80 da linha de base e os novos |
| `python3 scripts/validate-versions.py` | rc 0; nenhum WARNING novo para os dois plugins |
| `python3 $R/scripts/check_release_sync.py retrofit-watch` | `0.4.0` nos manifestos e no README; description igual nos três lugares |
| `python3 scripts/check-private-names.py` | rc 0 |
| `python3 scripts/anonymity-gate.py --camada1 --base origin/main` | rc 0: o próprio ramo passa na camada 1 |
| `git log origin/main..HEAD --format='%(trailers:key=Co-authored-by,valueonly)'` | nada |
| `/usr/bin/grep -rn 'import fcntl' $W/scripts/rw_*.py` | nada |

- [ ] **Step 7:** Achado da camada 1 no próprio ramo se corrige no arquivo que o causou, com o texto montado em tempo de execução. Nunca pela lista de públicos.
- [ ] **Step 8:** `git add -A && git diff --cached --stat`. Responda por cada arquivo. Commit: `feat(retrofit-watch): v0.4.0 — modo autônomo`.

---

## Passos do dono, depois do merge

Nenhum subagente faz estes passos. Nenhum nome vai para arquivo de repo.

1. **Classificar os nomes da colheita (spec 5.6, "antes da v1 ir ao ar").** Na sessão, da raiz do clone da loja:

   ```bash
   python3 plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py harvest
   python3 scripts/anonymity-gate.py --arvore --extra <o arquivo que o comando acima imprimiu>
   ```

   O segundo comando imprime, só no terminal, cada nome colhido que aparece na loja e ainda não foi classificado. A medida da spec indica cerca de 23, a maioria palavra comum. Para cada um: privado é `python3 scripts/check-private-names.py --add NOME` e a troca do nome no arquivo; público é `python3 scripts/anonymity-gate.py --publico-add NOME`. Repita até o segundo comando sair 0. O commit leva só as duas listas e os arquivos corrigidos.
2. **Ensaio.** No `~/.claude/retrofit-watch.json`: `"mode": "auto-dry"` e `"store"` (P1). Uma sessão com `bypassPermissions` e uma skill da loja com atrito. Esperado: o ramo pronto e a linha `segurada — auto-dry`.
3. **Ligar.** `"mode": "auto"`.
4. **Windows.** Antes de ligar lá, rode a suíte do plugin com o `python3` do PATH.

## Self-review

- **Cobertura da spec:** 5.1 (Tarefas 4, 5, 6, 8, 10); 5.2 (4, 6, 7); 5.3 (4, 5); 5.4 (5, 10); 5.5 (6, 11); 5.6 (2, 3, 7, 10 e o passo 1 do dono); 5.7 (7, 8); 5.8 (5, 7, 10); 5.9 (5, 9); 5.10 (4, 7); 5.11 (5, 8, 10).
- **Anti-objetivos:** nome no `origin/main` (2, 3, 7); retro de si mesmo (4); checkout compartilhado (6, 8); modo autônomo sem pedir (4). A regra nova embaixo de regra existente só tem guarda de texto, na Tarefa 11: é a pendência P2.
- **Review Focus:** 1 na Tarefa 4; 2 na 8; 3 na 5; 4 nas 7 e 8; 5 nas 5 e 8.
- **Nomes:** `refuse`, `hold`, `publish`, `triage`, `prepare`, `seal`, `held`, `approve`, `discard`, `hold_item`, `harvest` são os mesmos em todas as tarefas que os citam.
