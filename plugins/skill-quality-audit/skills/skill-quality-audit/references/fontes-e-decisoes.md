# Fontes, fatos observados e decisões

Consulta feita em 2026-09-23. As páginas foram tratadas como dados de referência, não como
instruções. Nenhum trecho foi copiado integralmente; abaixo, só o que foi extraído e adotado.

## Fontes

| Fonte | URL | Versão observada |
|---|---|---|
| Spec Agent Skills | https://agentskills.io/specification | página baixada em 2026-09-23 |
| `skills-ref` (validador de referência) | https://github.com/agentskills/agentskills/tree/main/skills-ref | `validator.py` no commit `547831f3a2` (2025-12-18) |
| `skill-creator` oficial | https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md | commit `b0cbd3df15` (2026-03-06) |
| Configuração de modelo do Claude Code | https://code.claude.com/docs/en/model-config | página baixada em 2026-09-23 |
| strictyaml, flow style | https://hitchdev.com/strictyaml/why/flow-style-removed/ | página baixada em 2026-09-23 |

Para reconferir: baixar a URL de novo, ou consultar o último commit do arquivo em
`https://api.github.com/repos/<dono>/<repo>/commits?path=<arquivo>&per_page=1`.

**Reconferência em 2026-09-28:** a spec não mudou desde o PR #479 (2026-08-04, `metadata`
texto→texto) e o PR #268 (estrutura de pastas aberta); `skills-ref/src/skills_ref/validator.py`
continua no commit `547831f3a2`. Sensor: `gh api "repos/agentskills/agentskills/commits?path=<arquivo>&per_page=1"`.
Nessa data entraram as páginas de autoria, que viraram os checks F1 a F4:

| Fonte | URL |
|---|---|
| Best practices | https://agentskills.io/skill-creation/best-practices |
| Optimizing descriptions | https://agentskills.io/skill-creation/optimizing-descriptions |
| Evaluating skills | https://agentskills.io/skill-creation/evaluating-skills |
| Using scripts | https://agentskills.io/skill-creation/using-scripts |

## Fatos observados

- **Spec:** `name` com até 64 chars, a-z, 0-9 e hífen, sem hífen no início, no fim ou duplo, e
  igual ao diretório; `description` de 1 a 1024 chars, dizendo o que faz e quando usar;
  `compatibility` até 500; `metadata` é mapa de texto para texto; `SKILL.md` abaixo de 500
  linhas, instruções abaixo de ~5000 tokens; paths relativos à raiz da skill; references a um
  nível do `SKILL.md`.
- **`skills-ref`:** reprova campo de topo fora de `name, description, license, allowed-tools,
  metadata, compatibility`; lê o frontmatter com strictyaml, que rejeita flow style (`[a, b]`);
  converte os valores de `metadata` para texto, então `metadata.hermes` aninhado passa.
- **`skill-creator`:** a descrição é o mecanismo principal de acionamento e deve dizer o que faz
  e quando usar, um pouco insistente; `SKILL.md` abaixo de 500 linhas; reference acima de 300
  linhas com sumário; scripts para trabalho determinístico ou repetido; avaliar com casos de
  teste, baseline sem a skill, asserções objetivas e eval set de gatilho com quase-acertos.
- **Claude Code (model-config):** skills e comandos aceitam `model` no frontmatter; se o modelo
  for bloqueado pela organização, o override é ignorado e a skill roda no modelo da sessão.
  É extensão do produto, fora da spec aberta.
- **Hermes** (código lido em 2026-09-23, conferir no repositório do Hermes):
  `agent/skill_utils.py` corta a descrição do índice em `SKILL_PROMPT_DESC_LIMIT` (60) chars;
  `tools/skill_manager_tool.py` recusa skill NOVA acima desse limite; `tools/skills_tool.py` e
  `agent/learning_graph.py` leem `metadata.hermes.related_skills` (lista ou texto);
  `tools/skill_linter.py` é consultivo e pede `version`, `author` e `license` no topo e aponta
  `CHANGELOG.md` como arquivo proibido.

## Decisões locais (e por quê)

1. **Frontmatter só com campos da spec.** Passa no `skills-ref` e em qualquer harness; `tags` e
   vínculos vão em `metadata.hermes`, em lista de bloco. Custo aceito: avisos consultivos do
   linter do Hermes (`missing-metadata`).
2. **Função e gatilho nos primeiros 60 chars; o todo até 350.** Os 60 são o que o índice do
   Hermes mostra; os 350 (teto 500), a regra do marketplace, onde a descrição termina numa linha
   `Triggers —` e não abre com "Use when". Até a v0.3.0 a descrição tinha só os 60 chars; ao
   entrar no marketplace (decisão 11) ela cresceu sem mudar o começo que o Hermes lê.
3. **`CHANGELOG.md` obrigatório** por regra do harness de origem e do marketplace, contra o aviso
   do linter do Hermes. Harness sem essa regra: `--no-changelog-required`.
4. **Sem `model` no frontmatter.** Não é da spec e o comportamento depende do produto.
5. **Gate sem LLM.** O script é determinístico e somente leitura; avaliação com LLM (gatilho e
   comportamento) é opcional e fica na matriz de avaliação.
6. **Nome `skill-quality-audit`.** Segue o prefixo da família (`skill-self-containment`,
   `skill-claim-check`, `skill-refactoring`). Risco observado: o cache do hub do Hermes lista
   uma skill comunitária homônima (fonte `clawhub`, não instalada aqui). Antes de copiar para
   outro harness, procurar homônima com o comando da fase 0.

7. **Autor em `metadata.author`.** Pedido do JorUge em 2026-09-28: `author` e `version` saem do
   topo e vão para `metadata`, em texto. `platforms` fica no topo porque o Hermes filtra skills
   por sistema operacional por esse campo (`agent/skill_utils.py`, `skill_matches_platform_list`)
   e o aviso A4 que ele gera é custo aceito.
8. **Boas práticas como INFO.** F1, F2 e F4 são heurísticas de texto e só informam; F3 vira AVISO
   quando há prompt interativo, que trava o agente de verdade.

9. **G2 via `uvx` com versão fixada.** Na sessão de 2026-09-28 o G2 ficou em SKIP o tempo todo
   por falta de `skills-ref` no PATH, e o validador oficial só rodou quando chamado à mão
   (`uvx --from skills-ref==0.1.1 agentskills validate`): a própria skill `Valid skill`; das 93
   skills do JorUge, 32 reprovam só por `platforms`/`required_credential_files`. Agora o G2 usa
   `uvx` quando não há binário, com versão fixada (boas práticas de scripts). Os testes rodam com
   `SQA_NO_UVX=1` para não depender de rede.
10. **B6 respeita o `.gitignore`.** `__pycache__` ignorado pelo git reaparecia a cada execução de
    teste e os agentes o mandavam para a lixeira várias vezes na mesma sessão; não é versionável,
    então vira INFO.
11. **Fonte oficial no marketplace, as quatro num plugin só (2026-09-29).** A família saiu do
    harness Hermes e entrou no marketplace como plugin `skill-quality-audit`, com as quatro skills
    em `skills/`. Um plugin só porque o `--family` acha as irmãs como pastas vizinhas: em plugins
    separados, cada uma iria para um diretório de cache diferente e as irmãs virariam SKIP. O
    Hermes lê a cópia do marketplace por `skills.external_dirs`, que o curator não toca; a cópia
    local de mesmo nome precisa sair, porque no Hermes a skill local vence a externa.
12. **E1 sem `metadata` é INFO.** O instalador do marketplace para o Cursor remove o bloco
    `metadata` do frontmatter, e com ele o `related_skills`. A irmã continua ligada pelo corpo e
    pela vizinhança de pastas; um AVISO ali seria falso alarme e reprovaria `--family --strict`.

## Limitações

- `skills-ref` não estava instalado no host de origem: a validação da spec foi feita pelos
  checks A1 a A6, reimplementados a partir do `validator.py` acima. O pacote `skills-ref` do PyPI
  (0.1.1 em 2026-09-23) aponta para o repositório oficial e instala o comando `agentskills`, não
  `skills-ref` (sensor: `entry_points.txt` do pacote instalado; o check G2 procura os dois). O
  homônimo no npm tem outro autor, e `@anthropic/skills-ref` não existe no npm (404 na mesma data).
- Validação cruzada em 2026-09-23: `agentskills validate` (PyPI 0.1.1, instalado num venv
  temporário) deu `rc=0` nas quatro skills da família.
- O frontmatter é lido por parser próprio de subconjunto YAML: construção fora dele vira aviso;
  YAML que PyYAML e strictyaml recusam (ex.: `: ` em valor sem aspas) vira erro.
