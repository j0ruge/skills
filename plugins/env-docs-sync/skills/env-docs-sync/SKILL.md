---
name: env-docs-sync
description: "Mirrors every .env* file of a repo into a restricted environments documentation page: one section per environment, one block per file, rewritten only when its hash changes. Values never reach logs or local state, which keeps only hashes. Triggers — env docs, .env sync, environments page, env-docs-sync, .env-docs.json, environment variables docs."
license: MIT
compatibility: Python 3.11+, só biblioteca padrão (testado com o 3.12.3 em 2026-10-27). Na 0.1.0 existem o núcleo e a CLI mínima; os hooks do Claude Code e do Codex CLI, o destino kb e o Sync remoto ainda não existem.
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
Leia `references/config.md` quando for escrever, revisar ou depurar uma `.env-docs.json`: ele traz
o schema campo a campo, o formato dos padrões e o arquivo de estado. O exemplo completo e fictício
está em `assets/env-docs.example.json`.

## Linguagem

Os mesmos nomes valem aqui, na config, no código e na página.

| Termo | O que é | Onde aparece |
|---|---|---|
| Ambiente | `development`, `staging` ou `production`, nessa ordem | `environments.*`, `AMBIENTES` |
| Página de ambientes | a página do destino que documenta todos os ambientes | `doc.page_id`, `pagina_de_ambientes()` |
| Seção de ambiente | o h2 `[ambiente]` e os blocos sob ele | `secao_de_ambiente()` |
| Bloco de arquivo | o h3 com o caminho relativo, o `<pre>` com o conteúdo integral e a linha ⓘ; ganha o callout "ausente desde" quando o arquivo some | `bloco_de_arquivo()`, `marcar_ausente()` |
| Checkout da verdade | o checkout principal (não worktree) na máquina `environments.development.machine` | filtro do hook (planejado) |
| Fonte da verdade | onde vive a cópia que vale de cada ambiente | `environments.*.source_of_truth` |
| Varredura | achar os `.env*` e comparar o hash de cada um com o estado | `varredura()`, `diferencas()` |
| Sync remoto | ler o `.env` de staging e de production por ssh, só leitura | planejado |

## O que existe na 0.1.0

| Subcomando | Estado |
|---|---|
| `init` | planejado: o agente escreve a `.env-docs.json` do repositório |
| `sync` | **parcial:** só `development` e só o destino `--to-dir` (diretório local, para teste e inspeção). O destino `kb` é planejado |
| `sync --remote` | planejado (Sync remoto) |
| `status` | planejado: hash do bloco relido na página = hash do arquivo |
| `install --codex` | planejado: registra o hook no Codex e grava o trust |
| `hook` | planejado: PostToolUse de edição e de shell, Stop e SessionStart |
| `validate`, `scan`, `plan`, `render-page` | existem |

```bash
S=<pasta desta skill>/scripts/env_docs_sync.py
python3 "$S" validate --root .                       # a config vale? (rc 2 com a lista de erros)
python3 "$S" scan --root .                           # Varredura: caminho e hash curto
python3 "$S" plan --root . --state <estado.json>     # o que mudou desde o último sync
python3 "$S" sync --root . --state <estado.json> --to-dir <pasta>
python3 "$S" render-page --root . --out <pagina.html>  # a página inteira, 0600, para o replace
```

Códigos de saída: 0 ok · 1 erro de E/S, de conteúdo ou do destino · 2 config inválida ou uso
errado. Nenhum subcomando imprime valor: só caminhos, ações, contagens e o início do hash.

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

- O valor de um `.env*` só vai para o corpo do Bloco de arquivo, que é o destino. Nunca vai para
  stdout, stderr, mensagem de erro, `repr` da operação ou estado. Erro inesperado sai só com o
  tipo da exceção, porque a mensagem dela pode carregar dados.
- O estado guarda o hash do arquivo inteiro, nunca o de um valor isolado: hash de uma senha curta
  sozinha se quebra por força bruta.
- O conteúdo segue ao destino por stdin ou por arquivo 0600, nunca em argv, que o `ps` mostra.
- O destino tem que ser menos exposto que a origem. O adaptador kb vai recusar escrever se a
  página for visível a algum papel fora de `doc.allowed_roles`.
- Os testes usam um canário (`CANARIO_7c1d`) e afirmam que ele chega ao destino e a nenhum outro
  lugar.

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
  sobrescrever a página é o filtro do Checkout da verdade, que entra com o hook.

## Testes

```bash
cd <pasta desta skill> && python3 -B -m unittest discover -s tests -v
```

Só biblioteca padrão, sem rede. O teste `test_sem_marcas_da_empresa.py` varre o pacote inteiro
atrás de marcas da empresa de origem, porque o repositório é público, e prova numa cópia sabotada
que o sensor reprova.
