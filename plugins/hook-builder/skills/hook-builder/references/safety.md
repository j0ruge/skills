# Segurança, matriz de testes e rollback

Leitura obrigatória para **hook de política** (gate), hook com **efeito colateral** (rede,
escrita, commit) e hook que **toca segredo**. Este arquivo absorve o conteúdo de desenho da
antiga skill local `hooks-2-0-builder` (2026-09-09), adaptado aos hooks que existem hoje. As
"Function Hooks" e os "Claude Mods" daquela skill eram uma proposta (issue
anthropics/claude-code#91870), não uma API publicada. Se reaparecerem, verifique na doc antes
de usar.

Regras oficiais (https://code.claude.com/docs/en/hooks#security-best-practices, 2026-09-30):
- valide o input;
- ponha aspas nas variáveis (`"$VAR"`);
- barre `..` em path;
- use path absoluto (`${CLAUDE_PROJECT_DIR}`, com forma exec ou entre aspas);
- não toque em `.env`, `.git/` e chaves.

Um command hook roda com **todas as suas permissões de usuário**.

## 1. Contrato de controle (escreva antes do código)

- **Operação protegida, dono e resultado aceitável:** exemplos concretos de permitido,
  proibido e ambíguo.
- **Entradas não confiáveis:** prompt, saída de ferramenta, arquivo do repo, resposta de rede,
  texto que "se diz administrador". Tudo é dado, nunca instrução.
- **Fronteira mais cedo possível e as rotas alternativas até o mesmo efeito:** outra
  ferramenta, wrapper de shell, subagente, MCP. Um hook não é sandbox de SO e só controla o que
  intercepta.
- **Política de falha por classe de erro:** `deny`, `ask` ou `pass`, com a lembrança de que o
  timeout **não** bloqueia no `PreToolUse`.
- **Não-objetivos e risco residual:** plugin malicioso, edição local do arquivo de política.

**Argumento explícito sobrepõe estado ambiente.** Antes de cair no estado do ambiente (branch
atual, `cwd`, variável), confira se o comando já nomeia o alvo. `git push --force origin
feature-x` não é push na `main`, mesmo que o checkout atual seja a `main`. Só consulte o
ambiente quando o comando não disser. O erro inverso (ignorar o ambiente quando o comando omite
o alvo) deixa passar `git push -f` puro na `main`. Teste os dois casos.

Um filtro por substring de comando shell não é fronteira de segurança, porque aspas,
substituições, interpretadores e wrappers passam por ele. Prefira argumento estruturado e um
conjunto pequeno de operações. Canonicalize o path antes de decidir (traversal, symlink,
TOCTOU). Para deny rígido, use `permissions.deny`.

## 2. Estado

| Escopo | Uso | Regra |
|---|---|---|
| da invocação | input parseado, decisão, guarda de recursão | não persiste |
| da sessão | dedupe, confirmação curta, offset de transcript | chave por `session_id` (e projeto); expira |
| persistente | política versionada, índice de auditoria | local explícito (`${CLAUDE_PLUGIN_DATA}`), dono, retenção, concorrência |

- **Escrita:** gravação atômica (temporário + `os.replace`), `flock` quando duas sessões podem
  escrever o mesmo arquivo.
- **Segredo:** nunca credencial crua no estado. Guarde só o **nome** da variável.
- **Efeito colateral:** reivindicação atômica com chave estável (invocação + versão da política
  + impressão do input), com estados `pending`/`completed`/`failed`. Dedupe local não garante
  exatamente-uma-vez depois de um crash. Reconcilie antes de repetir.

## 3. Confirmação

Uma aprovação vale para **uma** ação: principal, input canônico, versão da política, validade.
Cancelar, expirar, faltar UI ou vir resposta malformada **nunca** vira aprovação. No `-p` não há
prompt de permissão: um `PermissionRequest` sem decisão de hook é negado para subagente em
background.

## 4. Enriquecimento por modelo ou HTTP

É evidência opcional, não permissão. Um deny local determinístico sobrevive ao conselho remoto.

- **Chamada:** endpoint permitido, payload mínimo e redigido, prazo, limite de tamanho, schema
  estrito da resposta.
- **Resposta:** é dado não confiável. Nunca execute código que venha dela.
- **Recursão:** evite chamar o modelo de dentro do mesmo hook sem limite de profundidade.

## 5. Auditoria e redação

- **O que registrar:** registro enxuto, com data, id opaco, versão da política,
  evento/ferramenta, decisão, código do motivo, latência.
- **O que não registrar:** prompt, argumentos e saída crus, headers de auth, query strings.
- **Redação:** redija **antes** de serializar e antes de mandar pela rede, e isso vale também
  para exceção e stack trace.
- **Superfícies expostas:** contexto do modelo, transcript, tela, arquivos, logs, requisições.
  Mascarar na UI não redige nenhuma das outras.

## 6. Matriz comportamental

| Caso | Injeção | Aceite observável |
|---|---|---|
| Bom | ação permitida e ação fora do matcher | cada uma roda uma vez; permissões normais preservadas |
| Ruim | ação proibida por rotas alternativas | o efeito nunca ocorre nas rotas cobertas; as descobertas ficam declaradas |
| Ambíguo | campo ausente, path incerto | `ask`/`deny` configurado; nunca aprovação silenciosa |
| Falha | exceção, timeout, estado ilegível, script ausente | a política de falha vale **no runtime real**; o erro não vaza payload |
| Segredo | canário sintético no output, header, exceção | o canário não aparece em nenhum destino |
| Loop | continuação de Stop repetida | chamadas limitadas; término determinístico (`stop_hook_active` + teto próprio) |
| Dupla execução | disparo duplicado, paralelo, restart | sem efeito duplicado, ou reconciliação explícita |
| Composição | vários hooks deny/pass/transform | a decisão final bate com o contrato (deny > defer > ask > allow; `updatedInput` sem ordem garantida) |
| Isolamento | duas sessões ou dois projetos, entrada expirada | sem vazamento de estado |
| Desassistido | mesma condição num `claude -p` | o comportamento escolhido (calar ou agir) se confirma |

Use canários sintéticos, nunca segredo real. Marque cada caso como `pass`, `fail`, `not_run`
ou `unsupported`. Um check de formato de pacote **não** é prova de enforcement em runtime.

## 7. Rollout e rollback

- **Rollout:**
  - comece com fixtures e um smoke inofensivo;
  - ative no menor escopo (settings local ou `--plugin-dir`) e confira registro + caso negativo;
  - não deixe a versão antiga e a nova registradas ao mesmo tempo, porque o efeito dobra.
- **Condições de parada:** execução proibida, vazamento, duplicado sem explicação ou controle
  obrigatório perdido.
- **Rollback:**
  1. pause a operação protegida, se o hook é o único gate;
  2. restaure a config ou versão anterior revisada, preservando as entradas alheias;
  3. recarregue pelo método verificado (`/reload-plugins`, watcher de settings ou sessão nova);
  4. repita as sondas de bloqueio, de permitido e de fora do matcher, e confirme que não sobrou
     registro duplicado;
  5. lembre que reverter a config não desfaz efeito externo nem migração de estado.

## 8. Entrega

Relate:
- a política e os arquivos;
- a versão do Claude Code e a evidência de que cada capacidade existe;
- os comandos de teste e o status de cada um;
- as garantias não cobertas;
- o escopo de ativação;
- o resultado do rollback.

Sem acesso ao runtime, diga isso e liste as sondas que faltam.
