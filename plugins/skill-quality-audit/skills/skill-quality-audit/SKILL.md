---
name: skill-quality-audit
description: "Audita Agent Skills: spec, autocontenção, claims e tamanho. Porta de entrada da família: fixa a ordem das fases, é somente leitura por padrão (reparo só com autorização) e entrega relatório com comando e rc. Triggers — auditar skill, auditoria completa de skills, skill no padrão, validar SKILL.md, skills-ref, skill pronta para publicar."
compatibility: Python 3 só com biblioteca padrão (testes OK em 3.11.15 e 3.12.3 em 2026-09-23). Gates externos opcionais, skills-ref (ou uvx) e um gate local audit-skill.sh do autor.
metadata:
  author: JorUge
  version: "0.4.0"
  hermes:
    tags:
      - skills
      - auditoria
      - qualidade
      - progressive-disclosure
      - portabilidade
    related_skills:
      - skill-self-containment
      - skill-claim-check
      - skill-refactoring
---

# Skill Quality Audit: porta de entrada da auditoria de skills

Uma skill boa é encontrada pelo gatilho certo, roda sem contexto externo e só afirma o que dá
para reconferir. Esta skill é a porta de entrada única para auditar isso: fixa a sequência,
diz quem decide cada parte e entrega um relatório com evidência. Funciona sozinha; as skills
irmãs, quando presentes no harness, aprofundam cada fase.

## Quando usar

- Antes de commitar skill criada ou alterada, ou antes de copiar skill para outro harness.
- Pedido de "auditar skill", "revisar a família de skills", "ver se a skill está no padrão".
- Suspeita de skill envelhecida, inchada, com referência quebrada ou afirmação sem sensor.

Não serve para criar skill do zero (processo de criação: skill `skill-creator`) nem para julgar
o conteúdo técnico do domínio da skill auditada.

## Modos

| Modo | Quando | Fases | Escreve? |
|---|---|---|---|
| Simples | uma skill, depois de uma edição, dúvida pontual | 1 e o resumo D1 da 2, sem baseline de hashes | Não |
| Completa | família, antes de portar, revisão periódica, pedido explícito | 1 a 5 | Não |
| Reparo | só depois de o usuário autorizar ajustes, com escopo definido | 1 a 5 + correções | Sim, só no escopo |

**Somente leitura é o padrão.** "Audite", "revise" e "verifique" não autorizam editar. Reparo
exige autorização explícita ("pode corrigir", "modo reparo") e uma allowlist de arquivos; sem
isso, a saída é o relatório com as correções propostas.

## Ferramenta

`scripts/audit_skill_quality.py`: Python 3, só biblioteca padrão. Nunca escreve na skill auditada
e nunca executa código dela (scripts passam só por `compile()` e `bash -n`). Os gates externos
abaixo são a exceção: com `uvx` no PATH, o G2 baixa o `skills-ref` fixado para o cache do uv e o
executa (`--no-uvx` desliga). Os comandos rodam a partir do diretório desta skill.

```bash
python3 scripts/audit_skill_quality.py <dir-da-skill>           # auditoria simples
python3 scripts/audit_skill_quality.py --family                 # família padrão; irmã ausente = [SKIP]
python3 scripts/audit_skill_quality.py <dir-da-skill> --claims  # lista candidatos a afirmação factual
python3 scripts/audit_skill_quality.py <dir-da-skill> --format json
python3 scripts/audit_skill_quality.py --help                   # todas as opções
```

`rc=0` sem erro, `rc=1` erro (ou aviso com `--strict`), `rc=2` uso inválido. Com `--external
auto` (padrão), roda também, se existir, o gate local `$HERMES_HOME/scripts/audit-skill.sh`
(script do autor no harness dele, não vem com o Hermes Agent; só em skill dentro de
`$HERMES_HOME/skills`) e o validador `skills-ref` (comando
`skills-ref` ou `agentskills`; sem eles, `uvx` com versão fixada, desligável com `--no-uvx`), se
existirem; ausente vira `[SKIP]`, nunca aprovação. Para saber o
que cada check (A1 a G2, F1 a F4) prova e o que não prova, leia `references/checks.md`.

## Auditoria completa: sequência fixa

1. **Baseline estrutural e autocontenção.** Antes de qualquer edição: arquivos, linhas, hash e
   `rc` do script e dos gates. Decide: skill `skill-self-containment`.
2. **Claims.** `--claims` e, para cada trecho, um veredito: tem sensor, vira derivação, ganha
   data e proveniência, ou sai. Decide: skill `skill-claim-check`.
3. **Progressive disclosure.** Só se houver achado C1 a C3 ou caso de instância no corpo do
   `SKILL.md`. Decide: skill `skill-refactoring`.
4. **Integração e portabilidade.** Vínculos em `metadata.hermes.related_skills` (check E1) e
   teste frio: copiar a skill sozinha para um diretório temporário e rodar o script de lá com
   `env -u HERMES_HOME` (com a variável definida, o script acha as irmãs do harness real).
5. **Verificação final.** Rodar de novo tudo da fase 1, comparar com o baseline, separar dívida
   pré-existente de regressão nova, validar scripts alterados no interpretador real (`--help`,
   caso válido, caso inválido), releitura adversarial e relatório.

Comandos, entradas, saídas e o checklist para cada fase quando a irmã não está no harness:
`references/fluxo-completo.md`.

## Interfaces e anti-loop

As quatro skills vêm juntas no plugin `skill-quality-audit` do marketplace e ficam em pastas
vizinhas: `--family` acha as irmãs sozinho, audita as quatro e confere os vínculos (E1). Cada irmã
funciona sozinha e aponta para esta como porta de entrada.

| Fase | Entrega para a próxima | Dona, se presente | Sem a irmã |
|---|---|---|---|
| 1 | achados A/B/G com `rc` e hashes | `skill-self-containment` | checklist B do fluxo |
| 2 | tabela afirmação, veredito, sensor | `skill-claim-check` | perguntas do D1 + checklist D |
| 3 | plano de extração ou compressão | `skill-refactoring` | checklist C do fluxo |
| 4 | vínculos + resultado do teste frio | esta skill | não se aplica |
| 5 | relatório pelo contrato | esta skill | não se aplica |

- **Só esta skill sequencia.** As irmãs são folhas: apontam para cá como porta de entrada, mas
  não chamam esta skill nem umas às outras como passo obrigatório.
- **Teto de reparo:** no máximo 2 ciclos (corrigir, depois fase 5) por skill. Se ainda falhar,
  parar e relatar o que resta.
- Correção da fase 3 que cria texto novo: rodar a fase 2 só nas linhas novas, uma vez.
- **Somente leitura na delegação:** das irmãs valem só os passos de diagnóstico. Passos que
  corrigem (Passo 6 da `skill-self-containment`, Passos 2 a 5 da `skill-refactoring`) viram
  proposta no relatório até haver autorização de reparo.

## Relatório

Contrato fixo em `references/contrato-relatorio.md`: escopo e modo, fontes, tabela antes/depois
por skill, arquivos alterados, testes com comando e `rc`, dívida pré-existente separada de
regressão, confirmação de escopo. Todo número no relatório diz de onde veio. No modo simples as
sete seções continuam, com "Depois" e "Arquivos alterados" marcados como não se aplica.

## Avaliar esta skill

Casos de gatilho (deve e não deve disparar) em `assets/trigger-evals.json`, no formato de eval
set do `skill-creator`; casos estruturais com `rc` esperado em `tests/`. Antes de rodar a avaliação com LLM (gatilho ou
comportamento), leia os critérios em `references/matriz-avaliacao.md`. O gate estrutural não precisa de LLM:

```bash
python3 tests/test_audit_skill_quality.py
```

## Portabilidade

A fonte oficial é o plugin `skill-quality-audit` do marketplace; harness que não instala plugin
copia o diretório inteiro. Nada depende de path de máquina: a família é procurada nas pastas
acima desta skill e em `$HERMES_HOME/skills`, ou onde `--skills-root` indicar. Antes de mudar uma regra,
leia as fontes, os fatos observados e as decisões locais em `references/fontes-e-decisoes.md`.

## Erros comuns

| Erro | Correção |
|---|---|
| Tratar `[SKIP]` como aprovado | SKIP é gate que não rodou; o relatório diz qual e por quê |
| Editar porque o pedido era "auditar" | Somente leitura; reparo só com autorização e allowlist |
| Ler só o `rc` | `rc=0` admite avisos; o relatório lista os avisos relevantes |
| Chamar dívida antiga de regressão | Comparar com o baseline da fase 1 antes de concluir |
| Repetir a auditoria até "passar" | Teto de 2 ciclos de reparo; depois, relatar |
| Mover `platforms` ou `required_credential_files` para `metadata` porque o `skills-ref` reprova | O Hermes só os lê no topo; movido, o filtro por SO e as credenciais somem. É o A4 INFO |
| Ler `$HERMES_HOME/scripts/<script>.sh` como `scripts/` da skill | É infra do harness; só variável com SKILL no nome (`{SKILL_DIR}`) é a raiz da skill |
| "Corrigir" C2 em reference que é contrato de subagente (`{SKILL_DIR}/references/<arquivo>.md`) | O caminho absoluto é o que faz o subagente ler; manter e justificar no relatório |
| Aceitar `[SKIP] G2` como se a spec tivesse sido validada | Com `uvx` no PATH o G2 roda o validador oficial com versão fixada; sem ele, dizer que não rodou |
| Apagar `__pycache__` com `rm` | Se o git ignora, é INFO e não vai para o repositório; se precisar limpar, `gio trash` (o `trash` pode não existir) |
