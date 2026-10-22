# Retomada — loja Codex

**Estado:** implementação executada em modo nativo, tarefa por tarefa; revisão
independente reservada para novo `/clear`. R01 continua `partial` por falta de
verificação desktop. Nenhum `/goal` foi criado nesta execução.

**Repositório:** `/home/joruge/repos/skills` (`j0ruge/skills`).
**Worktree da implementação:** `/home/joruge/.codex/worktrees/4fa1/skills`.
**Branch:** `feat/codex-marketplace`, base `main` conforme `CLAUDE.md` local.
**Revisão base:** `cff1494c17c21774885e2a58ae6a5eb42cdd95d9`.
**Revisão candidata testada:** `f98c06d34f06ee86cc64c5a1e60419e806e73d8f`.
**Revisão final:** HEAD de `feat/codex-marketplace`; o fechamento após o candidato
altera somente evidências/documentação. Resolver com `git rev-parse HEAD`.
O checkout original em `main` foi preservado; retome pelo worktree acima.

## Ler antes de agir

1. `CLAUDE.md` do worktree: contratos e manutenção Codex.
2. [Especificação](../superpowers/specs/2026-10-22-codex-marketplace-design.md): R01–R12 e desenho aprovado.
3. [Plano PDCA](../superpowers/plans/2026-10-22-codex-marketplace.md): checks de cada incremento e reversão.
4. [Verificação](../codex/verification.md): procedimento, resultados e matriz R01–R12.
5. [Compatibilidade](../codex/compatibility.md): inventário completo, requisitos e seis exclusões.
6. [Smokes de entrada](../codex/smokes.json) e [prova da revisão Git](../codex/distribution-evidence.json).
7. `CONTEXT.md` e `KAIZEN_LOG.md`: decisões persistentes e Check DDD/Kaizen.

As sete perguntas de produto foram respondidas; não repetir a entrevista.
Preservar instalação individual e agrupamentos. Conteúdo canônico fica em
`plugins/`; catálogo Codex e adaptações são gerados e versionados.

## Entrega verificada

- Catálogo Codex oferece exatamente **25 plugins / 28 workflows**, enquanto o
  catálogo Claude mantém os 31 plugins. Instalar um não instala os demais.
- Quatro comandos foram adaptados com nomes preservados e templates relativos
  ao diretório instalado. `commands: []` no manifesto Codex evita duplicatas
  `source-command-*` geradas automaticamente pelo host.
- Todos os publicados passaram por instalação limpa, descoberta e smoke seguro
  de entrada. `release` foi testada com invocação explícita e ausente do contexto
  automático sem invocação. Nenhuma operação de produção dos workflows foi rodada.
- No candidato Git, **289 arquivos** dos 25 pacotes foram conferidos por bytes e
  SHA256. O auditor instalado achou as quatro skills irmãs, sem erros ou skips.
- Fixture nova com template removido reprovou a conferência da cópia instalada.
- Uma origem Git com duas revisões comprovou refresh, versão/conteúdo novos,
  remoção do cache antigo, reinstalação e remoção de plugin/marketplace.
  No CLI testado, `marketplace upgrade` atualiza também os plugins instalados.
- Instalador Codex somente mostra comandos; não exige o binário e não instala
  nem escreve configurações pessoais. Fluxos Claude/Cursor preservados.
- Gate confere derivados e falha se faltar PyYAML. Hook executável exporta o
  índice; correção não staged não esconde pacote inválido. Casos de 2.500 arquivos
  e commit real inválido foram exercitados.

**Checks finais observados em Ubuntu 24.04 / Python 3.12.3 / Codex CLI 0.163.0:**

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
# 44 testes, OK; inclui três provas reais de distribuição, sem modelo/autenticação.
python3 plugins/skill-quality-audit/skills/skill-quality-audit/tests/test_audit_skill_quality.py
# 55 testes, OK.
python3 scripts/codex-adapters.py --check
python3 scripts/codex-marketplace.py --check
python3 scripts/validate-versions.py
git diff --check
```

Dois avisos documentados permanecem: `disable-model-invocation` em release e
`argument-hint` em ticket continuam úteis para Claude/Cursor e não são aceitos
silenciosamente como campos Codex. A política explícita Codex é separada e testada.

## Lacunas e decisões da execução

- Desktop, macOS e Windows: `not_checked`. O procedimento desktop está no
  relatório; a versão mínima do Codex não foi estabelecida. Não declarar R01
  completo nem suporte operacional Windows com base em leituras no Linux.
- `statusline`, `hook-builder` e `retrofit-watch`: `unsupported`, por contratos
  específicos do runtime Claude sem equivalência comprovada nesta missão.
- `codereview`, `dotnet-wpf` e `retrofit-skill`: `partial`, por roteamento
  Agent/sonnet, setup/hook Claude no agrupamento WPF e resolução externa de
  scripts/irmãs respectivamente. Excluídos do catálogo sem fragmentar pacotes.
- As conclusões dos smokes registram observações de domínio sobre exemplos
  Zitadel e referências CORS; ficam para tarefa própria do mantenedor.
- `task-start` da skill procurava títulos “Task N”; os briefs foram extraídos
  manualmente de “Tarefa N”, preservando o plano aprovado. Custo se incorreto:
  rastreabilidade, mitigada pelos briefs/ledger e commits mantidos.
- A revisão final automática da skill de execução foi reservada à segunda
  retomada conforme a instrução explícita do usuário. Custo: revisão independente
  permanece pendente antes de integrar; não houve afirmação de grades A.
- As três classificações `partial` são uma decisão conservadora de publicação.
  Custo se incorretas: esses pacotes ficam indisponíveis até prova de adaptação.

Artefatos brutos permanecem no diretório ignorado do worktree
`.superpowers/sdd/2026-10-22-codex-marketplace/`: `progress.md`, briefs,
`probe.jsonl`, `discovery-*.json`, `*-smoke-final.jsonl`, `workflow-*/smoke.jsonl`,
`workflow-*/result.json`, `release-implicit.jsonl`, `final-tests.log`,
`final-auditor.log`, `final-validation.log` e logs RED/GREEN. Os arquivos de
`docs/codex/` consolidam a evidência versionada sem credenciais.

## Segunda retomada — revisão

Após novo `/clear`, usar o worktree e branch acima. A revisão deve comparar:

```bash
git diff cff1494c17c21774885e2a58ae6a5eb42cdd95d9...feat/codex-marketplace
```

Prompt de retomada:

```text
/goal Use codereview:codereview para revisar a implementação da loja Codex
no worktree /home/joruge/.codex/worktrees/4fa1/skills, branch feat/codex-marketplace.
Parta de docs/handoffs/2026-10-22-codex-marketplace.md. Verifique o diff desde
cff1494, R01–R12 e as evidências; corrija achados e repita os checks necessários
até todos os grades serem A. Não altere a régua para obter A nem declare
concluída uma verificação pendente. Desktop/macOS/Windows não foram testados.
```

Criar o objetivo somente quando o usuário invocar essa etapa. A execução atual
não fez push, merge, publicação ou instalação no perfil pessoal. A configuração
pessoal foi preservada; testes de modelo usaram somente autenticação montada
como leitura, com dados e caches próprios e temporários.
