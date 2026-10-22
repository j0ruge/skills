# Verificação e retrofit após a implementação

Autorização: investigar os achados da retro e aplicar somente os confirmados.
Base desta etapa: `b3d0031befbe9361ab3a33f3c5f56fb112ed942c`, branch
`feat/codex-marketplace`. Cliente observado: Codex CLI 0.163.0 no Ubuntu 24.04.

## Resultado por skill

| Alvo | Verificação | Decisão |
|---|---|---|
| ddd | Plano para três contextos grandes, com contrato nativo de delegação informado. Produziu três chamadas `collaboration.spawn_agent`, sem campos Claude, com modelos permitidos e `fork_turns=none` ao configurar modelo/esforço. | Falha suspeita não reproduzida; fonte e versão preservadas. |
| codereview | Plano das fases B/B2 para cinco arquivos Python independentes. Produziu seis chamadas nativas válidas, incluindo o sweep, usando modelo permitido e preservando os contratos das referências. | Falha suspeita não reproduzida com o contrato completo; fonte e versão preservadas. |
| cors | Agente leu a skill e as referências pelo cache instalado e identificou destino incorreto para `Vary: Origin` e aviso incompatível com a sonda parametrizada. Fixture corrigida e pacote final 1.1.2 passaram no mesmo cenário. | Retrofit completo aplicado, commit `13f2cc023a7c828b09bd51c46f0c694f6fbd2146`. |

Os controles de delegação retornaram planos; não executaram subagentes ou revisão.
Um piloto inicial de codereview usava contrato incompleto sobre forks e foi
repetido com a restrição real: fork com histórico completo herda modelo/esforço;
overrides exigem fork sem histórico nesta interface. Só a rodada com contrato
completo sustentou a decisão. Isso não comprova execução integral do plugin nem
muda sua classificação `partial` no catálogo.

A [documentação oficial sobre subagentes](https://learn.chatgpt.com/docs/agent-configuration/subagents)
foi consultada. Nomes e argumentos dos controles seguem o schema disponível na
sessão; a lista de modelos é entrada da fixture, não uma recomendação permanente.

## CORS — correção e prova

- Antes: a triagem de `Vary: Origin` apontava para `casos-limite.md` §3, cujo título
  real é `Access-Control-Expose-Headers`. O destino foi trocado para `seguranca.md`
  §4, que contém o assunto solicitado.
- Antes: o §1a dizia que a sonda atual usava método fixo, enquanto o comando
  já enviava `Access-Control-Request-Method: $METODO`. O aviso e a explicação da
  triagem agora distinguem a sonda parametrizada do exemplo com `POST` fixo.
- O agente reproduziu as duas contradições no pacote antigo; na fixture corrigida
  e na instalação final 1.1.2, leu a seção correta e confirmou a coerência do método.
  Não foram executadas sondas HTTP ou operações externas do workflow.
- Versões da skill, manifesto, catálogo Claude e README conferidas em 1.1.2.
  A descrição permaneceu igual nos três espelhos, com 464 caracteres.

Baseline da auditoria local SQA: 138 linhas / 8.612 caracteres, zero erros e avisos. Depois:
138 linhas / 8.619 caracteres, zero erros e avisos. O gate de regressão não
registrou `NOVO` nem `SUMIU`. Validadores externos ficaram desligados com
`--external off` nos dois lados; não foram contados como verificados. As linhas substituídas corrigem os dois defeitos
reproduzidos; a atualização de `metadata.version` é conferida pelos manifestos
e pelo cheque de sincronismo, sem alterar o gatilho da skill.

A auditoria de prompts foi feita em modo nativo, com leitura integral do
SKILL.md e dos quatro arquivos de referências. O brief histórico do repositório
foi consultado; seu guia `shared/prompt-audit.md` não estava disponível. Não foi
alegada execução do comando Claude `/claude-api prompt-audit`. As outras
observações de conteúdo ficaram registradas como dívida fora deste retrofit:
a abertura sobre requisição já processada versus falha de preflight, e o texto
de diagnóstico sem mensagem CORS versus log suprimido. Não houve limpeza ampla.

## Checks e revisão candidata

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 plugins/skill-quality-audit/skills/skill-quality-audit/scripts/audit_skill_quality.py plugins/cors/skills/cors --external off --format json --claims --desc-budget 0
python3 /home/joruge/.agents/skills/retrofit-skill/scripts/check_release_sync.py cors
python3 scripts/codex-adapters.py --check
python3 scripts/codex-marketplace.py --check
python3 scripts/validate-versions.py
git diff --check
```

Os 44 testes gerais passaram antes do commit. Como os testes de distribuição
exportam `git archive HEAD`, os três cenários reais foram repetidos **depois**
do commit 13f2cc0 e também passaram: CORS instalada em 1.1.2, 25 pacotes,
289 arquivos conferidos, sabotagem detectada e ciclo Git comprovado. Esse é o
candidato posterior ao retrofit; a prova anterior em f98c06d continua histórica.

Baselines, planos JSON, leituras, auditoria de prompts e evidência estruturada
da distribuição ficam fora do repositório, em
`/home/joruge/.wt/retrofit-marketplace-20261022-fav0jevr/`.
O workspace ignorado mantém os mesmos controles em
`.superpowers/sdd/2026-10-22-codex-marketplace/retrofits/`.

Desktop/macOS/Windows, versão mínima e revisão independente da implementação
continuam pendentes conforme o handoff. Nenhuma instalação pessoal, push, merge
ou publicação remota foi feita nesta etapa.

## Retrofit posterior à revisão — codereview 2.26.10

Após a revisão da missão, o usuário autorizou incorporar a lição comprovada dos
hashes. Não foi retomada a suspeita anterior sobre delegação. O plugin continua
`partial` e excluído do catálogo Codex; os 25 pacotes publicados não mudaram.

§6.10 agora oferece um registro JSON com campo `sha256` antes da allowlist,
quando o contrato do manifesto puder mudar. Exige conferir todos os digests na
revisão fixada, preservar caminhos e valores, atualizar produtor e consumidores
e repetir o scan completo. O achado permanece até a nova prova limpa. O fallback
de configuração para schema imutável, a régua de grade F e read-only continuam.

Três fixtures independentes de `TestTypedHashManifest` comprovam o alerta
`generic-api-key` no formato original, ausência de findings no formato tipado e
detecção `github-pat` de um canário gerado em execução no mesmo manifesto. As
asserções exigem gitleaks em `scanners` e `errors: []`; não houve skip neste host.
Os 15 testes do scanner passaram. Nenhum valor de canário foi versionado.

Baseline e resultado SQA: zero erros/avisos, com `--external off` nos dois lados;
gate sem `NOVO` ou `SUMIU`. SKILL.md permaneceu em 247 linhas, com 20.000
caracteres após acrescentar um caractere ao número de versão. Descrição mantida
em 477 caracteres; os espelhos de versão foram atualizados para 2.26.10.

Auditoria de prompts nativa e teste de aplicação independente não encontraram
achados novos. O guia histórico de prompt audit continuava ausente, sem alegação
de executar o comando Claude ou benchmark de modelos. A divergência anterior
entre §6.10 e o contrato per-file sobre DOCS ficou registrada no CHANGELOG, fora
desta correção. Evidências de auditoria em
`/home/joruge/.wt/retrofit-codereview-hash-na3q03qc/`.

Comandos de verificação:

```bash
python3 -m unittest discover -s plugins/codereview/skills/codereview/tests -p 'test_*.py' -v
python3 plugins/skill-quality-audit/skills/skill-quality-audit/scripts/audit_skill_quality.py plugins/codereview/skills/codereview --external off --format json --claims --desc-budget 0
python3 /home/joruge/.agents/skills/retrofit-skill/scripts/check_release_sync.py codereview
python3 scripts/codex-adapters.py --check
python3 scripts/codex-marketplace.py --check
python3 scripts/validate-versions.py
git diff --check
```

Este incremento foi mantido na branch local da missão. A autorização de retrofit
não foi usada para publicar os commits da loja ou atualizar perfis pessoais.
