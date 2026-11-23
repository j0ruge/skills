# retrofit-watch: modo autônomo — desenho

**Data:** 2026-11-23 · **Base:** `f099db4` · **Plugins:** `retrofit-watch` 0.3.7, `retrofit-skill` 0.10.3
· **Pesquisa de apoio:** a análise de como o Hermes Agent (NousResearch, commit `b98c388`) corrige as
próprias skills, fora do repo · **Caso-modelo:** o retrofit autônomo assistido da `git-housekeeping`
(`30d70f5`, v0.10.0)

## 1. Por quê

Hoje a `retrofit-watch` pede a retro no Stop hook, e cada lição só vira retrofit depois de dois "sim"
do dono: a pergunta "Rodo /retrofit-skill?" da `retrofit-watch` e o passo 3 do `retrofit-skill`
("Espere minha confirmação"). O dono disse o que incomoda: "ter que dizer sim a cada retrofit". A meta
maior dele é que todos os seus sistemas aprendam sozinhos.

Aprender sozinho quer dizer fechar o laço sem o dono: a lição sai de uma sessão e vale na próxima.
O `retrofit-skill` no modo full já faz o fim do laço: push, `claude plugin marketplace update`,
`claude plugin update` e `diff` do cache contra a loja. Falta tirar os dois "sim" e pôr no lugar
deles guardas que façam o papel do olho do dono.

## 2. Objetivos, não objetivos e anti-objetivos

**Objetivos da v1**

1. Um modo `auto` na `retrofit-watch`, escolhido na config, ao lado do modo manual de hoje.
2. No modo `auto`, uma lição de skill da loja (modo full) que passa nas guardas é publicada sem
   nenhum "sim": commit, bump, merge no `main`, push e update da cópia instalada.
3. Uma conferência independente de cada lição antes de qualquer edição.
4. Um portão de anonimização que substitui a leitura do diff pelo dono.
5. O que não passa numa guarda fica **segurado** num ramo local e chega ao dono numa linha. Só aquele
   retrofit espera. Os outros seguem.
6. O plugin mede o próprio modo autônomo e avisa o dono quando a próxima versão pode entrar.

**Não objetivos da v1**

- Kit (`sdd`): continua manual. Entra na v2.
- Skill de projeto (modo lean, num repo do dono fora da loja): continua manual. Entra na v3.
- A fila das sessões headless (`queue.jsonl`): continua manual. Ela é quase toda do kit.
- Investigar sozinho uma lição "sem correção verificada".
- Mudar a `description` de uma skill sem o dono.
- Outros sistemas do dono fora do que a `retrofit-watch` vigia.

**Anti-objetivos** (falha mesmo que funcione)

- Um nome de projeto, empresa ou pessoa, um caminho com nome de usuário, um e-mail ou um segredo
  chega ao `origin/main` da loja, que é pública.
- O fluxo autônomo dispara outra retro de si mesmo. O Hermes registra uma tempestade de ~142 recusas
  num laço assim.
- O modo autônomo escreve no checkout compartilhado da loja ou na árvore de trabalho da sessão.
- Uma regra nova acrescentada embaixo de uma regra que já existe, em vez de corrigir a que errou.
- Quem instala o plugin da loja pública recebe o modo autônomo sem pedir.

## 3. Restrições

- **O hook não lança subagente.** Ele só devolve `additionalContext` ao turno (`build_output` em
  `scripts/retrofit_watch.py`) e `systemMessage` ao dono. Quem despacha os subagentes é o agente da
  sessão, porque um subagente não despacha outro.
- **O hook tem 10 s de timeout** (`hooks/hooks.json`) e roda também no Windows: só biblioteca padrão,
  sem `fcntl`, stdio cp1252, path com `\` (v0.3.2).
- **A loja é pública.** Sem trailer `Co-Authored-By`, sem nome privado em arquivo nem em mensagem de
  commit (`CLAUDE.md` da loja, seção Git). O sensor `scripts/check-private-names.py` só conhece os
  nomes da lista de hashes (68 hoje) e não lê a mensagem do commit.
- **O hook de pre-commit da loja não está ligado em todo clone** (`core.hooksPath` vazio no clone
  medido). O fluxo autônomo chama os sensores ele mesmo.
- **A skill usada dentro de um subagente não aparece no transcript principal** (`SKILL.md`, Gotchas).
  O `retrofit-skill` rodado pelo executor não cala a `retrofit-watch` sozinho.
- **A base é o `origin/main` em `f099db4`.** A outra sessão que se supunha mexer na fonte da
  `retrofit-watch` confirmou em 2026-11-23 que não mexe: ela só triou a fila. Antes da primeira
  tarefa, a execução confere de novo o `origin/main` e faz rebase se ele andou.
- **Modelos por papel:** o revisor é Opus com esforço `xhigh`, o executor é Opus com esforço `medium`.
  O despacho passa `model` e `effort` explícitos.
- **Medidas da loja em 2026-11-23:** 34 plugins, 8 com `tests/`, 19 com `scripts/`; 19 commits de
  retrofit desde outubro.

## 4. Caminhos considerados

| Caminho | Ganho | Custo | Escolha |
|---|---|---|---|
| **1. O agente da sessão orquestra, pelo texto do hook** | A evidência está viva no contexto, que é a ideia fundadora da `retrofit-watch`. Reusa o `retrofit-skill` e o modelo da `git-housekeeping` | Depende de o agente seguir o texto. Gasta um pouco do contexto da sessão | **escolhido pelo dono** |
| 2. O hook lança um `claude -p` destacado | Não depende do agente. Sobrevive ao fim da sessão | Só tem o transcript. Sessão paga e invisível. É o escritor a mais que a 0.3 tirou de propósito | descartado |
| 3. Só a fila, processada depois (startup ou rotina) | Custo em lote | A lição vale dias depois. A evidência vem do transcript. Cron no WSL some ao reiniciar | descartado |

Para a anonimização, o dono escolheu o caminho C entre três: A (lista mais colheita local), B (só
vocabulário novo, julgado por revisor), C (A e B em camadas, com o portão aprendendo). O A sozinho
deixa passar o vazamento mais provável, uma pessoa ou um cliente citado numa lição. O B sozinho é
caro e vago.

Para a conferência de uma skill sem testes (26 de 34), o dono escolheu o revisor independente, entre
três: revisor independente; um sensor por lição (um teste que só procura a frase prova pouco); a
skill sem testes fica manual (26 de 34 sem aprender).

Para o alcance, o dono escolheu ir até o push, entre três: tudo sozinho; sozinho até o merge local e
push em lote; sozinho só até o commit num ramo. Os dois últimos deixam a lição esperando o push, e o
laço não fecha.

## 5. O desenho

### 5.1 O fluxo

```
Stop hook (modo auto)
  └─ additionalContext: faça a retro, grave as lições em <dados>/auto/<id>/licoes.json
agente da sessão
  ├─ grava licoes.json (só lições com evidência; formato da seção 5.3)
  ├─ despacha o REVISOR (Opus xhigh, sem o contexto da sessão) ──► veredito.json
  ├─ para cada skill com lição "publicável": um EXECUTOR (Opus medium, worktree próprio)
  │     └─ retrofit-skill no modo autônomo: edita, testa, audita, commita no ramo; NÃO faz push
  │        └─ grava termos-novos.json (camada 2 da anonimização)
  ├─ despacha o REVISOR de novo, só sobre termos-novos.json ──► anonimato.json
  └─ roda a PORTA: retrofit_watch.py publish <id>
        ├─ confere os três arquivos, roda a camada 1, os testes e o validate-versions
        ├─ fetch, rebase; push; marketplace update; plugin update; diff do cache
        └─ grava a linha no registro (publicado | segurado | erro) e cala a retro da skill
```

**A unidade é a skill, não a lição.** Um retrofit autônomo junta, num commit e num bump só, todas as
lições publicáveis de uma skill naquela retro. Assim três lições da mesma skill não dão três bumps que
conflitam no rebase. A lição segurada da mesma skill fica fora do commit. A porta confere cada lição do
commit no `veredito.json`. Skills diferentes podem ter executores em paralelo, cada um no seu
worktree; a trava da porta serializa os pushes.

Uma linha ao dono no fim, pelo agente da sessão: `retrofit-watch: <skill> vX.Y.Z publicada sozinha
(<sha>)` ou `retrofit-watch: <skill> segurada — <motivo> (ramo <ramo>)`.

### 5.2 Configuração

No `~/.claude/retrofit-watch.json`, ao lado das chaves de hoje:

| Chave | Valor | Padrão |
|---|---|---|
| `mode` | `manual`, `auto` ou `auto-dry` (faz tudo e para na porta, sem push) | `manual` |
| `manual` | lista de plugins ou skills que ficam sempre no modo manual | `[]` |
| `private_sources` | caminhos de denylists locais que a colheita lê (nunca copiados para repo) | `[]` |
| `harvest_roots` | pastas onde a colheita procura repos git | a definir pelo builder |
| `auto_limits` | tetos da seção 5.10 | os da seção 5.10 |

O padrão `manual` garante que quem instala a loja pública não recebe o modo autônomo. O
`RETROFIT_WATCH=off` continua desligando tudo.

### 5.3 O arquivo de lições (`licoes.json`)

O agente da sessão grava, fora de qualquer repo, no diretório de dados do plugin. O hook dá o caminho
absoluto no texto, porque o agente não enxerga `CLAUDE_PLUGIN_DATA`. Cada lição tem:

- skill-alvo e plugin;
- tipo: `pitfall` ou `melhoria`;
- a evidência: o comando ou erro observado, literal, e onde ele está no transcript (caminho e um
  identificador da entrada);
- o padrão de falha que a skill passaria a evitar;
- o que resolveu, ou `sem correção verificada`;
- se a correção muda a `description`.

As regras da `references/criteria.md` (seções 1 a 4) continuam valendo para escrever a lição.

### 5.4 O revisor (conferência do achado)

Um agente novo do plugin `retrofit-watch` (`agents/`, como o `deck-reviewer` da `html-presentation`),
com `tools: Read, Grep, Glob, Bash`. Ele não recebe o contexto da sessão: recebe o `licoes.json`, o
transcript para conferir a evidência, e lê a skill-alvo no `origin/main` **nesta revisão** (uma
citação anterior não vale, como no Hermes).

Para cada lição, ele preenche a tabela do caso-modelo:

| Pergunta | Resposta |
|---|---|
| A evidência está no transcript, como a lição diz? | sim / não |
| A skill já cobre a lição? Onde (`arquivo:linha`)? | não / sim, em … |
| A lição é genérica, ou só vale num projeto? | genérica / do projeto |
| Procede? Quando a evidência é um comando, rodá-lo de novo **numa cópia ou fixture** mostra a falha? | procede / não procede / não reproduzível |
| Cai na lista do que não capturar? (falha de ambiente, alegação negativa sobre ferramenta, erro transitório, narrativa de tarefa única) | não / sim, qual |

O revisor nunca roda o comando da evidência sobre o estado real. Se não há como montar a cópia, a
resposta é `não reproduzível`, e a lição só passa se a evidência do transcript bastar sozinha (o
revisor diz por quê).

Uma lição é **publicável** só com: evidência confirmada, não coberta, genérica, procede, fora da
lista do que não capturar, correção verificada e sem mudança de `description`. Qualquer outra
combinação segura a lição ou a descarta (coberta, do projeto, não procede).

A mesma definição roda uma segunda vez sobre `termos-novos.json` (seção 5.6, camada 2).

### 5.5 O executor (o retrofit)

Um subagente Opus `medium`, num worktree ligado novo da loja a partir do `origin/main`, ramo
`retrofit-auto/<skill>-<id>`. Ele segue o `retrofit-skill` no **modo autônomo**, uma variante nova do
modo full:

- não espera a confirmação do passo 3; exige o `veredito.json` com a lição publicável, ou com a única
  pendência "muda a `description`" (então prepara o ramo pronto e para antes da porta, seção 5.8);
- grava o baseline da `skill-quality-audit` e roda o gate dela, como hoje;
- corrige a frase que errou em vez de acrescentar uma regra nova; procura a regra já escrita antes;
- nas skills com `tests/`: escreve o teste que falha antes da correção, aplica a correção, mostra o
  teste passando e mata os mutantes da correção (o caso-modelo);
- faz o bump, o `CHANGELOG`, o `marketplace.json` e o README como o modo full;
- marca o commit com um trailer próprio, por exemplo `Retrofit-Mode: autonomous`, e nunca com
  `Co-Authored-By`;
- **não faz push** e não faz update da cópia instalada: isso é da porta;
- extrai os termos novos do diff e da mensagem do commit para `termos-novos.json` (seção 5.6).

### 5.6 O portão de anonimização (caminho C)

**Camada 1, mecânica, bloqueia sem hesitar.** Roda sobre as linhas acrescentadas do diff e sobre a
mensagem do commit, não sobre a árvore inteira:

- a lista de hashes da loja (`scripts/private-names.sha256`);
- a colheita local: nomes de repos git sob `harvest_roots`, dono e nome de cada `origin`, `user.name`
  e e-mail do git, usuário do `$HOME`, hostname, e os termos das `private_sources`;
- padrões: e-mail, caminho absoluto com nome de usuário (`/home/<u>`, `/mnt/<x>/<pasta>`,
  `C:\Users\<u>`), forma de segredo ou token;
- tira os termos da lista de públicos da loja.

A colheita nunca grava nome em repo. Ela vive só na memória do processo ou num arquivo fora de repo.

Medida de 2026-11-23 para calibrar: 72 nomes de pasta locais, 9 deles na lista de hashes; 23 aparecem
em algum arquivo da loja, quase todos palavra comum (`Files`, `Users`, `System`). Por isso a camada 1
olha só o que é novo no diff, e a lista de públicos existe.

**Camada 2, o revisor julga o vocabulário novo.** O executor separa cada termo das linhas novas e da
mensagem do commit com cara de nome próprio ou identificador (maiúscula no meio da frase, CamelCase,
dígito ou `_` dentro da palavra, caminho, URL) que não existe em nenhum arquivo da loja no
`origin/main` nem na lista de públicos. O revisor (seção 5.4) julga cada um: `público`, `privado` ou
`dúvida`, com a linha de contexto e os nomes da colheita como referência. Só `público` em todos deixa
passar.

**O portão aprende.** Num retrofit segurado por nome, a resposta do dono fecha o caso:

- "privado": o termo entra na lista de hashes (`check-private-names.py --add`), e o executor troca o
  termo por um genérico (`um projeto`, `<repo>`) e tenta a porta de novo;
- "público": o termo entra na lista de públicos, e a porta roda de novo.

**Antes da v1 ir ao ar:** a varredura inteira da loja com a colheita achou quatro nomes com cara de
projeto local que não estão na lista. O dono os classifica uma vez (privado vai à lista; público vai
à lista de públicos). Os nomes não entram neste arquivo.

### 5.7 A porta de publicação (`retrofit_watch.py publish <id>`)

O único caminho do modo autônomo até o `origin/main`, à moda do `skill_manage` do Hermes: o executor
não faz push. A porta é um subcomando do script do plugin, determinístico, e recusa (sai ≠ 0, grava
`segurado` com o motivo) quando:

1. falta o `veredito.json`, ou a lição não é publicável nele;
2. falta o `anonimato.json`, ou um termo não é `público`;
3. a camada 1 acha qualquer coisa, rodada de novo pela porta sobre o diff final e a mensagem;
4. os testes da skill, o `validate-versions.py` ou o gate da `skill-quality-audit` falham;
5. o commit tem `Co-Authored-By`, ou não tem a marca autônoma;
6. o `fetch` e o rebase sobre o `origin/main` dão conflito;
7. o teto da seção 5.10 foi atingido;
8. o `mode` é `auto-dry`.

O `aprovado.json` do dono (seção 5.11) substitui só o item que segurou aquele retrofit, nunca os itens
3 a 6.

Passando tudo: push, `claude plugin marketplace update`, `claude plugin update`, `diff` do cache contra
a loja, linha `publicado` no registro e marca no estado da sessão de que a retro daquela skill acabou.
Uma trava no diretório de dados serializa duas portas ao mesmo tempo.

### 5.8 O que segura um retrofit

Há dois tipos de lição que não sai sozinha, conforme a correção já é conhecida ou não:

| Caso | A correção é conhecida? | O que fica |
|---|---|---|
| lição que muda a `description` | sim | um **ramo pronto**: o executor roda e para antes da porta |
| recusa da porta (anonimização, testes, rebase, teto, `auto-dry`) | sim | o ramo que o executor já fez |
| lição `sem correção verificada` | não | só a linha `segurado` no registro e a proposta ao dono, como hoje (investigar antes) |
| lição `não reproduzível` sem evidência bastante no transcript | não se sabe se procede | só a linha `segurado` e a proposta ao dono, como hoje |

Com ramo pronto, o "sim" do dono é uma palavra, porque o trabalho já está feito. Sem correção
conhecida, não há o que preparar.

O dono recebe uma linha no fim do turno e o resumo no startup seguinte. Nada é apagado: o ramo e o
worktree ficam até o dono decidir.

**Como o dono libera ou descarta (seção 5.11).**

### 5.9 O registro, o aviso de startup e o critério da próxima versão

**O registro:** `${CLAUDE_PLUGIN_DATA}/autonomo.jsonl`, só de acréscimo, uma linha por retrofit:
instante, sessão, skill, id, resultado (`publicado`, `segurado`, `descartado`, `erro`), motivo,
commit, ramo e versão.

**O aviso de startup** (o `pending` de hoje, ampliado; uma linha ao dono, fora do contexto):

- retrofits segurados à espera do dono, com o ramo de cada um;
- worktrees de retrofit autônomo sem registro de fim (a sessão fechou no meio);
- quando o critério da próxima versão se cumpre.

**O critério da v2 (o kit entra), escolhido pelo dono:** pelo menos 10 retrofits autônomos publicados
e 14 dias de uso, sem nenhum revertido pelo dono e sem nenhum achado do sensor de nomes, no
`origin/main`, num arquivo que um commit autônomo tocou. "Revertido" se mede por um commit no
`origin/main` que reverte um commit com a marca autônoma. O aviso fica assim, por exemplo:
`retrofit-watch: 10 retrofits autônomos, 0 revertidos, 0 nomes vazados desde <data> — o kit pode entrar (ver a spec do modo autônomo)`.

O critério da v3 (lean entra) usa a mesma forma, contado a partir da v2.

### 5.10 Custos e limites

Propostas minhas, na config (`auto_limits`):

- no máximo 2 retrofits autônomos por skill por sessão (o mesmo teto das retros de hoje); como a
  unidade é a skill (seção 5.1), o teto não corta lições: uma retro com cinco lições da mesma skill é
  um retrofit só;
- no máximo 3 retrofits autônomos por sessão, somando as skills;
- o fluxo autônomo não conta como trabalho ou atrito da skill para o gatilho (anti-objetivo da
  tempestade).

**Modo de permissão.** Fora do modo bypass, o fluxo pediria permissão para gravar fora do projeto,
criar o worktree e fazer o push, e um subagente em segundo plano pode não conseguir pedir. O hook já lê
o `permission_mode` do payload (para o modo `plan`). O modo `auto` só vale com `bypassPermissions`. Em
outro modo, o hook manda o texto do modo manual, e a linha ao dono diz por quê. O plugin não grava
regra `allow` nas configurações do dono.

**Entrypoint do transcript.** O modo `auto` exige também `"entrypoint":"cli"` no transcript da sessão.
Medido em 2026-11-23: as fases headless de um `sdd run` lançado de uma sessão interativa herdam
`CLAUDE_CODE_SESSION_ATTENDED=1` e `CLAUDE_CODE_ENTRYPOINT=cli` dela, e o transcript delas diz
`"entrypoint":"sdk-cli"`. O gate de hoje lê primeiro o ambiente e tomaria a fase por assistida. Nenhuma
das 6 fases medidas recebeu pedido de retro, mas no modo `auto` o erro lançaria um retrofit autônomo
dentro do run. Com outro `entrypoint`, a entrada segue o comportamento de hoje, e o motivo é
`entrypoint`.

### 5.11 O retrofit segurado: liberar ou descartar

Um verbo novo, ao lado do `pendentes` de hoje: `/retrofit-watch:retrofit-watch segurados`. Ele lista
os segurados do registro sem linha de fim, com o motivo, o ramo e o worktree. Para cada um, o dono diz:

- **liberar:** o "sim" vira um arquivo de aprovação do dono no diretório de dados (`aprovado.json`,
  com o id e o instante). A porta aceita esse arquivo no lugar do item que segurou, mas roda **todas** as
  outras guardas de novo: camada 1, testes, `validate-versions.py`, rebase. Num segurado por nome, o
  "privado" ou o "público" do dono ensina o portão (seção 5.6) antes de a porta rodar. Num segurado sem
  ramo (sem correção conhecida), liberar é o fluxo manual de hoje: o `/retrofit-skill`;
- **descartar:** uma linha `descartado` no registro. O ramo e o worktree ficam, porque nada é apagado;
  a limpeza é da `git-housekeeping`, com o sim do dono.

Um retrofit liberado pelo dono é publicado com a marca `Retrofit-Mode: autonomous-approved` e **não**
conta nos 10 do critério da v2, que mede o que saiu sem ele. Um segurado descartado também não conta.

## 6. Decisões do dono (23/11)

- O porquê e a meta (seção 1).
- O alcance: até o push e o update da cópia instalada, sem "sim".
- A anonimização pelo caminho C, com as quatro guardas: conferência do achado, sensor de nomes,
  update da cópia instalada, rastro com marca e aviso.
- A conferência por revisor independente; nas skills com testes, também teste antes e mutante depois.
- O escopo por versão: v1 a loja, v2 o kit, v3 lean.
- O critério da v2 (seção 5.9).
- O caminho 1 de construção.
- O plano que sair deste desenho passa por uma revisão do Fable antes da execução.

## 7. Decisões minhas, para o dono corrigir

- O gatilho do modo `auto` é o mesmo Stop hook de hoje, com os mesmos sinais e limiares.
- O modo se escolhe no `~/.claude/retrofit-watch.json`; o padrão é `manual`; há a lista `manual`.
- O modo `auto-dry`, que faz tudo e para na porta.
- A porta como subcomando do script do plugin, e não um passo do executor.
- O revisor como agente do plugin `retrofit-watch`; o modo autônomo como variante do modo full do
  `retrofit-skill`.
- Os tetos da seção 5.10.
- O revisor roda o comando da evidência só numa cópia ou fixture.
- A camada 1 olha só o que é novo no diff e na mensagem, não a árvore inteira.
- A unidade de um retrofit autônomo é a skill: as lições publicáveis dela num commit e num bump.
- Ramo pronto só quando a correção é conhecida; sem ela, o segurado é uma linha e a proposta de hoje.
- O verbo `segurados`, a aprovação do dono por arquivo e a porta rodando as outras guardas de novo; o
  liberado e o descartado não contam no critério da v2.
- O modo `auto` só com `bypassPermissions`; fora dele, o texto do modo manual.

## 8. O que fica para quem constrói

- A sintaxe do modo autônomo no `retrofit-skill` (argumento, flag ou arquivo de veredito).
- Os nomes e o formato exato de `licoes.json`, `veredito.json`, `termos-novos.json` e `anonimato.json`.
- Onde mora a camada 1: um modo novo do `check-private-names.py` (por exemplo `--diff` e nomes extras
  por arquivo) ou um script novo da loja; a lista de públicos e o nome dela.
- O padrão de `harvest_roots` e a profundidade da busca de repos.
- Como o agente da sessão marca no estado que a retro de uma skill acabou quando o executor rodou o
  `retrofit-skill` dentro de um subagente.
- Os testes: biblioteca padrão, a fixture de HOME da suíte de hoje, uma loja fixture (repo `--bare`
  como `origin` e um clone) para a porta; cada guarda nova com caso sabotado e mutante morto.
- A versão: `retrofit-watch` 0.4.0 e `retrofit-skill` 0.11.0, com `CHANGELOG`, `marketplace.json` e
  README no mesmo incremento.

## 9. Riscos conhecidos

- **O agente da sessão pode não seguir o texto do hook.** O mesmo risco existe hoje no modo manual.
  A porta não deixa um retrofit sem veredito chegar ao `origin/main`, mas não obriga ninguém a abrir o
  fluxo.
- **O revisor é um LLM.** Ele erra. A camada 1 da anonimização não depende dele; a conferência do
  achado depende. O critério da v2 conta os reverts do dono para medir esse erro.
- **Contexto da sessão.** Cada retrofit autônomo gasta o despacho e o relatório no contexto da sessão.
  Os relatórios voltam em uma linha.
- **Push público sem olho humano.** O anti-objetivo principal. A camada 1 roda duas vezes (no executor e
  na porta), e a camada 2 segura qualquer termo novo duvidoso.
