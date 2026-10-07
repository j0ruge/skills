# Padrões de hook

Cada padrão diz qual evento usa, qual canal de saída e o que costuma dar errado. Os exemplos
oficiais citados estão em https://github.com/anthropics/claude-plugins-official/tree/main/plugins
(`ralph-loop`, `security-guidance`, `explanatory-output-style`), consultados em 2026-09-30.

## Conteúdo

1. Contexto no início da sessão
2. Gate antes da ferramenta
3. Reação a falha de ferramenta
4. Gate de `/comando` digitado
5. Revisão no fim do turno com estado (o mais delicado)
6. Revisão em background com `asyncRewake`
7. Sessão assistida × desassistida

## 1. Contexto no início da sessão

- **Evento e saída:** `SessionStart` com matcher `startup|resume|clear|compact`. Stdout em texto
  puro já vira contexto; em JSON, use `hookSpecificOutput.additionalContext`.
- **Quando atualizar:** no `resume`, o hook roda de novo. É o momento de atualizar um valor que
  envelhece, como branch ou SHA.
- **Exemplo oficial:** o `explanatory-output-style` faz só isso.
- **Erro comum:** colocar aqui uma regra que nunca muda. Ela vai no `CLAUDE.md`.

## 2. Gate antes da ferramenta

- **Evento:** `PreToolUse` com matcher na ferramenta e `if` para o argumento (`Bash(git push *)`).
- **Saída:** exit 2 com o motivo no stderr, ou `permissionDecision: "deny"` com
  `permissionDecisionReason`. Nos dois casos o Claude recebe o motivo.
- **Não é fronteira de segurança.** Aspas, pipes, `$()`, interpretadores e wrappers passam por
  filtro de substring. O `if` é best-effort. Para deny rígido, use `permissions.deny`, e o hook
  só complementa.
- **Falha fecha quando o escopo é estreito:** exceção no script sai com exit 2. Com matcher
  largo (todo `Bash`), uma exceção no parser trava a ferramenta inteira; se o dano evitado é
  menor que isso, o gate falha **aberto** (exit 0 e registro em log) e bloqueia só na detecção
  positiva. Timeout **não** bloqueia (a ferramenta segue), então mantenha o gate rápido.
- **Gate sobre o texto do comando Bash** (medido num gate de `mineru parse -o` em 2026-10-07):
  - conte o binário só em **posição de comando**: depois de atribuições (`VAR=x`), opções e
    wrappers (`timeout`, `env`, `xargs`, `uvx`, `nohup`) e de palavras-chave (`do`, `then`,
    `else`, `{`, `!`). Sem as palavras-chave, `for f in *; do X …; done` escapa;
  - quebre em comandos simples com `shlex`, tratando a quebra de linha fora de aspas como
    separador: `shlex.shlex(cmd, posix=True, punctuation_chars="();<>|&\n")` com
    `lex.whitespace = " \t\r"`. No padrão, o `\n` vira espaço e a 2ª linha cola na 1ª;
  - remova o corpo dos heredocs antes de tokenizar: texto de documentação que só menciona o
    comando não pode disparar;
  - `2> arq` é o log de erro, não a saída do comando.

## 3. Reação a falha de ferramenta

- **Evento:** `PostToolUseFailure`, e **não** `PostToolUse`, que só roda em sucesso.
- **Payload capturado (Bash):** `"error": "Exit code 1"`, `"is_interrupt": false`. O
  `tool_response` do `PostToolUse` não traz exit code: não tente deduzi-lo do stderr.
- **Saída:** `additionalContext` (sem erro na tela) ou exit 2 com stderr, que vira aviso para
  o Claude.

## 4. Gate de `/comando` digitado

- **Evento:** `UserPromptExpansion` com matcher = nome do comando (`deploy`).
- **Saída:** `decision: "block"` + `reason`, que vai **para o usuário**, e a expansão não
  acontece. Também dá para somar `additionalContext` à expansão.
- **Erro comum:** regex em `UserPromptSubmit`. Funciona, mas roda em todo prompt e compete com
  o timeout de 30 s desse evento.

## 5. Revisão no fim do turno com estado

**Quando usar:** "se X aconteceu nesta sessão, faça o Claude revisar Y antes de encerrar".
Exemplos: a skill do marketplace foi usada, houve erro, arquivos de política mudaram.

### Esqueleto

1. **Evento:** `Stop`, com command hook e timeout curto (10 s).
2. **Guarda de loop:** `if stop_hook_active: return 0`. Nesse ponto, só registre o resultado.
3. **Leitura:** leia o transcript **a partir de um offset** salvo no estado por sessão
   (`${CLAUDE_PLUGIN_DATA}/sessions/<session_id>.json`), só até a última linha completa (`\n`).
   O arquivo é gravado de forma assíncrona. Grave o offset novo.
4. **Conta de sinais:**
   - trabalho: `tool_use` do assistente;
   - atrito: `tool_result` com `is_error: true`, e linhas do usuário com
     `[Request interrupted by user`.
5. **Adiar quando o turno espera pelo usuário:**
   - `last_assistant_message` termina em `?`;
   - a última ferramenta foi `AskUserQuestion` ou `ExitPlanMode`;
   - `permission_mode == "plan"`.

   Sem isso, a revisão atropela uma skill que faz uma pergunta por turno.
6. **Disparo com limiar e teto próprio:** por exemplo, 1ª revisão com atrito ≥ 1 ou
   trabalho ≥ 5, e no máximo 2 por sessão. Conte a revisão como feita **quando emitir**, não
   quando a resposta voltar: se o usuário interromper, não sai uma segunda.
7. **Saída:**
   - orientação: `{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"…"}}`,
     que aparece como "Stop hook feedback";
   - correção de erro: `decision: "block"`, que aparece como hook error.

   Texto curto (menos de 600 caracteres) e autocontido. Não mande ler um arquivo do plugin: o
   Read fora do projeto pode pedir permissão, e o path muda a cada versão.
8. **Uma saída só por Stop**, mesmo com vários motivos (junte-os).
9. **Nunca grave o texto do assistente** no estado, porque pode conter segredo. Métricas bastam.

### Detectar que uma skill rodou (e qual path)

No transcript, a entrada de carga de skill é:

```json
{"type": "user", "isMeta": true,
 "message": {"role": "user", "content": [{"type": "text",
   "text": "Base directory for this skill: /abs/path/da/skill\n\n# …"}]}}
```

- **Os dois caminhos gravam essa entrada.** O Skill tool (com `sourceToolUseID`) e o `/skill`
  digitado (sem `sourceToolUseID`, precedido de uma mensagem do usuário com
  `<command-name>/nome</command-name>`) produzem a mesma entrada. Isso foi confirmado em
  transcripts reais de sessão interativa e de `-p` (2.1.283, 2026-09-30).
- **Filtre pela estrutura.** Exija `type == "user"`, `isMeta == true` e um texto que
  **comece** com o prefixo. Um `grep` pela frase casa também com citações dela em
  `tool_result` e em mensagens: o próprio relatório que descreve o padrão, por exemplo.
- **Plugin só de comandos** não grava a linha. Nesse caso, use o nome `plugin:comando` do
  `tool_use` Skill (`input.skill`) ou da tag `<command-name>`, e cruze com
  `~/.claude/plugins/installed_plugins.json`. Formato observado na 2.1.283 (não documentado):

  ```json
  {"version": 2, "plugins": {
    "codereview@chewiesoft-marketplace": [
      {"scope": "user", "installPath": "<HOME>/.claude/plugins/cache/chewiesoft-marketplace/codereview/2.0.0",
       "version": "2.0.0", "installedAt": "…", "lastUpdated": "…", "gitCommitSha": "…"}]}}
  ```

  A chave é `<plugin>@<marketplace>` e o valor é uma lista, uma entrada por escopo. Para saber
  de qual marketplace é o plugin `p`, procure as chaves que começam com `p@`.
- **Dono da skill:** resolva o path com `realpath`, porque `~/.claude/skills/x` costuma ser
  symlink. Depois olhe o marketplace no path do cache
  (`~/.claude/plugins/cache/<marketplace>/<plugin>/<versão>/`) ou o git do diretório.
- **SessionStart com `resume|fork`:** grave o offset no fim do transcript quando ainda não
  houver estado, para que o histórico copiado de um fork não dispare nada.

A implementação de referência deste padrão é o plugin `retrofit-watch`, no mesmo marketplace
(`plugins/retrofit-watch/skills/retrofit-watch/`: o `retrofit_watch.py` da pasta de scripts e
`tests/test_retrofit_watch.py`).

### Exemplo oficial

O `ralph-loop` usa um Stop hook com estado em arquivo, `session_id` conferido, limite
`max_iterations` e uma tag de conclusão. Ele reinjeta o prompt com `decision: "block"`, que é
um uso de "erro a corrigir", no sentido literal.

## 6. Revisão em background com `asyncRewake`

- **Mecânica:** um command hook com `"asyncRewake": true` roda sem segurar o turno. Com exit 2,
  **acorda** o Claude e mostra o stderr como system reminder.
- **Exemplo oficial:** o `security-guidance` faz revisão por modelo do diff do turno assim. Ele
  para depois de 3 disparos seguidos, cobre até 30 arquivos por turno e sai cedo com
  `stop_hook_active`.
- **Quando serve:** trabalho demorado, como um teste ou uma revisão por modelo, que não deve
  atrasar o fim do turno.
- **Quando não serve:** o Claude acorda **depois** de ter terminado, e isso pode colidir com o
  que você já está digitando. Para orientação curta e barata, prefira o `Stop` síncrono.

## 7. Sessão assistida × desassistida

- **O problema:** um hook de revisão ou lembrete não tem com quem falar num `claude -p` de cron,
  CI ou missão automatizada, e só gasta um turno.
- **Sinais observados** no ambiente do processo do hook (2.1.283, 2026-09-30). São variáveis
  **não documentadas**, então reconfirme com `capture_payload.py` a cada versão:

  | Sessão | `CLAUDE_CODE_SESSION_ATTENDED` | `CLAUDE_CODE_ENTRYPOINT` |
  |---|---|---|
  | interativa | `1` | `cli` |
  | `claude -p` | `0` | `sdk-cli` |

- **Gate sugerido:** rode só com `ATTENDED == "1"`. Se a variável não existir, caia para
  `ENTRYPOINT == "cli"`. Ofereça uma variável própria (`MEUHOOK=force`) para os testes E2E com
  `-p`.
