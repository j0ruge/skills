# R21 — Retomada e documentação da revisão externa

Quatro casos foram reproduzidos no SHA publicado `677b798`. A revisão de R20 já tratou
o item nulo em `retired_skill_calls`. O R21 fecha os demais cenários sem alterar escopo ou versão.

- `4725193741`. Use a regra de campo ausente quando `slash_prior_calls` vier com tipo inválido.
  Preserve o slash pendente e o progresso do offset.
- `4725193751`. Um caminho externo sem ID válido mantém o tratamento conservador da atribuição,
  mas só uma carga vinculada e comprovadamente posterior aposenta o slash. Preserve os controles de R14.
- `4725193755`. Ignore `text` que não seja string antes da regex e de `user_text`, no delta e no replay.
  Campos válidos do mesmo bloco e chamadas novas continuam produzindo eventos.
- `4725193761`. A 0.4.0 pode salvar o offset sem ler o delta em `stop_hook_active`. Se o prefixo
  tiver donos distintos compatíveis com a mesma atribuição salva, conserve o crédito persistido e
  evite substituir a origem, a chamada ativa ou a prova de ordem por um candidato ambíguo.
  Recupere a origem nos controles em que o prefixo identifica um dono único. Limite o estado
  auxiliar ao necessário para distinguir unicidade de ambiguidade. Preserve os contadores.
- `4725193725`, `4725193728`, `4725193730` e `4725193733`. Isole o ambiente antes de ler o Git
  nas receitas históricas de r14, r15 e r19. Em r19, diga explicitamente que `check` recebe
  a célula à esquerda da seta. Use controles com o Git roteado para uma fixture.
- `4725193735`. Use caminho portátil para o scanner nos relatórios r24 a r27.
  Preserve as contagens e os SHAs históricos.
- `4725193738` e `4725193745`. A evidência compartilhada do P2 está na r29 e no R20.
  A guarda de fonte válida em `41f2952` corrigiu a correspondência com null. Verifique o
  comportamento na mesma regressão antes de tratar as threads.

Faça TDD nos quatro caminhos de Stop, com controles positivos e negativos da 0.4.0 e da versão atual.
Agrupe a verificação no R21 e preserve os 22 Checks anteriores. Rode F1 e as provas nativas no host.

~~~python
import json
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from test_retrofit_watch import StopTest, identified_load, skill_typed, tool


def run(case, legacy):
    t = StopTest()
    t.setUp()
    try:
        w = t.w
        ours = identified_load("codereview:coderabbit-pr", w.mkt_skill, "msg_own", "toolu_own")
        other = identified_load("superpowers:brainstorming", w.other_skill, "msg_other", "toolu_other")
        slash = skill_typed("graphify", w.graphify)
        if case == "slash_list":
            t.write(other, slash[:1], compact=True)
            assert t.run_hook() is None
            path = w.data / "sessions/s1.json"
            state = json.loads(path.read_bytes())
            state["slash_prior_calls"] = None
            path.write_text(json.dumps(state), encoding="utf-8")
            unused = identified_load("irrelevante", w.other_skill, "msg_unused", "toolu_unused")
            t.write(unused[:2], slash[1:], tool(error=True), compact=True)
        elif case == "slash_unlinked":
            del other[2]["sourceToolUseID"]
            t.write(other[:2], slash[:1], other[2:], slash[1:], tool(error=True), compact=True)
        elif case == "null_replay":
            t.write([{"type": "assistant", "message": {"content": [{"type": "text", "text": None}]}}],
                    compact=True)
            assert t.run_hook(script=legacy) is None
            t.write(ours, tool(error=True), compact=True)
        elif case in ("skipped_owner", "unique_owner"):
            t.write(ours, compact=True)
            assert t.run_hook(script=legacy) is None
            failed = ours
            if case == "skipped_owner":
                failed = identified_load("codereview:coderabbit-pr", w.mkt_skill, "msg_new", "toolu_new")
                t.write(failed, compact=True)
                assert t.run_hook(script=legacy, active=True) is None
                saved = json.loads((w.data / "sessions/s1.json").read_bytes())
                assert saved["offset"] == w.transcript.stat().st_size
            failed[1]["message"]["content"][0]["is_error"] = True
            t.write(failed[1:2], tool(error=True), compact=True)
        else:
            raise AssertionError(case)
        out = t.run_hook()
        if (w.data / "errors.log").exists():
            return "erro"
        if out is None:
            return "silêncio"
        return re.search(r"/retrofit-skill:retrofit-skill ([a-z-]+)", t.context_of(out))[1]
    finally:
        t.tearDown()


name = "plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py"
with TemporaryDirectory() as tmp:
    old = Path(tmp) / "legacy.py"
    old.write_bytes(subprocess.check_output(["git", "show", f"7e623fe:{name}"]))
    assert run("unique_owner", old) == "silêncio"
    for case in ("slash_list", "slash_unlinked", "null_replay", "skipped_owner"):
        print(f"{case}={run(case, old)}")
~~~
