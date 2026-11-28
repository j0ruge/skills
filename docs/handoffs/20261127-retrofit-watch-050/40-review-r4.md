---
missao: 20261127-retrofit-watch-050
fase: REVIEW
rodada: 4
status: done
sessao: 01a2215d-4439-7920-a8ad-cb0ed06ca4b4
data: 2026-11-28 06:01
gate: "Em eaf78b0011ea61f00a745b3cfe922b6b2061cebe, env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval \"$TEST_CMD\"' → rc 0, adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 144 do Stop e versões verificadas. A jornada de QA e 135 regressões dirigidas passaram na árvore inicial limpa. O gate de notas não passou: Code Quality (Zen), Error Handling e Test Coverage continuam em B, agora por achados no setup e aviso. Security subiu para A com R6. R9 está pending."
reviewed_head: eaf78b0011ea61f00a745b3cfe922b6b2061cebe
---

# Review — rodada r4 — Retrofit de skills locais com ensaio antes do push autônomo

## TL;DR

Revisei a missão inteira sobre a base integrada, com o handoff de QA e a sonda.
R6 e R7 passaram. O setup ainda substitui um destino vazio concorrente e pode impedir a retentativa.
Três achados de código formam R9. A receita manual de status vai ao backlog.
TEST_CMD e jornada verdes, nota geral B e gate técnico aberto.

## Nota da rodada

Revisão integral de `e14062c1a4fc159c8b88968fa44c4d7d4aae3e8d...eaf78b0011ea61f00a745b3cfe922b6b2061cebe`.
`4cf6673` integrou a base de `origin/main`. O diff tem 39 arquivos, 4.498 adições e 183 remoções.
O conteúdo das notas históricas ficou fora das leituras e varreduras, conforme o boot.

### Detecção de credenciais

| Arquivos lidos | Linhas novas | Detectores | Achados | Erros |
|---|---|---|---|---|
| 38 | 4.261 | regex, gitleaks | 0 | 0 |

A varredura usou `git -P diff e14062c...HEAD --unified=0 -- . ':(exclude)docs/handoffs/20261127-retrofit-watch-050/checkpoint-notas.md'` como entrada de `bash /home/joruge/.claude/plugins/cache/chewiesoft-marketplace/codereview/2.30.2/skills/codereview/scripts/scan_secrets.sh`. A camada 1 também saiu com rc 0 sobre o Git delegado no HEAD revisado, com o mesmo pathspec de exclusão aplicado às duas chamadas de diff do scanner. A checagem não certifica as notas omitidas.

### Cobertura, comportamento e documentação

| Área | Sensor e evidência |
|---|---|
| Classificação, pedido e janela | `test_fixture_private`, `test_lean_auto` e `test_lean_window`. Repo e transporte divergentes ficam fora da rota, revert reinicia a janela e histórico ilegível conserva o ensaio. |
| Preparação e startup | `test_lean_batch` e `test_lean_live`. Colisão de nome, trabalho fora do checkout de desenvolvimento, preservação da árvore na rota normal e aviso offline, com as lacunas de R9. |
| Porta e aprovação | `test_lean_gate`. Pre-push ausente não move o bare, emenda anula aprovação e a porta publica somente o SHA que conferiu na fixture. |
| Contratos e distribuição | `test_auto_docs`, `test_modo_autonomo` e verificadores de catálogo e versões. README, CHANGELOG, referências e contrato conferidos contra o runtime. A divergência da receita manual está no achado 4. |
| Jornada de QA | `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py` → rc 0. Ensaio preservou o bare, emenda reteve, nova aprovação alinhou bare, status capturado, registro e clone em `6f219e3586d0`. Em auto, publicou `fa80c40b0f02`. Após revert, o remoto ficou em `c10946779f0f` até a rota manual simulada alinhar `796042704cc1`. |
| Regressões dirigidas | `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests:plugins/retrofit-skill/tests python3 -B -m unittest test_fixture_private test_lean_auto test_lean_window test_lean_live test_lean_batch test_lean_gate test_auto_docs test_modo_autonomo` → rc 0, 135 testes, sem pulos. |

O TEST_CMD rodou uma vez no HEAD revisado, com o resultado do frontmatter. As três provas nativas
não foram repetidas neste sandbox. O EXEC registrou execução no host em `b5512cb`. A rota privada
usa bares locais e não mede disponibilidade de um serviço GitHub Enterprise.

A varredura de código morto (ruff e busca de referências) não encontrou símbolo introduzido ou
órfão pelo diff. O inventário de código morto preexistente não integrou a rodada.

### Overall Grade

| Criterion | Grade | Rationale |
|-----------|-------|-----------|
| Code Quality (Zen) | B | A identidade Git e a chamada de status foram corrigidas. O setup ainda separa a conferência do destino da operação que pode substituí-lo. |
| Type Safety | A | IDs de origem e patch continuam validados nos leitores. Os testes exercitaram os formatos privados e os contratos full, além dos registros de avanço. |
| Error Handling | B | A validação no caminho final recusa a origem trocada, mas deixa uma instalação inválida que bloqueia a retentativa. Uma falha de lançamento só chega ao log. |
| Security | A | Os controles de origem rejeitaram destinos não equivalentes antes do fetch. O patch revisto e o pre-push preservaram o vínculo da publicação. A varredura não encontrou credenciais no escopo lido. |
| Performance | A | O avanço continua destacado. O teste offline manteve o startup abaixo de 1 s, sem esperar pelo fetch. |
| Test Coverage | B | A suíte e a jornada passaram. Os testes de setup não cobrem a substituição no instante do rename nem exigem retentativa após a recusa final. A falha ao lançar o avanço também ficou sem sensor de aviso. |
| Documentation | B | O status autônomo e o contrato de publicação estão alinhados. A receita manual ainda não preserva a porta HTTPS não padrão. |
| **Overall** | **B** | R6 e R7 fecham os problemas anteriores. A revisão integral reproduziu dois problemas no setup e um no aviso de startup. |

Em relação à r3, Segurança subiu de B para A após os commits `8744b1d` e `38c46e3`.
As demais letras não regrediram. Ainda não há aprovação técnica da rodada.

## Achados da rodada

| # | Severidade | Achado | Onde |
|---|---|---|---|
| 1 | MEDIUM | O setup aceita e substitui um diretório vazio criado entre a última conferência e o rename. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:971` |
| 2 | MEDIUM | Falha na validação final deixa um clone inelegível no destino e impede repetir o setup mesmo após corrigir a causa. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/rw_store.py:975` |
| 3 | LOW | Se o processo de avanço nem iniciar, o último sucesso pode deixar o startup sem aviso. A exceção é observável no log. | `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py:1369` |
| 4 | MEDIUM | A receita manual de `local/ci` perde a porta HTTPS explícita com endpoint relativo. É um achado da instrução escrita, não da porta autônoma. | `plugins/retrofit-skill/references/modo-autonomo.md:49` |

### Reprodução dos achados

As sondas abaixo rodaram em `eaf78b0` por `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -`, com HOME descartável nas fixtures.

1. Em `PrivateWorld`, intercalei a criação de um diretório vazio imediatamente antes da chamada real a `Path.rename`. O setup retornou sucesso e o inode do diretório mudou. O teste existente em `test_lean_live.py:116` cria um destino não vazio e interrompe o setup antes da instalação. Ele não alcança essa janela.
2. Na mesma fixture, um `includeIf.gitdir` no HOME reescreveu a URL somente no destino final. A primeira chamada recusou a origem, mas deixou `LIVE_SETUP_PENDING` no clone e `live_clone` retornou `None`. Removi a regra e repeti `live_setup`. Retornou `destino já existe`. O teste em `test_lean_live.py:135` cobre a recusa e a inelegibilidade, mas não a recuperação. O caso contradiz a retentativa descrita em `README.md:484` e `plugins/retrofit-watch/CHANGELOG.md:19`.
3. Gravei um registro anterior `ok` e fiz `subprocess.Popen` levantar `OSError` com apenas o segmento de avanço ativo. `cmd_pending` retornou `None` e a falha foi gravada em `errors.log`. O teste offline verde mede erro **depois** que o processo inicia. Este caso é de observabilidade e não reduz a nota por si só.
4. Com `gh` 2.85.0, HOME isolado e autenticação sintética de fixture, o POST relativo com `--hostname 127.0.0.1` tentou a porta 443. No mesmo comando, passar `127.0.0.1:8443` a `--hostname` deu `invalid hostname`. Um POST com URL absoluta da API e hostname sem porta tentou a 8443. O sandbox recusou os sockets. A diferença medida é o destino da requisição, não a resposta da API.

## Incrementos de conserto (R<n>)

| R<n> | Achado | Check escrito no checkpoint |
|---|---|---|
| R9 | 1, 2 e 3 | Exige três regressões nomeadas para destino concorrente, recuperação após recusa e aviso quando o processo não inicia, seguidas da jornada de QA. |

## O que virou incremento

```text
| R9 | Preservar o destino concorrente, recuperar a instalação recusada e mostrar falha ao iniciar o avanço | `(env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_live.LiveTest.test_setup_does_not_replace_concurrent_empty_destination test_lean_live.LiveTest.test_setup_retries_after_final_origin_validation_failure test_lean_live.StartupTest.test_spawn_failure_warns_even_with_prior_ok >/dev/null && env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py >/dev/null); echo $?` → `0` | pending | — |
```

- R6 — fechado em `8744b1d`. Passaram `test_unverified_transport_equivalence_stays_manual` e `test_changed_transport_target_holds_before_fetch`.
- R7 — fechado em `38c46e3`. Passaram o teste do POST absoluto com porta HTTPS e o controle que não repassa a porta SSH à API. O cliente real aceitou a sintaxe nova e tentou 8443.
- R8 — em `af9095a`, passaram os testes que observam a trava antes da visibilidade, preservam um arquivo concorrente criado durante o clone e recusam uma origem efetiva trocada no caminho final. R9 cobre situações que esses sensores não exercitam.

## O que foi refutado

- **O trailer `autonomous-approved` deveria ser aceito no privado.** O contrato privado usa `autonomous` e um arquivo de aprovação separado, ligado ao patch. Em `GateTest`, mantive o trailer e o SHA originais, obtive retenção `auto-dry`, executei `approve` e publiquei o mesmo SHA no bare. O trailer alternativo pertence à rota full. Não há falha no fluxo privado suportado.
- **A sonda verde comprova a decisão de um executor manual real.** Entre as duas leituras na etapa sem confirmação, `sonda-qa.py:183–187` não chama um executor. A QA já descreve esse passo como simulação. A sonda prova os efeitos locais dos comandos selecionados, não a interpretação da confirmação por um modelo. Transformar esse procedimento em um comando decisor não é requisito da missão.
- **A porta autônoma ainda perde a porta HTTPS.** O teste de R7 compara a chamada completa. No cliente medido, a URL absoluta chegou à etapa de conexão na porta prevista. O achado de porta restante está limitado à receita manual.

## Achados fora de escopo

- A correção da receita manual de status (achado 4) foi registrada em `TODO.md` (2026-11-28), sem incremento de prosa.
- A corrida de avanço **depois** da prova de ancestralidade já está registrada em `TODO.md` pela r2. Não é a corrida de instalação de R9 e não foi contada de novo.

## Pendências / Decisions for a Human

Nenhuma decisão nova. A adoção e a validação do gate em cada repo real continuam com seu dono.

## Boot da próxima fase

Comece em `checkpoint.md`, R9. Aplique TDD aos três casos em `test_lean_live.py`.
Na corrida, a asserção precisa preservar a identidade do diretório vazio, não só rejeitar um
destino com conteúdo. Na retentativa, reproduza a regra de origem que se aplica só ao caminho
final, retire-a e confirme que o setup volta a funcionar sem intervenção sobre o destino.
Para o startup, preserve a entrega dos demais avisos e a prova offline. Repita a jornada de QA.

### Ações recomendadas

**Correções críticas:** nenhuma.

**Correções de alta prioridade:** nenhuma.

**Corrigir no EXEC:** R9, com as três regressões e a jornada.

**Prosa adiada:** receita de status manual no backlog.

_Cost footprint: skill v2.30.2 do cache instalado, carregada inicialmente v2.27.38; 10 tarefas por arquivo (gpt-6.1-terra), 0 verificadores, 1 varredura (gpt-6.1-terra), 28 leituras integrais reportadas pelos agentes, 3–12 chamadas por tarefa e 9 na varredura._
