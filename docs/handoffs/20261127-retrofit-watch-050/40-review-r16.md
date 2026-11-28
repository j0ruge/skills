---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 16
status: done
sessao: codex-revisao-estatica-r16
data: 2026-11-28 16:03
gate: "Revisão independente estática de a5a230248776d2e20cf2161be5b75d7d2be51206 a f1bbf79f4c5bb5a54d1edacc433e3a092f77f878. Nota geral B. As cinco regressões de R22 cobrem os casos centrais da r15. A saída de preparação e a liberação da trava do índice ainda podem perder evidência do estado real."
reviewed_head: f1bbf79f4c5bb5a54d1edacc433e3a092f77f878
---

# Review — rodada r16 — Recuperação do avanço

## Achados da r15

- A partir do início da materialização, uma falha inconclusiva conserva os arquivos, os OIDs e o índice anterior em `.git/rw-live-advance`. Uma nova execução identifica a pendência antes do fetch. A restauração automática exige a ref inicial, a árvore temporária limpa no alvo e uma nova preparação que mantenha as travas. `rw_store.py:1322`, `:1345` e `:1418`.
- O staging compara a configuração efetiva e recusa divergências antes de materializar. Ele preserva os padrões de sparse checkout. Os hooks validados nos testes executam no clone real, com a transação de ref no avanço e o `post-merge` após a atualização. `rw_store.py:1299`, `:1312` e `:1404`.
- Se faltar a confirmação depois da escrita, a `main` real no alvo, o índice instalado e o checkout limpo permitem reconhecer o avanço. A reconciliação dos casos cobertos ficou verde. A observabilidade e a retomada ainda têm as lacunas abaixo. `rw_store.py:1333` e `:1340`.

## Achados remanescentes

- **Médio — preparação encerrada à força pode perder a pendência.** O Git pode já ter criado as travas quando a preparação ultrapassa o prazo. Se o fechamento de stdin e a espera também falharem, `_live_ref_update` encerra o processo à força. A rotina de instalação ainda está com `writing=False`, relança o erro comum e o chamador apaga `.git/rw-live-advance`. Assim, uma trava em disco pode sobreviver sem o registro que bloquearia nova busca e orientaria a inspeção. O stderr da transação também continua descartado. Preservar a pendência quando não houver confirmação de abort ou de saída limpa da preparação. Registrar a fase e um diagnóstico Git sanitizado em canal separado dos ACKs. Preservar travas de atribuição desconhecida. `rw_store.py:1239`, `:1248`, `:1266`, `:1334` e `:1389`. [Estados da transação de refs no Git 2.43](https://git-scm.com/docs/githooks/2.43.0#_reference_transaction)
- **Médio — falha ao remover a trava do índice mascara o desfecho.** O `lock.unlink()` no `finally` pode lançar `OSError` após a atualização já confirmada ou enquanto uma exceção `LiveAdvanceUncertain` está em trânsito. No primeiro caso, o diretório de evidências já pode ter sido apagado e `live_advance` registra o OID anterior em `depois`, embora a `main` tenha avançado. No segundo, o erro da trava substitui o diagnóstico que apontava para a pendência. Tratar a liberação como etapa final, guardar o OID observado e a causa primária, e manter a pendência quando a limpeza inconclusiva exigir inspeção. `rw_store.py:1383`, `:1392`, `:1401` e `:1422`.
- **Baixo — o TODO ainda descreve o mecanismo substituído.** O item aberto diz que a operação move o ramo ativo depois da ancestralidade. O delta já seleciona `refs/heads/main` na atualização real e usa HEAD destacado no merge temporário. A âncora revisada aponta para a leitura do alvo em vez da operação descrita. Atualizar o item ao fechar o P2 e manter as pendências de recuperação e plataforma identificáveis. `TODO.md:275`, `rw_store.py:1245` e `:1328`.

## Evidência e alcance

O implementador registrou cinco Reds em `a5a2302` e Green em `f1bbf79` para confirmação ausente, escrita parcial, configuração divergente, sparse checkout e hook real. Os testes correspondem a `test_lean_live.py:1111`, `:1132`, `:1151`, `:1178` e `:1228`. Foram registrados 189 testes dirigidos, a seleção final de 25 casos de avanço, TEST_CMD com 154 testes da loja incluindo três pulos configurados e 144 do Stop, QA em bare local e camada 1 verdes. A distribuição separada registrou três testes verdes no Linux.

Esta revisão usou leitura estática e resultados existentes. A inspeção manual do delta não identificou credenciais literais. A evidência do avanço cobre Linux, Git 2.43 e repositórios de fixture. Windows nativo e recuperação após interrupção abrupta permanecem fora da evidência.

### Overall Grade

| Criterion | Grade | Rationale |
|---|---|---|
| Code Quality (Zen) | B | O descarte ainda usa início de escrita como separador de segurança. Representar preparação inconclusiva e liberação de trava como estados com consequência própria. |
| Type Safety | A | O código conserva Path, OIDs completos e o OID observado, inclusive sua ausência quando a leitura não conclui. |
| Error Handling | B | Escrita parcial e confirmação ausente são tratadas nos casos cobertos. Preservar a pendência e o resultado observado se a preparação ou a liberação da trava ficarem inconclusivas. |
| Security | A | A transação conserva o destino explícito, o OID anterior esperado e os hooks reais. A guarda de origem permanece antes da busca. |
| Performance | A | O avanço continua fora do Stop e os limites da transação permanecem explícitos. |
| Test Coverage | B | As cinco regressões cobrem materialização, configuração e reconciliação. Acrescentar evidência defensiva dos caminhos em que falham a finalização da preparação e a limpeza da trava. |
| Documentation | B | O guia descreve a pendência, mas o TODO ainda atribui a atualização ao ramo ativo. Atualizar o item do P2 e indicar a pendência real de recuperação. |
| **Overall** | **B** | R22 trata os cinco casos da r15. A aceitação do delta depende de conservar evidência e resultado diante de falha na preparação ou na liberação da trava. |
