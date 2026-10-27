# Templates dos artefatos Kaizen

Use estes templates ao gerar os artefatos. Adapte os campos ao contexto — o template serve ao trabalho, não o contrário.

## Plano PDCA

Salve como `docs/planos/PLANO-<slug-curto>.md` (ou onde o projeto guardar planos).

```markdown
# Plano PDCA — <título curto da mudança>

**Data:** <AAAA-MM-DD> · **Responsável:** <quem>

## Problema / objetivo (1 frase)
<O que dói hoje, ou que valor queremos entregar.>

## Métrica de sucesso
<Como saberemos que melhorou — número, comportamento observável ou teste que passa.>

## Gemba — situação atual
<O que foi observado no código/sistema real: arquivos afetados, fluxo atual, dados. E as premissas do
pedido sobre acesso ou exposição ("é interno", "é restrito"), conferidas no artefato (permissão, ACL).>

## Desperdícios evitados
<Itens cortados/adiados do escopo e por quê (superprodução, superprocessamento...).>

## Incrementos (Do)
| # | Incremento | Entrega verificável | Check (como verificar) |
|---|---|---|---|
| 1 | <menor passo de valor> | <o que fica pronto> | <teste/medição> |
| 2 | ... | ... | ... |

## Riscos e reversão
<O que pode dar errado em cada incremento e como reverter.>

## Act (após o Check)
<Preenchido ao final: o que padronizar, o que ajustar, entrada no kaizen log.>
```

## Validação de plano

Use quando o plano já foi decidido (grill, spec, ADR, plano de missão) e o pedido é conferir se ele
cumpre o Kaizen. Grave como seção do próprio plano ou da spec, não como arquivo novo que ninguém lê.
O produto não é uma nota: cada achado vira um **ajuste** que volta ao plano, ou uma justificativa
escrita na tabela de desperdícios.

```markdown
# Validação Kaizen — <plano>

**Data:** <AAAA-MM-DD> · **Plano:** <link> · **Veredito:** <passa | passa com ajustes | refatiar>

## Desperdícios contra o plano
| Desperdício | Onde aparece no plano | Contramedida, ou "justificado: <por quê>" |
|---|---|---|
| Superprodução | | |
| Espera | | |
| Transporte | | |
| Superprocessamento | | |
| Estoque | | |
| Movimentação | | |
| Defeitos | | |
| Talento não usado | | |
| Mura / muri | | |

## Ajustes (voltam ao plano)
| # | Achado (princípio ou armadilha) | Ajuste no plano |
|---|---|---|
| K1 | <ex.: o Check lê o código-fonte, e o consumidor recebe o pacote (rótulo ≠ artefato)> | <ex.: testar o pacote instalado num consumidor vazio> |

## Checklist
- [ ] Problema em uma frase e métrica de sucesso de cada entrega
- [ ] Primeira entrega verificável no primeiro incremento
- [ ] Todo incremento com Check; teste visto vermelho antes; sonda nova com caso sabotado montado do zero, cache da ferramenta incluído
- [ ] Check no artefato que chega ao destino, não no rótulo nem na cópia local
- [ ] Premissa do pedido sobre acesso ou exposição ("é interno", "é restrito") conferida na permissão do destino, não na palavra de quem pediu
- [ ] Poka-yoke antes de regra escrita; a regra que sobrar diz por que nenhum degrau acima coube
- [ ] Ação irreversível com o passo reversível antes, a confirmação de quem decide e os identificadores anotados
- [ ] Espera no caminho crítico nomeada, com dono e momento
- [ ] Estoque com dono: o que fica pronto e parado tem item e responsável
- [ ] Yokoten: onde mais a decisão vale, e se entra agora ou vira oportunidade
- [ ] Act: entrada no `KAIZEN_LOG.md` ao fechar, com "Padronizado em" conferido no arquivo
```

## Kaizen Log

Arquivo único `KAIZEN_LOG.md` na raiz do projeto, entradas mais recentes no topo.

```markdown
# Kaizen Log — <nome do projeto>

Registro de melhorias contínuas. Toda entrada tem: o que melhorou, o que aprendemos, o que virou padrão.

## <AAAA-MM-DD> — <título curto>
- **Tipo:** melhoria | correção de causa raiz | oportunidade (a fazer) | padronização
- **Antes:** <situação anterior em 1 linha>
- **Depois:** <situação nova em 1 linha, com métrica se houver>
- **Causa raiz (se defeito):** <resultado dos 5 porquês>
- **Padronizado em:** <convenção/doc/teste/CI atualizado — ou "pendente">
- **Yokoten:** <onde mais a mesma causa existe e o que foi feito lá — ou "não se aplica">

### Desperdícios evitados (cortes conscientes)
- <o que ficou fora do escopo e por quê — qual dos 7 desperdícios evitou>

### O que aprendemos
- <a pegadinha técnica que custou tempo e que a próxima pessoa redescobriria>
```

**Antes de fechar a entrada, abra o arquivo citado em "Padronizado em" e confirme que a
mudança está lá.** Esse campo é a única linha do log que afirma algo sobre o mundo **fora**
do log — todas as outras descrevem o que já aconteceu, e essa promete que algo mudou em
outro lugar. Escrever o caminho é rápido e dá a sensação de ter padronizado; ninguém
verifica depois, e a entrada passa a documentar uma convenção que não existe. Se a mudança
ainda não foi feita, escreva `pendente` — é informação honesta e acionável. É o mesmo
defeito que o Kaizen ensina a caçar em produção (ver *Rótulo ≠ artefato* em
`kaizen-conceitos.md`), aplicado ao próprio registro da melhoria: o campo é o rótulo, o
arquivo alterado é o artefato.

As duas últimas subseções são **opcionais** — inclua quando houver conteúdo real, não para
preencher formulário. Elas existem porque sem elas o log registra só *o que* mudou: o
**porquê do corte** vira "esqueceram de fazer" seis meses depois (e alguém reabre o escopo
já rejeitado), e a **lição** técnica é redescoberta do zero pela próxima pessoa. O corte
consciente é decisão de engenharia e merece o mesmo registro que a entrega.

## 5 Porquês

Registre dentro da entrada do kaizen log ou no corpo da correção do bug.

```markdown
### 5 Porquês — <defeito>
- **Sintoma:** <o que o usuário viu>
1. Por quê? <resposta>
2. Por quê? <resposta>
3. Por quê? <resposta>
4. Por quê? <resposta — pare antes se chegar à causa de processo>
5. Por quê? <causa raiz de processo>
- **Contramedida:** <poka-yoke que torna o erro impossível ou óbvio — tipo, validador, lint, hook, gate de CI — ou, se for só regra escrita, por que nenhum poka-yoke coube>
- **Teste que teria pegado:** <teste adicionado>
```

Regra de ouro: a causa raiz é sempre um processo ou uma ausência de salvaguarda, nunca uma pessoa ("fulano errou" → continue perguntando: por que o erro foi possível e passou?). Se um "por quê" bifurca em duas respostas verdadeiras, registre os ramos como 4a/4b e uma contramedida por ramo — é o Ishikawa em forma de lista.

## Retrospectiva

```markdown
# Retrospectiva — <ciclo/período>

## O que fluiu bem (manter)
- ...

## O que atrapalhou (desperdícios observados)
- <item + qual dos 7 desperdícios é>

## Experimentos para o próximo ciclo
| Experimento | Dono | Como saberemos que funcionou |
|---|---|---|
| <mudança pequena de processo> | <quem> | <sinal observável> |
```

Converta cada experimento aprovado em entrada do kaizen log quando concluído.
