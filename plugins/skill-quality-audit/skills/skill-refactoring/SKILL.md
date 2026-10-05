---
name: skill-refactoring
description: "Enxuga SKILL.md inchado com progressive disclosure. Decide entre extrair para references e scripts ou comprimir por tabelas, preservando a narrativa de execução e os pitfalls, e mede antes e depois. Fase 3 da skill-quality-audit. Triggers — SKILL.md acima de 500 linhas, skill inchada, progressive disclosure, mover para references, comprimir skill."
metadata:
  author: JorUge
  version: "0.6.0"
  hermes:
    tags:
      - skills
      - refactoring
      - progressive-disclosure
      - compressao
    related_skills:
      - skill-quality-audit
      - skill-self-containment
      - skill-claim-check
---

# Skill Refactoring — Progressive Disclosure Workflow

## Quando usar

Uma skill precisa de refatoração quando:
- SKILL.md com **+500 linhas** (teto da spec Agent Skills; ERRO no C1 do auditor) ou **+20 mil
  caracteres** (heurística local; AVISO no C1). Acima de 400 linhas o C1 dá INFO: considere
  comprimir. Caracteres, não bytes (Passo 1)
- Mistura workflows operacionais com material de referência (inventário, incidentes, configurações)
- Tem seções que poderiam ser scripts reutilizáveis
- A descrição não reflete o que a skill realmente faz
- Lições aprendidas de sessões recentes não foram incorporadas

## Estratégias de Compressão (Skill Shrinking)

Nem toda skill inchada precisa de extração para `references/`. Duas abordagens complementares:

### Estratégia A — Progressive Disclosure (clássica)

Extração de seções de referência para `references/` + scripts para `scripts/`. SKILL.md vira índice leve. Ideal quando a skill mistura **workflow operacional** com **material de consulta** (inventários, incidentes, documentação de API).

### Estratégia B — Compressão Estrutural (via tabelas)

Ideal quando a skill é **densa mas coesa** — todo o conteúdo é workflow, não há material de referência para extrair. A compressão substitui **bash blocks longos com comentários** e **listas verbosas** por **tabelas Markdown**.

| Antes | Depois |
|-------|--------|
| ```bash<br/># Explicação longa<br/># Mais explicação<br/>comando --flag1 --flag2 \|<br/>  grep coisa > output<br/>``` | `\| Passo \| O que \| Comando \|`<br/>`\|-------\|-------\|--------\|`<br/>`\| 1 \| Descrição curta \| `comando` \|` |
| 5 parágrafos descritivos | 1 linha na tabela |

**Resultados reais numa skill de troubleshooting de agente (758→569 linhas, -24.9%):**

| Seção | Antes | Depois | Técnica |
|-------|-------|--------|---------|
| Section A (Audit) | ~77 linhas | ~20 | 7 passos c/ bash blocks → tabela |
| Section B (Secure Ops) | ~64 linhas | ~24 | Regras longas → tabela única |
| Section C (Health Check) | ~59 linhas | ~18 | 5 passos c/ bash blocks → tabela |
| Section D (Update Audit) | ~88 linhas | ~32 | 7 fases c/ descrições → tabela |

**Regras da compressão estrutural:**
1. **Preservar pitfalls integralmente** — eles carregam experiência prática que não se comprime bem
2. **Manter todos os comandos** — só mudar o formato (de bash block para célula de tabela)
3. **Remover exemplos autoexplicativos** — se o comando é óbvio, não precisa de exemplo antes
4. **Remover duplicatas** — headings repetidos, `---` extras, fragmentos soltos entre seções
5. **NÃO fazer extração de funções** — ver pitfall abaixo

### ⚠️ Pitfall: Extração de funções quebra skills

❌ **Não tentar comprimir skills extraindo funções para arquivos separados e referenciando-as.**

Teste real com uma skill de instalação de agente de segurança (738 linhas):
- Extraiu funções (`check_venv_and_deps`, `run_agent_install`, `validate_os_compatibility`, `report_status`) para ~120 linhas
- Com a skill recarregada, o agente **perdeu contexto** — respondeu que não tinha informação sobre quais passos de instalação o ambiente exigia
- Revertido via `git stash pop`

**Causa raiz:** Skills carregam contexto via exemplos + instruções de **como** e **quando** usar cada bloco no SKILL.md. Extrair funções remove a narrativa de execução — o modelo não sabe mais como encadear os passos, só tem os verbos soltos.

**Alternativa:** compressão estrutural (Estratégia B) mantém o contexto narrativo e só muda o formato, ou merge de skills relacionados (fundir skills do mesmo domínio) preservando cada `claude.md` original.

## Workflow (6 passos)

### Passo 1 — Mapear a skill
```bash
# ex.: plugins/<p>/skills/<skill>; no Hermes, "${HERMES_HOME:-$HOME/.hermes}/skills/<cat>/<skill>"
python3 -c 'import sys; t=open(sys.argv[1], encoding="utf-8").read(); print(t.count("\n"), "linhas,", len(t), "caracteres")' <dir-da-skill>/SKILL.md
cat -n <dir-da-skill>/SKILL.md | grep -n '^##\|^###\|^>\|---\|^$\|^[A-Z]' | head -60
```

Caracteres, como o `len()` do C1, e não bytes: o `wc -c` conta bytes, e o acento em UTF-8 ocupa
dois. Em 05/10/2026 o `SKILL.md` da `ticket` tinha 20.478 bytes e 19.950 caracteres, e o `wc -c`
fez parecer acima do teto uma skill que estava abaixo.

Identificar:
- Todas as seções pelo marcador `##`
- Linhas de início e fim de cada seção
- Seções que são **referência** (não workflow) → candidatas a `references/`
- Seções que são **comandos reutilizáveis** → candidatas a `scripts/`
- Seções que são **lições/incidentes** → candidatas a `references/`

### Passo 2 — Extrair references/
Os Passos 2 a 5 editam a skill: só com pedido explícito de refatoração. Em pedido de auditoria,
o plano de extração ou compressão vai como proposta no relatório.

**Prova antes de remover.** Só sai do SKILL.md o que já está em outro lugar: o bloco ou a frase
que uma reference traz por extenso, ou a repetição do próprio SKILL.md. O script aponta os dois:

```bash
python3 scripts/repetidos.py <dir-da-skill>   # BLOCO, FRASE e REPETIDA; --json para outro script
```

O resto não sai por extração: é Estratégia B, reescrito no lugar com os comandos e as
armadilhas. Na `ticket` 1.9.0 (05/10/2026) o script achou os 3 blocos que a passada tirou, e
nenhuma frase: a passada anterior já tinha levado as repetições.

Para cada seção candidata, num arquivo **novo**: o `>` sobrescreve a reference que já existir
(com ela, edite-a e acrescente a seção):
```bash
[ -e references/<tema>.md ] && echo "references/<tema>.md já existe" \
  || sed -n 'LINHA_INICIO,LINHA_FIM p' SKILL.md > references/<tema>.md
```

Depois de mover, conserte quem apontava para o trecho: `grep -rn 'SKILL.md' references/ scripts/`
lista cada citação de volta, e a que cita uma seção que saiu passa a citar a reference. A passada
de 01/10 da `ticket` deixou o `templates.md` apontando para um comando que tinha saído do
SKILL.md, e só a leitura fria do Passo 6 achou.

Nomear arquivos pelo **tema**, não pela sessão:
| ✅ Certo | ❌ Errado |
|---|---|
| `hosts-inventory.md` | `inventario-18-jun.md` |
| `incidents.md` | `incidente-servidor-x.md` |
| `api-lessons.md` | `notas-sessao-api.md` |

### Passo 3 — Criar scripts/
Comandos/consultas recorrentes viram scripts Python (só lógica determinística; a narrativa de
quando e como encadear os passos fica no SKILL.md, ver pitfall acima):
- Usar `urllib` para chamadas HTTP (sem dependências externas)
- Credencial só por variável de ambiente ou `.env`; nunca no script nem em argumento
- Colocar `if __name__ == "__main__":` e `argparse` para reuso via terminal, com `--help`
- **Barreiras de segurança em scripts de ação:** sempre exigir `--dry-run` antes de efetivar. Em bulk operations acima de threshold (ex: >20 itens), exigir uma flag explícita (`--yes`) em vez de prompt interativo, que trava o agente. Filtro amplo sem escopo explícito (ex: `--search` sem `--ids`): exibir aviso + confirmação
- Validar no interpretador real com caso válido e inválido (regra 6 da skill `skill-claim-check`)
- Ao escrever script que fala com API de terceiro, leia antes as regras que vieram de um caso
  real (lote por chamada, fallback para o banco, modo pós-ação):
  `references/estudo-de-caso-monitoramento.md`

Estrutura ideal de script:
```python
#!/usr/bin/env python3
"""Descrição clara do que o script faz."""
import argparse, json, re, sys, subprocess, urllib.request

def api_call(url, payload, token=None):
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    return json.loads(urllib.request.urlopen(req).read())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--search", help="Filtrar por texto")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar o que faria, sem efetivar")
    args = parser.parse_args()
    # ... lógica ...

if __name__ == "__main__":
    main()
```

### Passo 4 — Condensar SKILL.md
O molde abaixo é o de uma skill que **opera um sistema** (o estudo de caso). A SKILL.md
refatorada dela deve conter **apenas**:
1. YAML frontmatter com descrição **ativa** (começar com verbo de ação)
2. ⚠️ Regras obrigatórias antes de qualquer ação
3. Acesso rápido (URLs, auth, paths)
4. Workflows operacionais (passo a passo)
5. ✨ Seção "Ferramentas" apontando para scripts/
6. 🗂️ Tabela de referências (arquivo + conteúdo)
7. Lições críticas: as que evitam erro antes de abrir uma reference (lição só sai com prova,
   Passo 2)
8. Problemas conhecidos / TODO (se relevante)
9. **NUNCA**: inventários, incidentes, referências completas, docs de API

Numa skill de **fluxo** (os passos de um processo, como a `ticket`), os passos e a tabela de
armadilhas ficam no SKILL.md: ali elas evitam o erro antes de a reference ser lida. Um teto de
cinco lições cortaria 3 das 8 armadilhas da `ticket` (05/10/2026).

### Passo 5 — Registrar as lições da refatoração
No CHANGELOG da skill (ou numa reference), e não numa seção nova do SKILL.md: ela faria crescer o
arquivo que a passada quer encolher. Registre:
- O que estava errado e por que
- Decisões técnicas (ex: tamanho do lote, fallback para o banco)
- Padrões que não devem se repetir

No SKILL.md entra só a armadilha que evita erro no uso, uma linha na tabela.

### Passo 6 — Verificar
```bash
python3 -c 'import sys; t=open(sys.argv[1], encoding="utf-8").read(); print(t.count("\n"), "linhas,", len(t), "caracteres")' <dir-da-skill>/SKILL.md
# < 500 linhas (ERRO do C1 acima) e < 20 mil caracteres (AVISO); acima de 400 linhas é INFO
python3 -c 'import ast,sys; ast.parse(open(sys.argv[1]).read(), sys.argv[1])' scripts/<script>.py && echo "OK"   # sem gravar __pycache__
# Verificar todos os scripts
SQA="$(dirname <dir-desta-skill>)/skill-quality-audit"         # a skill-quality-audit, pasta vizinha
python3 "$SQA/scripts/audit_skill_quality.py" <dir-da-skill>   # C1 a C3 e B1 a B7 limpos
# Sem a skill-quality-audit instalada: a medida acima, e conferir à mão que cada references/ e scripts/ citado existe
```

**Leitura fria, depois da auditoria.** Ela vê a forma, não o uso: um agente sem contexto lê só a
skill e responde 3 a 5 perguntas cujas respostas dependem do que saiu do SKILL.md, citando de
onde tirou. Leia `references/leitura-fria.md` antes do primeiro teste (o prompt, como escolher
as perguntas e como ler o resultado). Na `ticket` 1.9.1 achou o ponteiro morto que a auditoria
deixou passar.

Refatoração é a fase 3 da auditoria completa da skill `skill-quality-audit`: vindo de lá, esta
skill termina no Passo 6 e devolve o controle (baseline e relatório são de lá). Refatoração
avulsa: medir antes e depois (linhas e caracteres), o gate acima e a leitura fria.

> 📄 **Antes de escolher entre extrair e comprimir**, leia o caso real em
> `references/skill-compression-test-0.md`: extração de funções (falhou) contra compressão
> estrutural (funcionou) numa skill de troubleshooting de agente.

## ⚠️ Armadilhas comuns

| Armadilha | Solução |
|---|---|
| Skill maior que 500 linhas após extração | Seções workflow também precisam ser condensadas. Apontar para references/ |
| References duplicadas entre skills | Verificar `ls <raiz-das-skills>/*/references/` (no Hermes, layout `<cat>/<skill>`: `*/*/references/`) antes de criar |
| Script com SyntaxError | **NUNCA** pular verificação de lint no passo 6 |
| Senhas em texto claro em scripts | Credencial só por variável de ambiente ou `.env`, nunca no script nem em argumento |
| Não documentar padrões de segurança que emergiram durante refatoração | Adicionar pitfalls de segurança na descrição da skill — ex: confirmar antes de bulk, sempre dry-run primeiro |
| Skills crescem após refatoração (+1.7K chars em 1 mês no estudo de caso) | Monitorar tamanho periodicamente, com os limiares do C1: INFO acima de 400 linhas, AVISO acima de 20 mil caracteres |
| Esquecer de criar CHANGELOG.md na refatoração | Criar entrada no CHANGELOG com data, motivação e como reverter (quando o repo exige) |
| Nome de skill muito específico da sessão | Nomear pelo **tema**, não pelo caso concreto |

## Exemplo real: skill que opera sistema de terceiro (Jun a Jul/2026)

1.677 para 240 linhas no SKILL.md, com 8 references e 3 scripts. Para comparar com a sua
refatoração, as métricas completas e as regras de script do caso estão em
`references/estudo-de-caso-monitoramento.md`.

## Referência: Progressive Disclosure

- **Spec Agent Skills** (https://agentskills.io/specification, seção Progressive disclosure):
  metadata sempre carregada, SKILL.md inteiro quando a skill ativa (abaixo de 500 linhas),
  arquivos de `references/`, `scripts/` e `assets/` só quando necessários, a um nível do SKILL.md.
- **Regra do autor para arquivos de índice:** arquivo de índice nunca contém o que pode estar em
  arquivo de detalhe; nunca fazer dump completo em arquivo carregado toda sessão.

## Avaliar esta skill

Casos de gatilho (deve e não deve disparar, com quase-acertos das irmãs) em
`assets/trigger-evals.json`, no formato de eval set do `skill-creator`. Antes de rodar com LLM,
leia os critérios na matriz de avaliação da `skill-quality-audit`.

## Relação com outras skills

As quatro vêm no mesmo plugin (`skill-quality-audit`) e se acham como pastas vizinhas.

- **`skill-quality-audit`**: porta de entrada da auditoria completa; esta skill é a fase 3. Os
  checks C1 a C3 dela dizem quando entrar aqui, e o script mede o antes e o depois.
- **`skill-self-containment`**: garante que o resultado da refatoração não dependa de nada
  externo; útil depois de extrair.
- **`skill-claim-check`**: números e limites que sobrarem no corpo precisam de sensor.