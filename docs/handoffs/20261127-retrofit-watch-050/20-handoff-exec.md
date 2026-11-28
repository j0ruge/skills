---
missao: 20261127-retrofit-watch-050
fase: EXEC
status: done
sessao: 01a220f9-54c7-7321-a439-40e3767d6a7e
data: 2026-11-28 04:15
gate: "source .sdd/config.sh; env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp bash -c \"$TEST_CMD\" em 04a1a77 → rc 0, 154 testes da loja (3 pulados), 144 do Stop, adaptadores, catálogo e versões válidos. O Check de I4 no checkpoint imprimiu 0.5.0 0.12.0."
---

# Handoff — EXEC — Retrofit de skills locais listadas

> Escrito no fim de cada fase. A próxima fase é uma **sessão nova sem memória**: se algo que ela
> precisa saber não está aqui (ou nos artefatos linkados), está perdido.

## TL;DR

I1–I4 concluídos. O Check de I4 em `04a1a77` imprimiu `0.5.0 0.12.0` e o TEST_CMD ficou verde.
QA deve repetir a jornada no bare de fixture e as provas nativas em host com Bubblewrap.
O portão da branch ainda acusa três dados sintéticos anteriores a I4.

## Estado do repo

- **Branch:** `feat/retrofit-watch-050-loja` — 12 commits à frente de `origin/main` local, antes deste handoff.
- **Último commit de produto:** `04a1a77` — sincroniza as versões do retrofit local.
- **Working tree:** limpo após o commit de checkpoint, notas e handoff.
- **Suíte:** `source .sdd/config.sh; env -u GIT_DIR -u GIT_WORK_TREE TMPDIR=/tmp bash -c "$TEST_CMD"` → rc 0 em `04a1a77`. Loja 154 (3 pulados); Stop 144; adaptadores, catálogo e versões válidos.
- **E2E:** sem `E2E_CMD` na config. Jornada automatizada em `test_lean_gate` com bare de fixture. Nenhum deploy ou repo privado real.

## O que foi feito

- `d929f44` — elegibilidade por origem e janela v2 local, com ensaio quando a prova não é suficiente.
- `785c388` — clone dedicado, avanço `--ff-only`, triagem, worktree e selo por origem.
- `ff7025b` — porta privada, revisão e aprovação por patch, status `local/ci`, startup e retro manual.
- `04a1a77` — manifesto, metadata, catálogo, README e CHANGELOGs sincronizados. O sensor de release ficou vermelho nas versões antigas, passou nas novas e acusou 17 mutações em cópia descartável sob grupo próprio, 10 s e 512 MiB por processo.

## Artefatos

| Arquivo | O que contém |
|---|---|
| `docs/handoffs/20261127-retrofit-watch-050/checkpoint.md` | Quatro Checks e seus commits. |
| `docs/retrofit-watch/clone-dedicado.md` | Contrato de clone, selo, ensaio, publicação e avanço. |
| `plugins/retrofit-watch/skills/retrofit-watch/tests/test_auto_docs.py` | Cópia de distribuição com contratos dos dois plugins e controles do catálogo. |
| `KAIZEN_LOG.md` e `TODO.md` | Medida da fixture, limite da adoção e achados fora do escopo. |

## Boot da próxima fase

Leia `00-missao.md`, `01-plano.md` e `checkpoint.md` deste diretório. Repita os quatro Checks. Não use um
`TMPDIR` com ancestral Git. Desarme `GIT_DIR` e `GIT_WORK_TREE` do runner antes de executar testes que criam repos.
A jornada que muda para o usuário é o Stop de uma skill em repo listado, seguido de pedido, selo, revisão e porta.
Comece com `PrivateWorld` em `plugins/retrofit-watch/skills/retrofit-watch/tests/fixture_private.py` e
`test_lean_gate`. Compare o SHA do bare antes do ensaio e depois de aprovar. Emende o patch aprovado, confira
a retenção, depois compare o SHA publicado no bare, no status capturado `local/ci` e no clone em uso.
Repita com a janela cumprida, após revert e pela rota manual com e sem confirmação. Preserve a prova de
atribuição da 0.4.1 no Stop.

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

- Aprovação pública da v1 não vinculada ao patch revisto → `TODO.md`, rulings da retrofit-watch 0.4.0.
- Segunda skill full do mesmo plugin ausente no estado, inclusive na base → `TODO.md`, recorrência I4.
- Camada 1 sinaliza a impressão digital pública do plano (§ Contexto verificado) e as duas URLs SSH
  no teste `OriginTest.test_only_supported_origin_shapes` → `TODO.md`, minors adiados.
- kit: o EXEC recebeu as variáveis `GIT_DIR` e `GIT_WORK_TREE` da cópia privada do runner
  (`bin/sdd`, ambiente delegado do EXEC). Testes que criam repos podem operar na cópia do runner
  em vez da fixture. A receita com as duas variáveis desarmadas passou, sem alterar o Check externo.
