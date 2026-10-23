# Distribuição individual de plugins no Codex

**Data:** 2026-10-22 · **Estado do desenho:** `approved` · **Implementação:** `implemented_with_gaps`

O usuário aprovou o desenho apresentado após a entrevista de sete perguntas.
Este documento formaliza aquele desenho; os detalhes de implementação serão
verificados pelo [plano PDCA](../plans/2026-10-22-codex-marketplace.md).
Pesquisa, respostas e checklists estão no [CONTEXT.md](../../../CONTEXT.md).

## Objetivo e experiência desejada

Uma pessoa registra a loja Chewiesoft no Codex CLI ou desktop, escolhe um plugin
e passa a usar suas skills e comandos portáveis. A instalação de um plugin não
instala o restante do catálogo. Plugins que hoje reúnem várias skills continuam
como uma unidade de instalação.

O público alvo inclui todos os ambientes oficialmente suportados pelo Codex.
Restrições de sistema operacional, ferramentas e autenticação de cada workflow
serão documentadas por plugin. A cobertura efetivamente testada será indicada
separadamente do alvo de suporte.

## Requisitos e critérios de aceitação

| ID | Requisito | Evidência de aceitação |
|---|---|---|
| R01 | Distribuir por marketplace nativo para CLI e desktop. | Loja e plugin visíveis nos dois clientes, com versão do cliente registrada. |
| R02 | Instalar por plugin, mantendo os agrupamentos atuais. | Instalar um plugin de várias skills carrega todas as suas skills e não instala outro plugin. |
| R03 | Incluir skills e comandos portáveis. | Auditoria de todos os candidatos e smoke seguro da entrada de cada workflow publicado. |
| R04 | Oferecer apenas plugins validados para Codex. | O conjunto mostrado pelo cliente corresponde ao catálogo Codex; incompatíveis constam apenas na documentação. |
| R05 | Compartilhar conteúdo canônico entre plataformas. | Alteração em uma fonte canônica é refletida nos artefatos derivados por geração ou acusada pelo validador. |
| R06 | Acrescentar Codex ao `install.py` como orientação. | Menu mostra registro da loja e comandos individuais, sem executar instalação ou escrever na configuração pessoal. |
| R07 | Preservar os fluxos existentes de Claude Code e Cursor. | Validador existente e regressões dos fluxos afetados passam; agrupamentos e nomes existentes são preservados. |
| R08 | Publicar compatibilidade e requisitos verificáveis. | README cobre suporte, exclusões, dependências, versões testadas e restrições por plugin; lacunas de teste ficam explícitas. |
| R09 | Manter o conteúdo instalado autocontido. | Skills, scripts, referências e templates usados pelo pacote existem e são legíveis no destino instalado. |
| R10 | Preservar contratos de invocação e chamadas entre skills. | Workflows explícitos continuam explícitos; nomes publicados e dependências entre workflows são conferidos no cliente. |
| R11 | Documentar e verificar o ciclo de instalação. | Registro, instalação, atualização e remoção têm comandos comprovados e efeitos observados em ambiente isolado. |
| R12 | Retomar a execução só depois do `/clear` do usuário. | Nesta fase só são alterados documentos; a retomada usa o handoff e o plano. |

## Arquitetura e fontes canônicas

Adicionar `.agents/plugins/marketplace.json` como catálogo Codex filtrado. Ele
será um artefato derivado e versionado, disponível no clone Git sem exigir que o
consumidor execute um build. Suas entradas apontarão para os plugins existentes
em `plugins/`.

O fluxo de dados será:

```text
fontes de conteúdo + manifestos atuais
                  │
       declaração de suporte Codex
                  │
     geração e validação determinísticas
                  │
      catálogo Codex + adaptações necessárias
                  │
        instalação individual pelo host
```

| Informação | Fonte canônica | Derivados e verificações |
|---|---|---|
| Localização e participação na loja atual | `.claude-plugin/marketplace.json` | Resolver e validar cada caminho de plugin antes de gerar o catálogo Codex. |
| Nome, versão, autoria e plataformas do plugin | `plugins/<plugin>/.claude-plugin/plugin.json` | Espelhos nos catálogos e em eventuais manifestos Codex; preservar a regra atual de conciliação de versão com o CHANGELOG. |
| Descrição de skill | `SKILL.md`, conforme `CLAUDE.md` | Validação de consistência já existente, estendida quando houver derivados Codex. |
| Workflow de skill e seus recursos | Diretório canônico `plugins/<plugin>/skills/<skill>/` | Referência direta sempre que o host aceitar o formato existente. |
| Workflow de comando | `plugins/<plugin>/commands/<command>.md` e seus recursos empacotados | Adaptação gerada somente quando a carga nativa não preservar o comportamento necessário. |
| Inclusão no catálogo Codex | `codex` em `platforms`, acrescentado após validação | Catálogo gerado contém exatamente esse conjunto; a evidência funcional vive no relatório de compatibilidade. |

O slug continuará `chewiesoft-marketplace`, a marca continuará Chewiesoft e os
endereços de distribuição usarão `j0ruge/skills`.

Os formatos externos serão tratados na fronteira de distribuição. Não haverá
uma segunda árvore de conteúdo mantida manualmente. Se o Codex exigir manifesto
próprio ou conteúdo adaptado, esses arquivos terão origem identificada e uma
verificação determinística de sincronismo.

## Compatibilidade e adaptação

A primeira prova deve verificar: precedência do catálogo Codex sobre o catálogo
Claude no mesmo repositório; resolução dos manifestos existentes; carregamento
de um plugin com skill e referências; e comportamento de um plugin de comando.
Esses são fatos a medir na execução, não decisões a devolver ao usuário.

Para cada plugin, registrar um dos estados:

| Estado | Significado | Publicação no catálogo Codex |
|---|---|---|
| `supported` | Pacote carrega; entrada dos workflows e recursos passam no smoke seguro; dependências e restrições estão documentadas. | Incluir. |
| `partial` | Uma parte essencial do plugin ainda não funciona no Codex. | Excluir até resolver, preservando o agrupamento aprovado. |
| `unsupported` | Depende de recurso específico sem adaptação portável dentro desta missão. | Excluir e explicar. |
| `not_checked` | Falta evidência para classificar. | Excluir até verificar. |

Uma restrição inerente ao domínio, como uma skill de WPF exigir Windows, não é
por si só incompatibilidade com o Codex. Ela precisa aparecer nos requisitos da
skill. Suporte a todos os hosts não transforma ferramentas Windows em ferramentas
multiplataforma.

O smoke funcional verifica a seleção da skill correta, a leitura dos recursos
empacotados, a interpretação da entrada e o próximo passo do workflow. Não exige
executar deploys, apagar recursos ou modificar serviços externos para testar a
distribuição. Avaliação integral das regras de negócio de cada skill permanece
fora do escopo desta integração.

Adaptações devem tratar, quando presentes, argumentos, nomes de ferramentas e
subagentes, caminhos de instalação, invocação explícita e referências entre
skills. Não presumir que remover um campo de frontmatter ou substituir um nome
de ferramenta preserva o comportamento. O caso `criar-prd` exige verificar o
template de fallback empacotado, usado quando o projeto não tem template próprio.

## Instalador e erros

O `install.py` manterá execução com a biblioteca padrão do Python. Sua opção
Codex lerá o catálogo distribuído e apresentará instruções de registro e
instalação individual. A pessoa executará os comandos no ambiente apropriado.

As opções Claude Code e Cursor continuam disponíveis. O rótulo atual `Both`
deverá passar a identificar explicitamente a combinação Claude Code + Cursor,
evitando ambiguidade com a terceira plataforma.

Catálogo ausente, JSON inválido, seleção inconsistente ou fonte inexistente
produzem erro explícito e retorno diferente de zero. Uma falha na distribuição
não pode produzir uma lista vazia acompanhada de sucesso. O gerador valida todas
as entradas antes de substituir o catálogo e não altera arquivos na modalidade
de conferência.

## Validação e manutenção

Estender `scripts/validate-versions.py` e sua integração em `scripts/pre-commit`
para verificar o catálogo derivado e as adaptações. O auditor em
`plugins/skill-quality-audit/skills/skill-quality-audit/scripts/audit_skill_quality.py`
também possui regras por plataforma; elas precisam ser alinhadas e cobertas pelos
testes afetados quando `codex` for introduzido.

Os testes devem provar tanto a entrada válida quanto falhas intencionais:
plugin incompatível incluído, recurso ausente, caminho inválido, artefato derivado
desatualizado e catálogo ilegível. Fixtures independentes impedem que um pacote
instalado em teste anterior esconda a falha.

README e CLAUDE.md serão atualizados com as instruções para usuários e autores.
Mudanças em plugins seguirão os bumps e CHANGELOGs exigidos pelo repositório.
O `KAIZEN_LOG.md` registrará o Check observado e os validadores efetivamente
entregues; a aprovação do desenho não comprova esses resultados.

## Alternativas e limites

Reutilizar diretamente o catálogo Claude, como o Matt, foi considerado. O
catálogo Codex próprio foi aprovado porque permite publicar um subconjunto
validado. A duplicação manual de skills acrescentaria manutenção e divergência,
portanto a adaptação usará fontes canônicas e derivados conferidos.

Esta entrega não inclui pacote obrigatório com todas as skills, instalação
avulsa para a extensão de IDE ou submissão ao diretório público da OpenAI.
Portar APIs exclusivas do Claude é uma mudança futura se não houver equivalência
pequena e comprovada dentro dos workflows já escolhidos.

## Referências

Consultadas em 2026-10-22; a pesquisa detalhada e o exemplo do Matt estão no CONTEXT.

- [Package your plugin — OpenAI](https://developers.openai.com/plugins/build/plugins): formatos e distribuição por marketplace.
- [Plugins — OpenAI](https://learn.chatgpt.com/docs/plugins): superfícies de uso.
- [Build skills — OpenAI](https://learn.chatgpt.com/docs/build-skills): conteúdo e controles de skills.
- [DDD — referências estratégicas](../../../plugins/ddd/skills/ddd/references/strategic-design.md): linguagem e fronteiras.
- [Kaizen — templates](../../../plugins/kaizen-software/skills/kaizen-software/references/templates.md): PDCA e verificação por artefato.
