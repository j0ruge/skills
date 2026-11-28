---
missao: 20261127-retrofit-watch-050
fase: EXEC
status: done
sessao: 01a22124-f0cb-7542-8307-f26fe34a7de6
data: 2026-11-28 05:02
gate: "Em 30d619b, env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval \"$TEST_CMD\"' → rc 0. Adaptadores e catálogo válidos, 154 testes da loja (3 pulados), 144 do Stop e versões validadas. O Check de R3 no checkpoint, incluindo a sonda de QA, imprimiu 0."
---

# Handoff — EXEC — Retrofit de skills locais listadas

> Escrito no fim de cada fase. A próxima fase é uma **sessão nova sem memória**: se algo que ela
> precisa saber não está aqui (ou nos artefatos linkados), está perdido.

## TL;DR

I1–I4 e R1–R3 concluídos. A porta privada vincula aprovação ao patch e os efeitos ao servidor autorizado.
O setup pode ser repetido após falha, o avanço reconfere o clone após o fetch e os avisos são por dono/repo.
O TEST_CMD e a sonda local passaram. QA deve repetir os Checks da rodada e validar distribuição nativa.

## Estado do repo

- **Branch:** `feat/retrofit-watch-050-loja` — base de comparação `origin/main` local.
- **Último commit de produto:** `30d619b` — recupera o setup e preserva o clone durante o avanço.
- **Working tree:** limpo após o commit de checkpoint, notas e handoff.
- **Suíte:** `env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 bash -c 'source .sdd/config.sh; eval "$TEST_CMD"'` → rc 0 em `30d619b`. Loja 154 (3 pulados), Stop 144, adaptadores, catálogo e versões válidos.
- **E2E:** sem `E2E_CMD` na config. Jornada automatizada em `sonda-qa.py` com remotos bare de fixture. Nenhum deploy ou repo privado real.

## O que foi feito

- `d929f44` — elegibilidade por origem e janela v2 local, com ensaio quando a prova não é suficiente.
- `785c388` — clone dedicado, avanço `--ff-only`, triagem, worktree e selo por origem.
- `ff7025b` — porta privada, revisão e aprovação por patch, status `local/ci`, startup e retro manual.
- `04a1a77` — manifesto, metadata, catálogo, README e CHANGELOGs sincronizados. O sensor de release ficou vermelho nas versões antigas, passou nas novas e acusou 17 mutações em cópia descartável sob grupo próprio, 10 s e 512 MiB por processo.

### Rodada 1 de revisão

- `fe68792` — R1 inclui no digest privado todos os arquivos alterados da skill, inclusive os caminhos
  reservados às listas no fluxo público.
- `bc8a164` — R2 mantém slug e servidor associados na classificação, porta, status e avanço.
- `30d619b` — R3 limpa a reserva do setup quando a criação falha, confere o ramo e a árvore novamente
  após o fetch e separa os registros por slug completo. O startup distingue falta de registro
  de JSON inválido. Controle de 20 testes do clone e 43 mutações detectadas com tetos de 30 s e 512 MiB.

## Artefatos

| Arquivo | O que contém |
|---|---|
| `docs/handoffs/20261127-retrofit-watch-050/checkpoint.md` | Sete Checks e seus commits. |
| `docs/retrofit-watch/clone-dedicado.md` | Contrato de clone, selo, ensaio, publicação e avanço. |
| `plugins/retrofit-watch/skills/retrofit-watch/tests/test_auto_docs.py` | Cópia de distribuição com contratos dos dois plugins e controles do catálogo. |
| `KAIZEN_LOG.md` e `TODO.md` | Medida da fixture, limite da adoção e achados fora do escopo. |

## Boot da próxima fase

Leia `00-missao.md`, `01-plano.md` e `checkpoint.md` deste diretório. Priorize os Checks R1–R3 e repita os quatro de I1–I4. Não use um
`TMPDIR` com ancestral Git. Desarme `GIT_DIR` e `GIT_WORK_TREE` do runner antes de executar testes que criam repos.
A jornada que muda para o usuário é o Stop de uma skill em repo listado, seguido de pedido, selo, revisão e porta.
Comece com `PrivateWorld` em `plugins/retrofit-watch/skills/retrofit-watch/tests/fixture_private.py` e
`test_lean_gate`. Compare o SHA do bare antes do ensaio e depois de aprovar. Emende o patch aprovado, confira
a retenção, depois compare o SHA publicado no bare, no status capturado `local/ci` e no clone em uso.
Repita com a janela cumprida, após revert e pela rota manual com e sem confirmação. Preserve a prova de
atribuição da 0.4.1 no Stop.

Para R3, use `test_lean_live`. O Check reproduz erro no setup, troca de ramo durante o fetch,
colisão de basenames e JSON inválido. Execute também `sonda-qa.py` conforme a célula do checkpoint.
O clone continua em `<live_dir>/<repo>`. O registro que alimenta o startup agora fica em
`<dados>/live/<dono>/<repo>.json`, sem migração. O aviso de um repo não substitui o de outro.

Em `04a1a77`, além do TEST_CMD, os contratos `test_auto_docs test_modo_autonomo` passaram com 44 testes.
`TMPDIR=/var/tmp python3 -m unittest discover -s plugins/retrofit-skill/tests -v` passou com 11.
`python3 scripts/validate-versions.py` e `python3 plugins/retrofit-skill/scripts/check_release_sync.py`
com cada um de `retrofit-watch` e `retrofit-skill` passaram, assim como `claude plugin validate` nos
dois diretórios de plugin (com avisos). `python3 scripts/check-private-names.py` saiu com rc 0.

Para a distribuição, em host com Bubblewrap, rode `env -u GIT_DIR -u GIT_WORK_TREE
SKILLS_SKIP_NATIVE_DISTRIBUTION=0 python3 -m unittest discover -s tests -p 'test_codex_distribution.py'`.
O executor não abriu PR, não alterou repos reais e não repontou links.

## Pendências / Decisions for a Human

- A adoção privada fica com cada dono. Inventariar e preservar estado ignorado ou não rastreado
  antes de repontar links. Medir o gate real no ambiente do dono, fora desta missão.

## Riscos e não-feitos

- O avanço reconfere o checkout depois do fetch, mas essa conferência e o merge são comandos
  Git separados. O clone é dedicado e não deve ser usado como checkout de desenvolvimento.
- Registros do caminho anterior não são migrados. O próximo avanço grava no novo caminho.
- `/var/tmp` era somente leitura no EXEC, e o marcador vazio `/tmp/.git` contaminou a
  detecção nas fixtures de colheita. Sob controle que ignorou só esse marcador no processo principal,
  `TMPDIR=/tmp python3 -B -m unittest discover -s plugins/retrofit-watch/skills/retrofit-watch/tests -v`
  completou as suítes fora do Stop e atingiu o teto de 240 s já na suíte de Stop. Com os 144 testes
  do Stop verdes no TEST_CMD de cada revisão, foram cobertos 555 testes da candidata e 554 da base
  `d28e095`, com as mesmas 7 falhas e 2 erros. Os subprocessos ainda veem o marcador.
  O Check de release não precisa de Git no temporário.
- As três provas nativas falharam antes de iniciar o cliente isolado. O Bubblewrap não pôde criar
  o namespace. Falta repetir no host da QA.
- `python3 scripts/anonymity-gate.py --camada1 --base d28e095` ficou limpo em I4. A comparação da
  branch inteira com `origin/main` retornou rc 1, com três sinalizações anteriores a I4.
  QA precisa reavaliar esse gate antes de encaminhar a entrega.

## Achados fora de escopo

- Caminhos de auditoria do executor privado (achado 7 da revisão) → `TODO.md`, item sobre
  os caminhos da loja no worktree errado. Não integra R3.
- Aprovação pública da v1 não vinculada ao patch revisto → `TODO.md`, rulings da retrofit-watch 0.4.0.
- Segunda skill full do mesmo plugin ausente no estado, inclusive na base → `TODO.md`, recorrência I4.
- Camada 1 sobre `origin/main` ainda sinaliza a impressão digital pública do plano e quatro URLs
  SSH de fixture em `test_lean_auto.py`, todas anteriores a R3 → `TODO.md`, minors adiados.
  `python3 scripts/anonymity-gate.py --camada1 --base 5c6c947` passou em `30d619b`.
- kit: o EXEC recebeu as variáveis `GIT_DIR` e `GIT_WORK_TREE` da cópia privada do runner
  (`bin/sdd`, ambiente delegado do EXEC). Testes que criam repos podem operar na cópia do runner
  em vez da fixture. Em R3, a primeira execução criou commits vazios e um ref na cópia do runner.
  O ramo foi recomposto sobre o estado de entrada com a mesma árvore testada. A receita com
  as duas variáveis desarmadas passou, sem alterar o Check externo.
