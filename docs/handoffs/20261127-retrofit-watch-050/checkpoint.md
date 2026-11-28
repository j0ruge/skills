---
missao: 20261127-retrofit-watch-050
atualizado: 2026-11-28 04:15
---

# Checkpoint — Skills locais da lista

| ID | Incremento | Check (comando → esperado) | Status | Commit |
|---|---|---|---|---|
| I1 | Elegibilidade e janela v2 | `TMPDIR=/var/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_fixture_private test_lean_auto test_lean_window >/dev/null; echo $?` → `0` | done | d929f44 |
| I2 | Clone dedicado e lote selado | `TMPDIR=/var/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_lean_live test_lean_batch >/dev/null; echo $?` → `0` | done | 785c388 |
| I3 | Porta, startup e retro manual | `TMPDIR=/var/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests:plugins/retrofit-skill/tests python3 -B -m unittest test_lean_gate test_lean_live.StartupTest test_auto_docs.PrivateFlowTest test_modo_autonomo.PrivateFlowTest >/dev/null; echo $?` → `0` | done | ff7025b |
| I4 | Versões e distribuição | `export TMPDIR=/var/tmp PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests:plugins/retrofit-skill/tests; if python3 -B -m unittest test_auto_docs.ReleaseTest.test_lean_release_in_fixture >/dev/null; then python3 -Bc 'import json; print(*(json.load(open(f"plugins/{p}/.claude-plugin/plugin.json"))["version"] for p in ("retrofit-watch","retrofit-skill")))'; else echo falhou; fi` → `0.5.0 0.12.0` | done | 04a1a77 |

Atualizar a linha depois do commit do incremento, com SHA curto nu. As notas de execução seguem em `checkpoint-notas.md` quando o relay materializar o layout do kit.

## Incrementos de fix (QA e REVIEW)

QA acrescenta `F<n>` com regressão e repetição da jornada impactada. REVIEW acrescenta `R<n>` para correções acionáveis segundo o contrato do kit. Cada correção volta ao EXEC com seu próprio Check.
