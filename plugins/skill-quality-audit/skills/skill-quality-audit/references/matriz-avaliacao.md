# Matriz de avaliação da skill-quality-audit

Inspirada no ciclo do `skill-creator` (casos de teste, baseline sem a skill, asserções
objetivas, eval set de gatilho), em três camadas. Só a camada 1 é gate; as outras pedem LLM e
são opcionais.

## Camada 1: estrutural, determinística, sem LLM (gate)

Comando: `python3 tests/test_audit_skill_quality.py` (a partir do diretório da skill). Passa
com `OK`; teste pulado aparece como `skipped` com o motivo.

| Caso | Entrada | Esperado |
|---|---|---|
| Uso | `--help` | `rc=0`, lista `--family` |
| Uso inválido | sem argumentos; path inexistente | `rc=2` |
| Skill quebrada | diretório sem `SKILL.md`; `SKILL.md` sem frontmatter | `rc=1`, achado A1 |
| Skill válida | fixture mínima com reference, script e CHANGELOG | `rc=0`, nenhum `[ERRO]` |
| Vários defeitos | name fora da spec, `tags: [a, b]`, reference ausente, path que sobe diretório (`..` + `/`), sem CHANGELOG, `.py` com erro de sintaxe | `rc=1` e A2, A4, A5, B1, B3, B5, B7 |
| Aviso e `--strict` | reference órfã | `rc=0`; com `--strict`, `rc=1` |
| Orçamento de descrição | descrição acima de 60 chars | INFO A3; some com `--desc-budget 0` |
| Frontmatter em bloco | `related_skills` como lista de bloco | JSON devolve a lista |
| Gates ausentes | `audit-skill.sh` e `skills-ref` inexistentes | `[SKIP]` G1 e G2, `rc=0` |
| Cópia fria | skill copiada sozinha para diretório temporário, `HOME` e `HERMES_HOME` falsos | autoauditoria `rc=0`; `--family` com irmãs `[SKIP]` e `rc=0` |
| Família no plugin | as quatro em `plugins/<p>/skills/`, sem Hermes; depois, irmãs sem bloco `metadata` (como o Cursor instala) | `--family --strict` `rc=0`, sem E0; E1 ausente, ou INFO sem `metadata` |
| Paridade de claims | fixture com os 4 tipos de afirmação, bloco ``` e bloco ~~~ | mesmas linhas que `listar-afirmacoes.sh` da irmã; pulado se a irmã não existe |
| Revisão adversarial | path de máquina entre crases; aspas com comentário; `: ` em valor sem aspas; `SKILL.md` em latin-1; `agentskills` no PATH; reference em subpasta ausente; dois níveis de `..` + `/` em script e um nível numa reference; bloco ~~~ | B4; sem falso A2; ERRO A1; ERRO A1; `[OK] G2`; B1; AVISO B3 só no script; sem D1 |

## Camada 2: gatilho (eval set, com LLM)

Arquivo: `assets/trigger-evals.json`, no formato `[{"query": ..., "should_trigger": ...}]` que o
otimizador de descrição do `skill-creator` consome. Os negativos são quase-acertos: pedidos que
mencionam skill ou auditoria mas pertencem a outra ferramenta (criar skill, auditar código,
auditar ERP). Critério: taxa de acerto por consulta, 3 execuções por item, e nenhum negativo
disparando com frequência maior que os positivos. Orçamento de descrição do harness: os
positivos precisam acertar lendo só os primeiros 60 caracteres.

## Camada 3: comportamento (com LLM, com e sem a skill)

Rodar cada prompt em sessão nova, uma vez com acesso à skill e outra sem (baseline), e avaliar
as asserções abaixo lendo transcrição e saída, não só a resposta final.

| Prompt | Asserções objetivas |
|---|---|
| "audite a skill X" | não edita arquivo; relatório segue o contrato; cita comando e `rc` |
| "audite a família de skills e corrija o que precisar" | pede allowlist ou declara uma antes de editar; baseline antes da primeira edição; no máximo 2 ciclos de reparo |
| "a skill Y está pronta para ir para outro harness?" | faz o teste frio (cópia sozinha); aponta paths de máquina e irmãs ausentes como SKIP, não como erro |
| "passou no gate, pode commitar?" | não trata SKIP como aprovado; separa dívida pré-existente de regressão |

Asserção não discriminante (passa com e sem a skill) não prova nada: trocar por outra.
