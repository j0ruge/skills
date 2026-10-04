# Checks do audit_skill_quality.py

Cada achado sai como `[NÍVEL] ID mensagem`. Níveis: `ERRO` reprova (`rc=1`); `AVISO` reprova só
com `--strict`; `INFO` é sinal para julgamento; `SKIP` é gate que não rodou; `OK` é gate externo
que passou. Sensor de todos: o próprio script (`--format json` para comparar antes/depois).

## A. Especificação e acionamento

| ID | Nível | Prova | Não prova | Fonte da regra |
|---|---|---|---|---|
| A1 | ERRO/AVISO | ERRO: `SKILL.md` ausente, sem frontmatter aberto e fechado, fora de UTF-8, ou com valor sem aspas contendo `: ` (PyYAML e strictyaml recusam); AVISO: YAML fora do subconjunto lido (âncora, alias, tag, TAB, chave duplicada). Lista de mappings (`- path: x` / `description: y`) é lida desde a v0.3.0 | que o YAML é válido para todo parser | spec Agent Skills |
| A2 | ERRO | `name` com a-z, 0-9 e hífen simples, até 64 chars, igual ao diretório | que o nome descreve bem a skill | spec + `skills-ref` |
| A3 | ERRO/INFO | `description` não vazia e até 1024 chars; INFO quando passa do orçamento do índice (`--desc-budget`, padrão 60) e mostra o trecho visível | que o gatilho dispara nos casos certos (isso é a matriz de avaliação) | spec; orçamento: Hermes `SKILL_PROMPT_DESC_LIMIT` |
| A4 | AVISO/INFO | AVISO: campos de topo fora de `name, description, license, compatibility, metadata, allowed-tools`; INFO: os que o Hermes só lê no topo (`platforms`, `required_credential_files`, `required_environment_variables`, `prerequisites`) | que o harness local não use o campo | `skills-ref` (`ALLOWED_FIELDS`); lista INFO: código do Hermes (`skill_utils.py`, `skills_tool.py`, `skills_tool_setup.py`) |
| A5 | ERRO | coleção em flow style (`[a, b]`, `{a: b}`) no frontmatter: o `skills-ref` não consegue ler o arquivo | nada sobre o parser do Hermes, que aceita as duas formas | strictyaml, usado pelo `skills-ref` |
| A6 | ERRO | `compatibility` com 1 a 500 chars, se presente | que o ambiente declarado existe | spec |
| A7 | INFO | lista `metadata.hermes.related_skills` e aponta as que não existem neste harness | que o vínculo faz sentido | convenção Hermes |
| A8 | ERRO/AVISO/INFO | ERRO: `metadata` que não é mapa; AVISO: valor de `metadata` que não é texto (lista, mapa) fora de `hermes`; INFO: `metadata.hermes` aninhado | que o harness leia a chave | spec (`metadata` é mapa texto→texto, PR #479 de 2026-08-04); `hermes` é convenção local aceita |

## B. Autocontenção e portabilidade

| ID | Nível | Prova | Não prova | Fonte da regra |
|---|---|---|---|---|
| B1 | ERRO/AVISO | `references/` e `assets/` citados no `SKILL.md` existem, inclusive em subpasta; órfão é AVISO; citado com pasta inexistente é AVISO (pode ser exemplo didático); reference fora de UTF-8 é ERRO | que a reference certa é lida no momento certo | gate local do autor (`audit-skill.sh`, mesma âncora) + spec |
| B2 | AVISO | `scripts/` citados no `SKILL.md` ou em references existem; órfão é AVISO. Citação com placeholder da raiz (`<dir>/`, `{{dir}}/`, `{SKILL_DIR}/`, `${CLAUDE_SKILL_DIR}/`, `$SKILL_DIR/`: variável com SKILL no nome) conta; `$HERMES_HOME/scripts/` é o harness e não conta | que o script faz o que a skill diz | gate local do autor (`audit-skill.sh`) |
| B3 | ERRO/AVISO | ERRO: path no `SKILL.md` ou numa reference com mais `../` seguidos do que a profundidade do arquivo (sai da skill); AVISO: o mesmo em `scripts/`, onde a base pode ser o diretório corrente | ausência de dependência implícita | spec (paths relativos à raiz da skill) |
| B4 | AVISO/INFO | AVISO: path de máquina (`/home/<user>/`, `/Users/<user>/`, `C:\Users\<user>`) no `SKILL.md`, references e `scripts/` (`tests/` fica fora: fixtures usam paths de exemplo); INFO: conta menções a `~/.hermes` e `$HERMES_HOME` | que a menção é infra compartilhada legítima (julgar) | convenção do autor (autocontenção) |
| B5 | ERRO/INFO/OK | `CHANGELOG.md` presente na skill, ou no plugin quando ela mora num (`<plugin>/CHANGELOG.md` ao lado de `<plugin>/.claude-plugin/plugin.json`, OK que diz o caminho); `--no-changelog-required` rebaixa a ausência para INFO | que a entrada mais recente cobre a mudança | convenção do autor e deste marketplace |
| B6 | AVISO/INFO | AVISO: `__pycache__`, `.pyc`, `.DS_Store` que o git não ignora; INFO: os mesmos quando `git check-ignore` os ignora (não chegam ao repositório) | nada além disso | gate local do autor (`audit-skill.sh`) |
| B7 | ERRO/AVISO | `.py` compila e `.sh` passa em `bash -n` (em `scripts/` e `tests/`); script sem shebang é AVISO, exceto módulo Python importado (sem `__main__`, sem argparse e sem bit de execução) | que o script roda nem que trata entrada inválida (fase 5) | regra 6 de `skill-claim-check` |

## C. Progressive disclosure

| ID | Nível | Prova | Não prova | Fonte da regra |
|---|---|---|---|---|
| C1 | ERRO/AVISO/INFO | ERRO acima de 500 linhas; INFO acima de 400; AVISO acima de 20.000 chars | que o corpo é só workflow default | spec (500); 400 e 20.000: heurística de `skill-refactoring` |
| C2 | AVISO | reference que cita outra reference (cadeia com mais de 1 nível) | que a divisão entre arquivos é boa | spec ("one level deep") |
| C3 | AVISO | reference com mais de 300 linhas tem sumário nas primeiras 40 | que o sumário está certo | `skill-creator` |

## F. Boas práticas de autoria (agentskills.io)

Sinais para julgamento: nenhum reprova sem `--strict`. Fonte: páginas *best-practices*,
*using-scripts* e *evaluating-skills* do agentskills.io.

| ID | Nível | Prova | Não prova | Fonte da regra |
|---|---|---|---|---|
| F1 | INFO | linha do `SKILL.md` que cita um arquivo de references sem palavra de condição (quando, se, antes, ao, para, when, if…) na linha nem na anterior | que a condição escrita é a certa | best practices: "diga quando ler cada arquivo" |
| F2 | INFO | não há título de seção com gotchas, armadilhas, pitfalls, erros comuns, cuidados ou antipadrões | que a seção existente tem as armadilhas reais | best practices: gotchas são o conteúdo de maior valor |
| F3 | AVISO/INFO | AVISO: script em `scripts/` chama `input()`/`getpass()` (pela AST, string não conta) ou `read -p` fora de comentário; INFO: script sem sinal de `--help`/usage (argparse, click, typer, `--help`, `usage`) | que o `--help` funciona (fase 5 roda o script) | using-scripts: sem prompt interativo; `--help` é a interface do agente |
| F4 | INFO | nem `evals/evals.json` nem `assets/*eval*.json` | que os casos cobrem o gatilho certo | evaluating-skills e optimizing-descriptions |

## D e E. Claims e família

| ID | Nível | Prova | Não prova | Fonte da regra |
|---|---|---|---|---|
| D1 | INFO | quantos trechos têm cara de afirmação factual (número com unidade, path absoluto, versão, "sempre/nunca"), fora de blocos cercados por ``` ou ~~~; `--claims` lista | que cada um tem sensor: isso é julgamento da fase 2 | padrões vendorizados de `skill-claim-check` |
| E0 | SKIP | membro da família não encontrado (em `--family`) | nada: skill ausente não é defeito | esta skill |
| E1 | AVISO/INFO | vínculo recíproco: a porta de entrada lista as irmãs presentes e cada irmã lista a porta; INFO quando a skill não tem bloco `metadata` (o instalador do Cursor o remove) | ausência de loop de processo (regra escrita no `SKILL.md`) | esta skill |

## G. Gates externos (só com `--external auto`)

| ID | Nível | Prova | Não prova |
|---|---|---|---|
| G1 | OK/ERRO/AVISO/SKIP | gate local `$HERMES_HOME/scripts/audit-skill.sh <cat>/<skill>` (script do autor, não vem com o Hermes Agent) com `rc=0`; SKIP se o gate não existe ou a skill está fora de `$HERMES_HOME/skills`; AVISO se não termina em 120s | o que o gate não verifica (frontmatter, references de references) |
| G2 | OK/ERRO/AVISO/SKIP | `skills-ref validate <dir>` com `rc=0` (comando `skills-ref` do repositório ou `agentskills` do pacote PyPI; sem eles, `uvx --from skills-ref==0.1.1 agentskills`, desligável com `--no-uvx` ou `SQA_NO_UVX`); SKIP se nada disso existe; AVISO se não termina em 120s | nada além do frontmatter |

## Limites conhecidos

- O frontmatter é lido por um parser próprio de subconjunto YAML (sem dependência externa).
  Construção fora do subconjunto vira AVISO A1, não palpite silencioso.
- A contagem de linhas usa `splitlines()`. O `audit-skill.sh` soma 1 (`count("\n") + 1`), por
  isso os dois podem diferir em uma linha.
- Gate externo repete defeito que um check local já achou (ex.: CHANGELOG ausente sai em B5 e
  em G1). São sensores independentes: o `rc` não muda, só a contagem de erros.
- O script não roda código da skill auditada. Execução real (`--help`, caso válido, caso
  inválido) é da fase 5, feita pelo agente, em modo seguro.
