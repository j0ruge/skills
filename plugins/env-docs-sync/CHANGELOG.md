# Changelog — env-docs-sync

## [0.1.0] — em construção

Em construção, por incrementos: o núcleo puro com testes offline, a entrada do hook nos dois hosts, o
Sync remoto e o destino kb. O plugin ainda não está no catálogo da loja.

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
- **CLI mínima:** `validate`, `scan`, `plan`, `sync --to-dir` (destino local de teste) e
  `render-page`. Nenhum subcomando imprime valor.
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
  - fábrica de destino injetável por `doc.backend`. O backend `kb` recusa com o aviso "adaptador kb
    ainda não implementado", e o estado não muda.
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
