# Documentação — Retrofit de skills locais

## Drift checklist

| Área alterada | Documento | Status | Evidência |
|---|---|---|---|
| Catálogo e versões dos plugins | `README.md`, changelogs de retrofit-watch e retrofit-skill | ✅ | `04a1a77` sincronizou manifestos, catálogo, notas e versões. |
| Elegibilidade, atribuição e janela v2 | `plugins/retrofit-watch/skills/retrofit-watch/SKILL.md`, `plugins/retrofit-watch/skills/retrofit-watch/references/modo-autonomo.md` | ✅ | `ff7025b` descreve o fluxo e `8744b1d` documenta a identidade efetiva do destino. |
| Clone, retomada e prazo do hook | `docs/retrofit-watch/clone-dedicado.md`, `README.md` | ✅ | `c4b6192` documenta a consulta Git local e o prazo compartilhado. `4f64998` confirma o ramo após a consulta e preserva o diagnóstico na retomada. |
| Preparação, selo e auditoria privada | `plugins/retrofit-skill/commands/retrofit-skill.md`, `plugins/retrofit-skill/references/modo-autonomo.md`, `plugins/retrofit-watch/agents/retrofit-reviewer.md` | ✅ | `ff7025b` documenta a preparação e a segunda passada do revisor. `3162507` define a loja como fonte dos scripts e o worktree do lote como alvo. |
| Status da publicação e adoção manual | `plugins/retrofit-skill/references/modo-autonomo.md`, `docs/retrofit-watch/clone-dedicado.md` | ✅ | `38c46e3` e `84a0b0e` documentam a porta HTTPS na API. A adoção de cada repo depende do mantenedor. |
| Decisão arquitetural | `docs/adr/0001-retrofit-lean-publicacao.md` | ✅ | `6d72029` registra a decisão de publicar com clone e lote separados. |
| Medição e evidências | `KAIZEN_LOG.md`, `20-handoff-exec.md`, `checkpoint.md` | ✅ | `04a1a77` registra o antes e depois. `071e298` registra 24 incrementos, QA em fixture e os testes do produto em `4f64998`. |
| Fixtures e regressões | `30-handoff-qa.md`, `20-handoff-exec.md` | ✅ | `1f1b008` registra a jornada em remoto local. `071e298` registra a repetição no último código do candidato. |
| Backlog da loja | `TODO.md` | ✅ | `d708375` e `6a791c0` vinculam as resoluções às provas. `8df070f` marca o achado do avanço como resolvido pela transação nomeada de `a5a2302`. |

## Achados conferidos

O avanço protege a `main` e registra os estados que exigem conferência. O guia do clone descreve a retomada e `checkpoint-notas.md` registra a validação em Linux com Git 2.43. O TODO conserva a validação do marcador no Windows e a falha preexistente de atribuição da segunda skill full. A adoção em repositórios reais pertence a cada mantenedor.
