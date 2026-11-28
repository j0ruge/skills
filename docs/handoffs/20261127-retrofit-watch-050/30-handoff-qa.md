---
missao: 20261127-retrofit-watch-050
fase: QA
status: done
sessao: 01a22103-fc6c-7fc2-85b8-e1adbe66b7c0
data: 2026-11-28 04:24
gate: "Em 8ff2681, env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py → rc 0. Stop abriu pedido privado, triagem preparou no clone dedicado, selo e revisão levaram a um pre-push verde com retenção e bare intacto em c0e29b6010c4. O approve não moveu o bare, e a emenda invalidou a revisão e a aprovação. Nova aprovação publicou 61509ed4001b no bare, no status local/ci capturado, no registro e no clone. Com a janela cumprida, auto publicou 4532a7d0e575 sem approve. O revert retomou auto-dry e preservou 72842585bd0a. A rota manual sem sim preservou esse SHA e, com sim, bare, local/ci e clone chegaram a 34428d720054. Em aba5090, env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B e2e/test_retrofit_watch_stop.py → rc 0, silêncio em linked, missing e empty com estado preservado. Em aba5090, env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval \"$TEST_CMD\"' → rc 0, adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 144 do Stop sem falhas e versões 0.5.0 e 0.12.0 validadas."
---

# Handoff — QA — Retrofit de skills locais com ensaio antes do push autônomo

> Escrito no fim de cada fase. A próxima fase é uma **sessão nova sem memória**: se algo que ela
> precisa saber não está aqui (ou nos artefatos linkados), está perdido.

## TL;DR

A QA percorreu seis cenários de CLI: cinco da rota privada e a atribuição 0.4.1 em três variantes.
Sem novos achados de produto, novas specs de regressão, incrementos de fix ou decisões escaladas.
Os quatro Checks e o TEST_CMD passaram. A suíte ampla repetiu os mesmos resultados vermelhos da base.
Antes da publicação da loja, a revisão precisa endereçar as três sinalizações da camada 1 e repetir a distribuição em host com Bubblewrap.

## Estado do repo

- **Branch:** `feat/retrofit-watch-050-loja`, sem upstream configurado, com base local `origin/main` em `9d679b1`.
- **Último commit:** `8ff2681`, registro da sonda, antes deste handoff. Produto testado em `aba5090`.
- **Working tree:** Limpa após o commit da sonda e antes da redação deste handoff.
- **Suíte:** `TEST_CMD` de `.sdd/config.sh` com o ambiente de `gate` → rc 0 em `aba5090`: 154 testes da loja (3 pulados) e 144 do Stop.
- **E2E:** Sem `E2E_CMD` ou `APP_URL`. As duas jornadas de terminal no campo `gate` saíram com rc 0.

## O que foi feito

- `8ff2681` — a sonda chama `live-setup`, `stop`, `triage`, `prepare`, `seal`, `publish`, `approve` e `live-advance` em subprocessos. Usa Git real em bares locais, vereditos de fixture e um dublê de `gh` para capturar o status. O pre-push recebeu o mesmo SHA, refs e argumentos em ensaio e push. O checkout de desenvolvimento ficou no ramo de trabalho, com refs, rascunho e lista de worktrees intactos. Na rota manual a sonda representa a decisão do operador, sem chamar um modelo ou um revisor real.
- `aba5090` — os Checks I1–I4 de `checkpoint.md` saíram com 12, 20, 41 e 1 teste, nessa ordem. I1–I3 devolveram rc 0 e I4 imprimiu `0.5.0 0.12.0`. As chamadas prefixadas com `env -u GIT_DIR -u GIT_WORK_TREE` usaram `/tmp` como fallback efetivo de `/var/tmp`.
- `aba5090` — os cinco pontos do Review Focus passaram nos Checks. `test_same_name_store_and_lean_never_merge` reteve a duplicata, `test_advance_leaves_wrong_branch_dirty_tree_and_divergence_alone` preservou o HEAD, `test_missing_gate` não moveu o bare, `test_changed_patch_invalidates_approval` exigiu novo patch aprovado e `test_offline_advance_is_in_child_and_reported_on_next_startup` mediu retorno em menos de 1 s e aviso no próximo startup.
- `aba5090` — `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests:plugins/retrofit-skill/tests python3 -B -m unittest test_auto_docs test_modo_autonomo` → 44 contratos verdes. `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/var/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s plugins/retrofit-skill/tests -v` → 11 testes verdes. A jornada do Stop e os 144 testes configurados preservaram a atribuição da 0.4.1.
- `aba5090` — `python3 scripts/validate-versions.py` no TEST_CMD e `python3 plugins/retrofit-skill/scripts/check_release_sync.py retrofit-watch` e `python3 plugins/retrofit-skill/scripts/check_release_sync.py retrofit-skill` passaram. `claude plugin validate plugins/retrofit-watch` e `claude plugin validate plugins/retrofit-skill` passaram com avisos. `python3 scripts/check-private-names.py` saiu com rc 0. O histórico de `origin/main..HEAD` não teve trailers de coautoria nem assinatura de geração. As opções `--check TODO.md` e `--anchors TODO.md` de `/home/joruge/.wt/sdd-kit-8a56249/tests/check-todo.sh` validaram 60 itens na candidata e 57 na base integrada, sem âncora fora do alvo.

## Artefatos

| Arquivo | O que contém |
|---|---|
| `docs/handoffs/20261127-retrofit-watch-050/sonda-qa.py` | Reprodução das cinco rotas privadas com remotos bare descartáveis. |
| `e2e/test_retrofit_watch_stop.py` | Sensor já existente da atribuição 0.4.1, repetido sem alteração. |
| `docs/handoffs/20261127-retrofit-watch-050/checkpoint.md` | Checks I1–I4 concluídos, sem incremento de fix aberto. |

## Boot da próxima fase

REVIEW começa pelo campo `gate`, por `checkpoint.md` e pelos cinco pontos de revisão de `docs/superpowers/plans/2026-11-25-retrofit-watch-lean-auto.md`. Compare `git diff origin/main...HEAD` e repita a sonda com o comando de `gate`. Para a liberação, verifique a camada 1 e repita a distribuição e a suíte ampla no host descrito abaixo. O aceite da jornada em fixture não atesta a prontidão do PR.

## Pendências / Decisions for a Human

- Nenhuma decisão nova. Configurar os repos reais, migrar o estado e autorizar a troca de links continua com cada dono, conforme `00-missao.md`.

## Riscos e não-feitos

- Em `aba5090`, `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/var/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s plugins/retrofit-watch/skills/retrofit-watch/tests -v` retornou rc 1, com 5 falhas e 176 erros em 555 testes. O mesmo comando na árvore extraída por `git archive 6d72029` retornou rc 1 com os mesmos casos de falhas e erros em 487 testes, desconsiderados apenas endereços de função. Aqui `/var/tmp` é somente leitura e o fallback para `/tmp` encontra um marcador `.git` vazio, que a guarda conservadora da colheita conta como ancestral. A falha da segunda skill full persiste também na base. Repetir a suíte ampla com um temporário gravável e sem esse marcador, sem alterar as guardas.
- Em `aba5090`, `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 SKILLS_SKIP_NATIVE_DISTRIBUTION=0 python3 -m unittest discover -s tests -p 'test_codex_distribution.py'` terminou em rc 1 nos três casos. Bubblewrap não teve permissão para criar um namespace de usuário e nenhum caso chegou à instalação. Repetir o comando no host que permita ao Bubblewrap iniciar.
- Em `aba5090`, `env -u GIT_DIR -u GIT_WORK_TREE PYTHONDONTWRITEBYTECODE=1 python3 scripts/anonymity-gate.py --camada1 --base origin/main` saiu com rc 1. Sinalizou uma impressão digital SHA-256 pública em `01-plano.md:17` e a forma SSH sintética em `test_lean_auto.py:17–18`. A publicação da loja ainda precisa de camada 1 limpa sobre a branch inteira.
- Nenhum repo real, link instalado ou configuração pessoal foi alterado. Não houve PR nem publicação externa.

## Achados fora de escopo

- A falha preexistente da segunda skill full já consta em `TODO.md`, seção `Revisão da atribuição da retrofit-watch`.
- As três sinalizações sobre valores sintéticos já constam em `TODO.md`, seção `Minors adiados (triagem)`. A aprovação pública desvinculada do patch permanece fora do escopo da missão e já consta no mesmo backlog. Nenhum achado foi duplicado.
