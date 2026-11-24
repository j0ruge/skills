# Modo autônomo: o fluxo da sessão

Esta página é para o agente da sessão do dono. Leia-a inteira ao receber o pedido autônomo do Stop hook
(`[modo autônomo: …]`) ou o verbo `/retrofit-watch:retrofit-watch segurados`.

No pedido autônomo, não pergunte nada ao dono sobre as skills do pedido. O dono só fala no passo 6.
Não rode o `/retrofit-skill` nesta sessão: quem o roda é o executor, num worktree próprio.

Dois nomes valem em toda a página:

- `retrofit_watch.py` é o comando que o pedido do hook dá: `"<python>" "<script>"`, com os dois caminhos
  absolutos. Fora do pedido (no verbo `segurados`), o script é `scripts/retrofit_watch.py` desta skill.
- `<dados>` é a pasta-mãe de `auto/` no caminho do `licoes.json` que o pedido dá.

A loja é o clone da chave `store` do `~/.claude/retrofit-watch.json`. Esse clone é o checkout
compartilhado: ninguém escreve nele. Cada lote tem o seu worktree.

## Formatos

| Arquivo | Diretório | Quem grava | Chaves |
|---|---|---|---|
| `pedido.json` | `<dados>/auto/<id>/` | o hook | `id`, `sessao`, `ts`, `transcript`, `cwd`, `modo`, `skills` |
| `licoes.json` | `<dados>/auto/<id>/` | você (passo 1) | `id`, `licoes` (o exemplo do passo 1) |
| `veredito.json` | `<dados>/auto/<id>/` | o revisor, primeira passada | `id`, `base`, `licoes` (o parecer de cada lição) |
| `retrofit.json` | `<dados>/auto/<id>/<lote>/` | o `prepare` e o `seal` | `id`, `lote`, `plugin`, `tipo`, `tentativa`, `worktree`, `ramo`, `base`, `licoes`, `fases`, `commit`, `versao`, `patch` |
| `termos-novos.json` | `<dados>/auto/<id>/<lote>/` | o `seal` | `patch`, `termos` (cada um com `termo`, `onde`, `contexto`) |
| `anonimato.json` | `<dados>/auto/<id>/<lote>/` | o revisor, segunda passada | `patch`, `termos`, `regra_repetida`, `fora_das_licoes` |
| `aprovado.json` | `<dados>/auto/<id>/<lote>/` | o `approve` | `id`, `lote`, `ts`, `motivos` |
| `colheita.txt` | `<dados>/` | o `harvest` | um nome privado por linha; nunca vai a repo |
| `autonomo.jsonl` | `<dados>/` | a triagem, a porta e os verbos | uma linha por lote ou por lição sem ramo |

Os arquivos de lote ficam no diretório do lote. Com dois lotes, um arquivo no diretório da retro seria
sobrescrito.

## 1. As lições

Faça a retro pelas seções 1 a 4 do `criteria.md`: só lições desta sessão, cada uma com a evidência e o
padrão de falha. Sem lição, responda só `retro <skill>: sem lições novas` e não grave nada.

Com lição, grave o `licoes.json` no caminho que o pedido dá, com a ferramenta `Write`:

```json
{
  "id": "<id do pedido>",
  "licoes": [
    {
      "n": 1,
      "plugin": "<plugin>",
      "skill": "<skill>",
      "tipo": "pitfall",
      "evidencia": {
        "texto": "<o comando ou o erro, literal>",
        "transcript": "<caminho do transcript>",
        "entrada": "<o uuid da entrada do transcript>"
      },
      "padrao": "<o padrão de falha que a skill passa a evitar>",
      "resolveu": "<o que resolveu>",
      "muda_description": false
    }
  ]
}
```

- `n` começa em 1 e não se repete. `tipo` é `pitfall` ou `melhoria`.
- `resolveu: null` quer dizer "sem correção verificada". A lição fica, e a triagem a segura.
- `muda_description: true` quando a correção muda a `description` da skill.
- Nunca cite valor de segredo, nem na evidência.

## 2. O revisor, primeira passada

Despache o revisor com a ferramenta `Agent`:
`subagent_type: "retrofit-watch:retrofit-reviewer"`, `model: "opus"`, `effort: "xhigh"`.

O prompt leva só três coisas: o diretório da retro (`<dados>/auto/<id>/`), o caminho da loja e "primeira
passada". Não ponha no prompt o contexto da sessão, um resumo das lições ou a sua opinião. O valor do
revisor está em não saber o que você sabe.

Espere a resposta. Confira que `<dados>/auto/<id>/veredito.json` existe. Sem ele, ou com o `triage` do
passo 3 saindo 2 por causa dele (ausente ou inválido), despache o revisor de novo, uma vez, com o mesmo
prompt. Se o arquivo ainda faltar ou ainda for inválido, pare: não rode a triagem e deixe o pedido aberto.
Diga ao dono, em uma linha, que o revisor não gravou um `veredito.json` válido. Nunca grave nem conserte
o arquivo você mesmo (passo 9).

## 3. A triagem

Rode `retrofit_watch.py triage <id>`. A saída é um JSON com três listas:

- `lotes`: o que vai ao passo 4. Cada lote tem `lote`, `plugin`, `tipo` e `licoes`. O lote `<plugin>` é do
  tipo `auto`. O lote `<plugin>__description` leva as lições que mudam a `description`: ele vira um ramo
  pronto, e a porta o segura com `muda-description`.
- `segurar`: a triagem já gravou a linha `segurado` de cada lição. Não faça nada agora: elas entram na
  linha ao dono e no verbo `segurados`.
- `descartar`: a triagem já gravou a linha `descartado`. Não faça nada: elas ficam fora do aviso de
  startup.

Rodar a triagem de novo não repete linha. Com rc 2 e a mensagem sobre o `veredito.json`, volte ao passo 2.

## 4. Por lote

Para cada lote, nesta ordem:

1. `retrofit_watch.py prepare <id> <lote>`. Ele faz `git fetch origin` na loja e cria o worktree do lote
   e o ramo `retrofit-auto/<lote>-<id>`. A saída é o `retrofit.json`.
2. Antes da primeira segunda passada da retro, rode `retrofit_watch.py harvest` uma vez. Ele grava
   `<dados>/colheita.txt`, que o revisor usa como referência.
3. Despache o executor com a ferramenta `Agent`:
   `subagent_type: "general-purpose"`, `model: "opus"`, `effort: "medium"`. Use este prompt-modelo:

   > Você é o executor de um retrofit autônomo. Trabalhe só no worktree `<worktree>`, no ramo `<ramo>`.
   > Leia `plugins/retrofit-skill/commands/retrofit-skill.md` nesse worktree e rode
   > `<plugin> --auto <dir do lote>` como ele manda. O `<dir do lote>` é `<dados>/auto/<id>/<lote>/`:
   > lá está o `retrofit.json`, e o `veredito.json` está na pasta-mãe. Não faça push e não rode
   > `claude plugin`. Não escreva no clone `<loja>`. O último passo é
   > `"<python>" "<script>" seal <id> <lote> --licoes <n,…> [--fases <fases>]`. O selo grava sozinho a
   > linha `segurado` com `executor-recusou` para cada lição do lote fora do `--licoes`. Responda em
   > até 5 linhas: o commit, a versão, as lições incluídas e as deixadas de fora, as fases e o
   > resultado do `seal`.

   Não chame `hold` para as lições que o selo deixou de fora: o `seal` já as segurou. Sem selo (o
   `commit` do `retrofit.json` continua `null`), vá ao passo 7.
4. Despache o revisor na segunda passada, com os mesmos `subagent_type`, `model` e `effort` do passo 2.
   O prompt leva o diretório da retro, o caminho da loja, "segunda passada", o diretório do lote e o
   worktree. Confira que `<dados>/auto/<id>/<lote>/anonimato.json` existe. Sem ele, despache o revisor
   de novo, uma vez, com o mesmo prompt. Se ele ainda faltar, pare este lote e deixe o pedido aberto.

   Uma lista grande de termos novos é normal: mais de cem, quase todos identificadores de código. O
   revisor julga cada termo, um por um. Nunca aceite um veredito só para a lista inteira. Um nome da
   colheita é `privado`, mesmo quando também é um identificador. Fora dela, um identificador, um nome de
   arquivo do diff ou uma palavra comum é `publico`. `duvida` fica para o termo que pode ser nome de
   pessoa, projeto, empresa, máquina ou usuário e que o contexto não decide.
5. Rode `retrofit_watch.py publish <id> <lote>` com `run_in_background: true`. A porta espera a trava por
   até 900 s, e o Bash em primeiro plano corta em 600 s. Espere a notificação. Leia o rc e a última
   linha do stdout, e siga a seção 5 desta página.

Lotes de plugins diferentes podem correr em paralelo, cada um no seu worktree: a trava da porta
serializa os pushes. Lotes do mesmo plugin correm em sequência, o `auto` antes do `description`, na
ordem que a triagem dá.

Na loja real, dois lotes de plugins diferentes que tocam linhas vizinhas do README dão conflito no
rebase. O segundo sai segurado com `rebase`. A saída é a do passo 6 (`prepare --redo`).

**O executor fora deste passo.** As saídas do passo 6 e da tabela do passo 8 que dizem "o executor
corrige…" usam o mesmo despacho do item 3: o mesmo `subagent_type`, `model` e `effort`, com a tarefa da correção no lugar do `--auto`.
O prompt leva o worktree, o ramo, o motivo e o `detalhe` da linha do registro, e a correção pedida.
O executor emenda o commit (`git -C <worktree> commit --amend`), mantém o trailer `Retrofit-Mode` e
termina com o `seal` de novo. Depois, o revisor refaz a segunda passada (item 4), e a porta roda (item 5).
No lote segurado por nome que o dono ensinou (passo 6), o `approve` vem antes dessa porta, logo depois da
palavra do dono.

## 5. A linha ao dono

A última linha do stdout do `publish` é a frase ao dono. Ela tem uma destas duas formas:

- `retrofit-watch: <plugin> vX.Y.Z publicada sozinha (<sha>)`
- `retrofit-watch: <plugin> segurada — <motivo> (ramo <ramo>)`

Copie a frase que a porta imprimiu, uma linha por lote, no fim do turno. Para a lição que a triagem
segurou sem ramo, use a segunda forma com `(sem ramo)` no lugar do ramo. Depois de uma publicação, peça
ao dono `/reload-plugins`: até lá, a sessão roda a cópia velha.

Todo `publish`, também o que a tabela manda rodar de novo, vai com `run_in_background: true`.

| rc | O que houve | O que fazer |
|---|---|---|
| 0 | publicado, com a cópia instalada em dia (ou o plugin não está instalado) | a frase e o pedido de `/reload-plugins` |
| 1 | segurado | a frase; o item entra no verbo `segurados` (passo 6) |
| 2 | erro de uso, ou a pasta de dados ausente: nada foi gravado | o comando saiu errado; confira o `<id>` e o `<lote>` e rode de novo |
| 3 | erro: `fetch`, `push`, `trava` ou `interno` | tire a causa (o `detalhe` da linha) e rode `publish` de novo; a porta retoma de onde parou |
| 4 | publicado, com a cópia instalada atrás | a frase, que diz o estado da instalação; rode `publish` de novo, que refaz só a instalação |

## 6. O verbo `segurados`

Nunca rode `approve`, `--publico-add` nem `--add` sem a palavra do dono nesta conversa.

Rode `retrofit_watch.py held`. Ele lista os itens em aberto (a última linha é `segurado` ou `erro`), com o
motivo, o ramo e o worktree. Mostre cada item ao dono, com o motivo da tabela do passo 8, e espere a
palavra dele:

- **liberar:** `retrofit_watch.py approve <id> <lote>`, depois `retrofit_watch.py publish <id> <lote>`. A
  aprovação substitui só o motivo da última recusa, e só se ele é substituível. A porta roda todas as
  outras guardas de novo. Se ela segurar de novo por outro motivo, leve esse motivo ao dono.
- **descartar:** `retrofit_watch.py discard <id> <item>`. O motivo padrão é `descartado-pelo-dono`. O
  ramo e o worktree ficam.

Um item em `erro` não se aprova: tire a causa e rode `publish` de novo (rc 3 da seção 5).

Os casos que pedem mais do que isso:

- **Segurado por nome** (`nome-privado`, `termo-nao-publico`, `sem-anonimato`): a aprovação não substitui
  a recusa. Só a resposta do dono sobre o termo, que ensina o portão.
  - "privado": rode `python3 "<worktree>"/scripts/check-private-names.py --add <termo>`. Depois, o
    executor (o despacho do passo 4) troca o termo por um genérico (`um projeto`, `<repo>`), no diff e
    na mensagem. Ele emenda o commit com a mudança da lista dentro dele e sela de novo. O revisor refaz a
    segunda passada.
  - "público": rode `python3 "<worktree>"/scripts/anonymity-gate.py --publico-add <termo>`. Depois,
    `git -C "<worktree>" commit -a --amend --no-edit`. A mudança da lista entra no commit emendado, e a
    mensagem fica a mesma. O `patch` não conta as listas e conta a mensagem: assim ele não muda, e a
    segunda passada continua valendo.
  - Os dois scripts gravam a lista ao lado deles: a do worktree, nunca a do checkout compartilhado. Uma
    lista mudada fora do commit segura o lote com `arvore-suja`.
  - Nos dois: `approve` logo depois da palavra do dono, antes de qualquer `publish`; depois, `publish`.
    O `approve` grava o motivo da última recusa por nome do lote, e é ele que deixa a porta aceitar a lista
    mudada. Um `publish` antes do `approve` segura o lote com `escopo`; o `approve` seguinte ainda grava
    o motivo de nome, e o `publish` depois dele passa.
  - Com `sem-anonimato`, o revisor refaz antes a segunda passada. Se um termo continuar não público, vale
    o par acima.
- **Segurado por `rebase`:** `retrofit_watch.py prepare <id> <lote> --redo`. Ele abre um worktree e um ramo
  novos, e o lote recomeça no passo 4. O worktree anterior fica.
- **Segurado por `revisao-desatualizada`:** sele de novo com
  `retrofit_watch.py seal <id> <lote> --licoes <n,…> [--fases <fases>]`, com as `licoes` e as `fases`
  do `retrofit.json`. O revisor refaz a segunda passada. Depois, `publish`.
- **Segurado sem ramo** (a lição que a triagem segurou): o `/retrofit-skill` manual, com o dono, no fluxo
  de sempre. Depois, `retrofit_watch.py discard <id> <item> --motivo resolvido-manual`.

## 7. O executor que falha

Se o executor falha, recusa o lote inteiro ou não chega ao selo, rode
`retrofit_watch.py hold <id> <id>/<lote> <motivo>`, com `executor-falhou` ou `executor-recusou`. O item
entra no verbo `segurados`. A lição que o selo deixou de fora já tem a linha dela.

## 8. A tabela de motivos

"Substituível" diz se a aprovação do dono (`approve`) substitui a recusa. "O executor corrige" é o
despacho do executor fora do passo 4, descrito no fim dele.

| Motivo | O que quer dizer | Substituível | Saída |
|---|---|---|---|
| `coberta` | a skill já cobre a lição; o `arquivo:linha` vai no detalhe | não | nenhuma: a lição está descartada |
| `do-projeto` | a lição só vale num projeto | não | a memória ou o `CLAUDE.md` do projeto (seção 3 do `criteria.md`) |
| `nao-procede` | a cópia ou a fixture não mostra a falha | não | nenhuma: a lição está descartada |
| `sem-evidencia` | a evidência não está no transcript como a lição diz | não | nenhuma: a lição está descartada |
| `nao-capturar` | a lição cai na lista do que não capturar | não | nenhuma: a lição está descartada |
| `sem-veredito` | a lição não tem parecer, ou o `veredito.json` falta ou é inválido | sim | no lote, `approve` e `publish`; na lição sem ramo, o `/retrofit-skill` manual e o `discard` |
| `fora-do-pedido` | a lição é de um plugin que o pedido não trouxe, excluído ou da lista `manual` | não | o `/retrofit-skill` manual e o `discard` com `resolvido-manual` |
| `nao-reproduzivel` | não houve cópia para rodar a evidência, e o transcript não basta | não | investigar com o dono, o `/retrofit-skill` manual e o `discard` com `resolvido-manual` |
| `sem-correcao` | a lição não tem correção verificada (`resolveu: null`) | não | investigar e verificar a correção, o `/retrofit-skill` manual e o `discard` com `resolvido-manual` |
| `descartado-pelo-dono` | o dono descartou o item | não | nenhuma: o ramo e o worktree ficam |
| `resolvido-manual` | o dono resolveu o item pelo `/retrofit-skill` manual | não | nenhuma |
| `executor-falhou` | o executor falhou ou não chegou ao selo | não | o dono decide: o `/retrofit-skill` manual e o `discard` com `resolvido-manual`, ou só o `discard` |
| `executor-recusou` | o executor deixou a lição ou o lote fora do commit | não | o dono decide, como no `executor-falhou` |
| `escopo` | o worktree ou o ramo não são os do lote, o ramo tem mais de um commit, um arquivo está fora do escopo, ou uma lista do portão mudou sem a aprovação por nome | não | o executor corrige o ramo e sela de novo; o revisor refaz a segunda passada; `publish` |
| `arvore-suja` | o worktree tem mudança fora do commit | não | o executor põe a mudança do lote no commit e sela de novo; outra mudança vai ao dono |
| `rebase` | o rebase sobre o `origin/main` deu conflito | não | `prepare --redo` e o passo 4 |
| `coautoria` | o commit tem `Co-Authored-By` | não | o executor emenda a mensagem sem o trailer e sela de novo; o revisor refaz a segunda passada; `publish` |
| `sem-marca` | falta o trailer `Retrofit-Mode: autonomous` | não | o executor emenda a mensagem com o trailer e sela de novo; o revisor refaz a segunda passada; `publish` |
| `sem-bump` | a versão do `plugin.json` no commit não é maior que a do `origin/main` (comparada por número, `X.Y.Z`) | não | o executor sobe a versão nos quatro lugares, emenda e sela de novo; o revisor refaz a segunda passada; `publish` |
| `nao-publicavel` | uma lição do commit não sai como publicável no veredito | sim | `approve` e `publish` |
| `muda-description` | o lote `description` tem o ramo pronto, ou um lote `auto` muda a `description` (no `plugin.json`, no bloco do `marketplace.json` ou num `SKILL.md` do plugin, contra o `origin/main`, com ou sem a flag `muda_description`) | sim | `approve` e `publish` |
| `nome-privado` | a camada 1 achou um nome, um e-mail, um caminho com usuário ou um segredo | não | o dono diz "privado" ou "público" (passo 6); um segredo sai do commit |
| `sem-anonimato` | falta o `anonimato.json`, ou ele é inválido | não | o revisor refaz a segunda passada; `publish` |
| `revisao-desatualizada` | o `patch` do `anonimato.json` não é o do commit | não | selar de novo, a segunda passada e `publish` |
| `termo-nao-publico` | um termo novo não é `publico` na segunda passada | não | o dono diz "privado" ou "público" (passo 6) |
| `regra-repetida` | o revisor diz que a mudança repete ou contradiz uma regra já escrita | sim | `approve` e `publish`, ou o executor corrige a frase que errou e o lote volta à segunda passada |
| `diff-alem-das-licoes` | o revisor diz que o diff faz mais do que as lições | sim | `approve` e `publish`, ou o executor tira o excesso e o lote volta à segunda passada |
| `testes` | um teste do plugin ou da raiz falhou, ou o ramo tira uma pasta de testes | não | o executor corrige, emenda e sela de novo; o revisor refaz a segunda passada; `publish` |
| `validate-versions` | o `validate-versions.py` saiu diferente de 0 | não | o executor corrige as versões, emenda e sela de novo; o revisor refaz a segunda passada; `publish` |
| `auditoria` | o gate da auditoria achou uma linha `NOVO`, ou o auditor falta no worktree | não | o executor corrige, emenda e sela de novo; o revisor refaz a segunda passada; `publish` |
| `fase-de-auditoria` | falta no selo uma fase da auditoria que a mudança exige | não | o executor roda a fase e sela de novo com ela no `--fases`; o revisor refaz a segunda passada; `publish` |
| `teto` | o teto de `auto_limits` da sessão foi atingido | sim | `approve` e `publish` |
| `auto-dry` | o `mode` é `auto-dry`: nada se publica | sim | `approve` e `publish` |
| `fetch` | o `git fetch origin` da porta falhou | não | tirar a causa e rodar `publish` de novo |
| `push` | o push da porta falhou | não | tirar a causa e rodar `publish` de novo |
| `trava` | a trava da porta não veio em 900 s | não | rodar `publish` de novo |
| `interno` | uma exceção dentro da porta | não | ler o `detalhe` e rodar `publish` de novo; repetida, levar ao dono |

## 9. O que nunca fazer

- Nunca faça push fora da porta. O único caminho até o `origin/main` é o `publish`.
- Nunca escreva no checkout compartilhado da loja. Edição, commit e selo acontecem no worktree do lote.
- Nunca apague um ramo ou um worktree, nem de um lote descartado. A limpeza é da `git-housekeeping`, com
  o "sim" do dono.
- Nunca grave nem corrija `veredito.json` ou `anonimato.json`: só o revisor os grava. A porta não sabe quem
  gravou esses arquivos, e um arquivo gravado pela sessão passaria por cima do revisor independente.

## O aviso de startup

O aviso de startup junta numa linha ao dono um segmento por assunto:

- `N retrofits segurados (…) — /retrofit-watch:retrofit-watch segurados`: o verbo `segurados` (passo 6).
- `N retrofits autônomos sem registro de fim (…)`: uma sessão fechou no meio do fluxo. Num lote com
  `retrofit.json` e sem linha, confira o selo e o `anonimato.json` e rode `publish`; sem selo, rode
  `hold` com o motivo do executor (passo 7). Numa retro com lição sem linha, rode `triage <id>` de novo
  e leve cada lote dela ao passo 4. Se o `triage` sair 2 por causa do `veredito.json`, volte ao passo 2.
- `N plugins com a cópia instalada atrás da última publicação (…)`: o aviso conta só a última publicação
  de cada plugin, o lote com o push mais recente. Uma publicação mais nova do mesmo plugin substitui a
  anterior: um lote antigo que ficou atrás sai do aviso, e não precisa de `publish` de novo. O aviso só
  nomeia os plugins. O `<id>` e o `<lote>` estão na linha `publicado` do lote mais recente de cada plugin
  em `<dados>/autonomo.jsonl` (chaves `id` e `lote`). Rode `publish <id> <lote>` desse lote de novo.
- `… — o kit pode entrar (…)`: o critério da v2 se cumpriu. Só informa.
