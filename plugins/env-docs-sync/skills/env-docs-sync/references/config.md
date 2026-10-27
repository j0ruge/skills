# Referência da `.env-docs.json`

A `.env-docs.json` fica na raiz do repositório que adota o plugin, e é versionada. Ela nomeia o que
o hook executa, então mudá-la é mudar o que roda: leia a `safety.md`, *Confiança na config*, antes
de adotar o plugin ou de revisar uma mudança nela. Ela não guarda segredo: diz onde estão os
arquivos, onde vive a Página de ambientes e quem pode vê-la. O exemplo completo e fictício está em
`assets/env-docs.example.json`, e `env_docs_sync.py validate --root .` confere uma config real.

Regras gerais, conferidas por `validar_config`:

- **Campo faltando é erro, nunca default.** A única exceção é `remote_check_every`, que só é
  exigido quando algum ambiente usa `source: "ssh"` ou quando `ci.secrets` é `"gh"`.
- **Chave desconhecida é erro.** Assim um erro de digitação (`exlude`) não vira config ignorada.
- **Chave duplicada no JSON é erro.** O `json` do Python ficaria só com a última.
- **Todos os erros saem juntos**, um por linha, com o caminho JSON: `config.doc.page_id: campo
  obrigatório ausente`. Na CLI, o código de saída é 2.

## Topo

| Campo | Tipo | Obrigatório | O que é |
|---|---|---|---|
| `doc` | objeto | sim | o destino: backend, página e papéis (ver abaixo) |
| `values` | `"full"` | sim | o conteúdo integral vai para a página restrita; é o único modo da 0.1.0 |
| `remote_check_every` | texto `<n>m`, `<n>h` ou `<n>d` | só com ambiente ssh ou `ci.secrets: "gh"` | intervalo mínimo entre a última leitura boa de um ambiente ssh (ou a última consulta ao gh) e a próxima que a SessionStart dispara (ex.: `"24h"`). O gatilho por host citado num comando do shell e o `sync --remote` não olham a janela |
| `include` | lista não vazia de padrões | sim | os arquivos que entram na Varredura |
| `exclude` | lista de padrões (pode ser vazia) | sim | somados ao piso `EXCLUDE_PADRAO` |
| `environments` | objeto | sim | um objeto por Ambiente (ver abaixo) |
| `run` | lista (pode ser vazia) | sim | os comandos da seção "Como rodar" |
| `ci` | objeto ou `null` | sim | a seção CI/CD (ver abaixo); `null` a deixa com a frase "sem CI/CD declarado" |

## `doc`

| Campo | Tipo | O que é |
|---|---|---|
| `backend` | `"kb"` | o único backend da 0.1.0: a CLI `kb` de um BookStack, chamada por subprocesso (o contrato está em `kb.md`) |
| `cli` | texto | caminho da CLI do backend (aceita `~`, expandido pelo `HOME` do processo). O plugin não traz a CLI: ela é dependência declarada. Um caminho que não existe vira aviso no hook (`rc 2` do interpretador) |
| `python` | texto | o interpretador que roda a CLI (o do venv dela, se houver; aceita `~`). Ausente: aviso "programa não encontrado" |
| `target` | texto | o valor passado ao `--target` do backend (ex.: `prod` ou `staging`) |
| `page_id` | inteiro > 0 | o id da Página de ambientes no destino |
| `allowed_roles` | lista não vazia, sem repetição | os papéis que podem ver a página, pelo nome de exibição do papel no BookStack (`role.display_name`). Entram no callout da página e na trava do adaptador: página que herda do livro, com fallback `view` ou visível a papel fora desta lista, nada se escreve |

## `include` e `exclude`

Os padrões são relativos à raiz, com `/`, sem `..` nem barra invertida, e casam com o caminho
relativo inteiro:

- `**/` casa com zero ou mais pastas: `**/.env` pega `.env` e `packages/api/.env`.
- `*` e `?` não cruzam `/`: `.env*` pega só a raiz, e `a/*/.env` não pega `a/b/c/.env`.
- `[0-9]` e `[!x]` são classes de caractere.

O padrão `.env*` também pega `.envrc`, que é script do direnv. Por isso o exemplo usa dois
padrões, `**/.env` e `**/.env.*`, que pegam `.env`, `.env.local`, `.env.example` e afins.

O piso `EXCLUDE_PADRAO` vale sempre, mesmo com `exclude: []`: `**/.git/**`,
`**/node_modules/**`, `**/dist/**`, `**/graphify-out/**`, `**/test-results/**`,
`**/playwright-report/**`, `**/.worktrees/**`, `**/.claude/worktrees/**` e
`**/.env-docs.json`. A Varredura também não desce em pasta com `.git` próprio, seja worktree,
submódulo ou clone aninhado. Symlink de arquivo entra só se o alvo estiver dentro da raiz; symlink
de pasta não é seguido.

## `environments`

O objeto aceita só as chaves `development`, `staging` e `production`, e `development` é
obrigatório. Todo ambiente tem estes campos, que formam a tabela da seção "Ambientes":

| Campo | Coluna na página | O que é |
|---|---|---|
| `source` | — | de onde o conteúdo vem: `"local"` em development, `"ssh"` nos outros |
| `server` | Servidor | a máquina onde o ambiente roda |
| `domain` | Domínio | o endereço do ambiente |
| `where` | Onde vive o .env | o caminho do arquivo que vale |
| `source_of_truth` | Fonte da verdade | quem materializa ou guarda a cópia que vale |

### `development`

| Campo | O que é |
|---|---|
| `source` | sempre `"local"` |
| `machine` | o hostname da estação do Checkout da verdade, comparado sem caixa e aceitando o nome curto (`estacao` casa `estacao.lan`). O hook só age no checkout principal dessa máquina |

Os arquivos de development saem da Varredura. Não há `files`.

### `staging` e `production`

| Campo | O que é |
|---|---|
| `source` | sempre `"ssh"` |
| `host` | o destino do ssh (`usuario@host` ou alias do `~/.ssh/config`), sem espaço e sem começar por `-`. É também o que o gatilho por host procura no comando do shell, sem o `usuario@` |
| `auth_env` | `null` quando o host aceita chave (`ssh -o BatchMode=yes`, sem sshpass); senão, o **nome** da variável de ambiente com a senha, que o Sync remoto entrega ao `sshpass -e` em `SSHPASS`, no ambiente do filho e nunca em argv. Nunca a senha. A variável precisa estar no ambiente do processo que roda o hook |
| `files` | objeto não vazio `{"caminho na página": "caminho remoto"}`. A chave é o h3 do Bloco de arquivo (relativa, com `/`, sem `..`); o valor começa por `/` ou `~/`, e o `~/` expande do lado do servidor. Cada arquivo é lido com `cat -- <caminho>`, até 1 MiB |

**Host com senha (`auth_env`).** Com `sshpass`, nem `BatchMode=yes` nem `NumberOfPasswordPrompts=1`:
os dois fazem a senha errada sair com rc 255, o mesmo da rede fora. Com o padrão, o sshpass vê o 2º
prompt, desiste depois de uma tentativa e sai 5 (medido no sshpass 1.09 com OpenSSH 9.6p1). O aviso
traduz o rc: 255 conexão ou autenticação, 5 senha, 6 chave do host desconhecida, 1 arquivo ausente
ou ilegível.

## `run`

Cada item é `{"label": texto, "command": texto}` e vira, na seção "Como rodar", o rótulo em
negrito e o comando num bloco de código. Lista vazia gera uma frase dizendo que não há comando.

## `ci`

| Campo | Tipo | O que é |
|---|---|---|
| `workflows` | pasta relativa ou `null` | de onde saem os workflows (`*.yml` e `*.yaml` do topo da pasta, como no GitHub). Cada job vira uma linha: workflow, arquivo, job, `runs-on` e `environment` |
| `secrets` | `"gh"` ou `null` | com `"gh"`, os **nomes** dos segredos e das variáveis do repositório e de cada environment, pelo GitHub CLI rodado na raiz (`gh secret list`, `gh variable list`, `gh api …/environments`). O GitHub não devolve valor de segredo, e o plugin recusa nome fora de `[A-Za-z_][A-Za-z0-9_]*` |

O `init` liga `{"workflows": ".github/workflows", "secrets": "gh"}` (e a janela de 24 h) quando a
pasta existe, e deixa `ci: null` quando não. O leitor de workflow não é um YAML completo: entende o
`name` do topo e, em cada job, o `runs-on` (texto, expressão, lista de fluxo ou de bloco) e o
`environment` (texto ou mapa com `name`). Forma que ele não entende, como `runs-on` em mapa de
`group`/`labels`, sai `?`, nunca um palpite. Job sem `runs-on` (workflow reusável) sai `—`.

Falha do `gh` (sem login, sem rede, sem permissão de ler segredos) não apaga nada: a seção fica como
estava, o hook avisa, e o próximo gatilho tenta de novo.

## Como a config vira página

| Placeholder do template | Sai de |
|---|---|
| `$allowed_roles` | `doc.allowed_roles`, separados por vírgula |
| `$environments_table` | `environments.*` (uma linha por ambiente, na ordem development → staging → production) |
| `$environment_sections` | uma Seção de ambiente por ambiente configurado, com um h3 por caminho, em ordem |
| `$ci_cd` | `ci` (workflows do disco e nomes do gh) |
| `$run` | `run[]` |

## O arquivo de estado

O estado não é config, mas é o outro arquivo que o plugin lê. A CLI recebe o caminho em
`--state`. O hook usa um arquivo por repositório, `<pasta>/repos/<sha256 do caminho absoluto da
raiz>.json`, com a trava `.lock` ao lado. A `<pasta>` é `CLAUDE_PLUGIN_DATA`, depois `PLUGIN_DATA`
e, fora de hook de plugin, `$XDG_STATE_HOME/env-docs-sync` (padrão `~/.local/state/env-docs-sync`);
os caminhos medidos em cada host estão em `hosts.md`. O estado é gravado em 0600, atomicamente, e
tem esta forma:

```json
{
  "version": 1,
  "environments": {
    "development": {
      ".env": {"sha256": "<64 hex>", "synced_at": "2026-10-27T14:05:00-03:00"},
      "old/.env": {"sha256": "<64 hex>", "absent_since": "2026-10-27"}
    }
  },
  "remote_checked_at": {"staging": "2026-10-27T14:05:00-03:00"},
  "derived": {"inputs_sha256": "<64 hex>", "sha256": "<64 hex>", "checked_at": "2026-10-27T14:05:00-03:00"}
}
```

`derived` é opcional: o estado das seções derivadas. `inputs_sha256` resume o que elas leem do disco
(versão do plugin, template, config e workflows), `sha256` é o hash delas renderizadas, e
`checked_at` a última vez que foram conferidas, que é também a última consulta ao gh.

O `validar_estado` recusa qualquer chave ou valor fora disso, e a mensagem de erro não repete o
valor recusado. Um estado corrompido é erro, e não vira estado vazio em silêncio.
