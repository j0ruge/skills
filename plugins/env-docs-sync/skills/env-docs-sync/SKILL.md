---
name: env-docs-sync
description: "Mirrors every .env* file of a repo into a restricted environments documentation page: one section per environment, one block per file, rewritten only when its hash changes. Values never reach logs or local state, which keeps only hashes. Triggers — env docs, .env sync, environments page, env-docs-sync, .env-docs.json, environment variables docs."
license: MIT
compatibility: Python 3.11+, só biblioteca padrão (testado com o 3.12.3), git 2.31+. Hooks medidos em 2026-10-27 no Claude Code 2.1.309 e no codex-cli 0.164.0 (payload real capturado nos dois). Sync remoto com o ssh do OpenSSH (medido no 9.6p1) e, para host com senha, o sshpass (medido no 1.09). O destino kb ainda não existe na 0.1.0.
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
| `references/hosts.md` | ao mexer no hook ou depurar um disparo: o payload, o ambiente e a pasta de dados medidos no Claude Code e no Codex, e a receita de captura |
| `references/safety.md` | antes de mudar qualquer caminho por onde passa conteúdo de `.env*`: o que pode sair, por onde, e os testes que provam |

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

## O que existe na 0.1.0

| Subcomando | Estado |
|---|---|
| `init` | planejado: o agente escreve a `.env-docs.json` do repositório |
| `sync` | **parcial:** só `development`. Escreve no destino de `doc.backend` ou, com `--to-dir`, num diretório local (teste e inspeção). O adaptador `kb` é planejado: hoje o backend `kb` recusa com aviso |
| `sync --remote` | existe: lê também os ambientes ssh, sem olhar a janela; rc 1 se algum não foi lido |
| `status` | existe: por arquivo, `ok`, `diverge` ou `ausente`, comparando o hash do bloco relido no destino com o do arquivo; rc 3 se algo não está `ok`. Com `--remote`, confere também os ambientes ssh |
| `install --codex` | planejado: registra o hook no Codex e grava o trust |
| `hook` | existe: a entrada do `hooks/hooks.json` (PostToolUse de edição e de shell, Stop e SessionStart); sempre sai 0 |
| `validate`, `scan`, `plan`, `render-page` | existem |

```bash
S=<pasta desta skill>/scripts/env_docs_sync.py
python3 "$S" validate --root .                       # a config vale? (rc 2 com a lista de erros)
python3 "$S" scan --root .                           # Varredura: caminho e hash curto
python3 "$S" plan --root . --state <estado.json>     # o que mudou desde o último sync
python3 "$S" sync --root . --state <estado.json> [--to-dir <pasta>] [--remote]
python3 "$S" status --root . [--to-dir <pasta>] [--remote]   # ok / diverge / ausente por arquivo
python3 "$S" render-page --root . --out <pagina.html>  # a página inteira, 0600, para o replace
python3 "$S" hook < payload.json                         # o que o hooks.json roda
```

Códigos de saída: 0 ok · 1 erro de E/S, de conteúdo ou do destino · 2 config inválida ou uso
errado · 3 `status` com algum arquivo fora de `ok`. O `hook` sai sempre com 0. Nenhum subcomando
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
| PostToolUse `Write\|Edit` (no Codex, o `apply_patch` casa por alias) | se algum caminho editado é arquivo da Varredura, refaz a Varredura da raiz **do arquivo** e sincroniza; senão, calado |
| PostToolUse `Bash` | refaz a Varredura da raiz do `cwd`, sem interpretar o comando. Se o comando usa `ssh`, `scp`, `sshpass` ou `rsync` e cita o host de um ambiente da config, faz também o Sync remoto daquele ambiente |
| `Stop` | a mesma Varredura, que pega a edição à mão. Sai calado com `stop_hook_active`. Sem ssh |
| `SessionStart` | a mesma Varredura, mais o Sync remoto de cada ambiente cuja última leitura boa passou de `remote_check_every` |

O fluxo de cada raiz, em ordem, sempre com exit 0:

1. Sem `.env-docs.json`, calado.
2. **Checkout da verdade:** worktree (`--git-dir` ≠ `--git-common-dir`) ou hostname diferente de
   `environments.development.machine` (sem caixa; aceita o nome curto), calado. É isso que impede
   um worktree, um clone em outra máquina ou uma missão headless num worktree de sobrescrever a
   página.
3. Config inválida ou estado corrompido: um aviso, nada mais.
4. Hashes iguais aos do estado e nenhum ambiente remoto devido: calado, e o destino nem é montado
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

## Contrato com o destino kb (planejado)

O adaptador kb implementa a porta `Destino` (`ler_corpo`, `escrever`) chamando a CLI declarada
em `doc.cli`:

- **Bloco de arquivo:** `kb page section-set <page_id> --heading "<caminho>" --under "[<ambiente>]" [--create] --stdin --apply`.
  - O stdin é exatamente `Operacao.corpo`, sem o h3. `--under` é `Operacao.sob`.
  - `--create` vai quando `Operacao.acao == "criar"`.
- **Página inteira** (migração): `kb page replace <page_id> --html @<arquivo> --confirm <page_id> --apply`, com o arquivo 0600 de `render-page`.
- **Conferência antes do estado:** reler o bloco e comparar `hash_sha256(conteudo_do_bloco(corpo).encode())`
  com o hash do arquivo. `conteudo_do_bloco` tolera os ids que o destino acrescenta.

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
seção CI/CD sai como "a gerar" nesta versão.

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
- **Dois hosts, dois estados.** Claude Code e Codex não dividem a pasta de dados, então a mesma
  mudança é sincronizada uma vez por host. O destino precisa tratar conteúdo igual como "sem
  mudança" (no kb, `changed: false` sem PUT), senão cada host gera uma revisão.

## Testes

```bash
cd <pasta desta skill> && python3 -B -m unittest discover -s tests -v
```

Só biblioteca padrão, sem rede. Os payloads de `tests/fixtures/` são capturas reais dos dois hosts,
anonimizadas, e o teste troca a raiz anonimizada pela de um repositório git criado no momento
(worktree incluído). `test_hook.ComandoReal` roda a string inteira do `command` do `hooks.json` por
`sh -c`, inclusive com o script ausente e com stdin inválido. O teste `test_sem_marcas_da_empresa.py` varre o pacote inteiro
atrás de marcas da empresa de origem, porque o repositório é público, e prova numa cópia sabotada
que o sensor reprova.
