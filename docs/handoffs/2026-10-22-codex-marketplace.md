# Retomada — loja Codex

**Estado:** desenho aprovado; especificação e plano escritos; implementação não iniciada.
**Repositório:** `/home/joruge/repos/skills` (`j0ruge/skills`).
**Base:** `main`, conforme `CLAUDE.md` local. Confirmar o estado Git ao retomar.

## Ler antes de agir

1. [CLAUDE.md](../../CLAUDE.md): contratos do repositório e regras de distribuição.
2. [Especificação](../superpowers/specs/2026-10-22-codex-marketplace-design.md): desenho aprovado e critérios R01–R12.
3. [Plano PDCA](../superpowers/plans/2026-10-22-codex-marketplace.md): tarefas, interfaces, testes e reversão.
4. [CONTEXT.md](../../CONTEXT.md): pesquisa oficial, respostas da entrevista e checklist DDD/Kaizen.

## Decisões que persistem

- Marketplace nativo para CLI e desktop; instalação individual por plugin,
  mantendo os agrupamentos atuais.
- Catálogo Codex próprio e filtrado, com conteúdo canônico compartilhado.
- Skills e comandos portáveis entram após validação; exclusões ficam no README.
- `install.py` recebe Codex para mostrar comandos; a pessoa executa a instalação.
- Alvo em todos os ambientes oficialmente suportados pelo Codex; restrições de
  cada skill e cobertura efetivamente testada ficam documentadas.
- O usuário pediu `/clear` antes da execução e outro `/clear` antes da revisão
  com `/goal` e `codereview:codereview` até todos os grades A.

As sete perguntas de produto foram respondidas. Não repetir a entrevista.
Detalhes técnicos ainda sem prova têm tarefa e critério no plano. Se um teste
invalidar o desenho, explicar a evidência antes de mudar o contrato aprovado.

## Estado verificável da preparação

- Só documentação foi modificada nesta fase: pesquisa, especificação, plano,
  handoff, referências do README e registro de planejamento no KAIZEN_LOG.
- Nenhum catálogo Codex, adaptador ou mudança no instalador foi implementado.
- Nenhum plugin foi instalado para esta missão; configuração pessoal preservada.
- O baseline `python3 scripts/validate-versions.py` passou durante a pesquisa.
  O CLI observado foi `0.163.0`; isso não estabelece a versão mínima de suporte.
- O inventário estrutural está no CONTEXT; suporte Codex não foi atribuído com
  base nesse inventário. Os testes futuros permanecem desmarcados no plano.
- As retros de `kaizen-software` e `ddd` solicitadas pelo watcher não encontraram
  lições novas para incorporar às skills nesta sessão.

## Primeira retomada — implementação

Após o `/clear`, o usuário pode enviar:

```text
Leia docs/handoffs/2026-10-22-codex-marketplace.md e os documentos indicados.
Revise o plano e execute-o em modo nativo, tarefa por tarefa, usando
superpowers:executing-plans. Preserve o desenho aprovado e registre o Check
de cada incremento. A revisão com /goal e codereview ficará para outro /clear.
```

Capturar a revisão base antes de alterar código e preservar a preparação
documental. A recomendação é execução nativa, pois os incrementos compartilham
catálogo, metadados e validadores. O usuário pode escolher outro método na
retomada. As skills DDD e Kaizen seguem como critérios de verificação, sem
refatorações ou cerimônias adicionais fora do escopo.

Ao terminar, atualizar este handoff com revisão base/final, caminhos do relatório
de evidências, checks realizados e lacunas. Não declarar suporte testado em uma
superfície à qual o executor não teve acesso.

## Segunda retomada — revisão

Depois da execução e do novo `/clear`, o usuário pode enviar:

```text
/goal Use codereview:codereview para revisar a implementação da loja Codex,
partindo de docs/handoffs/2026-10-22-codex-marketplace.md. Verifique o diff,
os requisitos da especificação e as evidências do plano; corrija os achados
e repita os checks necessários até todos os grades serem A. Não altere a
régua da revisão para obter A e não declare concluída uma verificação pendente.
```

O objetivo deve ser criado somente nessa etapa. A preparação atual não inicia
automaticamente execução, revisão, push ou publicação.
