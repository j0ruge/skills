# Evidência de ensino

Esta tabela sustenta cada bloco do roteiro da aula. Um bloco sem fonte primária conferida sai do roteiro.

## Como cada fonte foi conferida

- Cada DOI existe no Crossref. O script `scripts/conferir-dois.py` confere isso. Ele prova que o registro existe. Ele não prova que a fonte sustenta a frase.
- Seção 1: as linhas herdam do `METODO.md` a leitura em nível de resumo, feita em 2026-11-21. Esta tarefa não leu
  esses resumos de novo. Ela só conferiu que cada DOI existe no Crossref.
- Seção 5: cada linha diz, na coluna "Lido", o serviço cujo resumo foi lido de fato. O Crossref traz resumo vazio ou
  cortado em várias fontes, então o OpenAlex ou o Europe PMC cobre essas linhas.
- Só Rosenshine (2012) foi lido no texto completo. Fonte marcada "não conferido no texto" vem de uma citação dentro de outra fonte.
- As colunas de aplicação são inferência de quem escreveu. Uma nota de evidência sem "D13" é juízo do pesquisador, pelo tipo de estudo.
- D13 = Dunlosky et al. 2013, *Psychological Science in the Public Interest*, doi 10.1177/1529100612453266.
- Fonte de divulgação não entra, exceto Rosenshine (2012), marcado como tal.

## 1. Técnicas com evidência

| Técnica (o que é) | Evidência | Fonte (DOI) | Aula por chat | Curso HTML |
|---|---|---|---|---|
| **Prática de recuperação**: lembrar sem olhar. | Alta (D13). Em sala, g = 0,50. O retorno corretivo aumentou os acertos e reduziu os erros aprendidos. | Roediger & Karpicke 2006, 10.1111/j.1467-9280.2006.01693.x; Yang et al. 2021, 10.1037/bul0000309; Butler & Roediger 2008, 10.3758/MC.36.3.604 | No fim do bloco, uma pergunta aberta, sem consulta. Depois, a correção. | Caixa "lembre sem olhar" no fim da seção, com a resposta em `<details>`. |
| **Prática espaçada**: rever o tema em dias diferentes. | Alta (D13). Para prova em 1 semana, o intervalo ótimo foi 20–40 % do prazo (fatos simples). | Cepeda et al. 2006, 10.1037/0033-2909.132.3.354; Cepeda et al. 2008, 10.1111/j.1467-9280.2008.02209.x; Rawson et al. 2013, 10.1007/s10648-013-9240-4 | Abrir a aula com 2–3 perguntas de 2–4 dias antes. A pergunta errada volta até ser acertada. | Plano de estudo com revisão no dia seguinte e nos dias finais. |
| **Intercalação**: misturar temas ou tipos de problema. | Moderada (D13). g = 0,42. O efeito é maior entre categorias parecidas e é ambíguo em texto expositivo. | Rohrer & Taylor 2007, 10.1007/s11251-007-9015-8; Brunmair & Richter 2019, 10.1037/bul0000209 | Sortear perguntas de capítulos diferentes. Pedir para distinguir métodos parecidos. | Tabela "parecidos, mas diferentes". |
| **Interrogação elaborativa**: responder "por que isto é verdade?". | Moderada (D13). Foi pouco testada em sala. | D13; Pressley et al. 1987, 10.1037/0278-7393.13.2.291 (não conferido no texto) | "Por que o material escolheu X e não Y?" | Cada afirmação central com um "por quê?" curto. |
| **Autoexplicação**: explicar a si mesmo cada passo. | Moderada (D13). Metanálise: g = 0,55 (69 efeitos). | Chi et al. 1989, 10.1207/s15516709cog1302_1; Chi et al. 1994, 10.1207/s15516709cog1803_3; Bisra et al. 2018, 10.1007/s10648-018-9434-x | Mostrar um passo do método e perguntar: "o que ele faz e por que vem aqui?" | "Explique a si mesmo" ao lado de cada etapa do diagrama. |
| **Codificação dupla e Mayer**: palavra e imagem ligadas, com segmentação, sinalização, coerência e contiguidade. | Forte. Metarrevisão (29 revisões, 1.189 estudos): os maiores ganhos vieram da contiguidade e da sinalização. Contiguidade: g = 0,63. | Noetel et al. 2022, 10.3102/00346543211052329; Schroeder & Cenkci 2018, 10.1007/s10648-018-9435-9; Rey et al. 2019, 10.1007/s10648-018-9456-4; Mayer & Moreno 2003, 10.1207/S15326985EP3801_6; Clark & Paivio 1991, 10.1007/BF01320076 (não conferido no texto) | Um conceito por mensagem. Diagrama pequeno junto do texto. Nada fora do tema. | Rótulo dentro da figura. Cor e seta só no caminho principal. Uma ideia por seção. |
| **Exemplo resolvido** (carga cognitiva): ver a solução passo a passo antes de resolver. | Forte para iniciantes. Perde o efeito, ou prejudica, quem já domina o assunto (reversão pela expertise). | Sweller 1988, 10.1207/s15516709cog1202_4; Atkinson et al. 2000, 10.3102/00346543070002181; Kalyuga et al. 2003, 10.1207/S15326985EP3801_4 | Um cálculo completo, depois um meio pronto, depois um sozinho. | Caixa "exemplo resolvido", com passos numerados e o porquê de cada um. |
| **Exemplo concreto**: a definição e um caso real. | Moderada. Definição com exemplos: d = 0,74 a 1,67. O efeito depende de a definição vir junto. | Rawson et al. 2015, 10.1007/s10648-014-9273-3 | Termo novo = definição + exemplo do material + contraexemplo. | Definição e exemplo na mesma caixa. |
| **Geração**: produzir a resposta em vez de ler. | Moderada. d = 0,40 (86 estudos). | Slamecka & Graf 1978, 10.1037/0278-7393.4.6.592; Bertsch et al. 2007, 10.3758/BF03193441 | Completar a frase-chave antes de vê-la. | Lacunas para completar. |
| **Pré-teste**: perguntar antes de ensinar. | Moderada e recente. Ajuda se a resposta certa vem depois. O tamanho do efeito varia. | Richland et al. 2009, 10.1037/a0016496; Kornell et al. 2009, 10.1037/a0015729; Pan & Carpenter 2023, 10.1007/s10648-023-09814-5 | Uma pergunta antes do bloco. Errar é esperado. | "Antes de ler, tente responder." |
| **Ensinar sem anotações**. | Moderada. Preparar para ensinar: g = 0,35. Ensinar: g = 0,56. O ganho apareceu quando a pessoa ensinou sem notas, isto é, com recuperação. | Kobayashi 2019, 10.1111/jpr.12221; Koh et al. 2018, 10.1002/acp.3410 | O aluno explica o bloco ao agente, que faz papel de leigo. | Roteiro "explique a um colega" por aula. |
| **Rosenshine**: 10 princípios, entre eles a revisão diária, os passos pequenos, checar a compreensão, cerca de 80 % de acerto e a revisão semanal e mensal. | Síntese de três linhas de pesquisa. Texto de divulgação, sem revisão por pares. Lido no texto completo. | Rosenshine 2012, *American Educator*, sem DOI: https://www.aft.org/sites/default/files/periodicals/Rosenshine.pdf | Não perguntar "alguma dúvida?". Exigir uma resposta. Abaixo de ~80 % de acerto, dividir o passo. | Cada aula abre com a revisão da anterior. |

## 2. Técnicas com evidência fraca

- **Reler**: baixa (D13). Em quatro experimentos, reler logo depois quase não melhorou as notas (Callender &
  McDaniel 2009, 10.1016/j.cedpsych.2008.07.001). A maioria dos alunos relê e tem ilusão de competência
  (Karpicke et al. 2009, 10.1080/09658210802647009). Reestudar aumentou a confiança, mas não a retenção após uma
  semana (Roediger & Karpicke 2006).
- **Grifar**: baixa (D13). Na metanálise de Ponce et al. 2022 (10.1007/s10648-021-09654-1), o grifo feito pelo
  aluno melhorou a memória (0,36), mas não a compreensão (0,20). O destaque dado pelo professor melhorou as duas
  (0,44). Então quem destaca é o guia.
- **Resumir, mnemônica de palavra-chave, imagem mental para texto**: baixa (D13). Ajudam alguns alunos, em
  algumas tarefas.
- **Estilos de aprendizagem**: a revisão achou "virtually no evidence" para a interação entre estilo e método
  (Pashler et al. 2008, 10.1111/j.1539-6053.2009.01038.x).
- **"Técnica de Feynman"**: sem estudo controlado em periódico de referência. As partes dela têm evidência
  própria: explicar (autoexplicação), sem olhar (recuperação), para alguém (ensinar). As pessoas superestimam
  quanto entendem de um mecanismo até tentarem explicá-lo (Rozenblit & Keil 2002, 10.1207/s15516709cog2605_1).

## 3. Regras para o agente que ensina

1. Feche cada bloco com uma pergunta aberta, respondida sem consulta. Não proponha reler. [Roediger & Karpicke 2006; Callender & McDaniel 2009]
2. Corrija logo após cada resposta: diga o certo e o porquê. [Butler & Roediger 2008; Yang 2021]
3. Abra cada aula com 2–3 perguntas de aulas de 2–4 dias antes. A pergunta errada volta na sessão seguinte, até ser acertada. [Cepeda 2008; Rawson 2013]
4. Ensine um conceito por mensagem. Avance com cerca de 80 % de acerto. Abaixo disso, divida o passo. [Rosenshine 2012; Rey 2019]
5. Nunca pergunte "ficou claro?". Peça que o aluno explique com as palavras dele. [Rosenshine 2012; Rozenblit & Keil 2002]
6. Antes de um conceito novo, faça uma pergunta-teste e diga que errar é esperado. [Pan & Carpenter 2023; Kornell 2009]
7. Para cada decisão do material, pergunte "por quê?" e "e se fosse diferente?". [D13; Pan & Rickard 2018]
8. Para um procedimento, mostre um exemplo resolvido, depois um parcial, depois um para o aluno resolver sozinho. Tire o apoio quando ele acertar. [Atkinson 2000; Kalyuga 2003]
9. Todo termo novo leva definição, exemplo do material e contraexemplo, juntos. [Rawson 2015]
10. Na revisão, misture aulas e peça para distinguir conceitos parecidos. [Brunmair & Richter 2019; Kornell & Bjork 2008, 10.1111/j.1467-9280.2008.02127.x]
11. No curso, ponha o rótulo dentro da figura, destaque só o caminho principal e corte o enfeite. [Noetel 2022; Schroeder & Cenkci 2018]

## 4. Como as aulas aplicam as regras

| Parte da aula | Regras |
|---|---|
| "Antes de ler, tente responder" no topo | 6 |
| "Revisão da aula anterior" (a partir da aula 2) | 3, 10 |
| Um conceito por seção, com diagrama ao lado e rótulo dentro da figura | 4, 11 |
| Caixa "por quê?" e "e se fosse diferente?" | 7 |
| "Exemplo resolvido" (um cálculo, um procedimento) | 8 |
| Termo novo com definição, exemplo do material e contraexemplo | 9 |
| "Lembre sem olhar" e "explique a um colega" | 1, 5 |
| Quiz com retorno imediato e o porquê | 1, 2 |

## 5. Lacunas pesquisadas em 2026-11-22

Quatro pontos do roteiro não tinham fonte. A busca usou o Crossref, o OpenAlex, o Europe PMC e a busca na web.
Cada linha traz o que a fonte mostra e o limite. A coluna "Lido" diz de qual serviço veio o resumo lido.
Nenhum texto completo foi lido nesta seção.

### 5.1 Analogia: ENTRA, com limites

| Técnica | Evidência e limite | Fonte (DOI) | Lido |
|---|---|---|---|
| **Analogia no lugar da definição literal** | Quatro experimentos. A forma literal deu mais acertos em perguntas de detalhe. A forma por analogia deu mais acertos em perguntas de inferência. O padrão foi mais forte em quem era novato no assunto. Limite: textos curtos de ciência, testes de múltipla escolha. | Donnelly & McDaniel 1993, 10.1037/0278-7393.19.4.975 | OpenAlex |
| **Comparar dois casos** (codificação analógica) | Estudantes novatos que compararam dois casos transferiram melhor do que os que estudaram os dois casos separados. Limite: três estudos, tarefa de negociação. | Gentner, Loewenstein & Thompson 2003, 10.1037/0022-0663.95.2.393 | OpenAlex |
| **Comparação de casos, em geral** | Metanálise de 57 experimentos (336 testes): d = 0,50, IC 95 % [0,44; 0,56]. Mais aprendizado quando o aluno procura semelhanças, quando o princípio vem depois da comparação, com conteúdo perceptual e com teste imediato. Limite: o efeito é de comparar casos, não de ouvir uma analogia pronta. | Alfieri, Nokes-Malach & Schunn 2013, 10.1080/00461520.2013.775712 | OpenAlex |

Regra que a evidência sustenta:

- Use a analogia para ajudar o iniciante a inferir e a entender a ideia geral.
- Dê também a definição literal, porque a analogia sozinha custou acertos nos detalhes.
- Prefira duas analogias ou dois casos, com a pergunta "o que os dois têm em comum?". Dê o princípio depois da comparação.

Não sustentado por fonte lida: dizer ao aluno onde a analogia deixa de valer. Essa frase é do roteiro, como cuidado de
quem escreve, e não carrega nota de evidência. Dois resultados também ficaram fora. Richland, Zur & Holyoak 2007
(10.1126/science.1142103): só a introdução do resumo foi lida, e ela não traz o achado. Duit et al. 2001 (*Learning and Instruction*,
DOI com parênteses, que o regex do script não lê): nenhum resumo achado.

### 5.2 Pausas e foco: ENTRA, só como cuidado de ritmo, sem número

| Técnica | Evidência e limite | Fonte (DOI) | Lido |
|---|---|---|---|
| **Pergunta de memória entre trechos** | Em dois experimentos com aula gravada, testes intercalados reduziram a divagação mental, aumentaram a anotação e melhoraram o aprendizado. Também reduziram a ansiedade com a prova final. Limite: aula em vídeo, laboratório. | Szpunar, Khan & Schacter 2013, 10.1073/pnas.1221764110 | Crossref e OpenAlex |
| **Troca breve de tarefa** | Lembrar de dígitos de vez em quando durante uma tarefa de vigilância evitou a queda de desempenho. Limite: tarefa de laboratório de vigilância, não de aprender conteúdo. | Ariga & Lleras 2011, 10.1016/j.cognition.2010.12.007 | Europe PMC (Crossref e OpenAlex sem resumo) |
| **Repouso depois de aprender** | Dez minutos de repouso acordado depois de ler uma história melhoraram a lembrança após 7 dias, contra dez minutos de jogo. Limite: histórias curtas, laboratório. | Dewar et al. 2012, 10.1177/0956797612441220 | Crossref e OpenAlex |
| **Micro-pausas** | Metanálise (22 amostras, N = 2.335): efeito pequeno em vigor (d = 0,36) e em fadiga (d = 0,35). Efeito geral em desempenho não significativo (d = 0,16). Pausas mais longas ajudaram mais. Limite: poucos estudos (19 registros). | Albulescu et al. 2022, 10.1371/journal.pone.0272460 | OpenAlex (o resumo do Crossref vem cortado) |
| **Atenção cai em 10–15 min?** | A revisão achou que a base dessa crença dá pouco apoio. O efeito varia entre pessoas. Limite: revisão da literatura, sem número. | Wilson & Korn 2007, 10.1080/00986280701291291 | Crossref e OpenAlex |

Regra que a evidência sustenta:

- Corte a aula com perguntas de recuperação. Elas servem ao mesmo tempo para fixar e para manter o foco (regra 1).
- Não prometa um limite em minutos. A crença de "10–15 min" não tem apoio. A skill deixa o limite de duração da aula
  ao autor do curso e só confere que o tempo prometido bate com o tamanho da aula.
- Sugira, no plano de estudo, um intervalo sem tela depois de uma aula. O apoio é fraco e de laboratório (Dewar 2012),
  então a frase sai como sugestão, sem número de ganho.
- Pausas não viram bloco da aula.

### 5.3 Objetivo da aula: ENTRA, como pergunta de pré-teste

| Técnica | Evidência e limite | Fonte (DOI) | Lido |
|---|---|---|---|
| **Objetivo antes do texto** | Três experimentos de laboratório. Mostrar o objetivo antes de cada trecho melhorou o teste final contra não mostrar. O resultado foi maior quando o aluno respondia perguntas de pré-teste do que quando só lia o objetivo. Com retorno sobre o pré-teste, o resultado piorou, o que contraria a regra 2 e vem de um só estudo. Limite: textos curtos, laboratório. | Sana et al. 2020, 10.1187/cbe.19-11-0257 | Europe PMC (o resumo do Crossref vem cortado) |
| **Revisão dos estudos de objetivos** | Mais de 25 estudos. O efeito de dar o objetivo antes depende do tipo de aprendizado e de quem aprende. A revisão não dá um número. | Duchastel & Merrill 1973, 10.3102/00346543043001053 | OpenAlex |
| **Quadro de objetivos e perguntas auxiliares** | Revisão que explica resultados discrepantes pelo processo que o objetivo ativa. Não dá um tamanho de efeito. | Hamilton 1985, 10.3102/00346543055001047 | Crossref e OpenAlex |

Regra que a evidência sustenta:

- Declare o objetivo no topo, em forma de pergunta que o aluno tenta responder (ligada ao bloco 2 do roteiro).
- Trate o objetivo como apoio modesto: a evidência é mista e antiga, com um estudo recente.
- Para o retorno do pré-teste, siga a regra 2. O resultado contrário de Sana et al. fica como aviso, não como regra.

### 5.4 Tarefa de aplicação: ENTRA, ligada ao uso real

| Técnica | Evidência e limite | Fonte (DOI) | Lido |
|---|---|---|---|
| **Aplicar o que se aprendeu a algo da própria vida** | Experimento de campo com alunos do ensino médio. Escrever como o conteúdo se liga à própria vida aumentou o interesse e as notas de quem esperava ir mal. Limite: ensino médio, uma matéria. O resumo só relata o ganho para quem esperava ir mal. | Hulleman & Harackiewicz 2009, 10.1126/science.1177067 | OpenAlex (o Crossref traz só o resumo do editor) |
| **Praticar com perguntas que pedem aplicação** | A recuperação com teste transfere (d = 0,40), e mais para perguntas de aplicação e inferência. Limite: a transferência cai com problemas de exemplo resolvido e com material não testado antes. | Pan & Rickard 2018, 10.1037/bul0000151 | OpenAlex |
| **Transferir para perguntas novas** | Quatro experimentos. Testar repetido produziu mais transferência, também para perguntas novas e de outras áreas, do que reestudar. Limite: textos em prosa, laboratório. | Butler 2010, 10.1037/a0019902 | OpenAlex |
| **Aprendizagem ativa** | Metanálise de 225 estudos em cursos de ciência, tecnologia, engenharia e matemática: +0,47 desvio-padrão nas provas. Chance de reprovar 1,95 vez maior com aula expositiva. Limite: ensino superior nessas áreas; "ativa" cobre muitas práticas. | Freeman et al. 2014, 10.1073/pnas.1319030111 | OpenAlex (o Crossref traz só o resumo de significância) |

Regra que a evidência sustenta:

- A tarefa pede ao aluno que use o conteúdo numa situação dele, e que escreva ou diga como o conteúdo se liga a ela.
- A tarefa inclui uma pergunta nova, de aplicação, que não repete o exemplo da aula.
- A tarefa é curta. Nenhuma fonte lida mede quanto tempo ela deve durar.

### 5.5 Decisão

| Lacuna | Decisão | Bloco do roteiro |
|---|---|---|
| Analogia | entra | 4d, com a regra de 5.1 |
| Pausas e foco | entra, sem número; destino: limite de duração e plano de estudo | nenhum bloco |
| Objetivo da aula | entra | 1, como pergunta de pré-teste |
| Tarefa de aplicação | entra | 7, ligada ao uso real |
