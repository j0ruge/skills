---
missao: 20261125-retrofit-watch-atribuicao
data: 2026-11-25
---

# Plano — Corrigir a atribuição da retrofit-watch na mesma mensagem

## Contexto verificado (não re-descobrir)

Executar da raiz do worktree. Nos comandos abaixo, `P=plugins/retrofit-watch`, `S=$P/skills/retrofit-watch`, `R=$S/scripts/retrofit_watch.py` e `T=$S/tests/test_retrofit_watch.py`.

- `git branch --show-current` → `fix/retrofit-watch-atribuicao-mesma-mensagem`. `git rev-parse --short HEAD` → `e45db9e`. `git status --porcelain` → saída vazia. `rg -n 'DEFAULT_BRANCH|OUTPUT_LANG|JIRA_ENABLED|TEST_CMD' .sdd/config.sh` → base `main`, idioma `pt-BR`, Jira desligado e descoberta explícita de `test_retrofit_watch.py`.
- `rg -n 'mesma mensagem|mesmo .message.id' TODO.md` → item da atribuição em `TODO.md:90` e direção em `TODO.md:95`. `rg -n 'retrofit_watch.py' TODO.md` → âncoras de `AUTO_MODES` e `_watch`. A campanha exige o controle da mensagem posterior em `docs/campaigns/20261125-loja-skills/campaign.md` e reserva a aprovação e o merge ao mantenedor.
- `rg -n 'def (_watch|invocation|skill_path|entry|scan|eligible|cmd_stop)\(|setdefault\(key, default\)|scanner.scan\(chunk\)' "$R"` → `421, 479, 556, 570, 582, 626, 640, 824, 870`. `sed -n '479,492p;556,625p' "$R"` mostra os dois caminhos de perda. `invocation` limpa `current` para plugin externo instalado. `skill_path` chama `_watch(None)` para caminho externo, que também limpa `current`. `entry` processa a chamada e o texto `Base directory` sem associar os respectivos IDs. Corrigir só um caminho deixa o outro apagar o alvo.
- `sed -n '399,431p;449,462p;824,837p;865,884p' "$R"` → `State` carrega JSON por sessão, completa chaves ausentes com `setdefault` e salva por substituição atômica. `cmd_stop` lê do offset salvo até a última linha completa e cria um `Scanner` para o delta. A atribuição atual e os contadores vivem no estado. A identidade da mensagem que originou a carga não consta entre os campos inicializados na 0.4.0.
- `rg -n 'def (skill_via_tool|tool\(|run_hook\(|test_two_skills_in_one_turn|test_third_party_skill_after_ours)' "$T"` → `142, 163, 295, 390, 397`. `sed -n '142,152p;285,319p;390,405p' "$T"` → `skill_via_tool` produz chamada, resultado e metadado, reutiliza `toolu_s` e omite `message.id`. O teste de terceiro existente prova o encerramento sem correlação. `HookHarness.run_hook` chama o script em subprocesso e devolve o JSON ou `None`. Conservar esse teste como controle independente.
- `PYTHONPATH=plugins/retrofit-watch/skills/retrofit-watch/tests python3 -B -m unittest test_auto_docs.ReleaseTest.test_the_four_places_agree_at_0_4_0_or_later` → `Ran 1 test`, `OK`. `rg -n 'def test_the_four_places_agree' "$S/tests/test_auto_docs.py"` → linha `368`. O teste compara manifesto, `metadata.version`, catálogo Claude, linha do README e primeira entrada do CHANGELOG. `rg -n '"version"' "$P/.claude-plugin/plugin.json"` → `7:  "version": "0.4.0",`. `rg -n 'última skill carregada' "$S/SKILL.md"` → linha `148`, a explicação vigente que precisa da exceção.
- O Check de I1 executado no HEAD com o plano em memória imprimiu `0 0 0 0 0 1`. Um `1` exige saída com o comando para `codereview`. Um `0` exige `None`. Saída para um alvo inesperado causa falha. Para PLAN usamos o `cmd_stop`, os construtores reais `skill_via_tool` e `tool`, o leitor de deltas, o carregamento dos defaults de `State` e o gerador de saída. A persistência física foi substituída por uma cópia JSON em memória. A execução com subprocessos e arquivo de estado real pertence ao teste durável de EXEC.

## Arquitetura da mudança

Manter o processamento incremental em `Scanner.entry`. Na chamada `Skill`, extrair o `message.id` do registro do assistente e o `id` do bloco `tool_use`. Uma carga pode estar em um bloco entre vários ou em um registro separado com o mesmo `message.id`. Na linha de metadados, resolver `sourceToolUseID` por aquela chamada. O `tool_result` pode chegar antes do `isMeta`, portanto o resultado sozinho não encerra a necessidade da correlação.

Guardar no estado da sessão a origem da atribuição vigente e os vínculos ainda necessários para completar cargas entre deltas. Usar campos JSON opcionais com defaults compatíveis com o padrão de `State`. Manter o registro mínimo, por sessão, descartando vínculos consumidos ou obsoletos. Não usar o último ID visto, posição no arquivo, proximidade temporal ou o caminho da skill como substitutos da identidade da chamada.

Aplicar a mesma decisão na classificação por nome e por caminho. Ao reconhecer uma monitorada, conservar a seleção e a contagem existentes e registrar sua origem confiável. Ao reconhecer a externa, preservar a monitorada vigente somente se as origens corresponderem à mesma mensagem. Origem posterior, ausente, inválida ou ambígua mantém a regra conservadora de hoje. Metadado atrasado não deve reativar uma atribuição já encerrada por mensagem posterior. Encerrar `current` atua sobre o trabalho futuro e preserva o trabalho já creditado. Manter os caminhos de slash digitado, plugin só de comandos, kits, múltiplas monitoradas e execução de `/retrofit-skill` conforme as regras existentes.

## Incrementos

### I1 — Corrigir a atribuição e entregar a 0.4.1

**Onde.** Lógica em `plugins/retrofit-watch/skills/retrofit-watch/scripts/retrofit_watch.py`. Testes em `plugins/retrofit-watch/skills/retrofit-watch/tests/test_retrofit_watch.py`. Usar um único incremento para que a versão distribuída corresponda ao comportamento testado.

**TDD e sensor durável.** Em `StopTest`, usar `World`, `HookHarness.write`, `run_hook` e os construtores existentes. Para os novos casos, preencher `message.id` e IDs de chamada distintos, consistentes no `tool_use`, no `tool_result` e em `sourceToolUseID`. Preservar as fixtures antigas sem IDs. Carregar `codereview:coderabbit-pr` de `w.mkt_skill`, carregar `superpowers:brainstorming` de `w.other_skill` e só então acrescentar `tool(error=True)`. Exigir o comando completo para `codereview` em `additionalContext` ou `assertIsNone` para silêncio. Cada cenário começa com sessão isolada.

1. Medir o par com IDs iguais e distintos em leitura contínua. Repetir nas duas chamadas de Stop. Para a retomada, gravar até o `tool_result` externo inclusive, chamar Stop sem trabalho elegível, acrescentar o `isMeta` externo e o trabalho, chamar Stop de novo. Só os dois positivos da mesma mensagem devem falhar antes da correção. Incluir uma disposição em que as duas chamadas aparecem antes dos metadados para exercitar o vínculo por ID.
2. Exercitar o fallback com `sourceToolUseID` ausente ou sem correspondência. Para a compatibilidade, preparar JSON válido no formato antigo em `w.data/sessions/s1.json`, com offset no corte, monitorada em `current`, `skills` e contadores conhecidos, sem as chaves novas. Retomar com o metadado externo e o trabalho. Conferir o silêncio, o avanço do offset e a preservação dos dados antigos. O cenário deve falhar se o código simplesmente descartar o estado ao encontrar o formato anterior.
3. Corrigir os dois caminhos descritos acima e repetir os controles. Rodar a suíte de atribuição inteira para cobrir slash, plugin só de comandos, kits, supressão, múltiplas monitoradas e leitura parcial. O teste permanente usa a persistência real do plugin. A sonda do plano abaixo serve para repetir a medição inclusive antes de qualquer edição.
4. Sincronizar `plugins/retrofit-watch/.claude-plugin/plugin.json`, `plugins/retrofit-watch/skills/retrofit-watch/SKILL.md` (`metadata.version` e a frase sobre a última carga), apenas o bloco da retrofit-watch em `.claude-plugin/marketplace.json`, a linha da versão em `README.md` e uma entrada `[0.4.1]` em `plugins/retrofit-watch/CHANGELOG.md`. Manter a entrada histórica `[0.4.0]`. O teste de release já aceita patches posteriores. No backlog, conferir a âncora de `_watch` após a edição e manter o rastreio do item #12 pelo ciclo `RESOLVED by <hash>` descrito em `TODO.md`, usando o hash real quando disponível. Na fase DOCS, registrar o resultado medido no `KAIZEN_LOG.md` com o ID da missão.

**Check executável.** Da raiz, executar a célula de I1 em `checkpoint.md`. Ela lê o bloco Python abaixo do plano materializado. `L1_PLAN` é opcional e permite a mesma leitura de um rascunho em memória no Linux. A ordem da saída é: mesma mensagem contínua, posterior contínua, mesma mensagem retomada, posterior retomada, estado antigo sem vínculo, monitorada sozinha. Esperado `1 0 1 0 0 1`. Antes da correção `0 0 0 0 0 1`.

No quinto caso, a chamada externa não tem `message.id` válido. Seu `sourceToolUseID` aponta
para a chamada, mas o prefixo não comprova que ela veio da mesma mensagem.

~~~python
import json
import os
from contextlib import ExitStack
from unittest.mock import patch
from test_retrofit_watch import rw, skill_via_tool, tool

def load_skill(ctx, name, path, message_id, call_id):
    rows = skill_via_tool(name, ctx.home / '.claude/plugins/cache' / path)
    call, result, meta = rows
    call['message']['id'] = message_id
    call['message']['content'][0]['id'] = call_id
    result['message']['content'][0]['tool_use_id'] = call_id
    meta['sourceToolUseID'] = call_id
    return rows

def measure(second_id=None, split=False, legacy=False):
    ctx = rw.Context(home='/fixture/home', data_dir='/fixture/data')
    ctx._installed = {'codereview': {rw.MARKETPLACE}, 'superpowers': {'claude-plugins-official'}}
    rows = load_skill(ctx, 'codereview:coderabbit-pr', 'chewiesoft-marketplace/codereview/2.0.0/skills/coderabbit-pr', 'm1', 'u1')
    if second_id:
        rows += load_skill(ctx, 'superpowers:brainstorming', 'claude-plugins-official/superpowers/6.4.1/skills/brainstorming', None if legacy else second_id, 'u2')
    rows += tool(error=True)
    chunks = (rows[:5], rows[5:]) if split else (rows,)
    snapshot = {}
    def save(state):
        snapshot.clear()
        snapshot.update(json.loads(json.dumps(state.data)))
    with os.fdopen(os.memfd_create('transcript'), 'wb') as stream:
        payload = dict(session_id='s1', transcript_path=f'/proc/self/fd/{stream.fileno()}', last_assistant_message='Feito.')
        for index, chunk in enumerate(chunks):
            for row in chunk:
                stream.write((json.dumps(row) + '\n').encode())
            stream.flush()
            with ExitStack() as io:
                for obj, attr in [(rw.Path, 'mkdir'), (rw, '_lock'), (rw, '_unlock')]:
                    io.enter_context(patch.object(obj, attr))
                io.enter_context(patch.object(rw.Path, 'read_text', return_value=json.dumps(snapshot)))
                io.enter_context(patch.object(rw.State, 'save', save))
                io.enter_context(patch.dict(os.environ, RETROFIT_WATCH='force'))
                out = rw.cmd_stop(payload, ctx)
            if split and index == 0:
                assert out is None and snapshot['offset'] == stream.tell()
                if legacy:
                    snapshot = {k: snapshot[k] for k in ('offset', 'skills', 'current', 'classified', 'pending', 'done')}
                    snapshot['current'] = 'full:codereview'
    if out is None:
        return 0
    assert '/retrofit-skill:retrofit-skill codereview' in out['hookSpecificOutput']['additionalContext']
    return 1

print(measure('m1'), measure('m2'), measure('m1', True), measure('m2', True), measure('m1', True, True), measure())
~~~

**Verificação do checkpoint antes da aprovação.** Após a materialização pelo relay e ainda no HEAD anterior à correção, executar da raiz:

~~~bash
checkpoint=docs/handoffs/20261125-retrofit-watch-atribuicao/checkpoint.md
kit=/home/joruge/repos/sdd_agents
bash "$kit/tests/check-checkpoint.sh" --check "$checkpoint"
bash "$kit/tests/check-checkpoint.sh" --red "$checkpoint"
~~~

Ambos os comandos retornaram rc 0 no worktree em `e45db9e`. O `--red` executou I1 e confirmou o vetor observado `0 0 0 0 0 1`, diante do esperado `1 0 1 0 0 1`. A aprovação continua em branco.

**Reversão.** Reverter o commit de I1 desfaz a lógica, os testes novos e o patch da loja em conjunto. O leitor da 0.4.0 carrega o dicionário de estado e consulta suas chaves conhecidas. Manter o significado e o tipo das chaves antigas para permitir essa volta.

## Riscos e não-feitos

| Risco | Probabilidade | Mitigação |
|---|---|---|
| Preservar a monitorada também após carga externa posterior | Média | O segundo e o quarto resultados do Check exigem `None`. Ambos produziram `0` no HEAD. |
| Perder a correlação no intervalo entre Stops | Alta no defeito atual | A terceira posição do Check imprimiu `0`; a meta é `1`. O teste durável repete o corte com dois subprocessos e o mesmo estado em disco. |
| Reinterpretar dados legados como prova de mesma mensagem | Média | A quinta posição imprimiu `0` com `current` preenchido e sem vínculo. Cobrir em EXEC a leitura do arquivo antigo e a integridade dos contadores. |
| Uma versão ficar divergente na loja | Baixa | O teste `ReleaseTest.test_the_four_places_agree_at_0_4_0_or_later`, executado no comando do contexto verificado, passou na 0.4.0. Repeti-lo na 0.4.1 e conferir o valor escolhido. |

## Verificação end-to-end

Depois de implementar, a célula de I1 deve imprimir exatamente `1 0 1 0 0 1`. Em ambiente de execução com diretório temporário gravável, rodar `python3 -m unittest discover -s plugins/retrofit-watch/skills/retrofit-watch/tests -p 'test_retrofit_watch.py' -v` e confirmar a execução dos novos casos. Repetir o teste de release identificado acima e conferir que o manifesto declara `0.4.1`. Por fim, executar `bash -c 'source .sdd/config.sh && eval "$TEST_CMD"'` da raiz e exigir rc 0. Falha de controle, de compatibilidade ou da suíte mantém I1 aberta. Após o commit, registrar o hash curto nu no checkpoint.
