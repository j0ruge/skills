# Changelog — env-docs-sync

## [0.1.0] — 2026-10-27

Primeira versão publicada, feita por incrementos: o núcleo puro com testes offline, a entrada do hook
nos dois hosts, o Sync remoto, o destino kb, a instalação no Codex, o `init` e a seção CI/CD com as
Seções derivadas. Entra no catálogo da loja para o Claude Code e o Codex CLI.

### Por quê

A página que documenta os ambientes de um projeto, com o conteúdo dos `.env*`, é mantida à mão e
envelhece: arquivos novos ficam de fora, valores mudam e ninguém atualiza. O plugin vai manter a
página sozinho, a partir de gatilhos do Claude Code e do Codex. O núcleo vem primeiro, sem rede,
para que hook, destino e ssh se encaixem por injeção e sejam testados um a um.

### Added

- **`scripts/env_docs_sync.py`, núcleo puro** (só biblioteca padrão):
  - config validada campo a campo, com todos os erros de uma vez e sem default silencioso;
  - Varredura por `include`/`exclude`, com piso de exclusão fixo, poda de outro checkout e
    symlink só para dentro da raiz;
  - sha256 dos bytes;
  - Bloco de arquivo (`<pre>` com o conteúdo escapado e a linha "sincronizado em … · commit …"),
    o inverso dele para conferir o hash relido, e o callout "ausente desde";
  - plano de operações `criar`/`trocar`/`marcar_ausente` em ordem fixa, que ignora ambiente não
    lido na rodada;
  - aplicação que para na primeira falha e registra só o que o destino aceitou;
  - estado 0600, atômico, que só aceita hashes e carimbos;
  - a Página de ambientes inteira a partir do template, para a migração por `replace`.
- **CLI do núcleo**, no primeiro incremento (os outros subcomandos vêm abaixo): `validate`, `scan`,
  `plan`, `sync --to-dir` (destino local de teste) e `render-page`. Nenhum subcomando imprime valor.
- **`assets/ambientes-template.html`**: o template genérico da Página de ambientes.
- **`assets/env-docs.example.json`**: uma config fictícia completa.
- **`references/config.md`**: o schema da config, campo a campo, e o formato do estado.
- **`tests/`** (unittest, sem rede):
  - config, Varredura, Bloco de arquivo, plano, estado, página e CLI;
  - o canário, que chega ao destino e a nenhum outro lugar;
  - o sensor que reprova marcas da empresa de origem no pacote, provado vermelho numa cópia
    sabotada.
- **Entrada do hook** (`hooks/hooks.json` + subcomando `hook`), a mesma para o Claude Code e o Codex
  CLI:
  - PostToolUse `Write|Edit` (no Codex, o `apply_patch` casa por alias) e `Bash`, `Stop` e
    `SessionStart`. Forma shell, sem `args`, `timeout` inteiro de 120 s, e nada de `"hooks"` no
    `plugin.json`;
  - o comando confere o script antes de rodar: `python3 <ausente>` sai 2, e um `Stop` com exit 2
    prende o turno até o teto de 8;
  - **síncrono, sem `async`:** o `systemMessage` é para a pessoa, e num hook `async` ele iria para o
    Claude no turno seguinte; o `async` também morre no fim de um `claude -p`. O caminho sem mudança
    custa ~50 ms num repositório de 2 GB;
  - filtro do Checkout da verdade: worktree (`--git-dir` ≠ `--git-common-dir`, com
    `--path-format=absolute`) ou hostname diferente de `environments.development.machine`, calado;
  - a edição usa a raiz do arquivo editado; shell, Stop e SessionStart refazem a Varredura da raiz do
    `cwd`, sem interpretar o comando;
  - `flock` por repositório, estado relido sob a trava, gravado só com o que o destino aceitou, e
    `systemMessage` com caminhos, nunca valores. Toda falha sai com exit 0 e aviso;
  - estado por repositório em `CLAUDE_PLUGIN_DATA`, `PLUGIN_DATA` ou `~/.local/state/env-docs-sync`;
  - fábrica de destino injetável por `doc.backend`, com o destino `kb` descrito mais abaixo. Uma
    falha do destino vira aviso, e o estado não muda.
- **`status`:** `ok`, `diverge` ou `ausente` por arquivo, comparando o hash do bloco relido no destino
  com o do arquivo; rc 3 quando algo não está `ok`. Tem caso sabotado: um byte trocado no arquivo
  ou no bloco dá `diverge`.
- **`sync` sem `--to-dir`** usa o destino de `doc.backend`.
- **`references/hosts.md`:** payload, ambiente e pasta de dados medidos no Claude Code 2.1.309 e no
  codex-cli 0.164.0, e a receita de captura. Medido: o Codex define `PLUGIN_DATA` e
  `CLAUDE_PLUGIN_DATA` (iguais) mas não cria a pasta; o Claude Code não define `PLUGIN_DATA`.
- **`references/safety.md`:** cada superfície por onde o conteúdo poderia sair, a regra e o teste.
- **`tests/fixtures/`:** 12 payloads reais (Edit, Write, Bash, Stop e SessionStart no Claude;
  `apply_patch`, Bash, Stop e SessionStart no Codex), anonimizados, e um derivado
  (`stop_hook_active`). Testes de gatilho, filtro, worktree, máquina, trava, falha do destino,
  canário e o `command` inteiro por `sh -c` (script ausente, stdin inválido). 8 mutantes dos
  guardas deixaram a suíte vermelha.
- **Sync remoto** (`source: "ssh"`):
  - cada arquivo de `files` sai de `ssh -o BatchMode=yes -o ConnectTimeout=10 -- <host> "cat -- <caminho>"`,
    com o `~/` expandido do lado do servidor; com `auth_env`, `sshpass -e` e a senha em `SSHPASS` no
    ambiente do filho, nunca em argv;
  - gatilhos: PostToolUse `Bash` cujo comando usa `ssh`/`scp`/`sshpass`/`rsync` e cita o host
    (ferramenta como palavra, host com borda), e a SessionStart no máximo uma vez por
    `remote_check_every`, pelo carimbo `remote_checked_at`;
  - falha (rede, senha, arquivo, mais de 1 MiB, 30 s) deixa o ambiente fora da rodada, com um
    aviso, e não marca nada como ausente. O carimbo só vai para o ambiente lido e escrito sem
    pendência;
  - medido no OpenSSH 9.6p1 com o sshpass 1.09: com `BatchMode=yes` ou
    `NumberOfPasswordPrompts=1`, a senha errada sai 255, como a rede fora; com o padrão, sai 5. Host
    inalcançável custa os 10 s do `ConnectTimeout`;
  - `sync --remote` e `status --remote` na CLI. Sem `--remote`, o `sync` diz quais ambientes ficaram
    fora da rodada;
  - testes com runner falso e com `ssh`/`sshpass` falsos num processo real, que gravam o próprio
    `/proc/<pid>/cmdline`: a senha não aparece em nenhum argv e chega ao `SSHPASS`. 12 mutantes
    dos guardas deixaram a suíte vermelha.
- **Destino kb** (`DestinoKb`, montado pela fábrica de `doc.backend`), pela CLI de `doc.cli`/`doc.python`:
  - **trava de permissão** antes da primeira escrita: recusa a página que herda do livro, que tem
    fallback `view` ou que é visível a papel fora de `doc.allowed_roles` (pelo `role.display_name`),
    falhando fechado. A recusa é aviso com exit 0 no hook, e o estado não muda;
  - cada bloco por `kb page section-set … --create --stdin --apply`, com o changelog
    `env-docs-sync: [<ambiente>] <caminho> @ <commit|sha>`, e a releitura do bloco conferida pelo hash
    antes de liberar o estado. `--create` vai em toda ação, para um h3 apagado à mão voltar;
  - **pula o bloco que a página já tem.** Medido no KB de staging: sem isso, a linha "sincronizado
    em" faria cada host, ou cada estado perdido, criar uma revisão sem mudança;
  - o estado é gravado depois de cada operação aceita, para um timeout do host no meio da rodada não
    perder o que já foi; e a mensagem lista só o que foi escrito (o que já estava fica calado).
- **`migrate`:** a página inteira pelo template, com todos os ambientes (um remoto que falha cancela),
  por `kb page replace --html=@- --confirm=<id>`, pela mesma trava; sem `--apply`, o dry-run da CLI
  (rc 4); com `--state`, grava o estado do que foi publicado. `status` lê a página uma vez só.
- **`references/kb.md`:** o contrato com a CLI, a trava, a escrita de um bloco e o check ao vivo no KB
  de staging: página herdando, visível a `Viewer` e restrita; migração; edição pelo comando real do
  hook; nada mudou; outro host com estado vazio; e K2 com 1 byte trocado na página.
- **Testes** contra um kb falso (`tests/kb_falso.py`), um processo de verdade que guarda a página num
  JSON, acrescenta os ids `bkmrk-` e devolve os rc e o JSON de erro da CLI real. 12 mutantes do
  adaptador deixaram a suíte vermelha.
- **`install --codex [--codex-home DIR] [--apply]`:** grava no `config.toml` do Codex o trust dos
  hooks do plugin instalado, o que o `/hooks` faria à mão:
  - chave `<plugin>@<loja>:hooks/hooks.json:<evento>:<grupo>:<handler>`, `trusted_hash` (a
    declaração normalizada) e `trusted_content_hash` (a impressão do pacote instalado), com o
    algoritmo lido no codex-rs na tag `rust-v0.164.0` (arquivo e linha na `hosts.md` §4);
  - conferido contra o próprio Codex: a fixture `codex-hooks-list-dourado.json` é um pacote
    sintético instalado pelo `codex plugin add`, com o `currentHash` que o `hooks/list` do
    `codex app-server` deu. O pacote força ordem por bytes, lixo ignorado, nome não ASCII, `async`,
    `statusMessage`, `commandWindows`, matcher descartado e os timeouts padrão e com teto;
  - recusa, sem tocar o arquivo: plugin fora do cache ou do `[plugins]`, mais de uma loja ou versão,
    forma de hook que o hash não modela, symlink no pacote, trust em tabela inline ou chave
    pontuada, `config.toml` que muda entre o plano e a gravação;
  - sem `--apply`, o diff sem contexto (rc 4), que só mostra linha do trust; com `--apply`, cópia
    `.bak` 0600, edição só das linhas do trust, releitura do TOML e gravação atômica com o mesmo
    modo, inclusive num `config.toml` que é symlink. Idempotente;
  - aviso quando o `codex --version` não está em `CODEX_MEDIDOS`, as versões em que o hash bateu
    com o próprio Codex (0.164.0 e 0.165.0).
- **`init`:** a `.env-docs.json` inicial pela Varredura e pelo hostname, com `null` no destino, na
  página, nos papéis, no servidor e no domínio: o `validate` lista cada um. Nunca sobrescreve.
- **Disparo ao vivo (CA4)**, num sandbox novo apontado para a página sintética do KB de staging, sem
  `--dangerously-bypass-hook-trust` no Codex: Claude `Edit` e `Bash`, Codex `apply_patch` e shell,
  edição à mão com SessionStart novo, e o update do pacote do Codex. Medido: o Codex honra o trust
  gravado; reinstalar o mesmo conteúdo e `remove` + `add` mantêm o trust; um byte mudado no pacote
  faz cada hook sair `Failed` até o `install --codex` rodar de novo; o `codex exec` não mostra o
  `systemMessage`. Os resultados estão na `kb.md` §5 e na `hosts.md` §4.
- **Testes:** `test_codex.py` e `test_init.py`; 22 mutantes dos guardas novos, rodados à mão,
  deixaram a suíte vermelha.
- **Seção CI/CD** (campo `ci` da config, obrigatório, `null` desliga):
  - os workflows de `ci.workflows`, lidos sem PyYAML: uma linha por job, com workflow, arquivo, job,
    `runs-on` e `environment`. Forma que o leitor não entende sai `?`;
  - com `ci.secrets: "gh"`, os **nomes** dos segredos e das variáveis do repositório e de cada
    environment, pelo GitHub CLI rodado na raiz. Nome fora de `[A-Za-z_][A-Za-z0-9_]*` é recusado,
    e do erro do `gh` sai só o rc. `remote_check_every` passa a ser exigido também com o gh;
  - o `init` liga a seção quando existe `.github/workflows`.
- **Seções derivadas** (a intro com os papéis, a tabela de Ambientes, a CI/CD e o Como rodar): o
  hook e o `sync` as refazem quando a config, um workflow ou a versão do plugin muda, e na
  SessionStart depois da janela, com o gh. Como o `section-set` só troca o corpo de um h3, elas vão
  por `page replace`, com as Seções de ambiente relidas da página como estão; a comparação ignora os
  ids `bkmrk-`, as entidades e o espaço entre tags, e bateu com a página real guardada pelo
  BookStack. O estado ganha `derived` (só hashes e carimbo), e o `status`, a linha
  `página	seções derivadas`. A edição da `.env-docs.json` ou de um workflow passa pelo filtro do hook.
- **`tests/oraculo_codex.py`**: a conferência à mão da fixture dourada contra o `hooks/list` de um
  Codex novo, que monta a loja, instala num `CODEX_HOME` descartável e compara. No 0.164.0: 9/9
  iguais; com a fixture sabotada, rc 1.
- **Testes:** `test_ci.py`, `test_derivadas.py` e os novos de config e `init`; 27 mutantes do leitor
  de workflow, do gh e das derivadas deixaram a suíte vermelha.
- **Codex 0.165.0**, que o próprio Codex instalou no dia da publicação: o oráculo deu 9/9 iguais
  (com a fixture sabotada, 0/9 e rc 1). O 0.165.0 entrou em `CODEX_MEDIDOS`, e o `install --codex`
  deixa de avisar nele. Teste novo e 4 mutantes vermelhos. A description ficou com 348 caracteres,
  igual no `SKILL.md`, no `plugin.json` e no catálogo.
- **`tests/mutantes.py`**, rodado à mão como o oráculo: os 31 mutantes da CI/CD, das seções derivadas
  e da versão do Codex, cada um numa cópia do plugin inteiro. Sai 1 com o mutante vivo, com o
  trecho que sumiu do script ou com o mutante que não compila; um mutante que não muda nada sai
  `VIVO`. O M22 (status sem a linha das derivadas) não compilava, e a suíte ficava vermelha só pelo
  import (16 erros): foi refeito e morre em 3 testes. Antes dos mutantes, o rodador roda a suíte sem
  nenhum (o controle) e sai 2 se ela já estiver vermelha, porque aí todo mutante sairia morto.
- **Revisão de código antes da publicação** (o codereview da loja, que deu F na 1ª rodada pelo
  portão de segredo):
  - a senha sintética do `test_remoto.py` passa a ser gerada a cada execução, e nenhum literal de
    senha fica no repositório;
  - git que não responde no Checkout da verdade (anterior à 2.31, timeout, rc ≠ 0) avisa, em vez
    de calar como se fosse worktree;
  - pasta que a Varredura não lista levanta, em vez de sumir com os arquivos, que virariam
    `ausente` na página;
  - o callout "ausente desde" é reconhecido pelo `<p class="callout danger">`, não pela frase,
    que também pode estar no conteúdo do `.env`;
  - o sha da linha "commit" sai do `_git`, sem os `GIT_*` herdados de um hook do git;
  - o protocolo `Destino` ganhou os métodos das Seções derivadas, e os símbolos públicos ganharam
    docstring;
  - o oráculo do Codex lê o `app-server` com prazo (antes travava sem resposta), encerra o processo
    no fim e sai 1 quando nada foi comparado;
  - a `safety.md` ganhou a seção "Confiança na config": a `.env-docs.json` nomeia o que o hook
    executa, e mudar a config é mudar o que roda na máquina declarada;
  - 4 testes novos e 6 mutantes (M32–M37), todos vermelhos.
