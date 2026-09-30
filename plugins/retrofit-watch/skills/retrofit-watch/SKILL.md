---
name: retrofit-watch
description: "Stop hook that notices when one of our skills (j0ruge/skills marketplace or a git-tracked project skill) did real work in the session and asks Claude for an evidence-backed retro that offers /retrofit-skill; also runs the retro on demand. Triggers — skill retro, retrofit-watch, session lessons, skill pitfalls, skill improvement, retrofit reminder."
license: MIT
compatibility: Claude Code 2.1.163+ (Stop additionalContext); testado na 2.1.283 em 2026-09-30. Hook em Python 3, só biblioteca padrão, e git no PATH.
metadata:
  author: JorUge
  version: "0.1.1"
---

# retrofit-watch

Sem este plugin, a melhoria de uma skill depende de alguém lembrar, no fim da sessão, de
pedir a análise e o `/retrofit-skill`. Com ele, um **Stop hook** percebe que uma skill nossa
trabalhou e pede ao Claude a retro dela ali mesmo, enquanto a evidência ainda está no contexto.
Se houver lição, o Claude pergunta se roda o `/retrofit-skill:retrofit-skill <alvo>`, e basta um
"sim".

O hook não edita nada, não commita e não roda o retrofit. Ele só pede a retro. O retrofit
continua exigindo a sua confirmação.

## Como o hook decide

1. **Detecta a skill.** Em cada Stop, lê só as linhas novas do transcript. A carga de uma skill
   deixa uma entrada `isMeta` com `Base directory for this skill: <path>`, tanto quando o
   Claude chama a skill quanto quando você digita `/skill`. Plugin só de comandos é
   reconhecido pelo nome `plugin:comando`.
2. **Classifica o dono** pelo `realpath` do path:

   | Origem | Modo | Argumento do retrofit |
   |---|---|---|
   | cache ou clone do `chewiesoft-marketplace` (j0ruge/skills), inclusive por symlink e worktree | full | o **nome do plugin** (`codereview:coderabbit-pr` → `codereview`) |
   | skill rastreada no git de um repo cujo `origin` é de `j0ruge`, `JRC-Brasil` ou `chewiesoft` | lean | o nome da skill |
   | `skills-lock.json`, `.agents/skills`, `~/.agents`, `~/.hermes`, outro marketplace, origin de terceiro, fora do git | ignora | — |

   Ficam sempre de fora `retrofit-skill`, `retrofit-watch` e a família `skill-quality-audit`.
3. **Conta os sinais** desde a carga, para a skill vigiada carregada por último:
   - **trabalho:** chamadas de ferramenta;
   - **atrito:** erro de ferramenta, interrupção, prompt seu com cara de correção ("não…",
     "errado", "na verdade", "de novo"), ou o próprio Claude narrando que a realidade não bate
     com a instrução ("não existe", "em vez de", "not in the expected location"). Este último é o
     pitfall contornado **sem** erro de ferramenta.
4. **Adia** quando o turno terminou esperando você (pergunta, `AskUserQuestion`,
   `ExitPlanMode`, plan mode).
5. **Pede a retro:**
   - na 1ª vez, com atrito ≥ 1, ou com trabalho ≥ 5 se não houve atrito;
   - na 2ª vez, com atrito ≥ 2 desde a anterior;
   - **no máximo 2 retros por skill por sessão**, e várias skills entram num pedido só.

   O pedido chega ao Claude como "Stop hook feedback" e a você como um aviso de uma linha.
6. **Cala:**
   - em sessão desassistida (`claude -p`, cron, missão);
   - numa continuação que o próprio Stop hook pediu (`stop_hook_active`);
   - depois que o `/retrofit-skill` rodou para aquela skill.

## Quando a retro for pedida (ou sob demanda)

Ao fazer a retro, leia `references/criteria.md`: sinais, filtro de evidência, triagem
skill × projeto × descarte, auto-audit de segredos e o formato do bloco. Em resumo:

1. **Levante as lições** desta sessão que caibam no escopo da skill:
   - **pitfall:** uma instrução da skill falhou ou estava errada (path, flag, ordem), ou faltou
     um aviso;
   - **melhoria:** faltou passo, gatilho ou exemplo.
2. **Mantenha só o que tem evidência.** Cada lição precisa ter o comando ou erro observado e o
   padrão de falha que a skill passaria a evitar. Palpite não entra.
3. **Diga o que resolveu.** Se nada resolveu, a lição **fica**, marcada "sem correção
   verificada". Uma instrução quebrada é o pitfall mais importante, e a tarefa ter falhado não é
   motivo para calar.
4. **Separe a lição que só vale neste projeto.** Ela vai para memória ou `CLAUDE.md` e não
   entra na skill.
5. **Responda no formato certo:**
   - sem lição: uma linha só, `retro <skill>: sem lições novas`;
   - com lição: o bloco "Retro", terminando com a pergunta
     `Rodo /retrofit-skill:retrofit-skill <alvo>?`;
   - com pitfall sem correção verificada: proponha investigar e verificar a correção antes do
     retrofit.
6. **Não execute o retrofit** sem o "sim". Nunca cite valor de segredo.

**Sob demanda:** `/retrofit-watch:retrofit-watch <skill>` faz a mesma retro sem esperar o hook.
Sem argumento, faz a retro de cada skill nossa usada na sessão.

## Controle

| Quer | Como |
|---|---|
| desligar | `RETROFIT_WATCH=off` no ambiente, ou desabilitar o plugin |
| testar em `claude -p` | `RETROFIT_WATCH=force` |
| mudar donos, incluir ou excluir skills | `~/.claude/retrofit-watch.json`: `{"owners": [...], "include": ["skill"], "exclude": ["plugin-ou-skill"], "deny_roots": ["~/x"]}` |
| ver o que aconteceu | `${CLAUDE_PLUGIN_DATA}/metrics.jsonl` (resultado de cada retro: `none`/`lessons`) e `errors.log` |

O estado fica em `${CLAUDE_PLUGIN_DATA}/sessions/<session_id>.json` e é apagado depois de
14 dias. O texto do assistente nunca é gravado.

## Gotchas e limites conhecidos

- **Skill usada dentro de subagente** não é vista: ela não aparece no transcript principal.
- **O gate de sessão desassistida** usa `CLAUDE_CODE_SESSION_ATTENDED` e
  `CLAUDE_CODE_ENTRYPOINT`, observadas na 2.1.283 mas não documentadas. Se uma versão nova
  mudar isso, o hook passa a pedir retro também em `-p`. Confira com o probe da skill
  `hook-builder`.
- **Skill local fora do git** (por exemplo `~/.claude/skills/<x>` sem repo) é ignorada, porque
  o retrofit lean commita no repo da skill. Versione a skill, ou ponha no `include`, sabendo
  que o retrofit não terá onde commitar.

## Arquivos

| Arquivo | Para quê |
|---|---|
| `references/criteria.md` | ao fazer a retro: critérios, triagem, formato e exemplos |
| `scripts/retrofit_watch.py` | o hook (`stop` e `baseline`). O plugin o registra no `hooks/hooks.json` da raiz, que o formato de plugin exige |
| `tests/test_retrofit_watch.py` | 30 testes: classificação e gatilho (`python3 tests/test_retrofit_watch.py`) |
