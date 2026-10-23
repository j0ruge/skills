# Verificação da loja Codex

Base de implementação: `cff1494c17c21774885e2a58ae6a5eb42cdd95d9`.
Ambiente observado em 2026-10-22: Ubuntu 24.04 x86_64, Python 3,
`codex-cli 0.163.0`, Python 3.12.3. Essa versão do CLI é a testada, não uma versão mínima comprovada.
Desktop, macOS e Windows: `not_checked`.

## Tarefa 1 — contrato medido

O baseline `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-versions.py`
retornou 0. Os helps de marketplace add, plugin add e plugin list foram lidos.
Foi usado um namespace de montagem Bubblewrap: raiz somente leitura, diretório
pessoal e cache temporários, ambiente limpo e cópias independentes dos plugins.
Nenhuma configuração pessoal foi escrita. Para smokes com modelo, somente o
arquivo de autenticação foi montado como leitura; nenhum segredo foi copiado
para os artefatos. O binário e seu `codex-code-mode-host` foram montados juntos.
O sandbox interno não permite namespaces aninhados neste host: os smokes usam
o isolamento externo, raiz somente leitura e instruções limitadas à leitura.

Cada cenário tem os três plugins no catálogo Claude e apenas o plugin sob teste
no catálogo `.agents/plugins/marketplace.json`. Comandos executados:

```bash
codex plugin marketplace add /tmp/work --json
codex plugin list --marketplace chewiesoft-marketplace --available --json
codex plugin add cors@chewiesoft-marketplace --json
codex plugin list --marketplace chewiesoft-marketplace --json
```

O seletor foi trocado para `codereview` e `criar-prd` em perfis novos.
Em cada cenário, `available[].name` continha exatamente o plugin da fixture;
após instalar, `installed[].name` continha somente ele, habilitado. A precedência
do catálogo Codex sobre o Claude foi comprovada. Campos medidos: `source.source`
igual a `local`, `source.path` relativo à raiz, `policy.installation=AVAILABLE`,
`policy.authentication=ON_INSTALL` e `category`. A versão vem do manifesto do
plugin, não precisa ser inventada como campo do catálogo.

| Pacote | Descoberta pelo `skills/list` em processo novo | Recursos instalados |
|---|---|---|
| cors 1.1.0 | `cors:cors` | 8 arquivos legíveis, incluindo referências |
| codereview 2.26.9 | `codereview:codereview`, `codereview:coderabbit-pr` | 22 arquivos legíveis |
| criar-prd 0.1.0 | `criar-prd:source-command-criar-prd` | 5 arquivos legíveis, incluindo template |

Os manifestos `.claude-plugin/plugin.json` são aceitos diretamente para skills.
O CLI migra comandos para `.codex-plugin/migrated-command-skills/`, acrescentando
`source-command-` ao nome e mantendo `${CLAUDE_PLUGIN_ROOT}` no corpo. O template
está instalado, mas o contrato do fallback não foi traduzido. Portanto os
comandos precisam de adaptação gerada para preservar nome e resolução de assets.
Não será duplicada manualmente a árvore de skills.

O template PRD instalado teve SHA256
`3c423739850e5b376edde9341c9a3a347ea21ef3ca1fd7746bb151459d6c8e6e`.
Smokes leem a skill e referência pelo cache instalado e pedem interpretação da
entrada e próximo passo, sem executar revisão, deploy, rede de domínio ou escrita.
Saída 0 do processo não basta: leituras com erro do sandbox foram identificadas e
repetidas após ajustar o cliente de teste.

Evidências brutas de desenvolvimento ficam no workspace ignorado
`.superpowers/sdd/2026-10-22-codex-marketplace/`: `probe.jsonl`,
`discovery-*.json`, `*-smoke-final.jsonl`. Os resultados finais e os comandos
reproduzíveis são consolidados neste relatório antes do handoff.

Resultados dos smokes: `cors:cors` leu `references/diagnostico.md` e pediu a
mensagem literal do Console. `codereview:codereview` leu `configuration.md` e
identificou o ajuste para Python; `coderabbit-pr` leu `pr-branch.md` e pediu o
número do PR ausente. `criar-prd` confirmou o template legível e apontou a
lacuna de variável e nome. Essa falha é a evidência para a tarefa 3.

## Tarefa 2 — guardas

O gerador tem modos `--check` (padrão) e `--write`, raiz configurável e escrita
atômica. Fixtures independentes provaram erro para catálogo ausente/inválido,
inclusão indevida, caminhos fora do pacote, symlinks externos, identidade/plataforma
divergentes e manifestos ausentes. Conferência não escreve. A versão é lida
diretamente do manifesto; alterações incoerentes são recusadas.
O hook exporta o índice Git para diretório temporário antes de validar: uma
correção não staged não esconde a entrada inválida do índice. O caso com 2.500
arquivos também passou após remover a saída antecipada que provocava SIGPIPE.
PyYAML ausente agora reprova o gate, em vez de pular verificações obrigatórias.

## Tarefa 3 — pacote e entrada dos workflows

25 plugins e 28 workflows passaram nos smokes de leitura, cada plugin em perfil
limpo: conjunto disponível exato, instalação individual, `skills/list`, hashes
dos arquivos instalados e leitura pelo agente da skill e de seu recurso indicado.
[smokes.json](smokes.json) registra versão do conteúdo testado, caminhos, comandos
de leitura e conclusão. Depois disso, os manifestos receberam o patch de
distribuição e `codex`; a cópia Git final é conferida separadamente na tarefa 5.

Quatro comandos precisaram de `codex-adapter.json`. A prova com somente `skills`
no manifesto Codex ainda mostrava uma duplicata `source-command-*`; acrescentar
`commands: []` deixou exatamente `criar-prd:criar-prd`. Essa forma medida foi
usada nos quatro adaptadores. Scripts de geração copiam assets, traduzem o
fallback e preservam a preferência pelo template do projeto. Testes cobrem
argumentos, template ausente, chamada declarada entre skills, múltiplos comandos,
versão/conteúdo desatualizados e política explícita, inclusive a herdada da fonte.

`release:release` carregou quando nomeada explicitamente; em processo novo,
sem invocação, o agente respondeu `[]` à lista de skills de plugin expostas
automaticamente, sem ferramentas. A guarda também reprova remover sua política
`allow_implicit_invocation: false`. O campo Claude permanece útil nas outras
plataformas. `ticket` mantém `argument-hint` para Claude, ignorado pelo Codex;
os dois campos geram aviso no gate local. Com o validador externo disponível,
o auditor classifica a reprovação estrita como `G2 ERRO` e retorna 1. Esse limite
não é aprovação externa nem herança de campos Codex; ver a segunda revisão abaixo.

As exclusões e dependências dos 31 plugins estão em [compatibility.md](compatibility.md).
Observações sobre exemplos de Zitadel e referências antigas de CORS apareceram
nos smokes e estão preservadas nas conclusões históricas. Depois do fechamento
inicial, o usuário autorizou investigar a retro: as duas referências inconsistentes
de CORS foram corrigidas em 1.1.2. O [registro do retrofit](retrofits-2026-10-22.md)
contém a nova prova do pacote; demais observações não foram objeto de correção
nem de uma revisão integral.

## Tarefa 5 — distribuição da revisão Git

Os testes em [test_codex_distribution.py](../../tests/test_codex_distribution.py)
exportam `git archive HEAD`, sem aproveitar arquivos ignorados ou cache pessoal.
Três cenários independentes usam um diretório pessoal temporário em Bubblewrap.
Nenhum precisa de autenticação ou modelo. Se CLI/Bubblewrap não estiverem
disponíveis, os testes registram `skip`; isso representa uma lacuna de cobertura.

```bash
python3 -m unittest discover -s tests -p 'test_codex_distribution.py' -v
```

Resultados estruturados: [distribution-evidence.json](distribution-evidence.json).
A revisão efetivamente exportada está em `revision` de cada cenário. A fixture
ofereceu exatamente 25 plugins, apesar dos 31 presentes no catálogo Claude.
Instalar primeiro `skill-quality-audit` instalou somente esse plugin; o cliente
descobriu as quatro skills qualificadas. Todos os plugins publicados foram
instalados, e 289 arquivos foram comparados por bytes e SHA256 com o candidato.
O auditor instalado também encontrou as quatro irmãs sem carregar outro plugin.

Uma fixture nova removeu `criar-prd/codex-skills/criar-prd/assets/prd-template.md`
antes da instalação. O host aceitou instalar, mas a comparação do pacote instalado
reprovou pelo arquivo ausente. Assim, saída 0 da instalação não substitui o Check.

A atualização foi medida com duas revisões de uma origem **Git**, não de uma
origem local. O CLI registrou `https://example.invalid/codex-marketplace.git`;
um `url.*.insteadOf` no perfil temporário redirecionou somente o transporte para
o repositório local da fixture. Houve clone/snapshot/fetch Git reais, sem publicar
ou acessar repositório remoto. `--ref main` acompanhou a segunda revisão.

Na prova inicial (`f98c06d`), o cenário iniciou `cors` em 1.1.1, depois mudou versão para 99.0.0 e acrescentou
um marcador ao SKILL.md na origem de teste. Após
`codex plugin marketplace upgrade chewiesoft-marketplace --json`, o cliente
listou 99.0.0 instalada, o marcador foi lido no cache novo e o cache 1.1.1 deixou
de existir. `plugin add` repetido também retornou 99.0.0. Portanto, neste CLI,
o refresh atualiza também a cópia instalada; remover/reinstalar não foi necessário.
Na repetição da revisão `7df2ea7`, a versão inicial foi 1.1.2, com os mesmos
efeitos de atualização e remoção comprovados. O teste inicial que supunha cache antigo preservado falhou e foi substituído pela
conferência dos artefatos observados. Não extrapolar isso para versões não testadas.

`plugin remove` removeu registro e cache. Depois de remover o plugin,
`marketplace remove` removeu a origem e a lista de marketplaces ficou vazia.
As remoções afetaram somente perfis temporários. Nenhum push, merge, instalação
pessoal ou publicação remota foi feito por esta execução.

## Rastreabilidade R01–R12

| Critério | Resultado | Evidência e limite |
|---|---|---|
| R01 | `partial` | CLI comprovado; desktop `not_checked`, com procedimento abaixo. |
| R02 | `passed` | Instalação individual da família de quatro skills e ausência dos demais plugins antes da sequência de instalações. |
| R03 | `passed` para o conjunto publicado | Inventário dos 31 candidatos; 25 plugins / 28 entradas com smokes reais; seis excluídos. Regras integrais de domínio fora do smoke. |
| R04 | `passed` | Nomes observados no CLI correspondem exatamente às 25 entradas Codex; os 31 plugins Claude não vazam para essa oferta. |
| R05 | `passed` | Geradores determinísticos; testes de fontes/versões/recursos alterados e artefatos desatualizados; bytes do candidato instalados. |
| R06 | `passed` | Oito testes do instalador: somente comandos, nenhum processo/escrita, erros explícitos e execução sem PyYAML/binário Codex. |
| R07 | `passed` nas superfícies afetadas | Validador existente, frontmatter Cursor e seleção dos fluxos Claude/Cursor passaram. Não houve instalação em perfis pessoais. |
| R08 | `passed` | README e matriz registram requisitos por pacote, seis exclusões, versões observadas e lacunas de sistemas/versão mínima. |
| R09 | `passed` | 289 arquivos comparados no cache; família instalada auditada sem erro; fixture independente com template ausente reprovou. |
| R10 | `passed` para o conjunto publicado | Nomes qualificados observados; quatro irmãs resolvidas pelo auditor instalado; argumentos/templates adaptados; release explícita e fora do contexto automático. |
| R11 | `passed` no CLI testado | Origem Git real com transporte local, duas revisões, conteúdo e versão novos no cache, reinstalação e remoções observadas. |
| R12 | `passed` | Preparação preservada em cff1494; execução e revisão ocorreram nas retomadas explicitamente solicitadas pelo usuário. |

Checks históricos do candidato `f98c06d34f06ee86cc64c5a1e60419e806e73d8f`:
44 testes gerais e 55 do auditor passaram; catálogo e adaptadores em `--check`,
validador principal e `git diff --check` passaram. Dois avisos de campos de
frontmatter preservados para outros hosts estão documentados, sem ignorar a
política explícita Codex. O fechamento daquela execução alterou documentação;
o retrofit posterior de CORS e a revisão abaixo têm evidências próprias.

## Segunda retomada — revisão e correções

Revisão completa de `cff1494` até `bad6ebd`, incluindo o retrofit CORS 1.1.2;
correções verificadas em `7df2ea752184401c820b5fe7e82d952daf3533e1`.
O fechamento `af278f1` altera somente documentação/evidências. Foram analisados
os seis arquivos de código alterados, seus testes, metadados, documentos e a
coerência entre geradores, instalador, auditor, hook e pacote instalado.

Foi usada `codereview:codereview` v2.26.8 do plugin local, idêntica ao SKILL.md
instalado no plugin 2.26.9. A cópia avulsa carregada inicialmente era v2.14.1;
as instruções atuais foram relidas integralmente. As fases B/B2 usaram ferramentas
nativas e `gpt-6.1-sol` com esforço `medium`, pois Sonnet não está disponível
neste runtime. Isso não altera a exclusão conservadora do plugin codereview.

| Achado confirmado | Correção e prova |
|---|---|
| MEDIUM: `assets/demo.md` e `assets/./demo.md` sobrescreviam o mesmo destino. | Deduplicação por `Path`; teste recusa a colisão antes de escrever qualquer derivado. |
| MEDIUM: overlay omitia skills padrão se `skills` não existisse no manifesto. | Mesmo default `./skills` do catálogo; teste confere ambas as árvores no overlay. |
| MEDIUM: erro no detector ou em Git fazia o hook pular o gate com sucesso. | Seleção Bash sem dependência de rg; erro de `git diff` fora da condição interrompe o hook. Dois testes reproduzem os erros. |
| MEDIUM: nomes com quoting de Git escapavam do filtro do hook. | Lista delimitada por NUL; teste com `ação.md` e `core.quotePath=true` exige execução do validador. |
| HIGH: quatro `main()` tocados sem documentação pública. | Docstrings em português acrescentadas; sonda AST confirma 12/12 símbolos públicos e 2/2 privados de produção documentados no diff. |
| LOW: dois trechos do README descreviam menu e estado anteriores. | Enumeração das quatro opções e estado de implementação corrigidos. |

Os cinco testes comportamentais novos falharam no código anterior pelos motivos
esperados e passaram após as correções. A revisão independente do diff das
correções não encontrou novos defeitos. O sweep de referências não encontrou
código morto introduzido ou abandonado pela missão; usou busca textual, sem
ferramenta dedicada. Código morto preexistente ficou fora do sweep solicitado.

A primeira varredura sinalizou três hashes como `generic-api-key`: os nomes
dos arquivos continham `api`/`token`. Todos os 289 valores foram conferidos por
SHA256 contra os bytes de `git show` da revisão registrada antes da conversão
para objetos `{ "sha256": "..." }`. O produtor da evidência usa o mesmo formato.
Não eram credenciais. Nenhum valor, regra de scanner ou whitelist foi alterado
para descartar os alertas. A nova varredura do diff completo, com regex e gitleaks,
retornou zero findings e zero erros.

Checks da revisão de código `7df2ea7`:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
# 49 testes, OK, sem skips; os três cenários reais exportam esse commit.
python3 plugins/skill-quality-audit/skills/skill-quality-audit/tests/test_audit_skill_quality.py
# 55 testes, OK; código do auditor preservado nesta revisão.
python3 scripts/codex-adapters.py --check
python3 scripts/codex-marketplace.py --check
python3 scripts/validate-versions.py
git diff --check
```

O hook também validou uma exportação do índice ao criar o commit. Nova prova
estruturada em [distribution-evidence.json](distribution-evidence.json): todos
os cenários fixam a revisão `7df2ea7`, com 25 pacotes, 289 arquivos, CORS 1.1.2,
as quatro skills irmãs e os casos de sabotagem/atualização/remoção aprovados.
Logs brutos ficam em `.superpowers/sdd/2026-10-22-codex-marketplace/review/`:
`tests-7df2ea7.log`, `auditor.log`, `adapters.log`, `catalog.log`, `versions.log`
e `distribution-7df2ea7.json`.

| Critério da revisão | Grade | Evidência |
|---|---|---|
| Code Quality (Zen) | A | Correções pontuais; fontes canônicas e sweep preservados. |
| Type Safety | A | Formatos inválidos, caminhos e colisões cobertos por fixtures. |
| Error Handling | A | Gate falha em erro; instalador mantém erros explícitos. |
| Security | A | Regex/gitleaks sem findings; fronteiras de caminho e isolamento conferidos. |
| Performance | A | Sem achado; caso de 2.500 arquivos staged permanece coberto. |
| Test Coverage | A | 49 testes gerais + 55 do auditor; provas reais sem skips no Linux. |
| Documentation | A | R01–R12, README, evidência e docstrings conferidos. |
| **Overall** | **A** | Sem achados CRITICAL/HIGH ou correções pendentes no escopo revisado. |

Grades seguem a régua original: A exige ausência de CRITICAL/HIGH e Secrets
Detection PASS. Elas qualificam a revisão; não convertem os limites de ambiente
em resultados aprovados. R01 continua `partial`; desktop/macOS/Windows continuam
`not_checked`, e versão mínima não estabelecida. Não houve push, merge,
publicação ou instalação no perfil pessoal.

O [retrofit posterior](retrofits-2026-10-22.md#retrofit-posterior-à-revisão--codereview-22610)
incorporou a lição dos hashes em codereview 2.26.10. Esse pacote continua excluído
do catálogo Codex; o conjunto publicado e a prova dos 289 arquivos em `7df2ea7`
permanecem válidos. Esse incremento tem verificações próprias e não promove R01.

## Resposta à revisão externa do PR #6 — aplicada e integrada

Claude Code revisou `467c75c`, com quatro achados no comentário
`6353481019`. Foram confirmados e tratados na branch `feat/codex-marketplace`:

| Achado | Correção e evidência |
|---|---|
| Ordem de plataformas divergente | Comparação por listas ordenadas após validar tipos; dois testes cobrem plugins incluídos e excluídos. |
| Rename para fora do pacote pula o gate | `--no-renames` inclui a remoção da origem; teste mantém só o rename staged e exige o bloqueio do snapshot sem o recurso. |
| Fallbacks mortos sem PyYAML | Retornos `no-yaml`/`PULADO` e relatório inacessíveis removidos; a guarda obrigatória e seu teste permanecem. |
| Regras repetidas nos geradores | `skill_paths` e `atomic_write` compartilhados; casos existentes cobrem ambos, com prova adicional de falha na troca atômica e limpeza do temporário. |

Baseline: 49 testes gerais, 55 do auditor e 15 do scanner aprovados. Após as
correções, 53 testes gerais, 55 do auditor e 15 do scanner passaram, sem skips.
Os mutantes das guardas, do default de
skills e da limpeza do temporário foram detectados. Logs em
`.superpowers/sdd/2026-10-22-codex-marketplace/pr/fixes/`.

CodeRabbit cobriu `467c75c` sem achados de código e manteve o aviso agregado de
docstrings. A sonda AST por linhas adicionadas encontrou 14/14 funções de produção
documentadas; funções de testes foram medidas separadamente (1/77). Essa população
não é a mesma dos 93 itens do relatório do bot; o aviso não foi apresentado como
eliminado nem o limiar foi alterado. Copilot não revisou por limite de cota.

A base avançou para `0d2e56d`, causando conflitos em cinco arquivos. A proposta de
reconciliação preserva as correções de CICD/deploy da main, o suporte Codex e o
histórico, com patches de distribuição CICD 2.39.1 e deploy 3.3.3. Após autorização
explícita, as correções e o retrofit foram commitados em `2511ba8`; a main foi
integrada em `cb7f95c`. Os pais desse merge são `2511ba8` e `0d2e56d`. R01 continua parcial.

O preview também passou nos três cenários reais de distribuição, com 25 pacotes
e 289 arquivos, incluindo CICD 2.39.1 e deploy 3.3.3. A origem foi a árvore Git
`838201420449b9f07a90bdab611626d95ebfd48e`, exportada sem criar um commit no PR;
não é uma revisão já enviada. A evidência distingue `merge-preview-tree` de
commit. Artefatos e patch proposto em
`/home/joruge/.wt/pr6-merge-preview-_nbcr7ug/`.

### Check do commit integrado

Depois do merge, os 53 testes gerais, 55 do auditor e 15 do scanner passaram, sem
skips. Os geradores, validador principal e hook staged também passaram. A prova
de distribuição foi repetida após o commit para que `git archive HEAD` exportasse
o candidato integrado real: três cenários aprovados em `cb7f95c`, com 25 pacotes
e 289 arquivos, CICD 2.39.1 e deploy 3.3.3. Os hashes, atualização Git e sabotagem
estão renovados em [distribution-evidence.json](distribution-evidence.json).

Codereview 2.27.0 / coderabbit-pr 4.6.0 acrescenta a detecção do comentário CLI
publicado como usuário e o caso de rename na passagem de sensores. Foram
executados 14 controles, consulta real ao GitHub e leitura fria; SQA antes/depois
sem erros/avisos e sem regressões. Descrições preservadas e limites de tamanho
respeitados. O plugin continua excluído do catálogo Codex.

Logs finais em `.superpowers/sdd/2026-10-22-codex-marketplace/pr/final/`:
`merged-general.log`, `merged-auditor.log`, `merged-scanner.log`,
`committed-distribution.log` e `committed-distribution.json`. O fechamento após
`cb7f95c` altera apenas documentação/evidências; os pacotes testados permanecem
idênticos. A cobertura da revisão original continua atribuída a `467c75c`.

## Fontes e limites

- [Package your plugin](https://developers.openai.com/plugins/build/plugins):
  formato do catálogo e compatibilidade dos manifestos.
- [Build skills](https://learn.chatgpt.com/docs/build-skills): controles de skills.
- [Plugins](https://learn.chatgpt.com/docs/plugins): CLI e desktop; iniciar sessão
  nova após instalação. Extensão IDE fora do escopo.

O teste desktop exige abrir o candidato no aplicativo, selecionar a loja em
Plugins, conferir o conjunto publicado, instalar um plugin múltiplo e iniciar
conversa nova. Invocar cada skill pelo nome mostrado, solicitar leitura de uma
referência e interpretação de entrada segura. Registrar versão, sistema, nomes
e recursos lidos. Até executar esse procedimento, R01 continua parcial.

## Segunda revisão do Claude Code — 92ea30e

O [comentário 6355341570](https://github.com/j0ruge/skills/pull/6#issuecomment-6355341570)
trouxe cinco achados. A execução CLI terminou com retorno 0 e confirmou o mesmo
SHA completo do head: `92ea30e91bb494165a9d87d8f0dc4d2a1d92660b`.

- YAML malformado passa a `ValueError` com origem; `invocations` exige mapa e
  valores textuais. Os dois consumidores relatam erros sem traceback e o gate
  preserva diagnósticos anteriores. Não houve ampliação genérica de `except`.
- DDD 0.5.2, PDF generation 1.6.4 e release 2.0.3 explicitam a mensagem do
  usuário como entrada quando o host mantém o placeholder literal. A substituição
  dos outros hosts permanece; release conserva sua política de invocação explícita.
- A documentação agora distingue `A4 AVISO`/gate local de `G2 ERRO` externo.
  Medição real por `uvx skills-ref==0.1.1`: release e ticket retornam 1 no auditor
  padrão com validação externa. A regra de interseção é intencional e foi
  preservada; não equivale a aprovação externa nem impede instalar o pacote.
- A prova de descoberta usa bytes sem buffer de texto, acumula linhas JSONL e
  mantém prazo global. Regressões cobrem duas respostas no mesmo burst, linhas
  fragmentadas e EOF antes da resposta.
- O instalador reutiliza `build_catalog` e recusa derivados divergentes, inclusive
  omissão de plugin habilitado. Continua somente leitura e sem dependência YAML.

Baseline: 53 testes gerais e 55 do auditor, sem falhas. Após as correções:
61 testes gerais, 55 do auditor e 15 do scanner aprovados. Oito regressões novas;
RED observado nos três defeitos de lógica e cinco mutantes detectados (YAML,
forma de invocations, leitura em lote, fragmentos e catálogo divergente).
SQA local antes/depois das três skills: nenhuma diferença de findings.
Os dois erros externos descritos acima são limites conhecidos, não checks verdes.

Evidências brutas: diretório ignorado
`.superpowers/sdd/2026-10-22-codex-marketplace/pr/round2/`.
A revisão cobre o SHA citado; as mudanças posteriores exigem nova revisão
independente para ampliar essa cobertura. R01 continua parcial por falta da prova
desktop; macOS/Windows e versão mínima permanecem sem comprovação.

### Distribuição após o commit da segunda resposta

Os três cenários reais foram repetidos por `git archive HEAD` depois do commit
`6bdc2ef3f6914e421786afaf11099918036ca37d`: 61 testes gerais aprovados,
sem skips; 25 pacotes / 289 arquivos conferidos byte a byte. A evidência atual
em `distribution-evidence.json` aponta esse commit, incluindo DDD 0.5.2, PDF
generation 1.6.4 e release 2.0.3. Passaram instalação individual, descoberta das
quatro irmãs, auditor da família instalado, sabotagem de template e ciclo Git de
atualização/reinstalação/remoção. O fechamento posterior muda somente documentos
da raiz e evidências, sem alterar esses pacotes.

## Interpretação real dos argumentos de release — 2026-10-22

O usuário autorizou investigar a ressalva do retrofit de release. A versão 2.0.3
foi exportada do commit `86bf29ca74f2bf08f6384d5be29e862d8d857d60`, instalada
em perfil isolado e comparada byte a byte com a fonte. Cada cenário usou um
processo novo do Codex CLI 0.163.0, invocação explícita `$release:release` e
leitura da skill no cache. O modelo executou somente `cat`; git e gh estavam
bloqueados. Nenhuma release foi publicada.

| Entrada de release 2.0.3 | Versão interpretada | Caminho interpretado | Pede versão? |
|---|---|---|---|
| `3.4.5 --path packages/api/` | `3.4.5` | `packages/api/` | não |
| `6.7.8` | `6.7.8` | ausente | não |
| `--path tools/app/` | ausente | `tools/app/` | sim |
| vazia | ausente | ausente | sim |
| `--path packages/ui/ 4.5.6` | `4.5.6` | `packages/ui/` | não |
| `5.6.7 --path "apps/My API/"` | `5.6.7` | `apps/My API/` | não |

**Resultado:** seis de seis casos atuais passaram. Dois controles com a release
2.0.2 (`92ea30e`), versão/caminho e entrada vazia, também passaram. Portanto a
falha de interpretação anterior não foi reproduzida nesses controles; o resultado
valida o comportamento atual, sem provar que o fallback tenha causado a melhora.
Não houve novo patch ou bump da skill. A pendência de verificar a interpretação
real fica encerrada para esses cenários.

[Evidência estruturada](release-arguments-evidence.json). Logs e o executor
ficam fora do Git em `/home/joruge/.wt/release-arguments-xeqm8ta1/`.
Para repetir, copie o executor `investigate.py` dessa pasta para um diretório
novo e execute a cópia. O destino das evidências é o diretório do próprio
executor; os casos existentes são preservados.
O modelo padrão do runtime não informou seu identificador no stream JSONL; não
foi atribuído um nome por suposição. Uma amostra por cenário não mede variação
estatística. A prova cobre somente a etapa 0 no CLI Linux: não altera R01 nem
comprova publicação, desktop, macOS ou Windows. Nenhum segredo foi copiado para
as evidências; a autenticação foi montada apenas para leitura.
