---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 13
status: done
sessao: codex-revisao-estatica-r13
data: 2026-11-28 15:19
gate: "Revisão independente estática em c4b6192a48ee3c9352fe0295d1bc88336ddfc41d. TEST_CMD rc 0, 178 regressões dirigidas, jornada em fixture, três provas de distribuição no Linux e varredura de segredos sem achados. Nota geral B com dois ajustes no R20."
reviewed_head: c4b6192a48ee3c9352fe0295d1bc88336ddfc41d
---

# Review — rodada r13 — Consulta Git e prazo do hook

A revisão independente conferiu o código e os resultados dos testes no Linux. A resolução da ref agora usa o Git local com transporte bloqueado. A elegibilidade e a medição da janela usam o mesmo prazo. As guardas de origem e o retorno ao modo de ensaio permanecem cobertos.

## Achados

- **Médio.** Uma mudança de `HEAD` durante a consulta pode deixar a leitura da entrada desatualizada até a conferência seguinte do avanço. R20 reconfere `HEAD` depois da consulta.
- **Baixo.** Uma falha de leitura durante a finalização do setup recebe o diagnóstico de troca de ramo. R20 melhora o diagnóstico e preserva a pendência.

Passaram 178 testes dirigidos, TEST_CMD, jornada de QA em bare local e as três provas nativas no Linux. As pendências de Windows e do avanço após a prova de ancestralidade estão registradas no TODO.

### Overall Grade

| Criterion | Grade | Rationale |
|---|---|---|
| Code Quality (Zen) | A | A consulta elimina o parser duplicado, reaproveita o executor Git e propaga um único prazo. |
| Type Safety | A | O delta conserva Path, distingue os três resultados da leitura e encaminha o prazo monotônico. |
| Error Handling | B | A leitura após mudança de HEAD e o diagnóstico da falha final ainda precisam de ajuste. |
| Security | A | A consulta bloqueia transporte e a origem da busca permanece vinculada à identidade autorizada. |
| Performance | A | A elegibilidade e a janela usam o saldo do mesmo prazo, com esgotamento simulado nos testes. |
| Test Coverage | B | Os testes cobrem a compatibilidade da ref e o prazo. O intervalo da nova consulta ainda precisa de uma regressão. |
| Documentation | A | O guia descreve a consulta local, o prazo e o retorno ao manual ou ensaio. |
| **Overall** | **B** | A R19 resolve a divergência de interpretação e preserva o orçamento do hook. R20 trata os dois casos restantes desta rodada. |
