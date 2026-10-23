# Retomada — loja Codex

**Estado atual:** resposta ao Claude Code aplicada em `2511ba8`; main `0d2e56d`
integrada na branch em `cb7f95c`, com nova prova dos 25 pacotes / 289 arquivos.
PR #6 permanece a via de integração. R01 continua `partial` por falta de teste
desktop. Resultados e limites em [verification.md](../codex/verification.md).
Os registros abaixo preservam o histórico das etapas anteriores.

**Repositório:** `/home/joruge/repos/skills` (`j0ruge/skills`).
**Worktree da implementação:** `/home/joruge/.codex/worktrees/4fa1/skills`.
**Branch:** `feat/codex-marketplace`, base `main` conforme `CLAUDE.md` local.
**Revisão base:** `cff1494c17c21774885e2a58ae6a5eb42cdd95d9`.
**Revisão candidata inicial:** `f98c06d34f06ee86cc64c5a1e60419e806e73d8f`.
**Candidato após retrofit autorizado:** `13f2cc023a7c828b09bd51c46f0c694f6fbd2146`,
com CORS 1.1.2 e nova prova de distribuição Git.
**Correções da revisão externa e retrofit 2.27.0:** `2511ba8`.
**Candidato integrado e testado:** `cb7f95c`, com os dois pais de merge preservados.
**Revisão final:** HEAD de `feat/codex-marketplace`; após `cb7f95c`, o fechamento
altera somente documentação/evidências. Resolver com `git rev-parse HEAD`.
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

No gate local, `disable-model-invocation` em release e `argument-hint` em ticket
geram avisos. O auditor externo estrito pode reprovar os mesmos campos com
`G2 ERRO` e retorno 1; não são aceitos pela interseção Codex. A política explícita
Codex é separada e testada. A segunda revisão detalha essa distinção.

## Lacunas e decisões da execução

- Desktop, macOS e Windows: `not_checked`. O procedimento desktop está no
  relatório; a versão mínima do Codex não foi estabelecida. Não declarar R01
  completo nem suporte operacional Windows com base em leituras no Linux.
- `statusline` e `hook-builder`: `unsupported`, por contratos específicos do
  runtime Claude sem equivalência comprovada nesta missão. `retrofit-watch` foi
  corrigido para `partial` em 2026-10-23: a adaptação Codex local funciona, mas
  ainda não integra o pacote distribuído por esta loja; ver a matriz atual.
- `codereview`, `dotnet-wpf` e `retrofit-skill`: `partial`, por roteamento
  Agent/sonnet, setup/hook Claude no agrupamento WPF e resolução externa de
  scripts/irmãs respectivamente. Excluídos do catálogo sem fragmentar pacotes.
- As duas referências inconsistentes de CORS foram corrigidas no retrofit
  autorizado 1.1.2. Exemplos Zitadel e outras observações de conteúdo continuam
  fora dessa correção; detalhes em `docs/codex/retrofits-2026-10-22.md`.
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

## Retrofits autorizados após o fechamento inicial

O usuário autorizou verificar os achados e aplicar apenas os confirmados.
DDD e codereview produziram planos nativos válidos nos controles; não sofreram
alterações. Os testes não executaram delegação ou revisão, portanto a classificação
completa de codereview não foi promovida. Ticket não recebeu retrofit.

CORS recebeu a versão 1.1.2: referência de Vary corrigida para seguranca.md §4 e
aviso de método fixo alinhado à sonda com $METODO. Auditoria SQA antes/depois sem
regressões, descrição preservada e versões sincronizadas. Os 44 testes gerais
passaram; depois do commit 13f2cc0, três provas reais de distribuição confirmaram
CORS 1.1.2 e os mesmos 25 pacotes / 289 arquivos.

Ver [registro desta etapa](../codex/retrofits-2026-10-22.md). A revisão com `/goal`
continua reservada ao novo `/clear`; o diff desde cff1494 inclui esse retrofit.

## Segunda retomada — revisão (roteiro executado)

Após o novo `/clear`, a revisão usou o worktree e branch acima, comparando:

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

O objetivo foi ativado pelo usuário na segunda retomada. Nenhuma etapa fez
push, merge, publicação ou instalação no perfil pessoal. A configuração
pessoal foi preservada; testes de modelo usaram somente autenticação montada
como leitura, com dados e caches próprios e temporários.

### Resultado da revisão

- Base `cff1494`; candidato inicial revisado `bad6ebd`; correções `7df2ea7`.
  O fechamento `af278f1` contém apenas documentação/evidências. Depois dele,
  codereview recebeu o retrofit 2.26.10, descrito abaixo.
- Dois defeitos no adaptador e duas causas de desvio do gate foram reproduzidos
  e corrigidos. Cinco regressões novas ficaram RED antes e GREEN depois.
- Quatro `main()` receberam docstrings; dois trechos desatualizados do README
  foram corrigidos. A revisão das correções não encontrou novos achados.
- 49 testes gerais e 55 do auditor passaram; os três cenários reais exportaram
  `7df2ea7`, conferindo os mesmos 25 pacotes / 289 arquivos, CORS 1.1.2 e o ciclo
  Git. Evidência estruturada renovada em `docs/codex/distribution-evidence.json`.
- Hashes da evidência passaram a objetos `sha256`, com todos os valores
  conferidos e preservados; regex/gitleaks sem findings nem alteração de regras.
- A revisão teve grades A. Isso não conclui R01 nem estabelece cobertura de
  desktop/macOS/Windows ou versão mínima. Integração/publicação continuam fora
  desta autorização. Uma nova retomada não deve repetir a revisão encerrada;
  deve partir desses limites e do escopo que o usuário solicitar.

### Retrofit autorizado após a revisão

Codereview 2.26.10 incorpora em §6.10 a alternativa de hash tipado antes da
allowlist, com prova dos bytes e canário no mesmo manifesto. Três casos novos e
os 15 testes do scanner passaram; auditoria antes/depois sem erros ou avisos.
O pacote continua excluído do catálogo Codex; os 25 pacotes / 289 arquivos da
prova em `7df2ea7` não mudaram. Detalhes, limites e comandos em
[retrofits-2026-10-22.md](../codex/retrofits-2026-10-22.md#retrofit-posterior-à-revisão--codereview-22610).
O incremento permanece local, sem publicação da missão ou atualização pessoal.

### PR #6 e resposta ao Claude Code

O usuário autorizou abrir o [PR #6](https://github.com/j0ruge/skills/pull/6) contra
main e solicitar revisão do Claude Code. A branch foi enviada em `467c75c`.
Claude Code publicou quatro achados, corrigidos em `2511ba8`: ordem de
plataformas, rename fora do pacote, fallbacks mortos de PyYAML e duplicação dos
helpers. A suíte local passou em 53 testes; ver o relatório de verificação.

A main avançou para `0d2e56d` durante a revisão. Os conflitos em
`.claude-plugin/marketplace.json`, `README.md`, `plugins/cicd/.claude-plugin/plugin.json`,
`plugins/cicd/CHANGELOG.md` e `plugins/deploy/CHANGELOG.md` foram resolvidos conforme
o preview aprovado. O usuário autorizou aplicação, integração da base, commit e
envio ao PR. `cb7f95c` preserva as duas linhas de trabalho, com CICD 2.39.1 e
deploy 3.3.3. A suíte integrada passou em 53 testes gerais, 55 do auditor e 15 do
scanner; os três cenários reais exportaram esse commit, sem skips.

O retrofit codereview 2.27.0 / coderabbit-pr 4.6.0 foi aplicado junto da resposta.
Quatorze controles, leitura fria e auditoria sem erros/avisos sustentam as duas
lições: origem de revisão separada do login e enumeração de renames do gate.
Os 25 pacotes continuam sendo o conjunto publicado; codereview permanece excluído.
A revisão original de Claude Code e CodeRabbit cobre `467c75c`, não os commits de
resposta. As evidências novas comprovam os checks do candidato integrado. R01,
desktop/macOS/Windows e versão mínima permanecem com os limites já registrados.

## Segunda resposta ao Claude Code

Comentário 6355341570, sobre `92ea30e`: normalização de erros de entrada nos
adaptadores; entrada textual explícita em DDD 0.5.2/PDF generation 1.6.4/release
2.0.3; transporte JSONL sem dependência de buffer de texto; contrato do instalador
reutilizado do gerador. O auditor mantém sua regra de interseção. Foi corrigida a
documentação: release/ticket têm aviso local, mas `G2 ERRO` e retorno 1 externo,
confirmados com `uvx skills-ref==0.1.1`. Checks e limites em
`docs/codex/verification.md`; 61 testes gerais, 55 do auditor e 15 do scanner.
