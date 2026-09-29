---
name: skill-self-containment
description: "Verifica se uma skill roda sozinha, sem nada de fora dela. Caça path de máquina, arquivo citado ausente ou órfão e dependência de outro repo, e diz o que vendorizar e o que é exceção legítima. Fase 1 da skill-quality-audit. Triggers — skill autocontida, self-contained, portar skill, path absoluto, reference quebrada, dependência externa."
metadata:
  author: JorUge
  version: "0.4.0"
  hermes:
    tags:
      - skills
      - self-contained
      - portable
      - auditoria
      - refactoring
      - progressive-disclosure
    related_skills:
      - skill-quality-audit
      - skill-claim-check
      - skill-refactoring
---

# Skill Self-Containment — Auditar e Garantir Skills Autocontidas

## Quando usar

- Criar uma skill nova e querer que ela nasça autocontida
- Auditar uma skill existente: ela funciona **sozinha** ou depende de arquivos/paths externos?
- Empacotar skill para outro harness (ex: transferir conhecimento entre máquinas)
- Refatorar skill inchada e garantir que o resultado não fique com dependências externas
- Verificar portabilidade antes de compartilhar/backup

## O que é uma skill autocontida

**Definição:** uma skill é autocontida quando **tudo que ela precisa para executar vive dentro do diretório dela** — instruções, referências, scripts, templates, assets. Outro agente (ou outro harness) pode pegar a pasta e fazer o trabalho **sem** docs originais, paths absolutos, ou conhecimento tribal da sessão que a criou.

**Exit standard (lefant):** uma skill autocontida é um pacote que outro agente pega *cold* — sem o repo original, sem a conversa original — e ainda faz o trabalho corretamente.

### Estrutura padrão

```
skill-name/
├── SKILL.md          # Obrigatório: frontmatter + workflow default
├── references/       # Detalhes lidos sob demanda
├── scripts/          # Lógica determinística/repetida
├── assets/           # Templates, fixtures, exemplos
└── CHANGELOG.md      # Quando o repo exige (como este marketplace)
```

## Abrangência: skills generalistas, não pontuais

Skills devem ser, sempre que possível,
**abrangentes** — cobrir uma *família/categoria de tarefa* (ex: "responder a incidente
de CPU em qualquer host Linux"), não uma *instância única* (ex: "investigar o servidor X").
Skill pontual serve uma vez; skill abrangente serve a produtividade continuamente e
evita multiplicar skills quase idênticas.

**Caso real:** uma skill criada na investigação de um pico de CPU num servidor específico
(com o nome do servidor no nome da skill) foi renomeada para `cpu-incident-response` — mesmo
método, agora parametrizado por host. O gatilho saiu de "incidente no servidor X" para "pico de
CPU/load em host Linux".

**Regras práticas ao criar/auditar uma skill:**
1. **Gatilho por categoria**, não por nome próprio: "pico de CPU/load em host Linux"
   > "problema no servidor X". Hosts/máquinas/instâncias viram **dados** (reference ou
   parâmetro), não o **nome** da skill.
2. **Dados específicos vão para references/** (ex: `references/<hosts>.md` com IPs,
   IDs, SO) — a skill fica abrangente e autocontida; a instância fica como dado
   consultável.
3. **Parametrize scripts**: em vez de hardcodar host/IP/janela, aceitar `--host` /
   `--id` / `--inicio` / `--fim` (default = último caso conhecido).
4. **Exceção legítima à abrangência:** quando o conhecimento é *verdadeiramente* de uma
   instância única sem perspectiva de reuso (ex: procedimento de um equipamento que não
   se repete). Na dúvida, generalize — o custo de generalizar é pequeno; o custo de uma
   skill pontual é outra skill quase igual no futuro.
5. **Abrangência não conflita com autocontenção nem progressive disclosure:** a skill
   continua com SKILL.md leve (workflow da categoria) e references para os detalhes de
   cada instância. Generalizar é mudar o *escopo do gatilho*, não inchar o corpo.

## Workflow de Auditoria (7 passos)

### Passo 1 — Mapear a skill
```bash
find <dir-da-skill>/ -type f | sort     # ex.: plugins/<p>/skills/<skill>; no Hermes, "${HERMES_HOME:-$HOME/.hermes}/skills/<cat>/<skill>"
wc -l <dir-da-skill>/SKILL.md
```

### Passo 2 — Caçar dependências externas (o coração da auditoria)

Procurar no SKILL.md e references/ por:
```bash
# Paths absolutos fora da skill (home do harness, máquina do usuário, sistema)
grep -rn "~/\.[a-z]\|/home/\|/Users/\|/root/\|/var/\|/opt/" <skill>/ --include="*.md"
# Paths relativos que escapam da skill (subir um nível: pai/desta/skill)
grep -rn "\.\./" <skill>/ --include="*.md"
# Referências a arquivos que NÃO existem dentro da skill
grep -rno "references/[a-z-]*\.md\|scripts/[a-z-_.]*\.py\|assets/[a-z-_.]*" <skill>/ --include="*.md" | sort -u
```

**Regra de ouro:** URL externa para **download de ferramenta** (ex: CLI oficial do fabricante de hardware) é aceitável — é fonte primária. O que NÃO pode: apontar para docs internos de repo, scripts de outro projeto, ou conhecimento que só existia na sessão de criação.

### Passo 3 — Verificar que references/scripts existem e são referenciados corretamente

```bash
# Para cada "📄 references/<arquivo>.md" no SKILL.md, o arquivo existe?
ls <skill>/references/
# Scripts citados são executáveis e têm shebang?
ls -la <skill>/scripts/ 2>/dev/null
```

**Cuidado:** reference órfã (arquivo existe mas não é citado no SKILL.md) = peso morto. Reference citada mas ausente = skill quebrada silenciosamente.

### Passo 4 — Verificar paths relativos e portabilidade

- Todos os paths de arquivos **dentro da skill** devem ser relativos ao diretório da skill
- Scripts não devem hardcodar a home do harness (`~/.claude/...`, `~/.hermes/...`) nem paths do usuário
- Script de uso da skill vive em `scripts/` dela; script compartilhado do harness só como exceção
  documentada
- Env vars devem ser lidas via `.env`/variáveis, nunca embutidas

### Passo 5 — Verificar SKILL.md como índice leve

| Check | Bom | Ruim |
|-------|-----|------|
| Tamanho | < 500 linhas / < 5000 tokens | > 500 linhas |
| Descrição | Diz o que + quando usar | Só diz o tema |
| Workflow default | 1 caminho claro + fallbacks | Menu de opções iguais |
| Material de referência | Em references/ | No corpo |
| Gotchas | Explícitos | Escondidos |

### Passo 6 — Corrigir dependências (se não autocontida)

Só com pedido explícito de correção. Em pedido de auditoria ("audite", "verifique"), este passo
vira proposta no relatório.

Para cada dependência externa encontrada:
1. **Vendorizar:** copiar/reescrever o conteúdo necessário para dentro da skill (`references/`, `scripts/`, `assets/`)
2. **Reescrever paths absolutos** como relativos à skill
3. **Remover conhecimento tribal:** transformar em instrução explícita no SKILL.md ou reference
4. **Remover referências a upstream docs** que não estão no pacote

### Passo 7 — Validar

**Gate automatizado:** a auditoria simples da skill `skill-quality-audit`, que vem no mesmo
plugin. `SQA` é o diretório dela, pasta vizinha desta:
```bash
SQA="$(dirname <dir-desta-skill>)/skill-quality-audit"
python3 "$SQA/scripts/audit_skill_quality.py" <dir-da-skill>   # rc=0 sem erro; --strict reprova aviso
```
- Os checks B1 a B7 são os Passos 2 a 4 desta skill automatizados: arquivo citado ausente ou órfão,
  path que sobe para fora da skill (inclusive em references), path de máquina, CHANGELOG,
  `__pycache__`, sintaxe e shebang dos scripts. O que cada check prova e não prova: o
  `checks.md` nas references da `skill-quality-audit`.
- Somente leitura e só biblioteca padrão; se o harness tiver gate próprio (ex.: um
  `audit-skill.sh` em `$HERMES_HOME/scripts/`), ela o roda junto como G1.
- Sem a `skill-quality-audit` instalada: os comandos dos Passos 2 e 3 e o Checklist Final.

**Citar reference de outra skill é seguro:** só conta como "desta skill" o que aparece como
`references/<arquivo>.md` sem path antes. Escrever `skills/outra/references/<arquivo>.md` não
contamina a contagem.

```bash
# Validador de referência da spec Agent Skills, se instalado: o repositório oficial instala o
# comando skills-ref; o pacote PyPI skills-ref (0.1.1) instala agentskills. O nome npm
# "@anthropic/skills-ref" não existe (404 em 2026-09-23): não usar.
V=$(command -v skills-ref || command -v agentskills)
if [ -n "$V" ]; then "$V" validate <skill>/; else echo "validador indisponível: a skill-quality-audit tenta via uvx (G2); sem uvx, checks A1 a A6 dela, senão o Checklist Final"; fi
# Lista final de dependências externas restantes (deve ser só URLs de download)
grep -rn "~/\.[a-z]\|/home/\|/Users/\|\.\." <skill>/ --include="*.md" | grep -v "URL de Download\|http" || echo "✅ autocontida"
```

## Poka-yoke do padrão — sensor automático (não depende de lembrar)

O gate manual acima exige que alguém **lembre** de rodar, e convenção escrita falha quando o
fluxo é rápido. Para skill fora do padrão nascer óbvia, ligue o mesmo gate a algo que roda
sozinho:

| Onde | Como |
|---|---|
| Hook `pre-commit` do repo de skills | rodar o gate só nas skills com arquivo no stage; `rc!=0` bloqueia o commit |
| Cron diário (harness com agendador) | auditar as skills cujo diretório mudou desde o último commit; silêncio quando está tudo ok, relatório só quando há violação |
| Varredura completa, de vez em quando | todas as skills ativas, para medir a dívida acumulada (baseline) |

- **Delta, não varredura, no dia a dia:** auditar só o que mudou mantém o alerta raro e útil;
  a varredura completa serve para medir o baseline, não para alertar todo dia.
- **Anti-padrão "item solto":** referência nova a script fora da skill (em diretório do harness)
  é o sinal mais comum de skill nascendo dependente. Baseline antigo e legítimo (wrapper exigido
  pelo agendador, exemplo didático) fica aceito; só a linha nova no diff alerta.
- Arquivo morto (`.archive/`, cópias de hub) fica fora do escopo nos dois modos.

**Pitfall de redação:** gate que procura `..` seguido de `/` pode casar reticências (`...` e
barra) se o regex não excluir o ponto anterior. Ao corrigir skill reprovada, conferir se é path
real ou reticência. Em texto didático sobre o gate, escrever `..` separado de `/` (ex.:
"`..` + `/`"), nunca a sequência literal, senão a própria skill deixa de passar.

## Checklist Final (antes de declarar autocontida)

- [ ] Diretório da skill contém tudo: SKILL.md + references/ (se houver) + scripts/ (se houver)
- [ ] Zero paths absolutos fora da skill em instruções
- [ ] Zero referências `..` + `/` para fora (path de subir nível)
- [ ] Zero menção a docs de repo externo como fonte de verdade
- [ ] Todo arquivo citado no SKILL.md existe dentro da skill
- [ ] Scripts têm shebang + são executáveis (se aplicável)
- [ ] Descrição no frontmatter diz **o que** + **quando usar** (trigger correto)
- [ ] SKILL.md é o menor arquivo que preserva o workflow default
- [ ] Detalhes/variantes estão em references/, não no corpo
- [ ] Gotchas e verificações explícitas
- [ ] CHANGELOG.md atualizado (quando o repo exige)
- [ ] **Teste mental:** outro agente pega esta pasta e faz o trabalho? (sem conversa original)

## Pitfalls Conhecidos

- **URL externa ≠ dependência:** link de download de ferramenta oficial (site do fabricante, GitHub) é fonte primária — não remover. Dependência proibida é doc interno de repo, script de outro projeto, path absoluto de máquina.
- **Reference órfã:** arquivo em references/ que ninguém cita no SKILL.md = peso morto. Ou cita no SKILL.md ou remove.
- **Reference citada mas ausente:** o SKILL.md diz "ver references/<arquivo>.md" mas o arquivo não existe — skill quebrada silenciosamente. Verificar sempre no Passo 3.
- **Vendorizar ≠ copiar cegamente:** ao trazer conteúdo de fora, adaptar ao contexto real (paths, nomes, exemplos) — senão vira dívida técnica com cara de docs.
- **Skill recém-criada já pode nascer não-autocontida:** o fluxo de criação (skill-creator, `skill_manage` do Hermes ou cópia à mão) não valida dependências. Rodar a auditoria após criar.

## Avaliar esta skill

Casos de gatilho (deve e não deve disparar, com quase-acertos das irmãs) em
`assets/trigger-evals.json`, no formato de eval set do `skill-creator`. Antes de rodar com LLM,
leia os critérios na matriz de avaliação da `skill-quality-audit`.

## Relação com outras skills

As quatro vêm no mesmo plugin (`skill-quality-audit`) e se acham como pastas vizinhas.

- **`skill-quality-audit`**: porta de entrada da auditoria completa (ordem das fases, reparo autorizado, relatório) e dona do script que automatiza o Passo 7. Esta skill é a fase 1 dela: vindo de lá, execute só o diagnóstico desta skill e devolva o controle. Fora dela, a auditoria de vários critérios ou de várias skills começa por lá.
- **`skill-claim-check`**: veracidade, toda afirmação da skill com sensor, derivação ou data. Ao vendorizar conteúdo (Passo 6), vale conferir com ela os números e limites trazidos de fora.
- **`skill-refactoring`** — refatorar skills inchadas (+500 linhas) via Progressive Disclosure. Complementar: refactoring reduz o SKILL.md; self-containment garante que o resultado não dependa de nada externo.

## Referências externas (fonte das melhores práticas)

- [lefant/agent-skills — skills-best-practices](https://github.com/lefant/agent-skills/tree/main/lefant/skills-best-practices) — self-contained packaging rule, authoring loop, exit standard
- [OpenLLM — SKILL.md: Self-Contained Capability Files for AI Agents](https://openllm.wavise.com/blog/skill-md-format-guide) — spec, estrutura, anti-patterns, validação
- [Anthropic — Agent Skills (repositório oficial)](https://github.com/anthropics/skills) — exemplos de skills autocontidas
- [agentskills.io/specification](https://agentskills.io/specification) — spec aberta do formato
