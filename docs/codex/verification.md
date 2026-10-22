# Verificação da loja Codex

Base de implementação: `cff1494c17c21774885e2a58ae6a5eb42cdd95d9`.
Ambiente observado em 2026-10-22: Ubuntu 24.04 x86_64, Python 3,
`codex-cli 0.163.0`. Essa versão é a testada, não uma versão mínima comprovada.
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
os dois campos seguem avisados no gate, sem aceitação silenciosa na interseção.

As exclusões e dependências dos 31 plugins estão em [compatibility.md](compatibility.md).
Observações sobre exemplos de Zitadel e referências antigas de CORS apareceram
nos smokes e estão preservadas nas conclusões; são conteúdo de domínio fora do
escopo desta distribuição, sem correção ou alegação de revisão integral.

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
