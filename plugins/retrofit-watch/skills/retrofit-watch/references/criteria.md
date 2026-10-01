# Critérios da retro de uma skill

Adaptado de `self-learning` (kulaxyz/self-learning-skills, MIT, commit `1304fce`, 2026-09-14):
sinais do momento, regra de promoção, triagem e auto-audit de segredos. A diferença de
propósito: a `self-learning` **cria** uma skill nova sozinha. Aqui a lição vai para uma skill que
**já existe**, e só pelo `/retrofit-skill`, que pede confirmação.

O formato do bloco segue o "Loop de auto-melhoria" de um agente de propostas de
um projeto interno: lição genérica → retrofit, lição do projeto → patch local, nenhuma → "sem lições
novas".

## 1. Sinais de que existe lição

Qualquer um destes, **ligado à skill em questão**:

- a tarefa só deu certo **depois de tentativas**, de um caminho errado ou de uma correção sua;
- a skill **mandou fazer algo que falhou**: comando, flag, path ou versão desatualizados;
- a skill **não avisou** de algo que mordeu: pré-requisito, efeito colateral, ordem de passos;
- foi preciso **descobrir** um fato que a skill deveria trazer (onde fica o arquivo, qual
  sensor usar);
- um passo da skill **sobrou** ou foi pulado sem prejuízo, o que é candidato a enxugar;
- você disse "lembra disso", "isso devia estar na skill", "não quero explicar de novo".

Pressa, cansaço e sessão longa não são sinais. Errar um comando por digitação não é lição da
skill.

## 2. Filtro: só passa o que tem evidência

Cada lição precisa dos três itens abaixo. Se faltar um, ela não sai no bloco:

1. **Evidência:** o comando, o erro ou a saída observada nesta sessão. "Pareceu", "acho que"
   e "costuma" não contam.
2. **Padrão de falha com nome:** o que a skill passa a evitar. Por exemplo, "cache antigo →
   erro fantasma de tipo". "Às vezes quebra" não serve.
3. **Escopo:** a lição vale para outros usos da skill, não só para este repositório.

E mais um, que muda a recomendação:

4. **O que resolveu:** o comando ou passo que funcionou e como você soube (teste passou, exit
   0, dado conferido). Se nada resolveu, a lição **continua valendo**: uma instrução da skill
   que falhou, como um path inexistente, uma flag removida ou um passo fora de ordem, é o
   pitfall mais importante de todos. Marque-a como **"sem correção verificada"** e proponha
   investigar (achar e verificar a correção) antes do retrofit, para não gravar um palpite na
   skill.

Um beco sem saída descartado, com o motivo, fortalece a lição: diga o que foi tentado e por que
não serviu. Sem os itens 1 e 2, anote como hipótese na memória, marcada "não verificada", ou
descarte.

## 3. Triagem: para onde vai cada lição

| A lição… | Destino |
|---|---|
| melhora a skill para qualquer projeto | **retrofit**: `/retrofit-skill:retrofit-skill <alvo>` |
| só vale neste repositório (path, env var, convenção local) | memória do projeto, `CLAUDE.md` ou `.claude/napkin.md`, e não a skill |
| é um fato solto de uma linha, sem procedimento | memória |
| é de uma skill de **terceiro** | nunca edite a cópia instalada; sugira uma issue ou um PR upstream |
| não deve se repetir | descarte |

O argumento do retrofit é o que o hook informou. No modo full é o **nome do plugin**
(`codereview`, não `coderabbit-pr`). No modo lean é o nome da skill.

## 4. Auto-audit de segredos (antes de escrever o bloco)

Passe cada linha por este filtro:

- **Credencial literal:** `Bearer `, `Basic `, `sk-`, `ghp_`, `xox[bpars]-`, `AKIA`, ou uma
  sequência base64/hex com 32 ou mais caracteres. Troque por onde o valor mora (`env:NOME`,
  arquivo, cofre).
- **Connection string com credencial:** `postgres://`, `mysql://`, `mongodb://`, `redis://`,
  `https://user:pass@`, `amqp://`. Mantenha só esquema, host e path.
- **Valor que você colou antes na conversa:** vira ponteiro para a origem.
- **Placeholder que algum hook preenche:** trate como segredo.

## 5. Formato da resposta

**Sem lição que passe no filtro:** uma linha só.

```
retro ticket: sem lições novas
```

**Com lição** (exemplo **fictício**, só para mostrar o formato):

```
**Retro — `ticket`** (full → `/retrofit-skill:retrofit-skill ticket`)
- **Pitfall:** a skill manda `acli jira workitem transition --status Done`, mas neste Jira o
  estado se chama "Concluído" → `Error: transition not found` (sessão) → resolvido listando as
  transições antes (`acli … transitions`). Evita: nome de estado presumido em projeto localizado.
- **Melhoria:** falta o passo de conferir o sprint ativo antes de criar a issue; a issue nasceu
  no backlog e foi movida à mão.
- Só deste projeto → memória: o board SQ usa o campo customizado 10020 para story points.

Rodo `/retrofit-skill:retrofit-skill ticket`?
```

**Regras do bloco:**
- no máximo 5 lições;
- cada uma em 1 a 3 linhas;
- a evidência entre parênteses ou citada;
- nada de lição inventada para preencher o bloco. "Sem lições novas" é uma resposta boa.

## 6. Depois do "sim"

Rode o comando indicado e deixe o `/retrofit-skill` conduzir. Ele escolhe o modo, faz baseline
de auditoria, mostra a proposta e pede confirmação antes de editar, commitar e dar push. O
`retrofit-watch` não pede outra retro daquela skill nesta sessão.

## 7. Quando quem trabalhou foi um kit (`sdd`)

O kit não é skill: a lição vira **achado no `TODO.md` do repo do kit**, para o laço do próprio kit
(`sdd kaizen`) triar. Não ofereça o `/retrofit-skill`. O bloco é o mesmo da seção 5, com
`(kit → TODO.md do sdd_agents)` no título e a pergunta "Registro no TODO.md do kit?".

Depois do "sim":

- leia o cabeçalho do `TODO.md` do kit e siga o formato dele: item com âncora `arquivo:linha`,
  data e "descoberto por", no máximo 8 linhas, na seção aberta;
- mova a catraca no mesmo commit (no `sdd_agents`: `todo-findings` em `tests/health-baseline.txt`);
- valide com o sensor do kit (`tests/check-todo.sh --check TODO.md`) antes de commitar;
- commite num branch e pergunte antes do push e do PR, como qualquer `chore(todo)` do kit.

Escrever o `TODO.md` com `Edit` ou `Write` encerra a retro do kit nesta sessão. Escrito por script
no Bash, o hook não percebe, e pode pedir uma segunda retro se o atrito continuar.
