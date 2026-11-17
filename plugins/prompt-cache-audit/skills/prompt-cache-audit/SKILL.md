---
name: prompt-cache-audit
description: "Audits prompt caching before anyone tunes it. Measures Claude Code's cache from local transcripts (hit rate, TTL, misses by cause, context size) and reviews code that calls the Claude API directly, ending with the cost in money. Triggers — prompt caching, cache hit rate, cache_control, cache TTL, low cache hit rate, API cost."
metadata:
  version: 0.1.0
---

# prompt-cache-audit

Mede o cache de prompt antes de mexer nele. O resultado mais comum de uma auditoria honesta é "já está ligado, e a
mudança que sobra custa mais do que economiza": a skill existe para chegar a essa resposta com números, e não para
ligar chaves.

`SCRIPTS` é a pasta `scripts/` ao lado deste arquivo ("Base directory for this skill").

| Arquivo | Para quê |
|---|---|
| `scripts/cache_audit.py` | o relatório do Claude Code (seção 2) |
| `tests/test_cache_audit.py` | os testes do script, com transcritos mínimos escritos à mão |
| `assets/trigger-evals.json` | as consultas que devem e as que não devem acionar a skill |

## 1. De qual tráfego se fala

Há dois tráfegos, com contas e consertos diferentes. Descubra qual é antes de qualquer medição:

| Sinal | Tráfego | Vá para |
|---|---|---|
| Aviso da Anthropic de "taxa de acerto de cache baixa", fatura do Console, chave de API | API direta: um programa que chama a Messages API | seção 3 |
| Limite da assinatura acabando cedo, sessões longas e caras no Claude Code | Claude Code | seção 2 |

O aviso de taxa de acerto baixa cobre só a API direta e diz que o Claude Code fica de fora, porque ele gerencia o
cache sozinho. Configurar o Claude Code não muda o número desse aviso. Leia o texto do aviso antes de assumir o alvo.

## 2. Claude Code: medir pelos transcritos

```bash
python3 "$SCRIPTS/cache_audit.py"                 # últimos 14 dias de ~/.claude/projects
python3 "$SCRIPTS/cache_audit.py" --days 0 --json # tudo, como JSON
```

Só leitura, só biblioteca padrão. Saída 2 quando não há transcritos ou o formato não é o esperado.

### Como ler o relatório

| Bloco | O que diz | Quando preocupa |
|---|---|---|
| `% lido` por modelo | leitura do cache sobre toda a entrada | modelo de uso contínuo abaixo de ~90%; modelo de subagente curto fica mais baixo por natureza |
| Escritas por TTL | quem escreve em 5 min e quem escreve em 1h | conversa principal escrevendo em 5 min numa assinatura: é uso além do plano |
| Tamanho do contexto | mediana e p90 de tokens por pedido | mediana na casa das centenas de milhares: o gasto é a releitura, e não o cache |
| Quedas de cache | vezes em que um pedido leu menos da metade do prefixo anterior, pela causa | muitas "pausa de mais de 1h" com milhões reescritos |
| TTL de 1h | a conta que diz se trocar 5 min por 1h compensa | só a linha que disser COMPENSA |

### O que decidir

1. **TTL.** Siga o veredito do script. A escrita de 1h custa mais que a de 5 min em **toda** escrita, então só
   compensa quando uma fração grande do que se escreve em 5 min é reescrita depois de pausas de 5 min a 1h (o script
   imprime o limiar, perto de 40% com os multiplicadores padrão). As chaves existem por conversa principal e por
   subagente; os nomes e a precedência estão na página de cache do Claude Code (abaixo). Não ligue nenhuma sem a
   linha COMPENSA.
2. **Pausas de mais de 1h.** Nenhuma chave resolve: o cache expirou. O que resolve é não retomar uma conversa
   grande depois de horas; comece outra, ou compacte antes de parar.
3. **Contexto grande.** Leitura de cache é barata por token e cara em volume. Com mediana de centenas de milhares
   de tokens, o que reduz gasto é contexto menor: conversa nova por tarefa, instruções de projeto enxutas,
   exploração ampla em subagente.
4. **Troca de modelo, effort ou modo rápido no meio da conversa.** Cada um tem o próprio cache; escolha no começo.

Se nada na lista tiver número que justifique, a resposta é "não mexer", e ela vai no relatório com os números.

### Fontes (lidas em 2026-11-17; confira antes de aplicar, porque mudam)

- Chaves de TTL, o que invalida o cache numa sessão e o TTL de cada tipo de pedido:
  `https://code.claude.com/docs/en/prompt-caching.md`
- Multiplicadores de preço da escrita e da leitura: `https://platform.claude.com/docs/en/build-with-claude/prompt-caching`.
  Os padrões do script (1,25, 2 e 0,1) são os dessa página nessa data; modelos mais novos leem por menos. Passe
  `--write-5m`, `--write-1h` e `--read` se a página disser outra coisa.

## 3. API direta: auditar o código que chama a API

Siga na ordem. Pare no primeiro passo que explicar o número.

1. **Ache as chamadas.** Procure `messages.create`, `messages.stream`, `/v1/messages` e `cache_control` no código.
   Sem `cache_control` nenhum, é esse o achado: ponha um ponto de cache no fim do trecho estável.
2. **Meça o que o programa já registra.** Em cada resposta, `usage` traz `input_tokens` (o que veio depois do
   último ponto de cache), `cache_read_input_tokens` e `cache_creation_input_tokens`; a entrada total é a soma dos
   três. Se o programa não guarda esses campos, guardar é a primeira mudança. Com os três zerados, o prefixo ficou
   abaixo do mínimo do modelo e nada foi posto em cache, sem erro.
3. **Separe o estável do variável.** O cache cobre o prefixo, na ordem ferramentas, sistema, mensagens, até o bloco
   marcado. Liste o que não muda entre chamadas e está **depois** de algo que muda (instruções longas, documento de
   referência, perfil do usuário, exemplos): é o único ganho que existe. O que muda a cada chamada não tem como
   entrar no cache, e a taxa de acerto nunca chega a 100% num programa de pergunta única.
4. **Procure o que invalida em silêncio.** Carimbo de data ou identificador dentro do sistema; lista de ferramentas
   montada em outra ordem; JSON serializado sem ordem estável; mudar entre chamadas `thinking`, `effort`,
   velocidade, `tool_choice` ou a presença de imagens; modelos diferentes (cada um tem o seu cache).
5. **Compare o TTL com o intervalo real.** Com 5 min, toda pausa maior reescreve o prefixo. Meça o intervalo entre
   chamadas no uso real, e não no teste em rajada, que sempre acerta.
6. **Faça a conta em dinheiro, e só então decida.**

   ```text
   economia por chamada = tokens estáveis fora do cache × preço da entrada × (1 − multiplicador da leitura)
   economia no período  = economia por chamada × chamadas no período − escritas a mais
   ```

   Compare com o gasto total do período e com o custo de validar a mudança. Mover um bloco muda a ordem do prompt:
   num programa com avaliação de qualidade, isso pede rodar a avaliação de novo. Centavos por mês não pagam isso.
   Registre o achado e a condição em que passa a valer (volume maior), e não mude o código.

## 4. O relatório

Entregue ao usuário, nesta ordem: de qual tráfego o aviso ou a queixa fala; os números medidos (com o comando que os
mediu); o que mudar e quanto economiza em dinheiro; o que **não** mudar e por quê. Não altere configuração nem
código de outra pessoa sem que o relatório tenha sido lido e a mudança, aprovada.

## Armadilhas

- **Configurar o harness por causa de um aviso que fala da API.** O aviso exclui o Claude Code. Leia o texto.
- **Ligar o TTL de 1h "porque é melhor".** Ele encarece toda escrita. Sem a conta, a mudança piora o gasto.
- **Ler taxa de acerto como meta.** Um programa de pergunta única tem a pergunta fora do cache por construção; 50 a
  60% pode ser o teto. A pergunta certa é quanto do que está fora é estável.
- **Medir em rajada.** A bancada que dispara chamadas em sequência acerta sempre; o uso real tem pausas.
- **Contar a mesma resposta duas vezes.** O transcrito repete a resposta a cada bloco de conteúdo; o script conta
  uma vez pelo `message.id`. Quem somar os `usage` à mão infla tudo.
- **Confiar em zeros.** O formato do transcrito não é documentado. Se o script sair com 2 dizendo que não achou
  `message.usage`, o formato mudou: conserte o script, não o relatório.
- **`--days` filtra pela data de modificação do arquivo**, não pela de cada resposta: uma conversa antiga retomada
  ontem entra inteira.
- **Fixar preço ou nome de chave na cabeça.** Mudam por modelo e por versão; as duas páginas acima são a fonte.
