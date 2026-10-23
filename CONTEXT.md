# Contexto — distribuição de skills no Codex

**Data:** 2026-10-22 · **Estado:** `implemented_with_gaps` · **Integração:** PR #6, resposta ao Claude Code e base reconciliada; R01 parcial.

Este documento registra a pesquisa e a entrevista `grill-with-docs`. As sete
perguntas iniciais de produto foram respondidas e o desenho foi aprovado.
A [especificação](docs/superpowers/specs/2026-10-22-codex-marketplace-design.md),
o [plano PDCA](docs/superpowers/plans/2026-10-22-codex-marketplace.md) e o
[handoff](docs/handoffs/2026-10-22-codex-marketplace.md) formalizam a retomada.
A pesquisa abaixo registra a preparação; o Check da execução está no final deste documento.

## Problema e resultado esperado

Permitir que usuários do Codex instalem individualmente os plugins portáveis da
Chewiesoft, aproveitando as skills e os comandos existentes.

**Critério de sucesso proposto:** em ambiente de teste, registrar a loja, escolher
um plugin, instalar e invocar suas skills com os recursos necessários presentes;
a seleção não deve instalar o restante do catálogo. Comandos portáveis também
devem ter uma forma funcional de invocação. Compatibilidade deve ser comprovada
por plugin e ambiente, preservando os fluxos atuais de Claude Code e Cursor.

## Glossário

| Termo | Significado nesta missão |
|---|---|
| Skill | Pasta com `SKILL.md` e seus recursos, como `references/`, `scripts/` e `assets/`. |
| Comando | Workflow atual em `commands/*.md`; sua distribuição no Codex precisa ser verificada e, quando necessário, adaptada para skill. |
| Plugin | Unidade instalável individual da loja; pode reunir mais de uma skill. |
| Marketplace / loja | Catálogo que apresenta plugins selecionáveis e aponta para suas fontes. |
| Manifesto | Metadados e pontos de entrada de um plugin ou catálogo, conforme o formato do host. |
| Portável | Workflow cujas instruções, recursos e dependências têm execução comprovada no Codex alvo. |
| Compatibilidade de formato | O host aceita o catálogo e o manifesto. Isso, sozinho, não comprova que o workflow funciona. |
| Adaptador de plataforma | Tradução necessária na fronteira com o host; sua forma ainda será definida. |
| Instalação individual | Escolher um plugin sem instalar obrigatoriamente o catálogo inteiro, mantendo os agrupamentos atuais de skills dentro de cada plugin. |

## Contexto combinado — evidências locais

- Repositório canônico: `https://github.com/j0ruge/skills`; marca **Chewiesoft**;
  slug atual **chewiesoft-marketplace**.
- `CLAUDE.md` da raiz define `main` como branch principal, sobrepondo a orientação
  global de usar `develop`. A sessão começou em `main`, commit `426eb55`, com
  working tree limpo. Os artefatos desta fase são documentais; a implementação e
  a publicação ainda não foram iniciadas.
- `.claude-plugin/marketplace.json` lista **31 plugins**; o inventário local
  encontrou **32 diretórios de skills**, **6 plugins somente com comandos** e
  **4 plugins declarados apenas para Claude Code**. São contagens estruturais,
  não uma certificação de portabilidade.
- `install.py` oferece Claude Code, Cursor e Both. A conversão existente atende
  Cursor, incluindo comandos e ajustes de frontmatter e `$ARGUMENTS`.
- `scripts/validate-versions.py` só aceita `claude-code` e `cursor` em
  `VALID_PLATFORMS`; também tem regras de frontmatter por plataforma.
- Baseline executado: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-versions.py`;
  retorno **0**, terminando em `All checks passed.`
- CLI disponível nesta sessão: `codex-cli 0.163.0`. Foram consultados apenas
  `--version` e os helps de `plugin`, `plugin add`, `plugin marketplace` e
  `plugin marketplace add`; nenhuma instalação foi realizada.
- Os helps confirmam `codex plugin marketplace add <SOURCE>` e
  `codex plugin add <PLUGIN@MARKETPLACE>`. A menor versão suportada ainda não foi
  estabelecida, e os comandos da nossa loja ainda não foram testados.
- Já existem `KAIZEN_LOG.md`, validadores e testes em plugins. Antes desta
  pesquisa, não existiam `CONTEXT.md` nem `docs/` na raiz.

## Pesquisa externa — fontes consultadas

### Documentação oficial OpenAI

- [Package your plugin](https://developers.openai.com/plugins/build/plugins):
  documenta catálogos em `.agents/plugins/marketplace.json`, registro pelo CLI e
  aceitação de formatos compatíveis com Claude. Para pacotes novos recomenda
  `plugin.json` na raiz; `.codex-plugin/plugin.json` continua como compatibilidade.
  Isso permite investigar o reaproveitamento antes de duplicar nossa estrutura.
- [Plugins](https://learn.chatgpt.com/docs/plugins): plugins têm suporte no CLI e
  no aplicativo desktop; a extensão de IDE não oferece esse suporte. A loja por
  repositório tem distribuição distinta da publicação no diretório público.
- [Build skills](https://learn.chatgpt.com/docs/build-skills): explica `SKILL.md`,
  invocação com `$` e `/skills`, recursos auxiliares e `agents/openai.yaml` opcional.
  O controle `policy.allow_implicit_invocation` permite restringir a ativação
  implícita. A necessidade de aplicar esse controle será avaliada por workflow.

As URLs antigas `developers.openai.com/codex/skills/` e `/codex/plugins/`
redirecionaram para as páginas de `learn.chatgpt.com` acima. O README passou a
referenciar as fontes consultadas, sem anunciar suporte Codex já entregue.

### Exemplo solicitado: mattpocock/skills

- [README](https://github.com/mattpocock/skills#installation-30-second-setup):
  orienta registrar `mattpocock/skills` e instalar
  `mattpocock-skills@mattpocock` com os comandos nativos do Codex.
- [Catálogo](https://github.com/mattpocock/skills/blob/main/.claude-plugin/marketplace.json):
  contém um único plugin `mattpocock-skills`, apontando para a raiz.
- [Manifesto do plugin](https://github.com/mattpocock/skills/blob/main/.claude-plugin/plugin.json):
  lista explicitamente as skills nas categorias engineering e productivity,
  inclusive `handoff`. A distribuição observada reutiliza o formato Claude.
- [handoff/SKILL.md](https://github.com/mattpocock/skills/blob/main/skills/productivity/handoff/SKILL.md):
  define o workflow de passagem de contexto; não implementa a instalação.

Os arquivos foram lidos na referência `main` em 2026-10-22. O exemplo ajuda a
entender a distribuição, mas seu pacote único não atende à escolha do usuário
de manter instalação individual.

## Fluxo e decisões resolvidas

| ID | Decisão | Origem |
|---|---|---|
| D01 | Primeira versão para **CLI e desktop**, pelo marketplace nativo. | Resposta à pergunta 1. |
| D02 | Instalação **individual por plugin**, sem exigir o catálogo inteiro e mantendo os agrupamentos atuais de skills. | Respostas à pergunta 2 e à pergunta 5 (opção 1). |
| D03 | Incluir **skills e comandos portáveis**, documentando incompatibilidades. | Resposta à pergunta 3. |
| D04 | Fazer pesquisa, entrevista e checklist nesta fase; execução somente depois do `/clear` solicitado pelo usuário. | Missão original. |
| D05 | Após a execução, novo `/clear` e depois `/goal` com `codereview:codereview` até todos os grades A, com evidências. | Missão original; etapa futura. |
| D06 | Acrescentar **Codex** ao menu de `install.py` para **mostrar os comandos nativos**, seguindo o fluxo orientativo já usado para Claude Code. | Resposta à pergunta 4: opção 1. |
| D07 | Oferecer no catálogo Codex apenas plugins compatíveis e validados; explicar as exclusões na matriz do README. | Resposta à pergunta 6: opção 1. |
| D08 | Contemplar todos os ambientes oficialmente suportados pelo Codex, documentando as restrições próprias de cada skill e a validação disponível. A versão mínima será determinada por evidência. | Resposta à pergunta 7: opção 1. |
| D09 | Desenho aprovado: catálogo Codex próprio e filtrado, conteúdo compartilhado, adaptações necessárias, opção orientativa no instalador e validações automáticas. Formalizar especificação, plano e handoff antes do `/clear`. | Resposta “aprovado” à proposta de desenho. |

Sequência combinada: pesquisa → entrevista → desenho e plano revisados → handoff
persistido → `/clear` do usuário → execução → novo `/clear` → objetivo de revisão.
Não criar o objetivo de revisão nem iniciar implementação nesta fase.

## Perguntas abertas — mapa inicial do grill

Perguntar uma por vez, com recomendação. As respostas podem revelar novas
ramificações; atualizar este mapa durante a entrevista.

### Decisões de produto e escopo

As perguntas 1–7 foram respondidas e consolidadas em D01–D08. Não há decisão de
produto pendente identificada nesta rodada. A revisão do desenho pode revelar
novas perguntas, que devem ser registradas antes de alterar o escopo.

### Desenho aprovado e alternativa considerada

1. **Aprovado:** catálogo nativo Codex filtrado, derivado dos metadados
   canônicos e apontando para os plugins portáveis existentes. Acrescentar o
   catálogo em `.agents/plugins/marketplace.json`; manter o conteúdo das skills
   sob `plugins/`. Automatizar a consistência entre a declaração de suporte e
   os plugins oferecidos. Adaptar comandos e contratos de host por plugin quando
   a verificação demonstrar necessidade.
2. **Alternativa:** registrar diretamente o catálogo Claude, como no exemplo do
   Matt. É a menor alteração estrutural, mas só atende D07 se houver uma forma
   comprovada de impedir a oferta dos plugins incompatíveis no Codex. O campo
   `platforms` do nosso repositório não deve ser presumido como filtro nativo.

O catálogo filtrado foi escolhido por permitir uma seleção própria para Codex
sem manter uma segunda versão manual do conteúdo das skills. A implementação
deve provar a precedência dos catálogos, a resolução dos manifestos existentes
e o empacotamento dos comandos antes de expandir a entrega.

O fluxo proposto de `install.py` acrescenta a opção Codex, mostra como registrar
a loja e lista comandos de instalação individual para os plugins publicados.
Os comandos efetivos serão conferidos no CLI e no pacote instalado. A documentação
de instalação, a matriz de compatibilidade e as regras de contribuição serão
atualizadas junto com a entrega.

O plano escrito contém incrementos verificáveis: prova de um
plugin completo → catálogo filtrado e guardas → cobertura dos demais workflows
portáveis → menu e documentação → verificação de instalação, invocação,
atualização e remoção. Cada incremento deve ter seu Check e forma de reversão.
O checklist DDD/Kaizen abaixo permanece aberto nos itens de execução.

### Perguntas técnicas a resolver por evidência

Estas verificações cabem ao agente no plano e na execução, após o `/clear`;
não exigir que o usuário decida detalhes que o repositório ou um teste respondem.

| ID | Verificação | Critério para decidir |
|---|---|---|
| T01 | O catálogo Codex aprovado tem precedência sobre o catálogo Claude e filtra a oferta no host? | Comparar os nomes realmente apresentados pelo Codex com o catálogo derivado, incluindo um caso incompatível apenas no catálogo Claude. |
| T02 | Quais manifestos precisam de adaptação? | Testar o formato existente; introduzir metadados extras só quando necessários. Evitar copiar fontes de skills. |
| T03 | Como distribuir os comandos portáveis? | Provar o carregamento nativo ou gerar skills com nomes, descrição, recursos e argumentos corretos. |
| T04 | Quais conteúdos dependem de ferramentas, agentes, slash commands, hooks ou APIs do Claude? | Auditar os plugins candidatos e registrar `supported`, `partial`, `unsupported` ou `not_checked` com motivo e prova. |
| T05 | Como preservar invocação explícita e evitar duplicatas? | Testar controles de ativação e documentar convivência com instalações avulsas; não presumir equivalência entre campos dos hosts. |
| T06 | Como manter metadados e catálogos consistentes? | Usar fonte canônica identificada e um validador que detecte divergências; geração determinística se houver arquivos derivados. |
| T07 | Como provar a experiência desktop? | Verificar descoberta, seleção e invocação no aplicativo; se não houver acesso, registrar a lacuna e não declarar o teste concluído. |
| T08 | Como funcionam atualização, remoção e reversão? | Consultar os comandos disponíveis e verificar seus efeitos em ambiente de teste, sem alterar instalações pessoais nesta fase. |
| T09 | Qual é a versão mínima suportada do Codex? | Estabelecer pela documentação e por testes dos recursos usados; a versão local observada não comprova uma versão mínima. |

## Validação DDD — checklist

**Parecer:** missão compatível com uma aplicação proporcional de DDD; a aderência
da implementação ainda não pode ser afirmada. O foco é linguagem, invariantes e
fronteiras de integração. Referências:
[strategic-design.md](plugins/ddd/skills/ddd/references/strategic-design.md)
(`[Evans Reference: Ubiquitous Language, Bounded Context]`) e
[heurísticas](plugins/ddd/skills/ddd/references/code-review-heuristics.md).

- [x] Problema e vocabulário distinguem skill, comando, plugin, marketplace e host.
- [x] Instalação individual foi identificada como requisito do usuário.
- [x] Compatibilidade de formato foi separada da execução funcional do workflow.
- [x] Confirmar a granularidade de seleção dos plugins com várias skills: manter os agrupamentos atuais.
- [x] Definir onde vivem os metadados canônicos e as traduções por host: tabela de fontes na especificação aprovada.
- [x] Garantir que selecionar um plugin não instala os demais.
- [x] Provar que recursos necessários ficam acessíveis no pacote instalado.
- [x] Validar nomes e invocações, inclusive chamadas entre workflows relacionados.
- [x] Revisar o diff e seus colaboradores diretos para detectar acoplamento novo.

## Validação Kaizen — checklist PDCA

**Parecer:** a descoberta segue Gemba e menor mudança primeiro. O ciclo PDCA
permanece aberto até desenho, execução, Check e padronização comprovados.
Referência: [kaizen-software](plugins/kaizen-software/skills/kaizen-software/SKILL.md).

- [x] **Plan / Gemba:** ler regras, catálogo, instalador, validador e exemplo real.
- [x] Registrar baseline verificável do validador atual.
- [x] Definir resultado observável e registrar escolhas já respondidas.
- [x] Evitar superprodução: sem pacote completo obrigatório ou segunda árvore de skills por antecipação.
- [x] Acrescentar ao README as fontes oficiais úteis à pesquisa.
- [x] Fechar perguntas, aprovar o desenho e escrever o plano PDCA com Check por incremento.
- [x] Revisar o plano detalhado na retomada antes de implementar.
- [x] **Do:** executar incrementos pequenos e reversíveis após a retomada.
- [x] **Check:** testar falha e sucesso das novas guardas, com fixtures independentes; aplicar TDD às mudanças de comportamento.
- [x] Conferir os arquivos efetivamente instalados e a invocação, além do resultado do instalador.
- [x] Revalidar os fluxos existentes afetados e tornar falhas visíveis antes de avançar.
- [x] **Act:** atualizar documentação e validações oficiais do projeto e registrar a melhoria no `KAIZEN_LOG.md`, sem declarar concluído o que estiver pendente.
- [ ] Após o segundo `/clear`, revisar com `codereview:codereview`, corrigir achados e registrar evidências até todos os critérios atingirem A.

## Retomada depois do `/clear`

Ler `CLAUDE.md` e o [handoff](docs/handoffs/2026-10-22-codex-marketplace.md), que
aponta para a especificação e o plano. Retomar na primeira tarefa incompleta;
preservar as respostas da entrevista e distinguir os resultados medidos dos
testes ainda previstos. A implementação depende da retomada explícita após o
`/clear`, conforme pedido pelo usuário.
Nenhum ADR foi criado: ainda não foi tomada uma decisão de arquitetura difícil
de reverter que justifique esse artefato.


## Check da implementação — 2026-10-22

A retomada explícita executou o plano nativamente, tarefa por tarefa, em worktree
isolado. Fonte base `cff1494`; candidato Git verificado `f98c06d`. O catálogo
publica 25 plugins / 28 workflows após smokes reais em perfis limpos. Três plugins
foram classificados `unsupported` e três `partial`; todos os 31 foram inventariados.
Quatro comandos receberam derivados gerados, sem segunda árvore manual.

A suíte geral passou em 44 testes, a do auditor em 55. O gate, o hook real com
snapshot staged, a conferência dos derivados, instalação individual, 289 hashes,
política explícita e atualização/remoção Git foram medidos. Resultados completos
em `docs/codex/verification.md`, `smokes.json` e `distribution-evidence.json`.

Check DDD proporcional ao diff: identidade e unidade de seleção continuam sendo
plugin; o manifesto canônico concentra versão/autoria/plataformas; adaptações de
host ficam na borda de distribuição. O instalador não importa geradores nem
PyYAML. Não foram introduzidos agregados, transações ou eventos de domínio.
O teste da família instalada confirmou a resolução das quatro skills por diretórios
irmãos, sem instalar outro plugin. Não houve refatoração dos workflows de domínio.

R01 permanece parcial: desktop/macOS/Windows sem teste e versão mínima em aberto.
O procedimento desktop está entregue; a revisão com `/goal` e codereview continua
pendente para a segunda retomada. Nenhum push, merge ou publicação foi feito.


## Retros verificadas após a implementação

O usuário autorizou investigar e executar retrofit apenas onde confirmado.
Controles de despacho de DDD e codereview produziram chamadas nativas válidas;
nenhum patch nessas skills. Isso não substitui prova integral de codereview,
que continua `partial` no catálogo. CORS 1.1.2 corrige navegação de Vary e aviso
sobre método fixo, com RED/GREEN por leitura no cache, auditoria sem regressão,
44 testes gerais e três provas Git repetidas após o commit 13f2cc0. Detalhes em
`docs/codex/retrofits-2026-10-22.md`. Naquela etapa, a revisão com `/goal` permanecia pendente.

## Check da revisão — segunda retomada

O objetivo de revisão foi ativado pelo usuário e retomado do handoff. Diff base
`cff1494`, candidato inicial `bad6ebd`, correções `7df2ea7`. Dois defeitos no
adaptador e duas causas de desvio do gate foram reproduzidos por cinco testes
RED/GREEN. Docstrings de quatro `main()` e dois trechos do README foram corrigidos.
Revisão das correções sem novos achados; grades A segundo a régua da skill,
com R01 ainda parcial e sem inferir cobertura de desktop/macOS/Windows.

49 testes gerais e 55 do auditor passaram; os três cenários de distribuição
exportaram `7df2ea7`, conferindo 25 plugins / 289 arquivos e o ciclo Git real
isolado. Evidência tipada por `sha256`, sem mudar valores ou regras dos scanners.
Resultados e rastreabilidade permanecem em `docs/codex/verification.md`, sem
substituir a matriz R01–R12. Nenhum push, merge ou publicação foi feito.

## Check da resposta ao PR #6

O usuário autorizou abrir o PR contra main e solicitar Claude Code. Os quatro
achados de `467c75c` foram corrigidos em `2511ba8`; main `0d2e56d` entrou na branch
por merge `cb7f95c`, preservando as mudanças recentes e o suporte Codex. CICD 2.39.1
e deploy 3.3.3 conciliam as versões. A autorização incluiu commit e envio ao PR.

Passaram 53 testes gerais, 55 do auditor e 15 do scanner. A distribuição real do
commit integrado repetiu os três cenários com 25 pacotes / 289 arquivos, sem
skips. Codereview 2.27.0 / coderabbit-pr 4.6.0 incorporou as duas lições verificadas,
com 14 controles e auditoria sem erros/avisos; permanece excluído do catálogo Codex.
Resultados e limites continuam em `docs/codex/verification.md`. A revisão original
cobre `467c75c`; os checks posteriores não substituem revisão independente do head
novo. Desktop/macOS/Windows e versão mínima continuam sem comprovação.

## Check da segunda revisão externa do PR #6

O Claude Code terminou a rodada sobre `92ea30e`, com cinco achados no comentário
6355341570. Correções e distinção entre gate local e auditor externo estão em
`docs/codex/verification.md`. 61 testes gerais, 55 do auditor e 15 do scanner
passaram; a auditoria externa de release/ticket reprova os campos de host com
retorno 1, limite agora documentado sem relaxar a regra. A cobertura do Claude
continua no SHA revisado, sem inferir aprovação das correções posteriores.
