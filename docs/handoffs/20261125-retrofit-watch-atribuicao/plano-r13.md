# R13 — Achados externos do PR #13

A revisão externa em `43e4686` trouxe um P2 do Codex e apontamentos do CodeRabbit.
O aceite é fechar os achados com prova no Stop real e manter as garantias de I1 a R12.

- Codex `4724314597`. Se o `tool_result` falho pertencer à origem ativa, invalidar a atribuição dessa carga. Preservar vínculos pendentes independentes e as evidências de colisão. Uma carga bem-sucedida na mesma mensagem continua recebendo crédito.
- CodeRabbit `4724097387`. Só ignore metadado externo antigo quando houver prova de que o ID foi aposentado por uma mensagem posterior. Limite a memória, preserve o encerramento conservador para IDs desconhecidos e mantenha a segurança no reuso de IDs. O item correspondente já consta no TODO. Use `RESOLVED by` com a prova e revise as citações atuais.
- CodeRabbit `4724097393` e `4724097398`. Uma tentativa irrelevante não apaga o slash explícito. Pule blocos não-dicionário em `isMeta`, preservando os demais blocos válidos, tanto no delta quanto na migração do prefixo.
- CodeRabbit `4724097382`. O teste de ponta a ponta prova que o primeiro Stop observou `full:codereview` e encerrou a atribuição antes do segundo Stop. Preserve a saída histórica de F1.
- CodeRabbit `4724097353`, `4724097357`, `4724097362`, `4724097366`, `4724097371` e `4724097376`. Fixe a revisão legada no reporte r1, isole o roteamento Git antes de ler os blobs históricos e explicite a célula do checkpoint que preenche `check` na r18. Resolva o caminho do kit no comando de validação de `45-docs.md`. Preserve os campos de evidência histórica.

Implemente em TDD nas fixtures permanentes do hook. Cubra continuidade, retomada, estado salvo e dois controles negativos distintos.
A sonda abaixo falhou no HEAD. Use a menor alteração que resolva os casos completos, como orienta a Ponytail.
Repita o TEST_CMD, todos os Checks anteriores, F1 em processo real e as três provas nativas no host.

~~~python
import re

from test_retrofit_watch import StopTest, identified_load, skill_typed, tool


def validate(case, resumed):
    test = StopTest()
    test.setUp()
    try:
        world = test.w
        ours = identified_load("codereview:coderabbit-pr", world.mkt_skill, "msg_local", "toolu_own")
        other = identified_load("superpowers:brainstorming", world.other_skill, "msg_other", "toolu_other")
        if case in ("failed", "loaded"):
            other[0]["message"]["id"] = "msg_local"
            if case == "failed":
                ours[1]["message"]["content"][0]["is_error"] = True
                first, second = ours[:2], other
            else:
                first, second = ours, other
        elif case in ("retired", "unknown"):
            if case == "unknown":
                other[2]["sourceToolUseID"] = "toolu_unknown"
            first, second = other[:2] + ours, other[2:]
        elif case == "slash":
            direct = skill_typed("graphify", world.graphify)
            unrelated = identified_load("irrelevante", world.other_skill, "msg_unknown", "toolu_unused")
            first, second = other + tuple(direct[:1]) + unrelated[:2], direct[1:]
        elif case == "malformed":
            ours[2]["message"]["content"].insert(0, None)
            first, second = ours[:2], ours[2:]
        else:
            raise AssertionError(case)
        test.write(first, compact=True)
        if resumed:
            assert test.run_hook(mode="plan") is None
        test.write(second, tool(error=True), compact=True)
        result = test.run_hook()
        if (world.data / "errors.log").exists():
            return "erro"
        if result is None:
            return "silêncio"
        match = re.search(r"/retrofit-skill:retrofit-skill ([a-z-]+)", test.context_of(result))
        assert match
        return match[1]
    finally:
        test.tearDown()


for name in ("failed", "loaded", "retired", "unknown", "slash", "malformed"):
    print(f"{name}=" + ",".join(validate(name, resumed) for resumed in (False, True)))
~~~
