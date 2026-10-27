---
name: env-docs-sync
description: "Mirrors every .env* file of a repo into a restricted environments documentation page: one section per environment, one block per file, rewritten only when its hash changes, plus a CI/CD section (workflows, runs-on, secret names via gh). Values never reach logs or local state, which keeps only hashes. Triggers — env docs, .env sync, environments page, env-docs-sync, .env-docs.json, environment variables docs."
license: MIT
compatibility: Python 3.11+, só biblioteca padrão (testado com o 3.12.3), git 2.31+. Hooks medidos em 2026-10-27 no Claude Code 2.1.309 e no codex-cli 0.164.0 (payload real capturado nos dois; trust do Codex conferido contra o hooks/list do app-server). Sync remoto com o ssh do OpenSSH (medido no 9.6p1) e, para host com senha, o sshpass (medido no 1.09). CI/CD pelo GitHub CLI 2.85.0, opcional. Destino kb conferido contra o KB de staging (BookStack v26.09) em 2026-10-27.
metadata:
  author: JorUge
  version: "0.1.0"
---

# env-docs-sync

A página que documenta os ambientes de um projeto envelhece calada: alguém muda um `.env*`, o
servidor ganha uma variável, e a página continua dizendo o que era verdade meses atrás. O
env-docs-sync tira essa página da mão das pessoas. Cada `.env*` do repositório, e o `.env` de cada
servidor, vira um Bloco de arquivo numa Página de ambientes restrita, reescrito só quando o hash
do arquivo muda.

O repositório que adota o plugin liga o sync com uma `.env-docs.json` na raiz. Sem ela, nada roda.
O exemplo completo e fictício está em `assets/env-docs.example.json`.

| Leia | Quando |
|---|---|
| `references/config.md` | ao escrever, revisar ou depurar uma `.env-docs.json`: schema campo a campo, padrões e o arquivo de estado |
| `references/hosts.md` | ao mexer no hook, depurar um disparo ou um trust do Codex: o payload, o ambiente e a pasta de dados medidos no Claude Code e no Codex, o algoritmo do trust com as fontes e o oráculo, e a receita de captura |
| `references/safety.md` | antes de mudar qualquer caminho por onde passa conteúdo de `.env*`: o que pode sair, por onde, e os testes que provam |
| `references/kb.md` | ao configurar o backend `kb`, depurar uma escrita recusada ou migrar a página: os comandos da CLI, a trava de permissão, a escrita de um bloco e o que foi medido no KB de staging |

## Linguagem

Os mesmos nomes valem aqui, na config, no código e na página.

| Termo | O que é | Onde aparece |
|---|---|---|
| Ambiente | `development`, `staging` ou `production`, nessa ordem | `environments.*`, `AMBIENTES` |
| Página de ambientes | a página do destino que documenta todos os ambientes | `doc.page_id`, `pagina_de_ambientes()` |
| Seção de ambiente | o h2 `[ambiente]` e os blocos sob ele | `secao_de_ambiente()` |
| Bloco de arquivo | o h3 com o caminho relativo, o `<pre>` com o conteúdo integral e a linha ⓘ; ganha o callout "ausente desde" quando o arquivo some | `bloco_de_arquivo()`, `marcar_ausente()` |
| Checkout da verdade | o checkout principal (não worktree) na máquina `environments.development.machine` | `checkout_da_verdade()`, `maquina_confere()` |
| Fonte da verdade | onde vive a cópia que vale de cada ambiente | `environments.*.source_of_truth` |
| Varredura | achar os `.env*` e comparar o hash de cada um com o estado | `varredura()`, `diferencas()` |
| Sync remoto | ler o `.env` de staging e de production por ssh, só leitura | `ler_remoto()`, `remotos_devidos()` |
| Seções derivadas | o que não é Bloco de arquivo: intro, Ambientes, CI/CD e Como rodar | `partes_da_pagina()`, `derivadas_devidas()` |

## O que existe na 0.1.0

| Subcomando | Estado |
|---|---|
| `init` | existe: escreve a `.env-docs.json` inicial pela Varredura e pelo hostname, com `null` no que só a pessoa sabe; nunca sobrescreve |
| `sync` | existe: `development` (e os ssh com `--remote`) no destino de `doc.backend` (o kb, com a trava de permissão) ou, com `--to-dir`, num diretório local (teste e inspeção); refaz as Seções derivadas quando mudam (com `--remote`, sempre) |
| `sync --remote` | existe: lê também os ambientes ssh, sem olhar a janela; rc 1 se algum não foi lido |
| `status` | existe: por arquivo, `ok`, `diverge` ou `ausente`, comparando o hash do bloco relido no destino com o do arquivo, mais uma linha `página	seções derivadas`; rc 3 se algo não está `ok`. Com `--remote`, confere também os ambientes ssh |
| `migrate` | existe: publica a Página de ambientes inteira (`kb page replace`), com todos os ambientes, a CI/CD e a trava; sem `--apply`, o dry-run da CLI (rc 4) |
| `install --codex` | existe: grava no `config.toml` do Codex o trust dos hooks do plugin instalado; sem `--apply`, o diff exato (rc 4) |
| `hook` | existe: a entrada do `hooks/hooks.json` (PostToolUse de edição e de shell, Stop e SessionStart); sempre sai 0 |
| `validate`, `scan`, `plan`, `render-page` | existem |

```bash
S=<pasta desta skill>/scripts/env_docs_sync.py
python3 "$S" init --root .                           # .env-docs.json inicial; o validate lista o que falta
python3 "$S" validate --root .                       # a config vale? (rc 2 com a lista de erros)
python3 "$S" scan --root .                           # Varredura: caminho e hash curto
python3 "$S" plan --root . --state <estado.json>     # o que mudou desde o último sync
python3 "$S" sync --root . --state <estado.json> [--to-dir <pasta>] [--remote]
python3 "$S" status --root . [--to-dir <pasta>] [--remote]   # ok / diverge / ausente por arquivo
python3 "$S" render-page --root . --out <pagina.html>  # a página inteira, 0600, para inspeção
python3 "$S" migrate --root . [--state <estado.json>] [--apply]   # página inteira no kb
python3 "$S" install --codex [--codex-home DIR] [--apply]   # trust do hook no Codex
python3 "$S" hook < payload.json                         # o que o hooks.json roda
```

Códigos de saída: 0 ok · 1 erro de E/S, de conteúdo ou do destino · 2 config inválida ou uso
errado · 3 `status` com algum arquivo fora de `ok` · 4 `migrate` ou `install --codex` sem `--apply`
(dry-run). O `hook`
sai sempre com 0. Nenhum subcomando
imprime valor: só caminhos, ações, contagens e o início do hash.

## Como o núcleo decide

O núcleo não abre rede, não chama o backend nem o ssh. Relógio, sha do commit, conteúdo dos
ambientes remotos e o leitor do corpo atual entram por parâmetro.

1. **Config.** `carregar_config` junta todos os erros, cada um com o caminho JSON
   (`config.doc.page_id: campo obrigatório ausente`). Campo faltando é erro, nunca default.
2. **Varredura.** `varredura(raiz, include, exclude)` soma o `exclude` da config ao piso
   `EXCLUDE_PADRAO`, que vale sempre: `.git`, `node_modules`, `dist`, `graphify-out`,
   `test-results`, `playwright-report`, as pastas de worktree e a própria `.env-docs.json`. Pasta
   com `.git` próprio (worktree, submódulo, clone aninhado) também fica de fora. Devolve caminhos
   relativos com `/`, em ordem.
3. **Hash.** sha256 dos bytes lidos do disco, do arquivo inteiro.
4. **Diferenças.** `diferencas(estado, hashes)` só compara hashes. Arquivo novo vira `criar`,
   mudado vira `trocar`, sumido vira `marcar_ausente`. Só os ambientes presentes no mapa contam:
   ambiente que não foi lido nesta rodada fica intocado. Ordem: development → staging →
   production, e os caminhos em ordem.
5. **Plano.** `planejar(...)` põe o corpo em cada operação: `bloco_de_arquivo(...)` para criar e
   trocar, e `marcar_ausente(ler_corpo(...))` para o arquivo que sumiu, que mantém o bloco antigo.
   O `commit` entra só em development; ambiente remoto não tem commit.
6. **Aplicação.** `aplicar(estado, operacoes, destino)` escreve em ordem, para na primeira falha e
   registra no estado só o que o destino aceitou. O próximo gatilho tenta o resto.
7. **Estado.** `gravar_estado` grava em 0600, atomicamente, e o validador recusa qualquer coisa
   que não seja hash ou carimbo, sem ecoar o valor recusado.

## O hook

O `hooks/hooks.json` liga o mesmo comando a quatro gatilhos, nos dois hosts:

| Gatilho | O que faz |
|---|---|
| PostToolUse `Write\|Edit` (no Codex, o `apply_patch` casa por alias) | se algum caminho editado é arquivo da Varredura, a config ou um workflow, refaz a Varredura da raiz **do arquivo** e sincroniza; senão, calado |
| PostToolUse `Bash` | refaz a Varredura da raiz do `cwd`, sem interpretar o comando. Se o comando usa `ssh`, `scp`, `sshpass` ou `rsync` e cita o host de um ambiente da config, faz também o Sync remoto daquele ambiente |
| `Stop` | a mesma Varredura, que pega a edição à mão. Sai calado com `stop_hook_active`. Sem ssh |
| `SessionStart` | a mesma Varredura, mais o Sync remoto de cada ambiente cuja última leitura boa passou de `remote_check_every`, e o gh, pela mesma janela |

O fluxo de cada raiz, em ordem, sempre com exit 0:

1. Sem `.env-docs.json`, calado.
2. **Checkout da verdade:** worktree (`--git-dir` ≠ `--git-common-dir`) ou hostname diferente de
   `environments.development.machine` (sem caixa; aceita o nome curto), calado. É isso que impede
   um worktree, um clone em outra máquina ou uma missão headless num worktree de sobrescrever a
   página.
3. Config inválida ou estado corrompido: um aviso, nada mais.
4. Hashes iguais aos do estado, nenhum ambiente remoto devido e as Seções derivadas em dia: calado,
   e o destino nem é montado
   (~50 ms num repo de 2 GB com `node_modules`, medido em 2026-10-27).
5. Trava `flock` por repositório (espera até 30 s; depois, aviso). Relê o estado, refaz o plano e
   monta o Destino pela fábrica de `doc.backend`.
6. Aplica. O estado só ganha o que o destino aceitou; a falha vira aviso com os caminhos pendentes,
   e o próximo gatilho tenta de novo.
7. Devolve um `systemMessage` com raiz, ambiente, caminho e ação. Nunca valores.

**Síncrono, não `async`.** O que o hook devolve é um `systemMessage` para a pessoa. Num hook
`async` do Claude Code, ele chega ao Claude no turno seguinte e não à pessoa; o `async` também é
morto no fim de um `claude -p` e não respeita `timeout`. O custo do síncrono só aparece quando um
`.env*` mudou, porque o caminho sem mudança custa ~50 ms. O `timeout` é 120 s em todos.

**O comando confere o script antes de rodar.** `python3 <script ausente>` sai 2, e um `Stop` com
exit 2 é bloqueio: o Claude continua o turno até o teto de 8. Por isso o comando é
`f="${CLAUDE_PLUGIN_ROOT}/…/env_docs_sync.py"; [ -f "$f" ] || { echo … >&2; exit 0; }; python3 "$f" hook`.

**Estado.** Um arquivo por repositório, `<pasta>/repos/<sha256 do caminho da raiz>.json`, 0600,
só hashes e carimbos, com a trava `.lock` ao lado. A pasta é `CLAUDE_PLUGIN_DATA`, depois
`PLUGIN_DATA` e, fora de hook de plugin (CLI à mão, hook registrado fora do plugin),
`$XDG_STATE_HOME/env-docs-sync` (padrão `~/.local/state/env-docs-sync`). Cada host tem a sua
pasta, e então cada host sincroniza uma vez por conta própria. Leia `references/hosts.md` quando
precisar dos caminhos medidos em cada host.

## Instalação no Codex

No Claude Code, o plugin instalado já roda. No Codex, cada hook de plugin precisa de trust no
`config.toml`, e hook sem trust é pulado sem erro. O `install --codex` faz o que o `/hooks` faria:

1. acha o pacote em `$CODEX_HOME/plugins/cache/<loja>/env-docs-sync/<versão>/` com a entrada
   `[plugins."env-docs-sync@<loja>"]` (mais de uma loja ou versão é recusa);
2. calcula a chave e o hash da declaração de cada handler do `hooks/hooks.json` instalado, e a
   impressão do pacote. Forma que o hash não modela (outro `type`, campo novo, evento só do Claude)
   é recusa, não palpite;
3. sem `--apply`, imprime o diff sem contexto do `config.toml` e sai 4. Com `--apply`, grava uma
   cópia `config.toml.env-docs-sync-<carimbo>.bak` (0600), troca só as linhas do trust ou acrescenta a
   tabela no fim, relê o TOML para conferir e grava atomicamente, com o mesmo modo. Já confiado, sai
   0 sem tocar o arquivo.

O algoritmo, as fontes no codex-rs, o oráculo `hooks/list` e o que foi medido estão em
`references/hosts.md` §4. O aviso de versão sai quando o `codex --version` não é o `CODEX_MEDIDO`.

## Seções derivadas e CI/CD

O que não é Bloco de arquivo sai da config, de `ci.workflows` (uma linha por job) e dos **nomes** de
segredo e variável pelo `gh`. O hook e o `sync` refazem essas seções por `page replace` quando a
config, um workflow ou a versão muda, e na SessionStart depois da janela, mantendo as Seções de
ambiente da página. Leia `references/config.md` (campo `ci`) ao configurar e `references/kb.md` ao
depurar a escrita.

## Sync remoto

Cada arquivo de `environments.<staging|production>.files` é lido com
`ssh -o BatchMode=yes -o ConnectTimeout=10 -- <host> "cat -- <caminho>"`. O conteúdo vem pelo stdout,
e o `~/` do caminho expande do lado do servidor (`aspas_remotas`). Com `auth_env`, o comando vira
`sshpass -e ssh -o BatchMode=no …`, e a senha vai em `SSHPASS` no ambiente do filho, nunca em argv;
a variável nomeada sai desse ambiente. Com `auth_env: null`, vale a chave, sem sshpass.

- **Falha não é ausência.** Rede fora, senha recusada, arquivo ilegível, mais de 1 MiB ou o tempo
  de 30 s esgotado: o ambiente inteiro fica de fora da rodada, com um aviso, e nada vira `ausente`.
  O próximo gatilho tenta de novo.
- **Carimbo.** `remote_checked_at` só ganha a data do ambiente lido **e** escrito sem pendência.
  Uma escrita que falhou é tentada na próxima SessionStart, sem esperar a janela.
- **Custo medido** (2026-10-27): falha de autenticação, 0,2 s; host inalcançável, os 10 s do
  `ConnectTimeout`. Fora da rede, toda SessionStart paga isso por ambiente devido, porque a falha
  não carimba.

## Destino kb

`DestinoKb` implementa a porta `Destino` chamando a CLI `kb` de `doc.cli` (o plugin não a traz).
Cada escrita segue quatro passos. Leia `references/kb.md` quando configurar o backend ou depurar uma
escrita recusada:

1. **Trava**, antes da primeira escrita: lê as permissões da página e recusa se ela herda do livro,
   se o fallback tem `view` ou se algum papel com `view` está fora de `doc.allowed_roles`.
2. **Pula** o bloco que a página já tem (mesmo hash no `<pre>`): nem outro host nem um estado perdido
   criam revisão sem mudança.
3. `kb page section-set <id> --heading=<caminho> --under=[<ambiente>] --create --stdin --apply`, com
   o corpo pelo stdin e o changelog `env-docs-sync: [<ambiente>] <caminho> @ <commit|sha>`.
4. **Relê e confere** o hash do bloco antes de liberar o estado.

## Segredo

O valor de um `.env*` só vai para o corpo do Bloco de arquivo, que é o destino. Nunca vai para
stdout, stderr, `systemMessage`, mensagem de erro, `repr` ou estado. O hook usa do payload só o
caminho e o comando, e lê o conteúdo do disco, embora o payload de edição traga o arquivo. Cada
regra, o porquê e o teste que a prova estão em `references/safety.md`: leia antes de mudar
qualquer rota por onde passa conteúdo.

## Template

`assets/ambientes-template.html` é a Página de ambientes genérica. O texto de introdução e o
callout de página restrita e gerada são fixos. Os placeholders são `$allowed_roles`,
`$environments_table`, `$environment_sections`, `$ci_cd` e `$run`, e faltar um deles é erro. A
seção CI/CD sai de `ci`; com `ci: null`, uma frase diz que não há CI/CD declarado.

## Armadilhas

- **`.env*` como include pega `.envrc`**, que não é arquivo de env. O exemplo usa `**/.env` e
  `**/.env.*`.
- **ssh fora do ar não é arquivo sumido.** Quem lê um ambiente remoto e falha omite o ambiente do
  mapa `atuais`. Mandar o ambiente com o mapa vazio marca todos os arquivos dele como ausentes.
- **Arquivo que volta com o mesmo hash ainda vira `trocar`**, porque o callout "ausente" precisa
  sair da página.
- **`marcar_ausente` exige `ler_corpo`.** Sem o corpo atual, o bloco antigo se perderia, e o
  `planejar` prefere falhar.
- **A `.env-docs.json` é versionada e chega a todo worktree e clone.** O que impede um worktree de
  sobrescrever a página é o filtro do Checkout da verdade.
- **`git rev-parse --git-dir --git-common-dir` sem `--path-format=absolute`** compara um caminho
  absoluto com um relativo numa subpasta do checkout principal, e o checkout da verdade parece
  worktree. O teste `test_subpasta_do_checkout_principal_nao_parece_worktree` guarda isso.
- **Editar o `.env*` de outro repositório** (sessão aberta em A, arquivo em B) sincroniza B: a raiz
  sai do arquivo editado, não do `cwd`. Shell, Stop e SessionStart só olham o `cwd`.
- **O Codex define `PLUGIN_DATA` e `CLAUDE_PLUGIN_DATA`, mas não cria a pasta** (o Claude Code
  cria). O estado nasce com `mkdir -p` e 0700.
- **O stdout do hook é JSON em ASCII, só com `systemMessage`.** O schema de saída do Codex 0.164.0
  tem `additionalProperties: false`, e o locale do host pode não ser UTF-8.
- **Com `sshpass`, nem `BatchMode=yes` nem `NumberOfPasswordPrompts=1`.** Os dois fazem a senha
  errada sair com rc 255, o mesmo da rede fora. Com o padrão, o sshpass vê o 2º prompt, desiste
  depois de uma tentativa e sai 5 (medido no sshpass 1.09 com OpenSSH 9.6p1). O aviso traduz o rc:
  255 conexão ou autenticação, 5 senha, 6 chave do host desconhecida, 1 arquivo ausente ou ilegível.
- **A variável de `auth_env` precisa estar no ambiente do host do agente** (o shell que abriu o
  Claude Code ou o Codex). Uma senha que só existe num arquivo `.env` não é vista, e o ambiente
  fica de fora com o aviso "a variável … não está definida".
- **O gatilho por host não interpreta o comando.** Ele procura a ferramenta como palavra e o nome
  do host com borda: `host.example` não casa `host.example.evil`, `192.0.2.6` não casa
  `192.0.2.60`, e `ssh-keygen -R host` não conta.
- **Dois hosts, dois estados.** Claude Code e Codex não dividem a pasta de dados, então cada host
  planeja a mesma mudança. O adaptador kb relê o bloco e pula o que a página já tem; sem isso, a
  linha "sincronizado em" faria cada host criar uma revisão (medido no KB de staging).
- **Edição feita na página não é desfeita pelo hook.** Ele decide pelo estado local, e o arquivo não
  mudou. O `status` acusa `diverge` (rc 3), e um `sync --state <arquivo novo>` reescreve só o bloco
  divergente.
- **Update do plugin no Codex desliga o hook até o `install --codex` rodar de novo.** O trust fica
  preso ao conteúdo exato do pacote: um byte mudado, e cada hook sai `hook: … Failed` no
  `codex exec`, calado na página. Reinstalar o mesmo conteúdo e `codex plugin remove` + `add`
  mantêm o trust, porque o `remove` não apaga o `[hooks.state]` (medido no 0.164.0).
- **O `codex exec` não mostra o `systemMessage`.** Sem `--json`, o stderr só diz `hook: <evento>
  Completed`; com `--json`, nada. Confira pelo `status` e pela revisão da página.
- **O `init` deixa `null`, não "a preencher".** Um texto passaria no `validate` e viraria aviso a
  cada disparo do hook; o `null` faz o `validate` listar cada campo que falta.
- **`--create` em toda escrita de bloco**, não só em `criar`: um h3 apagado à mão volta, em vez de
  travar o sync com "heading não encontrado" a cada gatilho.
- **O `gh` acha o repositório pela pasta** (`cwd` na raiz). Sem remoto do GitHub ou sem login, sai
  rc ≠ 0: aviso, e as derivadas ficam como estavam.

## Testes

```bash
cd <pasta desta skill> && python3 -B -m unittest discover -s tests -v
```

Só biblioteca padrão, sem rede. Os payloads de `tests/fixtures/` são capturas reais dos dois hosts,
anonimizadas, e o teste troca a raiz anonimizada pela de um repositório git criado no momento
(worktree incluído). `test_hook.ComandoReal` roda a string inteira do `command` do `hooks.json` por
`sh -c`, inclusive com o script ausente e com stdin inválido. A fixture
`codex-hooks-list-dourado.json` é o oráculo do trust: um pacote sintético e o `currentHash` que o
`hooks/list` do Codex deu para cada hook. O teste `test_sem_marcas_da_empresa.py` varre o pacote inteiro
atrás de marcas da empresa de origem, porque o repositório é público, e prova numa cópia sabotada
que o sensor reprova. O `tests/oraculo_codex.py`, fora do `discover`, confere à mão a fixture
dourada contra o `hooks/list` de um Codex novo.
