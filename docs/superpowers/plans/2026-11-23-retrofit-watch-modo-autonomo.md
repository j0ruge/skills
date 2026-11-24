# retrofit-watch 0.4.0 e retrofit-skill 0.11.0: modo autônomo — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** No modo `auto`, uma lição de skill da loja que passa nas guardas é publicada sem nenhum "sim" do dono, e a que não passa fica segurada num ramo local.

**Architecture:** O Stop hook continua só pedindo a retro, agora com o caminho de um diretório de dados por retro. O agente da sessão grava as lições, despacha um revisor independente e um executor por lote, e chama subcomandos determinísticos do script do plugin: `triage`, `prepare`, `seal` e `publish`. A porta (`publish`) é o único caminho até o `origin/main`. Ela roda de novo todas as guardas sobre o commit final e registra cada resultado num arquivo só de acréscimo. As duas camadas mecânicas da anonimização moram num script novo da raiz da loja, que a porta chama dentro do worktree do lote.

**Tech Stack:** Python 3 só com biblioteca padrão (`unittest`, `subprocess`, `json`, `tarfile`, `hashlib`), git, Markdown dos contratos da skill e do agente.

**Spec:** `docs/superpowers/specs/2026-11-23-retrofit-watch-modo-autonomo-design.md`

**Execução:** subagent-driven. Um subagente Opus com esforço `medium` implementa cada tarefa. Um Opus com esforço `xhigh` revisa cada uma. Esta versão do plano já traz as respostas do dono e os 14 achados da revisão independente de 23/11.

## Global Constraints

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
- Versões: `retrofit-watch` 0.4.0 e `retrofit-skill` 0.11.0, com `CHANGELOG`, `plugin.json`, metadata do `SKILL.md` ou do comando, `marketplace.json` e README no mesmo incremento. Nenhum dos dois tem `codex` em `platforms` (`["claude-code"]` e `["claude-code", "cursor"]`): nenhum derivado Codex muda. A `description` e as `keywords` dos dois ficam como estão.
- Contratos em português, como o resto dos dois plugins. A `description` do agente e a seção do README em inglês, como as vizinhas. Nomes de teste: em inglês nos testes do plugin, em português em `tests/` da raiz, como os existentes.
- Limites da spec, seção 5.10: no máximo 2 retrofits autônomos por skill por sessão e 3 por sessão. Critério da v2, seção 5.9: pelo menos 10 publicados e 14 dias.
- Abreviações: `W=plugins/retrofit-watch/skills/retrofit-watch`, `R=plugins/retrofit-skill`, `Q=plugins/skill-quality-audit/skills`, `<dados>` = `ctx.data_dir`.
- Suítes: `python3 $W/tests/<arquivo>.py` para um arquivo; `python3 -m unittest discover -s $W/tests -p 'test_*.py'` para o plugin; `python3 -m unittest discover -s tests -p 'test_*.py'` para a raiz.

## Decisões do dono (23/11, depois da revisão do plano)

| # | Decisão |
|---|---|
| O1 | A chave `store` na config aponta o clone de trabalho da loja. Sem ela, o `auto` não vale (motivo `sem-loja`). |
| O2 | A regra repetida tem guarda mecânica: a segunda passada do revisor responde se a mudança repete ou contradiz uma regra já escrita, e a porta recusa com `regra-repetida`. |
| O3 | Lição com evidência não confirmada, ou na lista do que não capturar, é descartada: linha `descartado` com o motivo, fora do aviso de startup. |
| O4 | O executor chama a família `skill-quality-audit` conforme a mudança: a fase 1 sempre; `skill-claim-check`, `skill-self-containment` e `skill-refactoring` pelos gatilhos da Tarefa 12. |
| O5 | A colheita inclui o projeto da sessão: o `pedido.json` grava o `cwd`, e a colheita lê a raiz e o `origin` desse repo. |
| O6 | Nome em minúsculas com hífen é candidato da camada 2, exceto flag, nome de arquivo com extensão e palavra que a loja já tem. |
| O7 | `termo-nao-publico` e `sem-anonimato` não são substituíveis. Um segurado por nome só sai quando o dono ensina o portão. |
| O8 | A segunda passada do revisor confere o diff contra as lições declaradas, com campo próprio e recusa `diff-alem-das-licoes`. |
| O9 | Contra a autoaprovação, uma regra escrita com teste: o texto do hook e a referência proíbem `approve`, `--publico-add` e `--add` sem a palavra do dono na conversa. |

## Decisões do planejador (spec, seção 8, e as que a revisão pediu)

| # | Decisão |
|---|---|
| D1 | Sintaxe no `retrofit-skill`: `/retrofit-skill <plugin> --auto <dir do lote>`. |
| D2 | A unidade é o **lote**: `<plugin>` (tipo `auto`) ou `<plugin>__description` (tipo `description`). A porta vira `publish <id> <lote>`. Lotes do mesmo plugin rodam em sequência, o `auto` primeiro. |
| D3 | Arquivos por retro em `<dados>/auto/<id>/`, e por lote em `<dados>/auto/<id>/<lote>/`. Chaves na seção *Formatos e motivos*. |
| D4 | A camada 1 e a extração da camada 2 moram num script novo da raiz, `scripts/anonymity-gate.py`. A lista de públicos é `scripts/public-names.txt`, em texto puro. A colheita mora no plugin e entra por `--extra ARQUIVO`, de fora do repo. |
| D5 | `harvest_roots` padrão: `["~/repos"]`, profundidade 2. |
| D6 | A porta marca a retro como feita no estado da sessão. A sessão vem do `pedido.json` que o hook gravou. |
| D7 | A porta faz `fetch` e rebase **antes** das guardas, para que cada guarda leia o commit que sobe. |
| D8 | Publicar é `git push origin HEAD:main` a partir do worktree do lote. O `main` local do checkout compartilhado não é tocado. |
| D9 | Guardas a mais na porta, nunca substituídas: o worktree e o ramo saem do `<id>` e do `<lote>`, nunca do `retrofit.json`; árvore limpa; um commit só; caminhos dentro do escopo. Os dois arquivos de lista só mudam com `aprovado.json`. |
| D10 | Auditoria na porta: a fase 1 da `skill-quality-audit` roda na base (extraída com `git archive`) e no commit. Qualquer linha `NOVO` do `audit_gate.py` segura. A porta passa `--external off`, para nenhum validador externo tocar a rede. |
| D11 | A porta roda os testes do plugin (`plugins/<p>/tests` e `plugins/<p>/skills/*/tests`) e a suíte `tests/` da raiz. |
| D12 | O lote `description` também passa pela porta: ela recusa com `muda-description` e registra o ramo pronto. |
| D13 | Enquanto um pedido autônomo está aberto, o hook não conta trabalho nem atrito de **nenhuma** skill e não abre pedido novo. O pedido fecha quando toda lição tem linha no registro, ou em 6 h. `licoes.json` ilegível deixa o pedido aberto até as 6 h. |
| D14 | Órfão no aviso de startup, depois de 1 h: lote com `retrofit.json` e sem linha no registro, ou pedido com `licoes.json` e lição sem linha. |
| D15 | O critério da v2 se mede pelos commits com `Retrofit-Mode: autonomous` no `origin/main` local, não pelo registro. Os 14 dias contam do primeiro deles. O startup não faz `fetch`; o resultado fica em cache por sha do `origin/main`. |
| D16 | A forma de segredo inclui sequência alfanumérica de 32 ou mais com letra e dígito. Hexadecimal de exatamente 40 passa: é sha de commit, e a regra da loja diz que hash fica. |
| D17 | A retro sob demanda (`/retrofit-watch:retrofit-watch <skill>`) continua manual: só o Stop hook abre um pedido autônomo. |
| D18 | A porta atualiza a cópia instalada só no escopo `user`. |
| D19 | A segunda passada grava no mesmo `anonimato.json` os campos `regra_repetida` e `fora_das_licoes`. `regra-repetida` e `diff-alem-das-licoes` são substituíveis pela aprovação do dono, como o item 1 da spec 5.7: os dois são juízo do revisor. |
| D20 | A chave `commit` sai de `termos-novos.json` e de `anonimato.json`. Entra `patch`: o sha256 das linhas `+`, `-` e dos nomes de arquivo de `git diff -U0 --no-renames origin/main...HEAD`, sem os cabeçalhos `@@` e sem os arquivos de lista. O rebase não o muda; uma emenda de conteúdo muda. A porta recusa com `revisao-desatualizada` quando ele não confere. |
| D21 | O `seal` recebe `--fases` e grava `retrofit.json["fases"]`. A porta confere três gatilhos mecânicos (Tarefa 8, guarda 19) e recusa com `fase-de-auditoria`. Tetos: 400 linhas e 16.000 caracteres. |
| D22 | A linha `publicado` sai logo depois do push, com `instalacao: "pendente"`. A falha de instalação fica nesse campo, não no resultado. Rodar `publish` de novo num lote já publicado refaz só a instalação. rc 4 é "publicado, instalação falhou". |
| D23 | Segurado por `rebase` se refaz: `prepare <id> <lote> --redo` abre a tentativa seguinte num worktree e num ramo novos. Nada é apagado. |
| D24 | `fora-do-pedido` não é substituível: a saída é o `/retrofit-skill` manual. |
| D25 | A porta espera a trava por até 900 s. Toda exceção dentro de `publish` vira linha `erro` e rc 3. |

## Formatos e motivos (valem para todas as tarefas)

| Arquivo | Quem grava | Conteúdo |
|---|---|---|
| `pedido.json` | o hook | `{"id", "sessao", "ts", "transcript", "cwd", "modo", "skills": [{"key", "plugin", "label", "skills"}]}` |
| `licoes.json` | o agente da sessão | `{"id", "licoes": [{"n", "plugin", "skill", "tipo", "evidencia": {"texto", "transcript", "entrada"}, "padrao", "resolveu", "muda_description"}]}`. `tipo` é `pitfall` ou `melhoria`. `resolveu: null` é "sem correção verificada". |
| `veredito.json` | o revisor, 1ª passada | `{"id", "base", "licoes": [{"n", "evidencia_confere", "coberta", "generica", "procede", "basta_o_transcript", "nao_capturar", "nota"}]}`. `procede` é `procede`, `nao-procede` ou `nao-reproduzivel`. `coberta` é `null` ou `arquivo:linha`. |
| `retrofit.json` | `prepare` e `seal` | `{"id", "lote", "plugin", "tipo", "tentativa", "worktree", "ramo", "base", "licoes", "fases", "commit", "versao", "patch"}` |
| `termos-novos.json` | `seal` | `{"patch", "termos": [{"termo", "onde", "contexto"}]}` |
| `anonimato.json` | o revisor, 2ª passada | `{"patch", "termos": [{"termo", "veredito", "nota"}], "regra_repetida", "fora_das_licoes"}`. `veredito` é `publico`, `privado` ou `duvida`. Os dois últimos campos: `null` é "não"; texto é "sim", com o `arquivo:linha` e o porquê. Chave ausente é arquivo inválido. |
| `aprovado.json` | `approve` | `{"id", "lote", "ts", "motivos": [...]}` |
| linha de `autonomo.jsonl` | `triage`, a porta e os verbos | `{"ts", "sessao", "id", "lote", "plugin", "item", "licoes", "resultado", "motivo", "detalhe", "commit", "ramo", "worktree", "versao", "aprovado", "instalacao"}`. `item` é `<id>/<lote>` no lote e `<id>/<plugin>#<n>` na lição sem ramo. `resultado` é `publicado`, `segurado`, `descartado` ou `erro`. `instalacao` é `pendente`, `ok`, `nao-instalado`, `update` ou `cache-difere`. |

| Conjunto | Motivos |
|---|---|
| `LESSON_REASONS` (triagem) | descarta: `coberta`, `do-projeto`, `nao-procede`, `sem-evidencia`, `nao-capturar`. Segura: `sem-veredito`, `fora-do-pedido`, `nao-reproduzivel`, `sem-correcao`. |
| `OWNER_REASONS` (`discard`) | `descartado-pelo-dono`, `resolvido-manual` |
| `AGENT_REASONS` (`hold`) | `executor-falhou`, `executor-recusou` |
| `GATE_REASONS` (a porta) | os da tabela de guardas da Tarefa 8 e os de `ERRORS` |
| `ERRORS` | `fetch`, `push`, `trava`, `interno` |
| `OVERRIDABLE` | `sem-veredito`, `nao-publicavel`, `muda-description`, `regra-repetida`, `diff-alem-das-licoes`, `teto`, `auto-dry` |

**A frase da O9**, igual no texto do hook e na referência do fluxo, guardada em `rw_auto.OWNER_WORD_RULE`: "Nunca rode `approve`, `--publico-add` nem `--add` sem a palavra do dono nesta conversa."

## Review Focus

1. **O fluxo atravessa vários turnos.** Subagente em segundo plano termina o turno, e o Stop hook dispara de novo no meio do fluxo, com erros de ferramenta no trecho novo e outra skill carregada. O dono espera silêncio, não outra retro. Testes na Tarefa 4.
2. **Duas portas ao mesmo tempo, de plugins diferentes.** As duas mexem no `marketplace.json` e no README. A segunda faz rebase sobre a primeira e publica, ou segura com `rebase`. Nunca um push forçado. Teste na Tarefa 9.
3. **JSON malformado escrito por um agente.** `veredito.json` ou `licoes.json` com lição faltando, chave a mais, tipo errado, BOM ou cerca de código. O dono espera uma recusa com o campo nomeado, e o hook em silêncio. Testes nas Tarefas 4 e 5.
4. **`origin` inalcançável, ou a porta morre depois do push.** O dono espera uma linha com o motivo, rc diferente de 0, o ramo intacto, e que rodar de novo conserte. Testes nas Tarefas 8 e 9.
5. **Saída com acento no stdio cp1252.** `held`, `triage` e `publish` imprimem motivo e caminho. O dono do Windows espera JSON válido. Testes nas Tarefas 5 e 9.

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
- `lista`: forma candidata cujo hash está na lista da loja. `colheita`: forma candidata igual a `cpn.chave` de uma linha de `--extra` (uma por linha, `#` comenta). O script não quebra o termo: quem o quebra é a colheita (Tarefa 7).
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
| `test_par_com_espaco_da_colheita_e_achado` | extra `aaa bbb`; linha nova com `Aaa Bbb` | um achado `colheita` | comparar só palavra solta |
| `test_linha_antiga_nao_e_achado` | o nome já está no commit base, e o commit novo muda outra linha | `[]` | varrer o arquivo inteiro |
| `test_caminho_de_arquivo_novo_e_varrido` | arquivo novo com o nome no caminho | achado na linha 0 | pular a linha 0 |
| `test_email_e_achado` | endereço montado em tempo de execução | tipo `email` | tirar o padrão |
| `test_caminho_com_usuario_e_achado` | as quatro formas, uma por `subTest` | tipo `caminho` | tirar uma forma |
| `test_placeholder_de_caminho_passa` | `/home/<u>`, `/home/$USER` | `[]` | tirar a isenção |
| `test_forma_de_segredo_e_achado` | cada prefixo; hexadecimal de 64; 33 alfanuméricos com letra e dígito | tipo `segredo` | tirar a sequência longa |
| `test_o_que_nao_e_segredo_passa` | sha de 7; sha de 40; 36 letras seguidas sem dígito; caminho longo com data; `Basic authentication` | `[]` | tirar a exigência de dígito (morre nas 36 letras); tirar a isenção do sha de 40 |
| `test_publico_isenta_nome_e_nunca_segredo` | termo da colheita que está nos públicos; segredo que está nos públicos | `[]`; depois um achado `segredo` | isentar tudo |
| `test_a_lista_de_hashes_e_isenta_so_de_segredo` | o commit acrescenta a `private-names.sha256` um hash novo **e** uma linha com um e-mail montado em tempo de execução | exatamente um achado, de tipo `email`, naquele arquivo | isentar o arquivo de todos os tipos (some o `email`); tirar a isenção (aparece `segredo`) |
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
- Candidato a termo: palavra com maiúscula fora do início da frase, CamelCase, palavra com dígito ou `_` dentro, caminho, URL, e nome em minúsculas com hífen (O6).
- Fora dos candidatos: número, data, versão (`v1.2.3`, `0.4.0`), sha em hexadecimal de 7 a 40, flag (`-x`, `--x-y`) e nome de arquivo com extensão (`notas-de-campo.md`).
- O termo é novo quando não existe na loja em `base` e não está nos públicos. A busca é uma chamada `git grep -F -i -w -q -e <termo> <base>` por termo distinto.

- [ ] **Step 1: Escreva os testes que falham.**

| Teste | Entrada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_nome_proprio_novo_e_termo` | linha nova com um nome inventado no meio da frase | o termo sai com `onde` e `contexto` | tirar a regra da maiúscula |
| `test_identificador_novo_e_termo` | CamelCase, `com_sublinhado`, `abc9def`, um caminho, uma URL | os cinco saem | tirar uma regra |
| `test_nome_minusculo_com_hifen_e_termo` | `acme-portal` numa frase | o termo sai | tirar a regra do hífen |
| `test_flag_e_arquivo_com_extensao_nao_saem` | `--dry-run`, `-x`, `notas-de-campo.md` | `[]` | tirar cada exceção |
| `test_termo_que_a_loja_ja_tem_nao_sai` | o mesmo nome já num arquivo do commit base, em outra caixa; um nome com hífen que a loja já tem | `[]` | tirar o `-i` ou a busca |
| `test_pedaco_de_palavra_da_loja_ainda_e_novo` | a loja tem `Acmecorp`, a linha nova tem `Acme` | `Acme` sai | tirar o `-w` |
| `test_publico_nao_sai` | termo dos públicos | `[]` | tirar a consulta aos públicos |
| `test_numero_data_versao_e_sha_nao_saem` | `0.4.0`, `2026-11-23`, `v1.2.3`, sha de 7 | `[]` | tirar a exclusão |
| `test_termo_da_mensagem_sai` | nome novo só na mensagem | `onde == "<mensagem>"` | não ler a mensagem |
| `test_inicio_de_frase_nao_e_termo` | `Depois rode o teste.` | `[]` | tratar toda maiúscula como nome |
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
- Modify: `$W/scripts/retrofit_watch.py` (`Context`, `_full`, `Scanner._watch`, `Scanner._bump`, `build_output`, `cmd_stop`, o fim do arquivo), `$W/tests/test_retrofit_watch.py` (só a extração do arnês)

**Interfaces:**
- Produces, em `retrofit_watch.py`:
  - `Context.mode -> str`: `manual`, `auto` ou `auto-dry`. Valor inválido ou ausente dá `manual`.
  - `Context.manual -> set[str]`, `Context.auto_limits -> dict` (padrão `{"per_skill": 2, "per_session": 3}`, fundido com a config), `Context.harvest_roots -> list[Path]` (D5), `Context.private_sources -> list[Path]`.
  - `Context.store -> Path | None` (O1): o caminho da config, quando é um diretório com `.git` cujo `.claude-plugin/marketplace.json` tem o nome da loja. Senão, `None`. É a **única** conferência do `store`: lê arquivo, não chama o git.
  - `_full` acrescenta `"skills": [skill]` à entrada (lista vazia para plugin só de comandos). `Scanner._watch` acrescenta à lista a skill nova de um plugin que já tem entrada. Estado antigo sem a chave se lê com `.get`.
  - `build_output(entries, auto_text=None, reasons=None)`: sem os dois argumentos novos, a saída é a de hoje.
  - Última linha antes do `if __name__`: `sys.modules.setdefault("retrofit_watch", sys.modules[__name__])`, para o `import retrofit_watch` dos módulos novos não carregar uma segunda cópia.
  - `class HookHarness` em `test_retrofit_watch.py`, com `write`, `run_hook` e `context_of` tirados de `StopTest`. `StopTest(HookHarness, unittest.TestCase)` mantém os 54 testes.
- Produces, em `rw_auto.py`:
  - `AUTO_DIR = "auto"`, `REGISTRY = "autonomo.jsonl"`, `AUTO_OPEN_TTL = 6 * 3600`, `OWNER_WORD_RULE` (a frase da seção *Formatos e motivos*).
  - `class Malformed(Exception)`.
  - `new_id(session_id, now=None) -> str`: `AAAAMMDD-HHMMSS-<8 caracteres seguros da sessão>`.
  - `retro_dir(ctx, rid) -> Path`, `lote_dir(ctx, rid, lote) -> Path`. Os dois recusam `rid` ou `lote` fora de `^[A-Za-z0-9][A-Za-z0-9_.-]*$` com `Malformed`.
  - `read_registry(ctx) -> list[dict]` (linha ilegível é pulada), `append_registry(ctx, line: dict) -> dict` (acrescenta `ts`, sob `_lock` de `<dados>/autonomo.lock`).
  - `used(registry, session, plugin=None, skip=None) -> int`: pares `(id, plugin)` distintos das linhas de lote (item sem `#`) da sessão.
  - `why_manual(ctx, payload, entry, registry, entrypoint) -> str | None`. `None` quer dizer que o modo autônomo vale. Motivos, na ordem: `modo`, `kit-ou-lean`, `lista-manual` (o plugin ou qualquer skill de `entry["skills"]` está em `ctx.manual`), `permissao`, `entrypoint`, `sem-loja`, `teto`. O `entrypoint` vale quando o último `"entrypoint"` lido do transcript (`st["entrypoint"]`) não é `cli`, ou falta (spec 5.10, "Entrypoint do transcript").
  - `open_request(ctx, payload, entries) -> dict`: grava `pedido.json` no formato da seção *Formatos e motivos*, com o `cwd` do payload.
  - `auto_text(ctx, pedido, entries) -> str`.
  - `flow_finished(ctx, pedido) -> bool`: verdadeiro quando `licoes.json` falta, ou quando toda lição dele aparece em `licoes` de alguma linha do registro com aquele `id`. `licoes.json` ilegível ou fora do formato devolve falso, sem exceção.

**Comportamento do `cmd_stop`:**
- `rw_auto` só é importado quando `ctx.mode != "manual"`. O caminho autônomo inteiro roda dentro de um `try`: qualquer exceção vai ao `errors.log` e o hook segue com o texto manual.
- Para cada entrada pronta, `why_manual` decide, com `st.get("entrypoint")`. As autônomas entram num pedido só. As manuais saem com o texto de hoje, no mesmo `additionalContext`.
- Ao pedir, grava `st["auto_open"] = {"id", "ts"}`. Enquanto existe e tem menos de `AUTO_OPEN_TTL`: `_bump` não conta para nenhuma chave, e o hook não devolve pedido nenhum, autônomo ou manual.
- O fechamento é conferido **depois** da varredura do trecho. No Stop de continuação (`stop_hook_active`), `licoes.json` ausente fecha o pedido.
- `systemMessage` no modo autônomo: `retrofit-watch: retro de <nomes> pedida ao Claude, modo autônomo (<id>)`. Com `mode` diferente de `manual` e a entrada caindo no manual por `permissao`, `sem-loja` ou `teto`, a mensagem de hoje ganha ` — modo manual: <motivo por extenso>`. O texto de `permissao` cita `bypassPermissions`. Com o motivo `entrypoint`, a saída é a de hoje, sem acréscimo.

**O texto autônomo contém, e os testes conferem:** o caminho absoluto de `<dados>/auto/<id>/licoes.json`; o caminho absoluto de `$W/references/modo-autonomo.md` e de `retrofit_watch.py`; a ordem de fazer a retro pelas seções 1 a 4 do `criteria.md`; a resposta `retro <label>: sem lições novas` sem gravar nada; a proibição de perguntar ao dono, de rodar o `/retrofit-skill` nesta sessão e de citar valor de segredo; a frase `OWNER_WORD_RULE`, inteira; quantos retrofits restam na sessão.

- [ ] **Step 1: Extraia o `HookHarness`** e rode `test_retrofit_watch.py`. Esperado: `Ran 54 tests`, `OK`.
- [ ] **Step 2: Escreva os testes que falham** em `test_auto_mode.py`. Todo teste autônomo grava o transcript com `with_entrypoint(..., "cli")`. Modelo:

```python
class AutoStopTest(HookHarness, unittest.TestCase):
    def config(self, **keys):
        (self.w.home / ".claude/retrofit-watch.json").write_text(json.dumps(keys))

    def work(self, n=6):
        self.write(with_entrypoint(skill_via_tool("codereview:coderabbit-pr", self.w.mkt_skill), "cli"),
                   *[tool()] * n)

    def test_auto_request_names_absolute_paths_and_writes_pedido(self):
        self.config(mode="auto", store=str(self.w.repo))
        self.work()
        out = self.run_hook(mode="bypassPermissions")
        pedido = next((self.w.data / "auto").glob("*/pedido.json"))
        text = self.context_of(out)
        self.assertIn(str(pedido.parent / "licoes.json"), text)
        self.assertIn("modo-autonomo.md", text)
        self.assertIn(rw_auto.OWNER_WORD_RULE, text)
        self.assertNotIn("Rodo /retrofit-skill", text)
        data = json.loads(pedido.read_text())
        self.assertEqual(data["skills"][0]["plugin"], "codereview")
        self.assertEqual(data["cwd"], str(self.w.proj))
```

| Teste | Entrada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_default_mode_is_manual_and_text_is_unchanged` | sem config, `bypassPermissions` | texto com `/retrofit-skill:retrofit-skill codereview`; `<dados>/auto` não existe | padrão `auto` |
| `test_invalid_mode_is_manual` | `mode: "sempre"` | como acima | aceitar qualquer valor |
| `test_auto_needs_cli_entrypoint` | `mode: auto`, `bypassPermissions`, `CLAUDE_CODE_SESSION_ATTENDED=1` no ambiente, transcript com `"entrypoint":"sdk-cli"` | `<dados>/auto` não existe; `why_manual` devolve `entrypoint`; a saída é a de hoje para essa entrada | tirar o `entrypoint`; ler o ambiente em vez do transcript |
| `test_auto_without_entrypoint_is_manual` | `mode: auto`, `bypassPermissions`, transcript sem nenhum `"entrypoint"` | `<dados>/auto` não existe; `why_manual` devolve `entrypoint`; a saída é a de hoje | tratar `entrypoint` ausente como `cli` |
| `test_auto_needs_bypass_permissions` | `mode: auto`, modo `default` | texto manual; `systemMessage` com `bypassPermissions` | tirar o `permissao` |
| `test_auto_request_names_absolute_paths_and_writes_pedido` | acima | acima | tirar a frase da O9 do texto |
| `test_manual_list_kit_and_lean_stay_manual` | uma skill da loja, uma lean e uma em `manual`, no mesmo Stop | um pedido só com a da loja; o texto manual das outras duas presente | tirar `kit-ou-lean` ou `lista-manual` |
| `test_second_skill_of_the_same_plugin_is_recorded` | duas skills do mesmo plugin carregadas; a segunda em `manual` | `entry["skills"]` tem as duas; a entrada cai em `lista-manual` | guardar só a primeira skill |
| `test_auto_dry_is_requested_like_auto` | `mode: auto-dry` | `pedido["modo"] == "auto-dry"` | — |
| `test_store_missing_or_not_the_marketplace_is_manual` | sem `store`; `store` num repo de terceiro | texto manual, motivo `sem-loja` | tirar a conferência do `marketplace.json` |
| `test_session_cap_reached_asks_manually` | 3 linhas de lote da sessão no registro | texto manual, motivo `teto` | trocar `>=` por `>` |
| `test_flow_in_progress_counts_no_work_or_friction` | depois do pedido: `licoes.json` gravado, 6 erros de ferramenta, Stop novo sem `stop_hook_active` | `None`; `work == friction == 0` no estado | tirar o silêncio do `_bump` |
| `test_open_flow_silences_a_lean_skill_too` | depois do pedido, uma skill lean é carregada e erra 3 vezes | `None`; os contadores da lean ficam em 0 | silenciar só as chaves do pedido |
| `test_no_second_request_while_a_flow_is_open` | estado com `auto_open` e outra skill da loja já elegível | `None`; um `pedido.json` só no disco | abrir pedido com fluxo aberto |
| `test_flow_without_lessons_closes_at_the_continuation_stop` | Stop com `active=True`, sem `licoes.json` | `auto_open` sai do estado | fechar só pelo TTL |
| `test_unreadable_lessons_keep_the_flow_open` | `licoes.json` com JSON quebrado; depois com uma lista no lugar do objeto | `None` nos dois; `auto_open` fica; `errors.log` não existe | tratar ilegível como "sem lições" |
| `test_flow_closes_when_every_lesson_has_a_line` | linhas no registro para todas as lições; depois 2 erros | o segundo Stop fecha; o terceiro pede a 2ª retro | fechar antes de varrer |
| `test_stale_open_flow_expires` | `auto_open.ts` com 7 h | o atrito volta a contar | tirar o TTL |
| `test_auto_failure_falls_back_to_manual` | `rw_auto.py` trocado, na cópia do teste, por um módulo que levanta ao importar | o texto manual sai; uma linha no `errors.log` | tirar o `try` |
| `test_auto_text_stays_ascii_on_cp1252_stdout` | `env=WINDOWS_STDIO` | a saída é JSON válido | — |
| `test_new_modules_do_not_import_fcntl` | o fonte de cada `rw_*.py` | `"fcntl"` ausente | — |

- [ ] **Step 3:** Rode. Esperado: falha por `rw_auto` ausente.
- [ ] **Step 4:** Implemente. O hook não chama o git no `store`.
- [ ] **Step 5:** Rode os dois arquivos de teste. Esperado: `OK`, e os 54 antigos continuam.
- [ ] **Step 6:** Mate os mutantes. `check-private-names.py` rc 0. Commit: `feat(retrofit-watch): modo auto na config e pedido autônomo no Stop hook`.

---

### Task 5: A triagem e os verbos do registro

**Files:**
- Modify: `$W/scripts/rw_auto.py`, `$W/scripts/retrofit_watch.py` (`main`, `cmd_queue`)
- Test: `$W/tests/test_auto_formats.py`

**A triagem, lição por lição. Primeiro o pedido, depois a classificação (spec 5.4, com a O3). Vale a primeira condição que casar:**

| Condição | Destino | Motivo |
|---|---|---|
| o plugin não está em `pedido.skills`, ou está em `ctx.excluded`, ou a skill da lição está em `ctx.manual` | `segurar` | `fora-do-pedido` |
| lição sem parecer no veredito | `segurar` | `sem-veredito` |
| `coberta` preenchida | `descartar` | `coberta` |
| `generica` falso | `descartar` | `do-projeto` |
| `procede == "nao-procede"` | `descartar` | `nao-procede` |
| `evidencia_confere` falso | `descartar` | `sem-evidencia` |
| `nao_capturar` preenchido | `descartar` | `nao-capturar` |
| `nao-reproduzivel` e `basta_o_transcript` nulo | `segurar` | `nao-reproduzivel` |
| `resolveu` nulo | `segurar` | `sem-correcao` |
| `muda_description` verdadeiro | `ramo-pronto` | `muda-description` |
| o resto | `publicar` | — |

**Interfaces:**
- Consumes: `Malformed`, `retro_dir`, `lote_dir`, `read_registry`, `append_registry` (Tarefa 4); `ctx.excluded`, `ctx.manual`.
- Produces, em `rw_auto.py`:
  - `LICAO_KEYS`, `EVIDENCIA_KEYS`, `PARECER_KEYS`, `TERMO_KEYS`, `ANONIMATO_KEYS`, `RETROFIT_KEYS`: conjuntos com as chaves da seção *Formatos e motivos*. `LESSON_REASONS`, `OWNER_REASONS`, `AGENT_REASONS`.
  - `load_pedido(path)`, `load_licoes(path) -> dict[str, dict]`, `load_veredito(path) -> dict[str, dict]`, `load_retrofit(path) -> dict` (a `tentativa` é um inteiro a partir de 1), `load_anonimato(path) -> dict`. `Malformed` nomeia o arquivo e o campo. Chave a mais, chave faltando e valor fora do domínio são `Malformed`.
  - `in_request(ctx, pedido, licao) -> bool`: a primeira linha da tabela. A Tarefa 8 a usa de novo.
  - `classify(licao, parecer) -> tuple[str, str | None]`: as outras linhas.
  - `triage(ctx, rid) -> dict`: `{"lotes": [{"lote", "plugin", "tipo", "licoes"}], "segurar": [...], "descartar": [...]}`. Os lotes `auto` vêm antes dos `description`. Grava uma linha `segurado` ou `descartado` por lição sem ramo. Rodar de novo não repete linha.
  - `last_lines(registry) -> dict[str, dict]`: a última linha de cada `item`.
  - `held(ctx) -> list[dict]`: os itens cuja última linha é `segurado` ou `erro`.
  - `hold_item(ctx, rid, item, motivo, detalhe="") -> dict`: linha `segurado`. Motivo fora de `AGENT_REASONS` é `Malformed`.
  - `approve(ctx, rid, lote) -> Path`: acrescenta a `aprovado.json["motivos"]` o motivo da última linha `segurado` do lote, sem repetir. Sem linha `segurado`, `Malformed`.
  - `discard(ctx, rid, item, motivo="descartado-pelo-dono") -> dict`: linha `descartado`. Motivo fora de `OWNER_REASONS` é `Malformed`.
- Produces, em `retrofit_watch.py`:
  - `data_dir_problem(ctx) -> str | None`: a recusa que hoje mora no `cmd_queue` (pasta de dados ausente ou ambígua), tirada para uma função. O `cmd_queue` passa a usá-la e mantém o rc 1.
  - `cli(argv, ctx) -> int` para os subcomandos de linha de comando novos. Antes de qualquer um, `data_dir_problem`: com problema, rc 2 e a mensagem no stderr. rc 0 certo, 1 recusado, 2 uso ou `Malformed` (stderr, sem traceback). Nesta tarefa: `triage <id>`, `held`, `hold <id> <item> <motivo>`, `approve <id> <lote>`, `discard <id> <item> [--motivo M]`. Todos imprimem JSON em ASCII.

- [ ] **Step 1: Escreva os testes que falham.**

| Teste | Entrada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_classification_table` | uma linha da tabela por `subTest`, mudando um campo de uma lição publicável | o destino e o motivo da linha | tirar cada condição, uma por vez |
| `test_unconfirmed_evidence_and_do_not_capture_are_discarded` | `evidencia_confere` falso; `nao_capturar` preenchido | linha `descartado` com o motivo; `held()` vazio | mandar os dois para `segurar` |
| `test_covered_wins_over_description` | `coberta` e `muda_description` juntos | `descartar` | trocar a ordem |
| `test_lesson_outside_the_request_is_held` | lição de um plugin que não está em `pedido.skills`; de `retrofit-skill` (sempre excluído); de uma skill em `manual` | as três em `segurar` com `fora-do-pedido`; nenhuma num lote | tirar cada uma das três condições |
| `test_triage_splits_lotes_and_orders_auto_first` | plugin A com 2 publicáveis e 1 de `description`; plugin B com 1 publicável | lotes `A`, `B`, `A__description`, nessa ordem | juntar tudo num lote |
| `test_triage_writes_held_and_discarded_lines_once` | 1 `sem-correcao`, 1 `coberta`; duas chamadas | 2 linhas no registro, não 4 | tirar a idempotência |
| `test_malformed_verdict_is_a_refusal_not_a_traceback` | chave a mais; `procede` fora do domínio; BOM; cerca de código; lista no lugar de objeto | `Malformed` nomeando o campo; pela CLI, rc 2 e stderr sem `Traceback` | tirar a validação de domínio |
| `test_anonimato_without_the_judgement_keys_is_malformed` | `anonimato.json` sem `regra_repetida`; sem `fora_das_licoes`; sem `patch` | `Malformed` nos três | tratar chave ausente como `null` |
| `test_lesson_missing_from_verdict_is_held` | `veredito.json` sem a `L2` | `L2` em `segurar` com `sem-veredito` | tratar ausente como publicável |
| `test_path_traversal_in_id_or_lote_is_refused` | `../x` | `Malformed` | tirar o padrão |
| `test_held_lists_only_open_items` | um segurado, um segurado e depois publicado, um descartado | só o primeiro | ler a primeira linha em vez da última |
| `test_approve_needs_a_held_lote` | lote sem linha `segurado` | rc 2; `aprovado.json` ausente | aprovar sem linha |
| `test_approve_appends_each_reason` | segurado por `muda-description`, `approve`; depois segurado por `teto`, `approve` | `motivos == ["muda-description", "teto"]` | sobrescrever a lista |
| `test_discard_accepts_resolved_by_hand` | `discard … --motivo resolvido-manual`; depois um motivo inventado | linha `descartado` com o motivo; depois rc 2 | aceitar qualquer motivo |
| `test_new_subcommands_refuse_a_missing_or_ambiguous_data_dir` | sem `CLAUDE_PLUGIN_DATA` e sem pasta; com duas pastas | rc 2 e a mensagem do `queue` em cada subcomando novo | pular a conferência |
| `test_cli_output_is_valid_json_on_cp1252` | `held` com detalhe acentuado, `PYTHONIOENCODING=cp1252` | rc 0 e JSON válido | `ensure_ascii=False` |

- [ ] **Step 2:** Rode. Esperado: falha por função ausente.
- [ ] **Step 3:** Implemente.
- [ ] **Step 4:** Rode a suíte do plugin. Esperado: `OK`, com os testes do `queue` inalterados.
- [ ] **Step 5:** Mate os mutantes. `check-private-names.py` rc 0. Commit: `feat(retrofit-watch): triagem e registro do modo autônomo`.

---

### Task 6: A loja fixture

**Files:**
- Create: `$W/tests/fixture_store.py`, `$W/tests/test_fixture_store.py`

**Interfaces:**
- Consumes: `World`, `git`, `GIT_ENV` de `test_retrofit_watch.py`; `scripts/anonymity-gate.py` (Tarefas 2 e 3).
- Produces, em `fixture_store.py`:
  - `class StoreWorld(World)`:
    - `origin`: repo `--bare` sob o diretório temporário. `store`: o clone, que faz o papel do checkout compartilhado. O `origin` do `World.repo` herdado, que é a URL real da loja, é trocado pelo `origin` da fixture no `__init__`.
    - dois plugins, `demo` e `demo2`, na 1.0.0, cada um com `SKILL.md`, `CHANGELOG.md`, `skills/<nome>/tests/test_<nome>.py`, bloco no `marketplace.json` e linha no README.
    - a raiz traz as cópias de `scripts/` da loja real, o `install.py`, o `audit_skill_quality.py` (sem o `SKILL.md` dele), o `audit_gate.py` do `retrofit-skill` e um `tests/test_root.py` mínimo.
    - a config do HOME fixture tem `mode: auto` e `store`.
  - `StoreWorld.retro(licoes, pareceres, skills=("demo",)) -> str`: grava `pedido.json`, `licoes.json` e `veredito.json` e devolve o `id`.
  - `StoreWorld.retrofit(wt, plugin="demo", files=None, message=None, version="1.0.1", trailer="Retrofit-Mode: autonomous") -> str`: faz no worktree um commit de retrofit completo (arquivos, `plugin.json`, metadata do `SKILL.md`, `CHANGELOG`, `marketplace.json`, README) e devolve o sha.
  - `StoreWorld.advance_origin(files, message, date=None) -> str`: um commit no `origin` vindo de outro clone.
  - `StoreWorld.origin_main() -> str`, `StoreWorld.shared_state() -> tuple` ((HEAD, ramo atual, `status --porcelain`) do clone).
  - `StoreWorld.assert_fixture_origin(path)`: levanta `AssertionError` quando o `origin` do repo em `path` não está sob o diretório temporário. O `push` da fixture (Tarefa 9) chama isto antes de empurrar.
  - `requires_store`: decorador que pula o teste quando a raiz da loja real não está acima do arquivo (cópia instalada) ou quando falta o PyYAML.

- [ ] **Step 1: Escreva os testes que falham.**

| Teste | Asserção |
|---|---|
| `test_fixture_passes_its_own_gates` | `validate-versions.py` rc 0 na fixture; os testes do `demo`, do `demo2` e o `tests/test_root.py` passam; a auditoria do `demo` não tem ERRO |
| `test_every_remote_is_under_the_temp_dir` | o `origin` de `store` e o de `World.repo` começam pelo diretório temporário; nenhum remoto tem `github` |
| `test_assert_fixture_origin_rejects_a_real_remote` | um repo com `origin` em https faz `assert_fixture_origin` levantar |
| `test_retrofit_helper_makes_a_valid_full_mode_commit` | depois de `retrofit()`: `validate-versions.py` rc 0; um commit à frente do `origin/main`; o trailer presente |
| `test_broken_fixture_is_caught_by_the_real_gates` | `retrofit()` seguido de uma versão diferente no `marketplace.json`: `validate-versions.py` rc 1 |
| `test_advance_origin_moves_origin_main` | depois de `advance_origin` e de um `fetch`, o `origin/main` do clone é o sha novo |

- [ ] **Step 2:** Rode. Esperado: falha por módulo ausente.
- [ ] **Step 3:** Implemente a fixture.
- [ ] **Step 4:** Rode a suíte do plugin. Esperado: `OK`. Anote o tempo de criar uma `StoreWorld`.
- [ ] **Step 5:** `check-private-names.py` rc 0. Commit: `test(retrofit-watch): loja fixture com origin bare para a porta`.

---

### Task 7: A colheita, `prepare` e `seal`

**Files:**
- Create: `$W/scripts/rw_store.py`, `$W/tests/test_auto_store.py`
- Modify: `$W/scripts/retrofit_watch.py` (`cli`)

**Interfaces:**
- Consumes: `Context.store`, `Context.harvest_roots`, `Context.private_sources` (Tarefa 4); `triage`, `load_pedido`, `load_retrofit`, `lote_dir` (Tarefa 5); `StoreWorld` (Tarefa 6); a CLI do `scripts/anonymity-gate.py`.
- Produces, em `rw_store.py`:
  - `RUN_TIMEOUT = 900`, `MIN_WORD = 4`, `PHASES = {"claim-check", "self-containment", "refactoring"}`.
  - `class StoreError(Exception)`.
  - `run(cmd: list, cwd=None, timeout=RUN_TIMEOUT) -> tuple[int, str]`: rc e saída juntos. Timeout dá rc 124; binário ausente, rc 127. Nunca levanta. O `_git` de 2 s não se usa neste módulo.
  - `store_clone(ctx) -> Path`: `ctx.store`, ou `StoreError` quando é `None`. Não repete a conferência.
  - `expand(term) -> set[str]`: o termo; e, quando ele tem 2 ou mais palavras, cada par de palavras vizinhas nas duas formas (`a b` e `a_b`) e cada palavra com `MIN_WORD` letras ou mais.
  - `harvest(ctx, cwd=None) -> set[str]`, já passado pelo `expand`: o nome da pasta de cada repo git sob `harvest_roots` até a profundidade 2, o dono e o nome de cada `origin`, o `user.name` e o e-mail do git, o nome da pasta do HOME, o hostname, cada linha das `private_sources` e, com `cwd`, o nome da raiz e o dono e o nome do `origin` do repo do `cwd` (O5).
  - `write_harvest(ctx, cwd=None) -> Path`: grava `<dados>/colheita.txt`, um termo por linha, com permissão `0o600`.
  - `worktree_path(ctx, rid, lote, tentativa=1) -> Path` (`~/.wt/retrofit-auto-<lote>-<rid>`, com `-r<n>` a partir da segunda) e `branch_name(rid, lote, tentativa=1) -> str` (`retrofit-auto/<lote>-<rid>`, com o mesmo sufixo).
  - `prepare(ctx, rid, lote, redo=False) -> dict`: `git fetch origin` no clone; `git worktree add -b <ramo> <worktree> origin/main`; grava e devolve o `retrofit.json`. Chamado de novo, devolve o que já existe. Com `redo`, só quando a última linha do lote é `segurado` por `rebase`: abre a tentativa seguinte e deixa a anterior no lugar.
  - `patch_id(worktree) -> str` (D20).
  - `layer1(ctx, rid, worktree) -> list[str]`: **colhe de novo a cada chamada**, com o `cwd` do `pedido.json`, e roda `anonymity-gate.py --camada1 --base origin/main --extra <colheita>` do worktree.
  - `new_terms(worktree) -> list[dict]`.
  - `seal(ctx, rid, lote, licoes: list[str], fases: list[str]) -> dict`: confere que cada lição é do lote pela triagem e que cada fase está em `PHASES`; completa `retrofit.json` com `licoes`, `fases`, `commit`, `versao` e `patch`; grava `termos-novos.json`; roda a camada 1. Devolve `{"commit", "versao", "patch", "termos", "camada1"}`.
- Produces, na CLI: `prepare <id> <lote> [--redo]`; `seal <id> <lote> --licoes L1,L2 [--fases a,b]` (rc 1 com achado da camada 1); `harvest`, que imprime só `{"termos": N, "arquivo": "<caminho>"}`.

- [ ] **Step 1: Escreva os testes que falham.**

| Teste | Entrada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_run_reports_timeout_and_missing_binary` | um comando que dorme, com timeout de 1 s; um binário que não existe | rc 124; rc 127; nenhuma exceção | deixar a exceção subir |
| `test_prepare_creates_a_linked_worktree_from_origin_main` | `advance_origin` antes | o worktree é `worktree_path(...)`; o ramo é `branch_name(...)`; `base` é o sha novo do `origin/main` | tirar o `fetch` |
| `test_prepare_leaves_the_shared_checkout_untouched` | arquivo sujo no clone | `shared_state()` igual antes e depois | criar o ramo com `checkout -b` no clone |
| `test_prepare_is_idempotent` | duas chamadas | o mesmo `retrofit.json`; um worktree só | criar de novo |
| `test_redo_opens_the_next_attempt_only_after_a_rebase_hold` | `--redo` sem linha; depois com a linha `segurado` por `rebase` | rc 2; depois `tentativa == 2`, worktree e ramo com `-r2`, e os da tentativa 1 ainda existem | aceitar `--redo` sempre |
| `test_store_missing_is_an_error_with_the_reason` | config sem `store` | `StoreError`; pela CLI, rc 2 | — |
| `test_expand_breaks_a_long_name` | um nome de três palavras | os dois pares, nas duas formas, e as palavras de 4 letras ou mais; a palavra de 2 letras fica fora | tirar os pares; tirar o piso |
| `test_harvest_collects_every_source` | HOME fixture com 2 repos, um não-repo, `.gitconfig` e uma `private_sources` | cada fonte da lista aparece; a pasta que não é repo não | tirar uma fonte |
| `test_harvest_includes_the_session_project` | `cwd` num repo fora de `harvest_roots` | o nome da raiz, o dono e o nome do `origin` dele aparecem; sem `cwd`, não | ignorar o `cwd` |
| `test_harvest_respects_depth_and_survives_bad_roots` | repo no nível 3; raiz inexistente | o do nível 3 fica fora; nenhuma exceção | tirar o limite de profundidade |
| `test_harvest_cli_prints_no_name` | `harvest` pela CLI | stdout sem nenhum termo colhido; o arquivo existe fora de qualquer repo | imprimir a lista |
| `test_layer1_harvests_again_on_every_call` | `colheita.txt` antigo e vazio no disco; commit com o nome de um repo do HOME fixture | o achado aparece | reusar o arquivo |
| `test_patch_id_survives_a_rebase_and_changes_with_content` | rebase sobre um commit alheio; emenda de uma linha; mudança só em `public-names.txt` | igual; diferente; igual | incluir os `@@`; incluir os arquivos de lista |
| `test_seal_writes_terms_patch_and_reports_layer1` | commit com um nome colhido numa linha nova | rc 1; `camada1` nomeia arquivo e linha; `termos-novos.json` tem `patch` | não passar `--extra` |
| `test_seal_refuses_a_lesson_from_another_lote` | `--licoes` com a lição de `description` no lote `auto` | rc 2; `retrofit.json` sem `commit` | tirar a conferência |
| `test_seal_refuses_an_unknown_phase` | `--fases revisao-geral` | rc 2 | aceitar qualquer fase |

- [ ] **Step 2:** Rode. Esperado: falha por módulo ausente.
- [ ] **Step 3:** Implemente.
- [ ] **Step 4:** Rode a suíte do plugin. Esperado: `OK`.
- [ ] **Step 5:** Mate os mutantes. `check-private-names.py` rc 0. Commit: `feat(retrofit-watch): colheita, worktree do lote e selo do executor`.

---

### Task 8: A porta — as recusas

**Files:**
- Create: `$W/scripts/rw_gate.py`, `$W/tests/test_auto_gate.py`

**Interfaces:**
- Consumes: `StoreWorld` (Tarefa 6); `load_*`, `in_request`, `classify`, `used`, `append_registry` (Tarefas 4 e 5); `run`, `store_clone`, `worktree_path`, `branch_name`, `layer1`, `new_terms`, `patch_id` (Tarefa 7).
- Produces:
  - `OVERRIDABLE`, `ERRORS`, `GATE_REASONS`: os conjuntos da seção *Formatos e motivos*.
  - `SCOPE` (prefixos e arquivos que um retrofit pode tocar: `plugins/<plugin>/`, `.claude-plugin/marketplace.json`, `README.md`, `.agents/plugins/marketplace.json`, `docs/codex/compatibility.md`, `docs/codex/smokes.json`) e `OWNER_ONLY = ("scripts/private-names.sha256", "scripts/public-names.txt")`.
  - `SKILL_MAX_LINES = 400`, `SKILL_MAX_CHARS = 16000`.
  - `refuse(ctx, rid, lote, notes: list) -> tuple[str, str] | None`: `(motivo, detalhe)` da primeira guarda que reprova, ou `None`. O que a porta pulou entra em `notes`.
  - `hold(ctx, rid, lote, motivo, detalhe) -> dict`: grava a linha `segurado`, ou `erro` quando o motivo está em `ERRORS`, e a devolve.

**A ordem das guardas em `refuse`:**

| Ordem | Guarda | Motivo | Spec 5.7 |
|---|---|---|---|
| 1 | o worktree é `worktree_path(rid, lote, tentativa)` e o ramo é `branch_name(...)`: os dois saem do `<id>`, do `<lote>` e da `tentativa`, nunca dos campos `worktree` e `ramo` do `retrofit.json`. O worktree não é o clone do `store`. O ramo atual é o esperado e não é `main` | `escopo` | D9 |
| 2 | `git status --porcelain` vazio | `arvore-suja` | D9 |
| 3 | `git fetch origin` | `fetch` | 6 |
| 4 | `git rebase origin/main`; com conflito, `git rebase --abort` | `rebase` | 6 |
| 5 | um commit só em `origin/main..HEAD`; cada caminho em `SCOPE`; `OWNER_ONLY` só com `aprovado.json` | `escopo` | D9 |
| 6 | o commit não tem `Co-authored-by` | `coautoria` | 5 |
| 7 | o trailer `Retrofit-Mode` é `autonomous`; com `aprovado.json`, também vale `autonomous-approved` | `sem-marca` | 5 |
| 8 | `veredito.json` existe e é válido | `sem-veredito` | 1 |
| 9 | cada lição do `retrofit.json` é do plugin do lote e passa em `in_request` | `fora-do-pedido` | D24 |
| 10 | cada lição classifica como `publicar`; no lote `description`, `ramo-pronto` reprova com `muda-description` | `nao-publicavel`, `muda-description` | 1 |
| 11 | `layer1` vazia | `nome-privado` | 3 |
| 12 | `anonimato.json` existe e é válido | `sem-anonimato` | 2 |
| 13 | `anonimato["patch"] == patch_id(worktree)` | `revisao-desatualizada` | D20 |
| 14 | cada termo de `new_terms`, recalculado agora, está no `anonimato.json` como `publico` | `termo-nao-publico` | 2 |
| 15 | `regra_repetida` é `null` | `regra-repetida` | O2 |
| 16 | `fora_das_licoes` é `null` | `diff-alem-das-licoes` | O8 |
| 17 | os testes do plugin e os da raiz passam (D11) | `testes` | 4 |
| 18 | `validate-versions.py` rc 0 | `validate-versions` | 4 |
| 19 | a auditoria, abaixo | `auditoria`, `fase-de-auditoria` | 4, O4 |
| 20 | `used` abaixo de `auto_limits`, sem contar este lote | `teto` | 7 |
| 21 | `ctx.mode` não é `auto-dry` | `auto-dry` | 8 |

Com `aprovado.json`, é pulada cada guarda cujo motivo está em `aprovado["motivos"]` **e** em `OVERRIDABLE`. Todas as outras rodam. `retrofit.json` ausente ou inválido é `Malformed` (rc 2), sem linha no registro.

**A guarda 19.** Leia antes, no `$R/commands/retrofit-skill.md`, as seções *Localizar o auditor e os scripts deste comando* (linhas ~85–124) e *Gate da auditoria* (linhas ~324–334): é o mesmo gate, rodado pela porta.
- O auditor é `$Q/skill-quality-audit/scripts/audit_skill_quality.py` do worktree, e o comparador é `$R/scripts/audit_gate.py` do worktree. Qualquer um dos dois ausente segura com `auditoria`.
- Para cada skill do plugin: `antes.json` sai da base (`git archive origin/main plugins/<plugin>`, lido com `tarfile`, num diretório temporário fora do repo) e `depois.json` do worktree, os dois com `--format json --claims --desc-budget 0 --external off`. O `diff.txt` é `git diff -U0 origin/main...HEAD -- <dir da skill>`. Skill nova não tem `antes.json`: o baseline é uma lista vazia de achados.
- rc 2 do auditor é uso inválido, e segura com `auditoria`. Linha `NOVO` do `audit_gate.py` segura com `auditoria`.
- Plugin sem nenhum `SKILL.md` (só de comandos): a guarda é pulada, e `notes` ganha `auditoria: plugin sem SKILL.md`.
- As fases (D21), com motivo `fase-de-auditoria` e a fase que falta no `detalhe`:

  | Gatilho mecânico | Fase exigida em `retrofit.json["fases"]` |
  |---|---|
  | alguma linha `CLAIM` na saída do `audit_gate.py` | `claim-check` |
  | o commit cria arquivo sob `references/`, `scripts/` ou `assets/` de uma skill | `self-containment` |
  | um `SKILL.md` que o commit tocou passa de `SKILL_MAX_LINES` ou de `SKILL_MAX_CHARS` | `refactoring` |

- [ ] **Step 1: Escreva os testes que falham.** Cada teste parte de `clean_retrofit(**sabotagem) -> (rid, worktree)`, um auxiliar da classe de teste que monta um retrofit limpo do `demo` com veredito, selo e `anonimato.json`, e sabota uma coisa. Todos terminam conferindo que `origin_main()` não mudou. Modelo:

```python
def test_co_authored_by_refuses(self):
    rid, wt = self.clean_retrofit(message="fix(demo): v1.0.1\n\nCo-Authored-By: " + "x <x" + "@" + "x.dev>")
    self.assertEqual(rg.refuse(self.ctx, rid, "demo", [])[0], "coautoria")
    self.assertEqual(self.w.origin_main(), self.base)
```

| Teste | Sabotagem | Motivo esperado | Mutante que ele mata |
|---|---|---|---|
| `test_clean_retrofit_passes_every_guard` | nenhuma | `refuse` devolve `None` | — |
| `test_retrofit_json_cannot_point_the_gate_elsewhere` | `retrofit.json` com `worktree` no clone do `store` e `ramo: "main"` | a porta olha o worktree derivado e passa; o clone não é tocado | ler o worktree do `retrofit.json` |
| `test_the_store_clone_and_main_are_refused` | o caminho derivado trocado, no teste, por um link para o clone do `store`; depois `branch_name` trocado, no teste, para devolver `main` | `escopo` nos dois | tirar cada uma das duas recusas |
| `test_branch_other_than_the_lote_refuses` | o worktree em outro ramo | `escopo` | tirar a conferência do ramo |
| `test_dirty_worktree_refuses` | arquivo sem commit no worktree | `arvore-suja` | guarda 2 |
| `test_unreachable_origin_is_an_error_not_a_pass` | URL do `origin` trocada por um caminho que não existe | `fetch`; `hold` grava `erro` | tratar falha do `fetch` como "em dia" |
| `test_rebase_conflict_refuses_and_leaves_the_branch_intact` | `advance_origin` na mesma linha | `rebase`; o HEAD do worktree é o de antes; nenhum rebase em andamento | tirar o `--abort` |
| `test_rebase_over_unrelated_commits_passes` | `advance_origin` em outro arquivo | `None`; o HEAD do worktree tem o `origin/main` novo como pai | — |
| `test_two_commits_refuse` | segundo commit no ramo | `escopo` | guarda 5, contagem |
| `test_path_outside_scope_refuses` | o commit toca `scripts/check-private-names.py` | `escopo` | guarda 5, caminhos |
| `test_list_files_need_owner_approval` | o commit toca `scripts/public-names.txt` | `escopo`; com `aprovado.json`, passa desta guarda | `OWNER_ONLY` sempre permitido |
| `test_co_authored_by_refuses` | acima | `coautoria` | guarda 6 |
| `test_commit_without_marker_refuses` | `trailer=None` | `sem-marca` | guarda 7 |
| `test_missing_verdict_refuses` | sem `veredito.json` | `sem-veredito` | guarda 8 |
| `test_lesson_outside_the_request_refuses_at_the_gate` | `retrofit.json` com a lição de um plugin fora de `pedido.skills`; com o plugin posto em `exclude` depois da triagem | `fora-do-pedido` nos dois | guarda 9 |
| `test_lesson_not_publishable_refuses` | lição com `resolveu` nulo no `retrofit.json` | `nao-publicavel` | guarda 10 |
| `test_description_lote_is_held_as_ready_branch` | lote `demo__description` | `muda-description`; a linha de `hold` tem o ramo | — |
| `test_private_name_in_diff_refuses` | nome inventado com hash acrescentado à lista da fixture | `nome-privado` | guarda 11 |
| `test_three_word_name_in_the_commit_message_refuses` | `user.name` de três palavras no `.gitconfig` do HOME fixture; duas delas, vizinhas, na mensagem do commit | `nome-privado` | colher sem o `expand` |
| `test_session_project_name_in_diff_refuses` | o nome do repo do `cwd` do pedido numa linha nova; o repo fica fora de `harvest_roots` | `nome-privado` | passar a colheita sem o `cwd` |
| `test_missing_anonimato_refuses` | sem `anonimato.json` | `sem-anonimato` | guarda 12 |
| `test_review_of_an_older_diff_refuses` | emenda uma linha do commit depois do `anonimato.json`, sem selar de novo | `revisao-desatualizada` | guarda 13 |
| `test_term_in_doubt_refuses` | um termo com `duvida` | `termo-nao-publico` | aceitar `duvida` |
| `test_term_only_in_the_message_refuses` | emenda só a mensagem, com um nome novo, depois do `anonimato.json` | `termo-nao-publico` | ler `termos-novos.json` em vez de recalcular |
| `test_repeated_rule_refuses` | `regra_repetida` com texto | `regra-repetida` | guarda 15 |
| `test_diff_beyond_the_lessons_refuses` | `fora_das_licoes` com texto | `diff-alem-das-licoes` | guarda 16 |
| `test_failing_plugin_test_refuses` | o commit quebra `test_demo.py` | `testes` | guarda 17 |
| `test_failing_root_test_refuses` | `tests/test_root.py` que falha, vindo do `origin` | `testes` | pular a suíte da raiz |
| `test_version_out_of_sync_refuses` | `plugin.json` em 1.0.1 e `marketplace.json` em 1.0.0 | `validate-versions` | guarda 18 |
| `test_new_audit_finding_refuses` | o commit põe um campo de topo fora da spec no `SKILL.md` | `auditoria` | guarda 19, `NOVO` |
| `test_old_audit_debt_does_not_refuse` | o mesmo defeito já no `origin/main` | `None` | comparar sem a base |
| `test_missing_auditor_refuses` | a fixture sem o `audit_skill_quality.py` | `auditoria` | tratar auditor ausente como aprovado |
| `test_plugin_without_skill_md_skips_the_audit_with_a_note` | um plugin só de comandos na fixture | `None`; `notes` tem a frase | — |
| `test_missing_audit_phase_refuses` | um `subTest` por gatilho: linha nova com uma medida datada; arquivo novo em `references/`; `SKILL.md` com 401 linhas; cada um sem a fase e depois com ela | `fase-de-auditoria` com a fase no `detalhe`; depois `None` | tirar cada gatilho |
| `test_caps_refuse` | 2 linhas de outros ids do `demo` na sessão; 3 lotes de outros plugins; `auto_limits` na config mudando o teto | `teto`, `teto`, `None` | trocar `>=` por `>` |
| `test_auto_dry_refuses_last` | `mode: auto-dry` com um retrofit limpo; depois com um teste quebrado | `auto-dry`; depois `testes` | pôr a guarda 21 no começo |
| `test_approval_replaces_only_the_reasons_it_lists` | `aprovado.json` com `muda-description` e um teste quebrado; depois com `["muda-description", "teto"]` e o teto atingido | `testes`; depois `None` | pular todas as guardas com aprovação |
| `test_approval_never_replaces_a_name_refusal` | `aprovado.json` com `nome-privado`, `termo-nao-publico` e `sem-anonimato`, e cada defeito ainda presente | o motivo de cada defeito | tirar a conferência de `OVERRIDABLE`; pôr os motivos de nome em `OVERRIDABLE` |

- [ ] **Step 2:** Rode. Esperado: falha por módulo ausente.
- [ ] **Step 3:** Implemente `refuse` e `hold`. Todo comando sai por `rw_store.run`, com `sys.executable` para os scripts Python.
- [ ] **Step 4:** Rode a suíte do plugin. Esperado: `OK`. Anote o tempo do arquivo novo no relatório.
- [ ] **Step 5:** Mate os mutantes da tabela, um por vez.
- [ ] **Step 6:** `check-private-names.py` rc 0. Commit: `feat(retrofit-watch): as guardas da porta de publicação`.

---

### Task 9: A porta — publicar, liberar e registrar

**Files:**
- Modify: `$W/scripts/rw_gate.py`, `$W/scripts/retrofit_watch.py` (`cli`, `_lock`)
- Test: `$W/tests/test_auto_gate.py`

**Interfaces:**
- Consumes: `refuse`, `hold`, `OVERRIDABLE` (Tarefa 8); `State`, `_unlock`, `MAX_REVIEWS` de `retrofit_watch.py`; `assert_fixture_origin` (Tarefa 6).
- Produces:
  - `retrofit_watch._lock(path, timeout=None)`: sem `timeout`, o comportamento de hoje. Com `timeout`, tenta a trava sem bloquear, a cada 0,5 s, e levanta `OSError` no prazo.
  - `PUBLISH_LOCK_WAIT = 900`.
  - `class Effects`, com `push(worktree) -> tuple[bool, str]` (`git push origin HEAD:main`, sem força), `refresh_install(plugin) -> tuple[bool, str]` (`claude plugin marketplace update <loja>` e `claude plugin update <plugin>@<loja> --scope user`, com o binário de `shutil.which("claude")`; sem ele, `(False, "claude ausente")`; plugin fora do escopo `user`, `(True, "nao-instalado")`) e `cache_matches(ctx, worktree, plugin, versao) -> tuple[bool, str]` (compara `plugins/<plugin>` do worktree com `~/.claude/plugins/cache/<loja>/<plugin>/<versao>`, fora o `.in_use`).
  - `already_published(worktree, retrofit) -> bool`: o HEAD não é a `base` do `retrofit.json` e é ancestral do `origin/main`.
  - `publish(ctx, rid, lote, effects) -> dict`: a última linha gravada no registro. `effects` é obrigatório. Nunca levanta.
  - `mark_done(ctx, session, key) -> None`: no estado da sessão, sob a trava dele, põe a chave em `done` e `reviews = MAX_REVIEWS`.
  - CLI: `publish <id> <lote>`. rc 0 publicado e instalado; 1 segurado; 2 uso; 3 erro; 4 publicado com a instalação falha. Imprime a linha em JSON e, na última linha do stdout, a frase da spec 5.1: `retrofit-watch: <plugin> vX.Y.Z publicada sozinha (<sha>)` ou `retrofit-watch: <plugin> segurada — <motivo> (ramo <ramo>)`, em ASCII com escape. No rc 4, a primeira frase ganha ` — cópia instalada não atualizada: <motivo>`.

**A sequência de `publish` (D22, D25):**
1. Prende `<dados>/publish.lock` com `_lock(path, PUBLISH_LOCK_WAIT)` até o fim. `OSError` na trava: linha `erro`, motivo `trava`.
2. `git fetch origin`. Com `already_published`, pula para o passo 6.
3. `refuse`. Com recusa, `hold` e fim.
4. Com `aprovado.json`: troca o trailer por `Retrofit-Mode: autonomous-approved` com `commit --amend`. A árvore do commit tem de ficar igual.
5. `effects.push`. Falha: linha `erro`, motivo `push`. Certo: linha `publicado` **agora**, com `commit`, `versao`, `ramo`, `licoes`, `aprovado` e `instalacao: "pendente"`, e `mark_done` para a sessão do `pedido.json`.
6. `effects.refresh_install`, depois `effects.cache_matches` quando o plugin está instalado. Uma segunda linha `publicado` fecha o campo: `ok`, `nao-instalado`, `update` ou `cache-difere`.
7. Qualquer exceção, em qualquer passo: linha `erro`, motivo `interno`, com o tipo e a mensagem no `detalhe`, e rc 3.

- [ ] **Step 1: Escreva os testes que falham.** `FixtureEffects(Effects)` herda o `push` real, chama `assert_fixture_origin` antes dele, e troca `refresh_install` por uma cópia do plugin para o cache do HOME fixture, com as chamadas anotadas.

| Teste | Entrada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_publish_pushes_exactly_the_reviewed_commit` | retrofit limpo | `origin_main()` é o HEAD do worktree; um commit a mais; o trailer é `autonomous`; a última linha é `publicado` com `instalacao: "ok"` | publicar outro ref |
| `test_refused_retrofit_never_reaches_the_effects` | retrofit sem veredito | nenhuma chamada anotada; `origin_main()` igual | chamar o `push` antes do `refuse` |
| `test_rejected_push_is_an_error_and_keeps_the_branch` | `push` que devolve `(False, …)` | linha `erro`, motivo `push`; o ramo existe; nenhum `refresh_install` | seguir depois do push falho |
| `test_install_failure_after_push_is_still_published` | `refresh_install` que devolve falso | rc 4; duas linhas `publicado`, a última com `instalacao: "update"` e o `commit`; a sessão marcada como feita | gravar `erro` no lugar de `publicado` |
| `test_cache_mismatch_is_recorded_in_the_install_field` | o `refresh_install` copia uma versão alterada | rc 4; `instalacao: "cache-difere"` | não comparar |
| `test_rerun_after_push_redoes_only_the_install` | primeira chamada com `refresh_install` falho; depois o `veredito.json` é apagado e a segunda chamada tem os efeitos certos | nenhum `push` na segunda; rc 0; `instalacao: "ok"`; `origin_main()` igual ao da primeira | rodar `refuse` de novo num lote já publicado |
| `test_crash_after_push_is_recovered_by_a_rerun` | `refresh_install` que levanta `RuntimeError` | rc 3; linha `erro`, motivo `interno`; o commit está no `origin`; a segunda chamada dá rc 0 | deixar a exceção subir |
| `test_fresh_worktree_is_not_taken_as_published` | lote recém-preparado, sem commit, com o `origin/main` terminando num commit autônomo de outro lote | `already_published` falso | tirar a comparação com a `base` |
| `test_lock_failure_is_an_error_line` | `rw._lock` trocado por uma função que levanta `OSError` | rc 3; linha `erro`, motivo `trava`; `origin_main()` igual | prender a trava fora do `try` |
| `test_lock_wait_has_a_deadline` | a trava presa por outro descritor; `_lock(path, timeout=1)` | `OSError` em menos de 5 s (só onde há `fcntl`) | bloquear sem prazo |
| `test_the_lock_is_held_during_the_push` | o `push` do teste tenta a trava com `timeout=0` | a tentativa falha | soltar a trava antes do push |
| `test_plugin_not_installed_is_still_published` | `refresh_install` devolve `nao-instalado` | rc 0; `instalacao: "nao-instalado"`; `cache_matches` não é chamado | — |
| `test_published_skill_is_silenced_in_the_session_state` | publica; depois 3 erros de ferramenta e um Stop | o hook devolve `None` | tirar o `mark_done` |
| `test_second_gate_rebases_over_the_first_publication` | um lote do `demo` e um do `demo2`, da mesma base; publica um, depois o outro | os dois commits no `origin`; as duas versões no `marketplace.json`; o `anonimato.json` do segundo continua valendo | tirar o rebase; pôr os `@@` no `patch_id` |
| `test_second_lote_of_the_same_plugin_conflicts_and_is_held` | dois lotes do `demo` da mesma base | o segundo sai `segurado`, motivo `rebase` | — |
| `test_a_rebase_hold_can_be_redone_and_published` | o segurado acima; `prepare --redo`; novo commit, selo e segunda passada | `publicado`; o ramo da tentativa 1 ainda existe | derivar o worktree sem a `tentativa` |
| `test_owner_approval_publishes_with_the_approved_marker` | lote `description` segurado; `approve`; `publish` de novo | trailer `autonomous-approved`; linha com `aprovado: true`; a árvore do commit é a mesma | não trocar o trailer |
| `test_shared_checkout_is_untouched_by_a_publication` | publicação completa | `shared_state()` igual antes e depois | — |
| `test_fixture_push_refuses_a_real_remote` | o `origin` do worktree trocado por uma URL https | `AssertionError` antes de qualquer `git push` | — |
| `test_cli_publish_in_auto_dry_never_calls_effects` | `mode: auto-dry`, pela CLI | rc 1; `origin_main()` igual; a última linha do stdout tem `segurada` | — |
| `test_real_effects_without_claude_fail_closed` | `Effects().refresh_install` com um PATH sem `claude` | `(False, "claude ausente")`, sem exceção | — |
| `test_cli_lines_are_ascii_on_cp1252` | recusa com detalhe acentuado, `PYTHONIOENCODING=cp1252` | rc 1 e stdout decodificável | — |

- [ ] **Step 2:** Rode. Esperado: falha por `publish` ausente.
- [ ] **Step 3:** Implemente. O `_lock` sem `timeout` não muda: os 54 testes antigos são a prova.
- [ ] **Step 4:** Rode a suíte do plugin. Esperado: `OK`.
- [ ] **Step 5:** Mate os mutantes. `check-private-names.py` rc 0. Commit: `feat(retrofit-watch): a porta publica, libera e registra`.

---

### Task 10: O aviso de startup e o critério da v2

**Files:**
- Modify: `$W/scripts/rw_auto.py`, `$W/scripts/rw_store.py`, `$W/scripts/retrofit_watch.py` (`cmd_pending`)
- Test: `$W/tests/test_auto_notice.py`

**Interfaces:**
- Consumes: `held`, `last_lines`, `read_registry`, `load_licoes` (Tarefa 5); `ctx.store`; `StoreWorld.advance_origin` (Tarefa 6).
- Produces:
  - `rw_auto.ORPHAN_AGE = 3600` e `rw_auto.orphans(ctx, now=None) -> list[dict]` (D14), dos dois tipos: lote com `retrofit.json` e sem linha; pedido com `licoes.json` e lição sem linha. `licoes.json` ilegível conta como órfão, sem exceção.
  - `rw_auto.install_behind(ctx) -> list[dict]`: itens cuja última linha é `publicado` com `instalacao` em `pendente`, `update` ou `cache-difere`.
  - `rw_store.V2_MIN_PUBLISHED = 10`, `rw_store.V2_MIN_DAYS = 14`.
  - `rw_store.criterion(ctx, now=None) -> dict | None`: `{"publicados", "dias", "revertidos", "vazados", "desde", "cumprido"}`. `None` sem `store`. A conta sai do `origin/main` **local** (D15): `publicados` são os commits cujo trailer `Retrofit-Mode` é exatamente `autonomous`; `desde` é a data do primeiro; `revertidos` são os commits com `This reverts commit <sha>` de um deles; `vazados` são os achados da lista de hashes nos arquivos que eles tocaram, com a lista e os arquivos lidos do `origin/main` por `git show`. `vazados` só é calculado quando os dois pisos já passaram. O resultado fica em `<dados>/criterio.json`, por sha do `origin/main`. As chamadas ao git saem por `run` com `timeout=3`, porque o startup tem 10 s.
  - `cmd_pending` junta os segmentos com ` · ` num `systemMessage` só: a fila de hoje; `N retrofit(s) segurado(s) (<plugin>: <ramo>, …) — /retrofit-watch:retrofit-watch segurados`; `N retrofit(s) autônomo(s) sem registro de fim (<ramo ou id>, …)`; `N publicado(s) com a cópia instalada atrás (<plugin>, …)`; e a frase do critério.
  - A frase do critério, da spec 5.9: `retrofit-watch: 10 retrofits autônomos, 0 revertidos, 0 nomes vazados desde <data> — o kit pode entrar (ver a spec do modo autônomo)`, com os números medidos.

- [ ] **Step 1: Escreva os testes que falham.** Os commits autônomos da fixture nascem por `advance_origin`, com o trailer na mensagem e a data pedida.

| Teste | Entrada | Asserção | Mutante que ele mata |
|---|---|---|---|
| `test_startup_without_auto_data_is_unchanged` | registro vazio, fila com 1 item, sem `store` | o `systemMessage` de hoje, byte a byte | — |
| `test_held_retrofit_is_announced_with_its_branch` | um segurado; um segurado e depois descartado; uma lição descartada pela triagem | um só, com o ramo e o verbo `segurados` | ler a primeira linha; anunciar descartado |
| `test_orphan_lote_is_announced_after_an_hour` | lote com `retrofit.json` e sem linha; pedido de 10 min, depois de 2 h | ausente; depois presente | tirar a idade |
| `test_orphan_lessons_are_announced_after_an_hour` | pedido de 2 h com `licoes.json` de duas lições e linha no registro só para uma; depois `licoes.json` quebrado | presente nos dois; nenhuma exceção | olhar só os lotes |
| `test_install_behind_is_announced` | última linha `publicado` com `instalacao: "update"`; outra com `ok` | só a primeira | — |
| `test_criterion_needs_ten_and_fourteen_days` | 9 commits e 20 dias; 10 e 13 dias; 10 e 14 dias | falso, falso, verdadeiro com a frase exata | trocar `>=` por `>` em cada limite |
| `test_criterion_counts_commits_not_registry_lines` | 10 commits autônomos no `origin/main` e o registro vazio; depois 10 linhas `publicado` no registro e nenhum commit | `publicados == 10`; depois `0` | contar pelo registro |
| `test_approved_commits_do_not_count` | 9 commits `autonomous` e 3 `autonomous-approved` | `publicados == 9` | casar o trailer por prefixo |
| `test_a_revert_on_origin_main_blocks_the_criterion` | 10 commits; um commit que reverte um deles | `revertidos == 1`, `cumprido` falso | não procurar o revert |
| `test_a_leaked_name_in_a_touched_file_blocks_the_criterion` | um arquivo tocado ganha, no `origin`, um nome da lista da fixture | `vazados == 1` | varrer o worktree em vez do `origin/main` |
| `test_startup_makes_no_fetch` | `origin` inalcançável, 10 commits e 14 dias já no `origin/main` local | o aviso sai; nenhum erro em `errors.log` | chamar `fetch` |
| `test_criterion_is_cached_by_origin_main_sha` | duas chamadas com o mesmo sha; depois um commit novo | a segunda não chama `git log`; a terceira chama | ignorar o cache |

- [ ] **Step 2:** Rode. Esperado: falha.
- [ ] **Step 3:** Implemente.
- [ ] **Step 4:** Rode a suíte do plugin. Esperado: `OK`.
- [ ] **Step 5:** Mate os mutantes. `check-private-names.py` rc 0. Commit: `feat(retrofit-watch): segurados, órfãos e critério da v2 no aviso de startup`.

---

### Task 11: O revisor, a `SKILL.md` e a referência do fluxo

**Files:**
- Create: `plugins/retrofit-watch/agents/retrofit-reviewer.md`, `$W/references/modo-autonomo.md`, `$W/tests/test_auto_docs.py`
- Modify: `$W/SKILL.md`, `$W/references/criteria.md` (seção 6: duas linhas dizendo que no modo autônomo não há "sim" e apontando a referência nova)

**Interfaces:**
- Consumes: os subcomandos da CLI (Tarefas 5, 7 e 9); `LICAO_KEYS`, `PARECER_KEYS`, `ANONIMATO_KEYS`, `LESSON_REASONS`, `OWNER_REASONS`, `AGENT_REASONS`, `GATE_REASONS`, `OVERRIDABLE`, `OWNER_WORD_RULE`.
- Produces: o agente `retrofit-watch:retrofit-reviewer`; o verbo `/retrofit-watch:retrofit-watch segurados`.

**O agente (spec 5.4).** Frontmatter: `name: retrofit-reviewer`, `description` em inglês, `tools: Read, Grep, Glob, Bash`, `model: opus`. O corpo diz:
- o que ele recebe: o diretório da retro, o caminho do clone da loja e qual das duas passadas fazer;
- **primeira passada, o achado:** `git -C <loja> fetch origin`, ler a skill-alvo em `origin/main` **nesta revisão**, conferir a evidência no transcript, responder as cinco perguntas da tabela da spec 5.4 e gravar `veredito.json`;
- **segunda passada, o diff:** ler o commit do lote (`git -C <worktree> show HEAD`) e as lições do `retrofit.json`, e gravar `anonimato.json` com: o `patch` copiado de `termos-novos.json`; cada termo julgado `publico`, `privado` ou `duvida`, com a linha de contexto e `<dados>/colheita.txt` como referência; `regra_repetida`, a resposta a "a mudança acrescenta uma regra que repete ou contradiz uma já escrita, em vez de corrigir a frase que errou?"; `fora_das_licoes`, a resposta a "o diff faz só o que as lições dizem?". Nos dois, `null` quando está certo e o `arquivo:linha` com o porquê quando não;
- nunca rodar o comando da evidência sobre o estado real: só numa cópia (`git archive` para dentro do diretório da retro) ou fixture. Sem cópia possível, `nao-reproduzivel`, e `basta_o_transcript` diz por que a evidência basta, ou fica nulo;
- gravar os dois arquivos pelo Bash, no diretório da retro, e não editar nenhum arquivo de repo. A resposta volta em até 10 linhas.

**A referência `modo-autonomo.md`**, para o agente da sessão, com os passos numerados:
1. As lições: o formato do `licoes.json` e as seções 1 a 4 do `criteria.md`.
2. O revisor, primeira passada: `subagent_type: "retrofit-watch:retrofit-reviewer"`, `model: "opus"`, `effort: "xhigh"`, sem o contexto da sessão no prompt.
3. `triage <id>`: o que fazer com `lotes`, `segurar` e `descartar`.
4. Por lote: `prepare`; o executor (`subagent_type: "general-purpose"`, `model: "opus"`, `effort: "medium"`, com o prompt-modelo que manda ler `plugins/retrofit-skill/commands/retrofit-skill.md` no worktree e rodar `<plugin> --auto <dir do lote>`); o revisor na segunda passada; `publish`. Plugins diferentes em paralelo. Lotes do mesmo plugin em sequência.
5. A linha ao dono, nas duas formas da spec 5.1, e o pedido de `/reload-plugins` depois de uma publicação. Com rc 4, rodar `publish` de novo.
6. O verbo `segurados`: `held`; liberar (`approve`, depois `publish`); descartar (`discard`). A frase `OWNER_WORD_RULE` abre este passo, inteira.
   - Segurado por nome (`nome-privado`, `termo-nao-publico`, `sem-anonimato`): a aprovação não substitui. Com "privado" do dono: `check-private-names.py --add` no worktree, o executor troca o termo por um genérico, emenda o commit, sela de novo, e o revisor refaz a segunda passada. Com "público" do dono: `anonymity-gate.py --publico-add` no worktree e emenda. Nos dois, `approve` e depois `publish`.
   - Segurado por `rebase`: `prepare --redo`, e o lote recomeça no passo 4.
   - Segurado por `revisao-desatualizada`: selar de novo e refazer a segunda passada.
   - Segurado sem ramo: o `/retrofit-skill` manual, e depois `discard … --motivo resolvido-manual`.
7. Executor que falha ou recusa a lição: `hold <id> <item> <motivo>`.
8. A tabela de motivos: cada código, o que quer dizer, se a aprovação do dono o substitui e qual é a saída.
9. O que nunca fazer: push fora da porta, escrever no checkout compartilhado, apagar ramo ou worktree.

**A `SKILL.md`:** o parágrafo de abertura passa a citar os dois modos. Seção nova *Modo autônomo* com até 25 linhas, que diz **quando** ler a referência (ao receber um pedido autônomo do hook ou o verbo `segurados`) e traz a frase `OWNER_WORD_RULE`, inteira. A tabela *Controle* ganha `mode`, `manual`, `private_sources`, `harvest_roots`, `auto_limits` e `store`. *Gotchas* ganha: só vale com `bypassPermissions` e com `entrypoint` `cli`; a retro sob demanda continua manual (D17); o revert só é contado quando tem a linha `This reverts commit`. A tabela *Arquivos* ganha os arquivos novos. Teto: abaixo de 250 linhas e de 20.000 caracteres (hoje 150 e 10.218).

- [ ] **Step 1: Grave o baseline da auditoria** da skill, como manda o `retrofit-skill` (seção *ANTES DE EDITAR*): `antes.json` fora do repo.
- [ ] **Step 2: Escreva os testes de contrato que falham.**

| Teste | Asserção |
|---|---|
| `test_every_cited_subcommand_exists` | cada `retrofit_watch.py <sub>` citado em `SKILL.md`, `modo-autonomo.md`, `criteria.md`, no agente e, quando o arquivo existe, em `plugins/retrofit-skill/references/modo-autonomo.md` está na tabela da CLI |
| `test_every_subcommand_is_documented` | cada subcomando da CLI aparece em `modo-autonomo.md` |
| `test_format_keys_are_documented` | cada chave de `LICAO_KEYS` aparece em `modo-autonomo.md`; cada chave de `PARECER_KEYS` e de `ANONIMATO_KEYS` aparece no agente |
| `test_every_reason_code_is_explained` | cada código de `LESSON_REASONS`, `OWNER_REASONS`, `AGENT_REASONS` e `GATE_REASONS` aparece na tabela de motivos; a coluna "substituível" diz sim exatamente para os de `OVERRIDABLE` |
| `test_owner_word_rule_is_written_where_it_matters` | `OWNER_WORD_RULE` aparece inteira no passo dos segurados da referência e na seção *Modo autônomo* da `SKILL.md` |
| `test_reviewer_asks_the_two_diff_questions` | o agente contém as duas perguntas da segunda passada e os nomes `regra_repetida` e `fora_das_licoes` |
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

### Task 12: `retrofit-skill` 0.11.0 — o modo autônomo do executor

**Files:**
- Create: `$R/references/modo-autonomo.md`, `$R/tests/test_modo_autonomo.py`
- Modify: `$R/commands/retrofit-skill.md`, `$R/CHANGELOG.md`, `$R/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (só o bloco do `retrofit-skill`), `README.md` (a linha da tabela e a seção de detalhes do plugin), `docs/codex/compatibility.md` (a contagem da linha do `retrofit-skill`: a previsão é de 3 para 4 arquivos; meça com `git ls-files` em `scripts/` e `references/`)

**Interfaces:**
- Consumes: `prepare` e `seal`, com `--fases` (Tarefa 7); o formato do `retrofit.json` e do `veredito.json`; `rw_store.PHASES` e os tetos `SKILL_MAX_LINES` e `SKILL_MAX_CHARS` (Tarefa 8).
- Produces: a sintaxe `/retrofit-skill <plugin> --auto <dir do lote>` (D1).

**O comando muda em quatro pontos, e só neles:**
1. A regra do argumento: `--auto <dir>` depois do nome escolhe o modo autônomo. O resto da regra fica.
2. Seção nova *Modo autônomo*, com até 20 linhas: só vale no modo completo; exige `<dir>/retrofit.json` e o `veredito.json` da retro; o veredito faz o papel da confirmação do passo 3; o fluxo para antes do push; manda ler `references/modo-autonomo.md` antes de editar.
3. Passo 3: depois de "Espere minha confirmação", a exceção do modo autônomo, numa frase.
4. Passo 4, no item do push e no item da loja: no modo autônomo, os dois são da porta.

**A referência cobre a spec 5.5, item por item:**
- as lições são as do lote, e nenhuma outra entra no commit. O revisor confere o diff contra elas;
- o worktree é o do `retrofit.json`: não criar outro, não tocar o checkout compartilhado;
- corrigir a frase que errou em vez de acrescentar uma regra, procurando antes a regra já escrita (`grep -rn` na skill). O revisor confere isso também;
- skill com `tests/`: o teste que falha antes da correção, a correção, o teste passando, e os mutantes da correção;
- **a auditoria (O4), pela família em `$Q` do worktree:**

  | Quando | O que roda | Nome em `--fases` |
  |---|---|---|
  | sempre | o baseline e o gate do script da fase 1, como hoje. ERRO ou AVISO novo segura | — |
  | a lição põe ou muda um número, limite, caminho, flag ou versão | `skill-claim-check`: leia o `SKILL.md` dela no worktree e dê veredito a cada `CLAIM` | `claim-check` |
  | a lição põe um caminho, uma reference ou uma dependência de fora da skill | `skill-self-containment` | `self-containment` |
  | o `SKILL.md` passa de ~400 linhas ou de ~16 mil caracteres depois da mudança | `skill-refactoring` | `refactoring` |

  A porta confere três gatilhos mecânicos e recusa quando a fase não está no selo. Rodar a fase e não a declarar segura o retrofit;
- bump, `CHANGELOG`, `marketplace.json` e README como no modo completo;
- um commit só, com `--trailer "Retrofit-Mode: autonomous"`, sem `Co-Authored-By`;
- nenhum push e nenhum `claude plugin`;
- o último passo é `seal <id> <lote> --licoes … --fases …`. Com achado da camada 1: trocar o termo por um genérico, emendar o commit e selar de novo, no máximo 2 ciclos;
- a lição que não cabe sem piorar a skill fica fora do commit e sai no relatório;
- o relatório volta em até 5 linhas: commit, versão, lições incluídas, lições deixadas de fora, as fases rodadas e o resultado do `seal`.

- [ ] **Step 1: Escreva o teste de contrato que falha.**

| Teste | Asserção |
|---|---|
| `test_o_comando_roteia_para_a_referencia` | o comando cita `--auto` e `references/modo-autonomo.md`, e a frase diz quando ler |
| `test_o_passo_3_tem_a_excecao` | o parágrafo de "Espere minha confirmação" cita o modo autônomo |
| `test_a_referencia_tem_as_ancoras_da_spec` | a referência contém `retrofit.json`, `veredito.json`, `seal`, `Retrofit-Mode: autonomous` e a proibição do `Co-Authored-By` |
| `test_as_fases_da_auditoria_batem_com_a_porta` | os nomes de fase da tabela são exatamente os de `rw_store.PHASES`, lido do fonte do `retrofit-watch` quando ele está no repo; as três skills da família são citadas pelo nome; os tetos da tabela são os de `rw_gate` |
| `test_a_referencia_nao_manda_publicar` | nenhuma linha da referência tem `git push` ou `claude plugin` fora de uma frase de proibição |
| `test_os_quatro_lugares_estao_na_0_11_0` | `plugin.json`, o `metadata.version` do comando, o bloco do `marketplace.json` e a linha do README dizem `0.11.0`; o `CHANGELOG` tem a entrada |

- [ ] **Step 2:** `python3 $R/tests/test_modo_autonomo.py`. Esperado: falha.
- [ ] **Step 3:** Escreva a referência e as quatro mudanças do comando.
- [ ] **Step 4:** Faça o bump para 0.11.0 nos quatro lugares e escreva a entrada do `CHANGELOG` com o quê e o porquê. Edite o `marketplace.json` só dentro do bloco do plugin, sem passar o arquivo por um parser.
- [ ] **Step 5:** Rode `$R/tests/test_modo_autonomo.py` e `$W/tests/test_auto_docs.py`. Esperado: `OK` nos dois.
- [ ] **Step 6:** `python3 scripts/validate-versions.py` (rc 0) e `python3 $R/scripts/check_release_sync.py retrofit-skill`. Leia os valores impressos: `0.11.0` nos dois manifestos e na linha do README.
- [ ] **Step 7:** `git add -A && git diff --cached --stat`. Responda por cada arquivo. `check-private-names.py` rc 0. Commit: `feat(retrofit-skill): v0.11.0 — modo autônomo para o executor do retrofit-watch`.

---

### Task 13: `retrofit-watch` 0.4.0 — versão, catálogo e conferência final

**Files:**
- Modify: `plugins/retrofit-watch/.claude-plugin/plugin.json`, `$W/SKILL.md` (`metadata.version`), `plugins/retrofit-watch/CHANGELOG.md`, `.claude-plugin/marketplace.json` (só o bloco do `retrofit-watch`), `README.md` (a linha da tabela e a seção de detalhes), `docs/codex/compatibility.md` (a contagem da linha do `retrofit-watch`: a previsão é de 2 para 6 arquivos; meça do mesmo jeito), `$W/scripts/retrofit_watch.py` (a docstring do topo e o `--help`: as chaves novas da config e os subcomandos)
- Test: `$W/tests/test_auto_docs.py`

**Interfaces:**
- Consumes: tudo das Tarefas 2 a 12.

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
| `/usr/bin/grep -rn '"python3"' $W/scripts/rw_*.py` | nada |

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

   O segundo comando imprime, só no terminal, cada nome colhido que aparece na loja e ainda não foi classificado. A medida da spec indica cerca de 23 nomes de pasta, a maioria palavra comum. A quebra dos nomes compostos (Tarefa 7) acrescenta as palavras deles à lista. Para cada um: privado é `python3 scripts/check-private-names.py --add NOME` e a troca do nome no arquivo; público é `python3 scripts/anonymity-gate.py --publico-add NOME`. Repita até o segundo comando sair 0. O commit leva só as duas listas e os arquivos corrigidos.
2. **Ensaio.** No `~/.claude/retrofit-watch.json`: `"mode": "auto-dry"` e `"store"` com o caminho do clone de trabalho da loja. Uma sessão com `bypassPermissions` e uma skill da loja com atrito. Esperado: o ramo pronto e a linha `segurada — auto-dry`.
3. **Ligar.** `"mode": "auto"`.
4. **Windows.** Antes de ligar lá, rode a suíte do plugin com o `python3` do PATH.

## Self-review

- **Cobertura da spec:** 5.1 (Tarefas 4, 5, 7, 9, 11); 5.2 (4, 7, 8); 5.3 (4, 5); 5.4 (5, 11); 5.5 (7, 8, 12); 5.6 (2, 3, 7, 8, 11 e o passo 1 do dono); 5.7 (8, 9); 5.8 (5, 8, 11); 5.9 (5, 9, 10); 5.10 (4, 8); 5.11 (5, 9, 11).
- **Anti-objetivos:** nome no `origin/main` (2, 3, 7, 8); retro de si mesmo (4); checkout compartilhado (7, 8, 9); regra nova embaixo de regra existente (8, guarda 15, e 11); modo autônomo sem pedir (4).
- **Decisões do dono:** O1 (4, 7); O2 (5, 8, 11); O3 (5); O4 (7, 8, 12); O5 (4, 7, 8); O6 (3); O7 (8, 11); O8 (5, 8, 11); O9 (4, 11).
- **Review Focus:** 1 na Tarefa 4; 2 na 9; 3 nas 4 e 5; 4 nas 8 e 9; 5 nas 5 e 9.
- **Nomes:** `refuse`, `hold`, `publish`, `triage`, `prepare`, `seal`, `held`, `approve`, `discard`, `hold_item`, `harvest`, `run`, `patch_id`, `in_request` são os mesmos em todas as tarefas que os citam.
