# Destino kb: o contrato com a CLI de um BookStack

O plugin não traz a CLI `kb`: ela é uma dependência declarada. O caminho do script vem de
`doc.cli`, o interpretador de `doc.python` (os dois aceitam `~`, expandido pelo `HOME` do processo) e
o alvo de `doc.target`. Leia isto ao configurar o backend `kb`, ao depurar uma escrita recusada ou
ao migrar a página. O adaptador é `DestinoKb`, e a fábrica `destino_da_config` o monta.

## 1. O que o adaptador chama

Todo comando leva `--target <doc.target>` no fim. Nenhum argv carrega conteúdo de arquivo: o corpo
vai pelo stdin.

| Uso | Comando | O que o adaptador espera |
|---|---|---|
| ler a página | `pages read <id>` | JSON com `raw_html` (ou `html`). Nunca é impresso |
| trava | `content-permissions read page <id>` | JSON com `fallback_permissions` (`inheriting`, `view`, …) e `role_permissions[]` (`view`, `role.display_name`) |
| Bloco de arquivo | `page section-set <id> --heading=<caminho> --under=[<ambiente>] --create --stdin --changelog=<…> --apply` | rc 0 e JSON (`changed`, `revision_count`, `backup`) |
| migração | `page replace <id> --html=@- --confirm=<id> --changelog=<…> [--apply]` | sem `--apply`, rc 4 com contagens; com, rc 0 |

- **Códigos de saída da CLI:** 0 ok · 1 API ou rede · 2 uso · 3 integridade · 4 dry-run.
- **Erro:** a CLI escreve `{"error": {"code", "message", "backup"?}}` no stderr. O aviso do plugin
  repete `rc`, `code` e a mensagem (até 240 caracteres). Com `backup`, ele diz "a escrita pode ter
  ocorrido", porque a falha veio depois do snapshot. Um stderr que não é esse JSON não é ecoado.
- **Opções com `=`:** `--heading=<caminho>` e `--html=@-` chegam como um token só. Assim um caminho
  que começa por `-` não vira opção, e o `@-` não depende de como o parser da CLI trata `@`.
- **`changelog`:** `env-docs-sync: [<ambiente>] <caminho> @ <marca>`, cortado em 180 caracteres
  (o limite da API). A marca é o commit curto em development, `sha256:<12>` num ambiente remoto e
  `ausente` no callout. A migração usa `env-docs-sync: migração ao template @ <commit curto>`.

## 2. A trava (o destino menos exposto que a origem)

Antes da primeira escrita de cada rodada (bloco ou página inteira), o adaptador lê as permissões
da página. Ele recusa sem escrever, com `ErroDePermissao`, quando:

- `fallback_permissions.inheriting` não é `false`: herdar do livro não prova restrição;
- o fallback tem `view` diferente de `false`;
- algum item de `role_permissions` com `view` diferente de `false` tem um `role.display_name` fora de
  `doc.allowed_roles`.

A regra falha fechado: resposta sem um dos campos, item ilegível ou `view` nulo contam como
visível. A recusa vira aviso com exit 0 no hook e rc 1 na CLI, e o estado não muda.

## 3. A escrita de um bloco

1. **Trava**, uma vez por destino.
2. **Pula o que já está lá.** O adaptador relê o bloco. Se o `<pre>` já tem o hash do arquivo, e o
   callout "ausente desde" bate com a ação, devolve `False` e não chama o `section-set`. Sem isso, a
   linha "sincronizado em" mudaria o corpo a cada rodada, e cada host (que tem o próprio estado) ou
   cada estado perdido criaria uma revisão sem mudança de conteúdo.
3. **`section-set --create` em toda ação**, não só em `criar`. A CLI só cria quando o h3 falta;
   assim um bloco apagado à mão ou perdido numa migração volta, em vez de travar o sync com
   "heading não encontrado" a cada gatilho. A página é gerada, e o template diz isso.
4. **Relê e confere** (`bloco_confere`): o hash do conteúdo do `<pre>` relido tem que ser o do
   arquivo. Só então a operação entra no estado. Divergiu: aviso, e o estado não muda.

A localização do bloco (`corpo_da_secao`) segue a regra da CLI: texto exato do heading (sem tags,
entidades resolvidas, espaços colapsados), o h3 procurado só dentro da faixa do h2 `[ambiente]`, e
o corpo vai até o próximo heading de nível ≤ 3. h2 ou h3 repetido é erro.

## 4. A migração (`migrate`)

`migrate` renderiza a Página de ambientes inteira pelo template e a publica com `page replace`.
Ela lê **todos** os ambientes, inclusive os ssh. Se um deles falhar, nada é enviado, porque a página
nova perderia aqueles blocos. Ela passa pela mesma trava. Sem `--apply`, imprime o dry-run da CLI
(contagens de unidades, bytes e sha curto, nunca texto) e sai com rc 4. Com `--apply --state <arquivo>`,
grava o estado do que foi publicado.

## 5. Medido no KB de staging (2026-10-27)

Uma página sintética num livro sandbox do KB de staging (BookStack v26.09), com `.env*` sintéticos,
a config local do sandbox e a CLI `kb` com o `section-set` e o `replace` novos:

| Caso | Resultado |
|---|---|
| página herdando do livro | `migrate --apply` e `sync` recusam (rc 1, "herda"), revisão igual, sem estado |
| restrita a dois papéis permitidos + `Viewer` com `view` | `migrate --apply` recusa (rc 1, "Viewer"); o comando real do hook (Stop) sai 0 com aviso; revisão igual, sem estado |
| restrita aos papéis permitidos (fallback todo `false`) | `migrate` sem `--apply`: rc 4, revisão igual. Com `--apply`: rc 0, revisão +1. `status`: 3 `ok` |
| `.env` editado + comando real do hook (PostToolUse `Edit`) | 5,3 s, revisão +1. Os outros 2 blocos já estavam na página e foram pulados; o hash do bloco relido = o do arquivo |
| nada mudou | o Stop fica calado e a revisão não muda |
| outro host (estado vazio) | calado, revisão igual: os 3 blocos já estavam na página |
| K2: 1 byte trocado no bloco, direto na página | `status`: `diverge`, rc 3. `sync` com estado vazio reescreve só esse bloco, e o `status` volta a `ok` |

O caso K2 mostra um limite: o hook decide pelo estado local, então uma edição feita na **página**
não é desfeita enquanto o arquivo não muda. O `status` acusa, e um `sync` com estado novo conserta.
