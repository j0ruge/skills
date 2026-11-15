# codereview 2.29.0: nota escrita para prosa e rodada de verificação — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A linha Documentation do `/codereview` passa a sair de um critério escrito, e a re-rodada de um conserto só de prosa vira uma rodada de verificação com escopo calculado por script.

**Architecture:** Um script novo (`prose_units.py`) lê o diff do intervalo e imprime, em JSON, o tipo de cada arquivo e as unidades de prosa em volta de cada linha mudada. O `SKILL.md` roteia os arquivos de prosa de uma re-rodada para um agente verificador com contrato próprio (`references/verify-agent.md`), que só lê essas unidades. Os agentes e a sessão marcam cada achado de documentação como `behavior` ou `form`, e o `report-template.md` dá a letra por tabela.

**Tech Stack:** Python 3 só com biblioteca padrão (`unittest`, `subprocess`, `json`), Markdown dos contratos da skill, git.

**Spec:** `docs/superpowers/specs/2026-11-15-codereview-rodada-de-prosa-design.md`

## Global Constraints

- Trabalhar no worktree `~/repos/skills-rodada-de-prosa`, branch `docs/rodada-de-prosa-design`. Nenhum `git push`, PR ou merge: são do dono.
- Repositório público: nenhum nome de projeto, empresa ou pessoa em arquivo ou mensagem de commit. `python3 scripts/check-private-names.py` tem de imprimir `ok` antes de cada commit; a mensagem de commit ninguém varre, então releia.
- Commits sem `Co-Authored-By` e sem "Generated with". Conferir: `git log -1 --format='%(trailers:key=Co-authored-by,valueonly)'` imprime nada.
- Texto dos contratos da skill (`SKILL.md`, `references/*.md`) em inglês, como o resto deles. `CHANGELOG.md` e nomes de teste em português, como os existentes.
- `SKILL.md` fica abaixo de 500 linhas (hoje 248) e ganha no máximo 25 linhas. `references/configuration.md` ganha no máximo 15 linhas. O contrato do verificador mora só em `references/verify-agent.md`.
- A regra *The agents never see the earlier reports* continua: nenhum prompt de agente recebe achado de rodada anterior.
- A skill continua só de leitura: o script novo não escreve arquivo.
- Abreviação usada abaixo: `S=plugins/codereview/skills/codereview`.
- Testes da skill rodam de dentro de `$S`: `python3 tests/<arquivo>.py`.

## Review Focus

1. **Hunk que só apaga linhas num doc** (`@@ -10,3 +9,0 @@`): a unidade onde o texto saiu ainda tem de aparecer no escopo, porque o que sobrou pode ter ficado incoerente. Teste na Task 1.
2. **Arquivo apagado ou renomeado no intervalo:** o script não quebra; o apagado sai com `units: []`, o renomeado sai pelo caminho novo. Teste na Task 2.
3. **Docstring de Python mudada sem código:** o script não sabe reconhecer docstring, então o arquivo sai como `CODE` e segue o fluxo de hoje. Errar para `DOC_ONLY` esconderia código do agente por arquivo. Teste na Task 2.
4. **Item de lista com linhas de continuação e sub-itens:** a linha mudada na continuação devolve o item inteiro desde o marcador. Teste na Task 1.
5. **Re-rodada sem a lista de achados da rodada anterior:** o `SKILL.md` manda usar a re-rodada de hoje. Teste de contrato na Task 4.

---

### Task 1: `prose_units.py` — linhas mudadas e unidades de Markdown

**Files:**
- Create: `$S/scripts/prose_units.py`
- Test: `$S/tests/test_prose_units.py`

**Interfaces:**
- Produces:
  - `changed_lines(repo: Path, base: str, head: str) -> dict[str, dict]` — por caminho no head: `{"added": list[int], "removed_at": list[int], "status": "M"|"A"|"D"|"R"}`. `added` são as linhas `+` no head; `removed_at` é, para cada hunk sem linha `+`, a linha do head logo depois do corte (mínimo 1). Usa `git -P diff -U0 --find-renames <base>...<head>`.
  - `markdown_units(lines: list[str], targets: list[int]) -> list[tuple[int, int]]` — intervalos `(início, fim)` 1-indexados, inclusivos, sem repetição, em ordem.

Regras de unidade, na ordem em que se testam para a linha alvo:

| A linha está em | Unidade |
|---|---|
| bloco cercado por ` ``` ` ou `~~~` | o bloco inteiro, com as cercas |
| linha que começa com `\|` | só essa linha |
| título (`#` a `######`) | só essa linha |
| item de lista (`-`, `*`, `+`, `1.`, `1)`, com qualquer recuo) ou continuação dele | do marcador do item até a linha antes do próximo marcador de recuo menor ou igual, ou antes de uma linha em branco seguida de linha sem recuo |
| citação (`>`) | as linhas `>` contíguas |
| qualquer outra linha não vazia | as linhas não vazias contíguas que não são título, tabela, cerca nem marcador de lista |
| linha em branco | a unidade da linha não vazia anterior; se não houver, a da seguinte |

Sub-item pertence à unidade do item pai quando o alvo está no pai ou na continuação do pai; alvo dentro do sub-item devolve só o sub-item.

- [ ] **Step 1: Escrever os testes que falham**

Em `tests/test_prose_units.py`, com um repositório git temporário por teste (mesmo molde do `RepoComPR` em `tests/test_scan_secrets.py`: `git init`, commit base, commit head):

```python
class TestUnidadesMarkdown(unittest.TestCase):
    DOC = [
        "# Título",                      # 1
        "",                              # 2
        "Primeira frase do parágrafo",   # 3
        "segunda linha do parágrafo.",   # 4
        "",                              # 5
        "- item um, começo",             # 6
        "  continuação do item um",      # 7
        "  - sub-item",                  # 8
        "- item dois",                   # 9
        "",                              # 10
        "| a | b |",                     # 11
        "| c | d |",                     # 12
        "",                              # 13
        "```",                           # 14
        "codigo",                        # 15
        "```",                           # 16
    ]

    def test_paragrafo_inteiro(self):
        self.assertEqual(prose_units.markdown_units(self.DOC, [4]), [(3, 4)])

    def test_continuacao_devolve_o_item_desde_o_marcador_com_o_sub_item(self):
        self.assertEqual(prose_units.markdown_units(self.DOC, [7]), [(6, 8)])

    def test_alvo_no_sub_item_devolve_so_o_sub_item(self):
        self.assertEqual(prose_units.markdown_units(self.DOC, [8]), [(8, 8)])

    def test_linha_de_tabela_e_a_propria_linha(self):
        self.assertEqual(prose_units.markdown_units(self.DOC, [12]), [(12, 12)])

    def test_bloco_cercado_inteiro(self):
        self.assertEqual(prose_units.markdown_units(self.DOC, [15]), [(14, 16)])

    def test_titulo_sozinho(self):
        self.assertEqual(prose_units.markdown_units(self.DOC, [1]), [(1, 1)])

    def test_dois_alvos_na_mesma_unidade_saem_uma_vez(self):
        self.assertEqual(prose_units.markdown_units(self.DOC, [3, 4]), [(3, 4)])

    def test_linha_em_branco_cai_na_unidade_anterior(self):
        self.assertEqual(prose_units.markdown_units(self.DOC, [5]), [(3, 4)])


class TestLinhasMudadas(RepoTemporario):
    def test_linha_acrescentada(self):
        # base: 3 linhas; head: troca a linha 2
        self.assertEqual(self.mudadas()["doc.md"]["added"], [2])

    def test_hunk_que_so_apaga_registra_onde_cortou(self):
        # base: linhas 1..5; head: sem a linha 3
        m = self.mudadas()["doc.md"]
        self.assertEqual((m["added"], m["removed_at"]), ([], [3]))
```

- [ ] **Step 2: Rodar e ver falhar**

Run (de `$S`): `python3 tests/test_prose_units.py`
Expected: FAIL com `ModuleNotFoundError: No module named 'prose_units'`

- [ ] **Step 3: Implementar `changed_lines` e `markdown_units` em `scripts/prose_units.py`**

Ler os cabeçalhos `@@ -a,b +c,d @@` do diff `-U0`; `d == 0` é hunk que só apaga e registra `max(c + 1, 1)` em `removed_at`. Abrir arquivos com `encoding="utf-8", errors="replace"`.

- [ ] **Step 4: Rodar e ver passar**

Run: `python3 tests/test_prose_units.py`
Expected: `OK`, 10 testes

- [ ] **Step 5: Commit**

```bash
git add plugins/codereview/skills/codereview/scripts/prose_units.py plugins/codereview/skills/codereview/tests/test_prose_units.py
git commit -m "feat(codereview): prose_units.py calcula as unidades de Markdown em volta das linhas mudadas"
```

---

### Task 2: `prose_units.py` — comentário em código, tipo do arquivo, identificadores e a saída JSON

**Files:**
- Modify: `$S/scripts/prose_units.py`
- Test: `$S/tests/test_prose_units.py`

**Interfaces:**
- Consumes: `changed_lines`, `markdown_units` (Task 1).
- Produces:
  - `comment_units(lines: list[str], targets: list[int], path: str) -> list[tuple[int, int]]` — o bloco contíguo de linhas de comentário que contém cada alvo.
  - `file_kind(repo: Path, base: str, head: str, path: str) -> str` — `"DOCS"`, `"DOC_ONLY"` ou `"CODE"`.
  - `identifiers(lines: list[str], added: list[int]) -> list[str]` — trechos entre crases das linhas `added`, com 3 caracteres ou mais, sem repetição, na ordem em que aparecem.
  - CLI: `python3 scripts/prose_units.py --repo DIR --base SHA --head SHA` imprime um JSON e sai com rc 0; erro de git sai com rc 2 e a mensagem no stderr.

Prefixos de comentário por extensão (linha, depois de tirar o recuo):

| Extensões | Prefixos |
|---|---|
| `.cs .ts .tsx .js .jsx .java .go .rs .c .h .cpp .swift .kt` | `//`, `/*`, `*`, `*/` |
| `.py .sh .rb .yml .yaml .toml` | `#` |
| `.lua .sql` | `--` |

`file_kind`: `.md` e `.txt` são `DOCS`. Extensão da tabela é `DOC_ONLY` quando toda linha `+` e toda linha `-` do diff `-U0` é comentário ou vazia; senão é `CODE`. Qualquer outra extensão é `CODE`.

Forma do JSON:

```json
{
  "base": "<sha>", "head": "<sha>",
  "files": [
    {"path": "docs/a.md", "kind": "DOCS", "status": "M",
     "units": [{"start": 3, "end": 4, "changed": [4]}],
     "identifiers": ["Foo.Bar"]}
  ],
  "totals": {"prose_files": 1, "code_files": 0, "units": 1, "unit_lines": 2}
}
```

Arquivo `CODE` sai com `units: []`. Arquivo apagado sai com `status: "D"` e `units: []`. `changed` junta `added` e `removed_at` que caem na unidade.

- [ ] **Step 1: Escrever os testes que falham**

```python
class TestComentarioETipo(RepoTemporario):
    def test_bloco_de_comentario_inteiro(self):
        linhas = ["class A {", "    /// <summary>", "    /// texto", "    /// </summary>", "    void M() {}", "}"]
        self.assertEqual(prose_units.comment_units(linhas, [3], "A.cs"), [(2, 4)])

    def test_diff_so_de_comentario_e_doc_only(self):
        # head troca só a linha "/// texto"
        self.assertEqual(self.tipo("A.cs"), "DOC_ONLY")

    def test_diff_com_uma_linha_de_codigo_e_code(self):
        # head troca o comentário e também "void M() {}"
        self.assertEqual(self.tipo("A.cs"), "CODE")

    def test_docstring_de_python_cai_em_code(self):
        # head troca só o texto dentro de aspas triplas
        self.assertEqual(self.tipo("m.py"), "CODE")

    def test_markdown_e_docs(self):
        self.assertEqual(self.tipo("doc.md"), "DOCS")

    def test_identificadores_das_linhas_novas(self):
        linhas = ["o `Foo.Bar` chama o `X` e o `Foo.Bar` de novo", "velha `Baz.Qux`"]
        self.assertEqual(prose_units.identifiers(linhas, [1]), ["Foo.Bar"])


class TestSaida(RepoTemporario):
    def test_json_de_um_intervalo_misto(self):
        # head: doc.md com a linha 4 trocada, A.cs com código trocado, velho.md apagado
        saida = self.rodar_cli()
        por = {f["path"]: f for f in saida["files"]}
        self.assertEqual(por["doc.md"]["units"], [{"start": 3, "end": 4, "changed": [4]}])
        self.assertEqual((por["A.cs"]["kind"], por["A.cs"]["units"]), ("CODE", []))
        self.assertEqual((por["velho.md"]["status"], por["velho.md"]["units"]), ("D", []))
        self.assertEqual(saida["totals"], {"prose_files": 1, "code_files": 1, "units": 1, "unit_lines": 2})

    def test_arquivo_renomeado_sai_pelo_caminho_novo(self):
        # head: git mv a.md b.md e troca uma linha
        self.assertIn("b.md", {f["path"] for f in self.rodar_cli()["files"]})

    def test_sha_inexistente_sai_com_rc_2(self):
        self.assertEqual(self.rodar_cli_rc("--base", "0" * 40), 2)
```

`totals.prose_files` conta `DOCS` e `DOC_ONLY` que não foram apagados.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python3 tests/test_prose_units.py`
Expected: FAIL com `AttributeError: module 'prose_units' has no attribute 'comment_units'`

- [ ] **Step 3: Implementar `comment_units`, `file_kind`, `identifiers` e o `main()`**

- [ ] **Step 4: Rodar e ver passar**

Run: `python3 tests/test_prose_units.py`
Expected: `OK`, 19 testes

- [ ] **Step 5: Commit**

```bash
git add plugins/codereview/skills/codereview/scripts/prose_units.py plugins/codereview/skills/codereview/tests/test_prose_units.py
git commit -m "feat(codereview): prose_units.py classifica DOC_ONLY e imprime o escopo em JSON"
```

---

### Task 3: tipo do achado e critério da linha Documentation

**Files:**
- Modify: `$S/references/per-file-agent.md` (seção *Output format* e o item de DOCS em *What to apply*)
- Modify: `$S/references/report-template.md` (*Grading Scale* e *Recommended Actions*)
- Create: `$S/tests/test_prose_contract.py`

**Interfaces:**
- Produces (texto que a Task 4 e a sessão usam): a linha `Kind:` no achado; a subseção `### Documentation row`; o balde `**Deferred (form)**`.

- [ ] **Step 1: Escrever o teste de contrato que falha**

```python
REF = Path(__file__).resolve().parent.parent / "references"

class TestContratoDeProsa(unittest.TestCase):
    def test_agente_por_arquivo_pede_o_tipo(self):
        t = (REF / "per-file-agent.md").read_text(encoding="utf-8")
        for trecho in ("Kind: behavior — contradicted by {file}:{line}",
                       "Kind: behavior — missing evidence: {what}",
                       "Kind: form"):
            self.assertIn(trecho, t)

    def test_template_tem_o_criterio_e_o_balde(self):
        t = (REF / "report-template.md").read_text(encoding="utf-8")
        self.assertIn("### Documentation row", t)
        self.assertIn("**Deferred (form)**", t)
        self.assertIn("| A | no CRITICAL, HIGH or MEDIUM documentation finding, and no `behavior` finding |", t)
        self.assertIn("| B | a MEDIUM documentation finding, or a LOW `behavior` finding |", t)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python3 tests/test_prose_contract.py`
Expected: FAIL nos dois testes

- [ ] **Step 3: Editar `per-file-agent.md`**

No bloco de *Output format*, acrescentar a linha depois de `Suggestion:`, só para achado do 6.5.1, do 6.5.2 ou de legibilidade de comentário:

```
   Kind: behavior — contradicted by {file}:{line}  |  Kind: behavior — missing evidence: {what}  |  Kind: form
```

E um parágrafo, logo abaixo do bloco, com as definições da spec, seção 1: `behavior` é a frase que afirma comportamento, valor, estado ou garantia que o código ou a evidência contradiz (com a linha citada), a afirmação dada como medida ou como ausência sem a evidência exigida (com o nome do que falta), ou um comando no doc que falha; `form` é a frase verdadeira mas mal escrita, incompleta ou com ponteiro impreciso, e a docstring que falta com severidade LOW. O tipo não muda a severidade.

- [ ] **Step 4: Editar `report-template.md`**

Depois da lista de *Grading Scale*, a subseção `### Documentation row` com: a tabela A/B/C da spec, seção 2, com as duas linhas exatas do teste; a regra de que um `behavior` sem citação e sem evidência nomeada vira `form` na Fase C; a regra de que a sessão dá tipo também aos achados do passo 7; LOW `form` não baixa a linha Documentation nem a Overall; achado `pre-existing` fica fora da letra e continua listado; o 6.5.3 fica fora desta linha. Uma linha de medição: `Measured 2026-11-15 (a .NET rules engine, PR #30, four rounds): the table gives B, B, B, A, the letters the session gave by judgment.`

Em *Recommended Actions*, depois de *Consider Fixing*, o balde:

```
**Deferred (form)**:

- Each LOW `form` documentation finding with file:line. They do not lower the grade and ask for no round.
- If none: `_None._`
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python3 tests/test_prose_contract.py`
Expected: `OK`, 2 testes

- [ ] **Step 6: Commit**

```bash
git add plugins/codereview/skills/codereview/references/per-file-agent.md plugins/codereview/skills/codereview/references/report-template.md plugins/codereview/skills/codereview/tests/test_prose_contract.py
git commit -m "feat(codereview): achado de documentação ganha tipo e a linha Documentation sai de tabela"
```

---

### Task 4: contrato do verificador e roteamento no `SKILL.md`

**Files:**
- Create: `$S/references/verify-agent.md`
- Modify: `$S/SKILL.md` (References; Phase A; Phase B; Phase C; *Operating Principles*, item *Re-review the fix, not the branch*)
- Modify: `$S/references/configuration.md` (*Re-review rounds*, um item)
- Modify: `$S/references/report-template.md` (definição do `DOC_ONLY`, linha 198)
- Test: `$S/tests/test_prose_contract.py`

**Interfaces:**
- Consumes: a saída JSON do `prose_units.py` (Task 2); a linha `Kind:` e a subseção `Documentation row` (Task 3).
- Produces: sentinela `END_OF_VERIFICATION`; nome do modo "verification round"; argumento `verify=off`.

Valores fixados:
- Um verificador recebe no máximo **400 linhas de unidade** (`unit_lines`) e **12 arquivos**; acima disso, dividir por arquivo em mais verificadores. A Task 5 mede esse teto.
- A lista "outside scope" do verificador tem no máximo **5** itens.
- A rodada de verificação vale quando as três condições valem: a revisão tem `base=` de uma rodada anterior; a sessão tem a lista dos achados abertos dessa rodada (número, `file:line`, tipo, afirmação), na conversa ou num arquivo indicado; `verify=off` não foi passado. Sem a lista, a re-rodada é a de hoje.

- [ ] **Step 1: Acrescentar os testes de contrato que falham**

```python
SKILL = REF.parent / "SKILL.md"

class TestRodadaDeVerificacao(unittest.TestCase):
    def test_contrato_do_verificador_existe_e_fecha_com_a_sentinela(self):
        t = (REF / "verify-agent.md").read_text(encoding="utf-8")
        for trecho in ("END_OF_VERIFICATION", "Outside scope (max 5)", "Kind:"):
            self.assertIn(trecho, t)

    def test_verificador_nao_carrega_os_passes_de_codigo(self):
        t = (REF / "verify-agent.md").read_text(encoding="utf-8")
        self.assertNotIn("Read {SKILL_DIR}/references/detection-passes.md", t)

    def test_skill_roteia_e_diz_quando_ler(self):
        t = SKILL.read_text(encoding="utf-8")
        for trecho in ("scripts/prose_units.py", "references/verify-agent.md",
                       "verify=off", "without that list, the re-review runs as a full round"):
            self.assertIn(trecho, t)

    def test_skill_fica_abaixo_do_teto(self):
        self.assertLess(len(SKILL.read_text(encoding="utf-8").splitlines()), 280)

    def test_prompt_do_verificador_nao_leva_achado_anterior(self):
        t = SKILL.read_text(encoding="utf-8")
        ini = t.index("Read {SKILL_DIR}/references/verify-agent.md")
        bloco = t[ini: t.index('")', ini)]
        self.assertNotIn("finding", bloco.lower())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python3 tests/test_prose_contract.py`
Expected: FAIL nos cinco testes novos; os 2 da Task 3 continuam `ok`

- [ ] **Step 3: Escrever `references/verify-agent.md`**

Em inglês, no molde do `sweep-agent.md` (cerca de 50 linhas). Conteúdo, nesta ordem:

1. Primeira leva de chamadas: este contrato, `git -P diff {BASE}...{HEAD} -- {arquivos}`, e a leitura de cada unidade pelo intervalo de linhas (`Read` com `offset` e `limit`), nunca o arquivo inteiro.
2. Para cada unidade, os três passos da spec, seção 3: contradição dentro da unidade; cada afirmação das linhas mudadas contra o código ou a evidência (as regras do 6.5 que cabem aqui vão escritas neste arquivo, em até 12 linhas, sem mandar ler o `detection-passes.md`); busca dos identificadores nos docs do projeto com `/usr/bin/grep -rn -F`, relatando só frase que o texto novo passou a contradizer.
3. Escopo: não ler o resto do arquivo atrás de achado. O que notar fora das unidades vai na lista `Outside scope (max 5)`, com `Kind:`.
4. Formato de saída: o mesmo do agente por arquivo, com a linha `Kind:` em todo achado; depois a lista `Outside scope (max 5)`; depois `Units read: {n} | Tool calls: {n}` e `END_OF_VERIFICATION`. Sem achado: `No findings in {n} units`.
5. As duas regras de shell do agente por arquivo: `/usr/bin/grep` e `git -P`, e glob entre aspas.

- [ ] **Step 4: Editar o `SKILL.md`**

- *References*: uma linha para `references/verify-agent.md` — "read it yourself only when a verification round runs inline; the verifier loads it".
- *Phase A*: um passo 9, só em re-rodada: `python3 {SKILL_DIR}/scripts/prose_units.py --repo . --base {MERGE_BASE} --head HEAD`, guardado como `PROSE_SCOPE`.
- *Phase B*: um parágrafo "Verification round" com as três condições e os tetos acima, a frase exata `without that list, the re-review runs as a full round`, e o prompt de lançamento:

```
Agent(model: REVIEW_MODEL, prompt: "
Start with ONE batch of parallel tool calls: Read {SKILL_DIR}/references/verify-agent.md and run
`git -P diff {MERGE_BASE}...HEAD -- {PROSE_FILES}`. Then follow verify-agent.md exactly.

- Repository: {REPO}
- Range: {MERGE_BASE}...HEAD
- Units: {one line per unit: path:start-end (changed: n, n)}
- Identifiers: {per file, from PROSE_SCOPE}
- Evidence: {path or none, per file}
- Skill dir: {SKILL_DIR}
- Hard rules: {CLAUDE.md prohibitions, verbatim, or none}
")
```

  Arquivo `kind: CODE` do `PROSE_SCOPE` segue os agentes por arquivo e a varredura, como hoje.
- *Phase C*: um passo entre o 1 e o 2 — para cada achado aberto da rodada anterior, ler o diff do intervalo sobre as linhas dele; ele fecha quando o diff tocou a unidade dele e o verificador não deu `behavior` nela; se o diff não tocou, continua aberto e conta na letra, salvo veredito escrito. Um `behavior` da lista "Outside scope" em linha que a branch escreveu conta; `form` de lá não.
- *Operating Principles*, item *Re-review the fix, not the branch*: trocar "stops at the first round that finds nothing" por "stops at the first round with no MEDIUM or worse and no `behavior` finding (report-template.md, *Documentation row*)".

- [ ] **Step 5: Editar `configuration.md` e `report-template.md`**

- `configuration.md`, *Re-review rounds*, primeiro item da lista: **"A prose-only fix gets a verification round, not a full one."** — o que é, o ponteiro para o `SKILL.md` e para o `verify-agent.md`, o limite declarado (drift antigo fora das unidades não é procurado; é trabalho da primeira rodada) e a medição de 2026-11-15 em uma frase. Nenhuma regra existente sai nesta versão.
- `report-template.md:198`, definição do `DOC_ONLY`: trocar "Decide it here, in Phase C" por "On a re-review `scripts/prose_units.py` decides it in Phase A (`kind: DOC_ONLY`); on a first round decide it here, in Phase C".

- [ ] **Step 6: Rodar tudo**

Run: `python3 tests/test_prose_contract.py && python3 tests/test_prose_units.py && python3 tests/test_scan_secrets.py`
Expected: três `OK`

- [ ] **Step 7: Commit**

```bash
git add plugins/codereview/skills/codereview
git commit -m "feat(codereview): rodada de verificação para conserto só de prosa"
```

---

### Task 5: repetição sobre o caso medido (só leitura) e o portão de aceite

**Files:**
- Create: `docs/superpowers/specs/2026-11-15-codereview-rodada-de-prosa-medicao.md` (só números, datas e hashes)

**Interfaces:**
- Consumes: o script e os contratos das Tasks 1 a 4, lidos direto do worktree (`SKILL_DIR` = caminho absoluto de `$S`). Nada é instalado.

O repositório do caso medido é privado. O dono indica o caminho na execução; ele não entra em nenhum arquivo deste repositório. Nada é escrito nem commitado lá. Antes de começar, conferir que nenhuma outra sessão usa aquele worktree.

Intervalos: r3 `e195f52...b87d5c7`, r4 `b87d5c7...e652c6d`, r5 `e652c6d...5e65896`, r6 `5e65896...786b348`.

- [ ] **Step 1: Rodar o `prose_units.py` nos quatro intervalos**

Run, para cada um: `python3 $SKILL_DIR/scripts/prose_units.py --repo <caminho> --base <base> --head <head>`
Expected: rc 0 nos quatro; anotar `totals` de cada um. Conferir à mão, no intervalo da r5, que o bullet da cor do roteiro do projeto sai como uma unidade só, do marcador até a última linha de continuação.

- [ ] **Step 2: Lançar o verificador três vezes por intervalo**

Doze agentes no total, modelo `opus`, com o prompt de lançamento da Task 4 preenchido pela saída do Step 1, em levas de quatro. Guardar de cada um: achados, lista "Outside scope", `Units read`, tokens e duração da notificação.

- [ ] **Step 3: Conferir contra o que as rodadas originais acharam**

| Intervalo | Tem de aparecer | Aceite |
|---|---|---|
| r5 | a contradição dentro do bullet da cor (o MEDIUM da r5) | nas 3 execuções |
| r4 | a célula de tabela que ainda dizia "sem bloco"; a lista de casos do resumo de `EffectData` que parecia completa | cada um em pelo menos 2 de 3 |
| r6 | o ponteiro da R329 para o arquivo errado; o "mudar" sem sujeito | cada um em pelo menos 2 de 3 |
| r3 | sem alvo: é a rodada inicial sobre os docs e fica como referência de tamanho | — |

Registrar também o que o verificador **não** acha por estar fora do escopo (o MEDIUM da r4 é o caso esperado).

- [ ] **Step 4: Medir a referência de hoje uma vez**

No intervalo da r4, lançar os agentes por arquivo do fluxo atual (4 agentes, mesmos grupos de arquivo da rodada original) e anotar tokens e duração, para a comparação.

- [ ] **Step 5: Portão**

Se o aceite da r5 falhar, ou dois ou mais dos quatro alvos da r4 e da r6 falharem: **parar**, não seguir para a Task 6, e levar os números ao dono. Se algum verificador estourar o contexto ou passar de 400 linhas de unidade, ajustar o teto no `SKILL.md`, rodar de novo o intervalo e registrar.

- [ ] **Step 6: Escrever o arquivo de medição e commitar**

Tabela por intervalo: unidades, linhas de unidade, achados por execução, alvos achados, tokens e duração por agente; e a linha da referência de hoje. Sem nome de projeto, de carta ou de pessoa.

```bash
python3 scripts/check-private-names.py
git add docs/superpowers/specs/2026-11-15-codereview-rodada-de-prosa-medicao.md
git commit -m "docs(codereview): medição da rodada de verificação sobre quatro intervalos gravados"
```

---

### Task 6: release 2.29.0

**Files:**
- Modify: `plugins/codereview/.claude-plugin/plugin.json:7` (`2.28.5` → `2.29.0`)
- Modify: `$S/SKILL.md:4`
- Modify: `.claude-plugin/marketplace.json:327`
- Modify: `README.md:151` e a seção `codereview` do README (uma frase sobre a rodada de verificação e o critério da Documentation)
- Modify: `plugins/codereview/CHANGELOG.md` (entrada nova no topo)
- Modify: `docs/superpowers/specs/2026-11-15-codereview-rodada-de-prosa-design.md:3` (`draft` → `approved`, `not_started` → `implemented`)

- [ ] **Step 1: Trocar a versão nos quatro lugares e escrever a entrada do CHANGELOG**

Entrada `## [2.29.0] — <data>`, em português, no formato das anteriores: o que muda (tipo do achado, tabela da Documentation, rodada de verificação, `prose_units.py`, `verify=off`), o limite declarado, e os números da Task 5. Minor: comportamento novo, sem quebrar argumento existente.

- [ ] **Step 2: Rodar os portões do repositório**

```bash
python3 scripts/codex-adapters.py --check
python3 scripts/codex-marketplace.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/validate-versions.py
python3 scripts/check-private-names.py
(cd plugins/codereview/skills/codereview && python3 tests/test_prose_units.py && python3 tests/test_prose_contract.py && python3 tests/test_scan_secrets.py)
```

Expected: rc 0 em todos.

- [ ] **Step 3: Varrer o próprio diff atrás de segredo e ler a lista de achados**

Run: `git diff origin/main...HEAD --unified=0 | bash plugins/codereview/skills/codereview/scripts/scan_secrets.sh`
Expected: JSON com `"findings": []`. Ler o campo `findings`, não só o rc (lição da 2.28.5).

- [ ] **Step 4: Commit e conferência dos trailers**

```bash
git add -A
git commit -m "feat(codereview): v2.29.0 — nota escrita para prosa e rodada de verificação"
git log -1 --format='%(trailers:key=Co-authored-by,valueonly)'
```

Expected: a última linha imprime nada.

- [ ] **Step 5: Entregar ao dono**

Relatar: os commits da branch, os números da Task 5, e que faltam o push, o PR e o merge, que são dele. Depois do merge, a skill instalada se atualiza por `claude plugin marketplace update`.
