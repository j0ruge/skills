# Changelog — retrofit-watch

## [0.1.1] — 2026-09-30

### Fixed

- **Pitfall contornado sem erro de ferramenta não disparava a retro.** No E2E com a cópia
  instalada, a skill de teste apontava para um arquivo inexistente. O Claude verificou antes de
  ler, achou o arquivo certo por `find` e terminou com trabalho = 4 e atrito = 0: nenhum
  `is_error`, abaixo do limiar de 5. O pitfall mais comum (instrução errada, contornada com
  elegância) passava em branco. Agora o texto do assistente que narra o desvio, com a skill
  vigiada ativa, conta como atrito: `não existe`, `em vez de`, `not in the expected location`,
  `instead of` e afins (`DEVIATION_RE`). Com a mudança, o mesmo prompt produziu a retro com a
  lição e a oferta do `/retrofit-skill`.
- 2 testes novos (narração de desvio conta; narração comum não conta), 30 no total. A mutação
  que remove o sinal é pega pelo teste novo.

### Como reverter

`git revert` deste commit. O limiar volta a depender só de erro de ferramenta, interrupção e
correção do usuário.

## [0.1.0] — 2026-09-30

Primeira versão. Um Stop hook percebe quando uma skill nossa trabalhou na sessão e pede ao
Claude a retro dela, com evidência, oferecendo o `/retrofit-skill`.

### Por que existe

Até aqui, a melhoria das skills dependia de o usuário lembrar, no fim de cada sessão, de pedir a
análise e depois o retrofit. Quando ele não pedia, o pitfall da sessão se perdia. Com o hook, a
retro é puxada pelo processo, no turno em que a evidência ainda está no contexto. O retrofit
continua exigindo confirmação.

### Added

- `hooks/hooks.json`:
  - `Stop` → `retrofit_watch.py stop`;
  - `SessionStart` (`resume|fork`) → `retrofit_watch.py baseline`, para que o histórico copiado
    de um fork não dispare.
- `skills/retrofit-watch/scripts/retrofit_watch.py` (stdlib, com git):
  - **detecção:** lê o transcript por offset e reconhece a carga de skill pela entrada
    `isMeta` `Base directory for this skill:`, tanto na chamada pelo Skill tool quanto no
    `/skill` digitado; o plugin só de comandos é reconhecido pelo nome;
  - **classificação:** full (marketplace, com o argumento igual ao **nome do plugin**) × lean
    (skill rastreada no git de um repo de `j0ruge`/`JRC-Brasil`/`chewiesoft`) × ignora
    (terceiros, `skills-lock.json`, `.agents/skills`, `~/.hermes`, fora do git);
  - **disparo:** adia quando o turno espera o usuário; teto de 2 retros por skill por sessão;
    fica calado em sessão desassistida e na continuação do próprio Stop;
  - **segurança:** nunca grava texto do assistente e nunca derruba a sessão.
- `skills/retrofit-watch/SKILL.md`: como o hook decide, o procedimento da retro e o uso sob
  demanda (`/retrofit-watch:retrofit-watch <skill>`).
- `skills/retrofit-watch/references/criteria.md`: sinais, filtro de evidência, triagem
  skill × projeto × terceiro, auto-audit de segredos e formato do bloco. Adaptado da
  `self-learning` (kulaxyz, MIT) e do loop "Lições" de um agente de propostas de
  um projeto interno.
- `skills/retrofit-watch/tests/test_retrofit_watch.py`: 28 testes com HOME fixture, repos git e
  transcripts sintéticos no formato real. Nove mutações do script (teto, filtro `isMeta`,
  adiamento, guarda de `stop_hook_active`, `.agents`, lock, gate de sessão desassistida,
  supressão pós-retrofit, adiamento em pergunta) são pegas pelo teste certo.

### Decisões

- **`additionalContext` no Stop, e não `decision: "block"`:** a doc indica essa forma quando o
  hook está funcionando como projetado e dá orientação. Aparece como "Stop hook feedback", e o
  `block` apareceria como "hook error" a cada retro.
- **Uma leitura do transcript, e não `PostToolUse(Skill)` + `UserPromptExpansion` +
  `PostToolUseFailure`:** o transcript cobre os dois caminhos de invocação, traz o path e dá o
  atrito sem um processo extra por chamada.
- **Pitfall sem solução entra na retro,** marcado "sem correção verificada", e a proposta é
  investigar antes do retrofit. O E2E mostrou o motivo: com o filtro antigo, que exigia "o que
  resolveu", uma skill que apontava para um arquivo inexistente saiu como "sem lições novas".
  O caso mais grave era justamente o que ficava de fora.
- **Gate de sessão desassistida por `CLAUDE_CODE_SESSION_ATTENDED`:** vale `1` na sessão
  interativa e `0` no `claude -p`, com fallback em `CLAUDE_CODE_ENTRYPOINT` (`cli` ×
  `sdk-cli`). As duas foram observadas na 2.1.283 e não são documentadas.

### Como reverter

Desabilite o plugin, ou use `RETROFIT_WATCH=off` para desligar sem desinstalar. `git revert` do
commit remove o plugin. O estado fica em `${CLAUDE_PLUGIN_DATA}` e sai no uninstall.
