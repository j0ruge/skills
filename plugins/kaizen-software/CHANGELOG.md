# Changelog — `kaizen-software`

Formato: [Semantic Versioning](https://semver.org/)

## [1.3.6] — 2026-10-05

### Armadilhas do Check: o que sumiu, o que a sonda não leu, a regra que ninguém pediu

Lições de uma sessão real (ingestão de três monografias num acervo em Markdown, com guarda de
anonimização no pré-commit):

- **Seção nova `## Armadilhas` no `SKILL.md`**, depois da Fase 3, uma linha por caso. A skill não
  tinha seção de armadilhas (INFO F2 da auditoria); ela nasce para estas lições.
- **Validador verde não prova que nada sumiu.** O wrapper de extração imprimiu "OK" e o validador do
  conversor saiu 0 com 58 de 59 e 88 de 90 páginas: epígrafe e dedicatória, no pé da página, vinham
  marcadas como rodapé, e o conversor descartava rodapé. A Fase 2 manda verificar pelo artefato, mas
  não dizia que, numa conversão, isso é contar as unidades nas duas pontas. Padrão de falha: aceitar
  "validou" como "está tudo lá".
- **Sonda verde porque não leu o artefato.** A guarda de anonimização no modo "árvore inteira" disse
  "nenhum achado" sobre 3.671 arquivos rastreados; os três arquivos novos ainda não estavam no índice,
  e o modo do índice, depois do `git add`, achou 4. A Fase 2 manda sabotar a sonda; faltava conferir
  que o escopo dela cobre o artefato sob teste. Padrão de falha: o verde de uma sonda que nunca abriu
  o arquivo novo.
- **Regra herdada de handoff.** O handoff dizia que os nomes dos autores ficavam fora do repositório;
  o registro do pedido do usuário não tinha a frase, e quatro documentos anteriores faziam o oposto.
  Complementa o Gemba da fase 1 e a 1.3.5: o que um agente escreveu se rastreia até o usuário antes de
  virar instrução. Padrão de falha: obedecer a uma restrição que ninguém pediu, ou perguntar sobre ela
  como se fosse do usuário.
- **Correção verificada no caso de origem:** a contagem achou as páginas (corrigidas no conversor,
  com teste e mutante); o modo do índice achou os 4 casos (conferidos e isentos); a pergunta ao
  usuário, com o registro original na mão, decidiu os nomes. Não foram testadas em outro caso.

## [1.3.5] — 2026-10-04

### Surpresa antes da hora: primeiro a pergunta a quem tem acesso, depois a investigação

Lição de uma sessão real (limpeza de discos no Windows, com uma pasta em quarentena para exclusão):

- **Fase 3, *Para ações irreversíveis*, item 3 (Jidoka):** a pasta de resgate e parte da pasta em
  quarentena sumiram horas antes da data marcada para apagar. A sessão parou a sequência, o que estava
  certo, e foi explicar a surpresa por conta própria: transcripts do agente, histórico do PowerShell e
  do bash, lixeira, detecções do Defender, logs de outra ferramenta de IA e pastas novas em três discos.
  Nada apontou o autor, e a exclusão ficou suspensa. Na sessão seguinte, uma pergunta resolveu: o
  usuário tinha apagado de propósito. O item 3 mandava parar até explicar, mas não dizia por onde
  começar a explicar. Agora diz: primeiro pergunte a quem tem acesso ao artefato; a investigação por
  conta própria fica para quando essa pessoa não pode responder.
- Complementa o Gemba da fase 1 ("releia o que já foi respondido antes de perguntar"). A ordem fica:
  o que está escrito, depois a pergunta a quem tem acesso, por último a investigação.
- Padrão de falha: investigar longamente uma mudança que o dono do artefato explicaria numa linha, ou
  travar a tarefa sem fazer a pergunta.
- **Correção verificada no caso de origem:** a pergunta respondeu o que a investigação não respondeu.
  Não foi testada em outro caso.

## [1.3.4] — 2026-10-04

### Sonda que normaliza pela própria amostra é sabotada com a amostra inteira

Lição de uma sessão real (verificador de qualidade de imagem num projeto de pesquisa):

- **Fase 2, item 6, e *Poka-yoke*:** o verificador mede "canal de cor ausente" pela razão entre o
  canal mais fraco e o mais forte, dividida pela mediana dessa razão na própria fonte de imagens,
  com um piso de 0,02 abaixo do qual a medida relativa fica vazia. Uma fonte inteira (20.326
  imagens) perdeu o canal verde: a mediana deu 0,003, a medida relativa ficou vazia em todas as
  linhas e o sinal disparou 0 vezes. Os testes do verificador só tinham imagem defeituosa no meio
  de imagens boas, então a sonda passou na sabotagem sem nunca ver o caso que a cega. Quem achou
  foi um relato de campo, não a sonda. A regra "vermelho no sabotado, verde no bom" não dizia que,
  quando a referência sai da própria amostra, o sabotado tem de ser a amostra inteira. Agora diz,
  com o caso no vocabulário.
- Padrão de falha: sensor que fica cego ao defeito generalizado (silent-blinding), validado só com
  defeito pontual.
- **Sem correção verificada.** Naquele projeto o sensor ficou como está, de propósito (é
  pré-registrado), e o defeito virou resultado a medir. O aviso é melhoria de texto vinda de um caso
  real e não foi testado em outra sonda: nenhuma sonda foi refeita com o caso "amostra inteira" para
  mostrar que ele a deixa vermelha.

## [1.3.3] — 2026-10-04

### O artefato é o que chega ao destino; a sonda é conferida em estado novo

Lições de uma sessão real (publicação de uma skill nova no marketplace, a `windows-disk-cleanup`):

- **Fase 2, item 6, e *Rótulo ≠ artefato*:** o passo de verificação herdado do handoff era
  "`chmod +x` e conferir com `ls -l`". O `ls -l` mostrava `-rwxr-xr-x` e o `git ls-tree HEAD`
  mostrava `100644`: o clone tem `core.fileMode=false`, e o git ignora o `chmod`. O check olhava a
  cópia local, e o que vai para quem clona é o commit. Agora o item 6 diz que o artefato é o que
  chega ao destino, e o vocabulário traz o caso.
- **Fase 2, item 6, e *Poka-yoke*:** o selftest da skill rodou numa pasta de uma rodada anterior. O
  `New-Item HardLink` falhou com "o caminho já existe", e mesmo assim o check do hardlink deu PASS,
  em cima do link que a rodada velha tinha deixado. A regra "vermelho no sabotado, verde no bom" não
  dizia que os dois casos precisam ser montados do zero. Agora diz, e o vocabulário sugere fazer o
  teste recusar diretório de trabalho que não esteja vazio.
- Evidência: o bit foi gravado com `git update-index --chmod=+x`, e o `git ls-tree` passou a mostrar
  `100755` antes do push (`9b103fc`). O selftest passou a recusar a pasta reaproveitada (`rc=2`) e
  deu 10/10 (`rc=0`) numa pasta nova.

## [1.3.2] — 2026-10-04

### O Check cobre a prosa derivada; o Gemba inclui o que já foi respondido

Lições de uma sessão real (amostra de estoque para uma reunião, com nota no vault e e-mail à equipe):

- **Fase 2, item 6 (Check explícito):** o Check do CSV passou em 20/20 peças, mas a nota escrita a
  partir dele trazia "DE-JRC 119", somado de cabeça; o agrupamento por comando dava 137. O Check
  verificava o artefato principal e deixava passar a prosa copiada dele (nota, e-mail, resumo). Agora
  todo número ou afirmação copiado para a prosa sai de um comando.
- **Fase 1, item 1 (Gemba primeiro):** a nota do projeto já respondia o que era o local "DE", e mesmo
  assim a dúvida virou pergunta a um terceiro no rascunho; o usuário teve de repetir ("Já te falei
  isso"). Agora o Gemba inclui reler memória, notas e a thread antes de perguntar.
- Evidência: o número foi recalculado (137 + 25 + 22 = 184, igual à coluna do CSV) e a pergunta
  redundante saiu do rascunho e da nota.

## [1.3.1] — 2026-10-01

### Poka-yoke para estado de "já feito"

Lição de uma sessão real: uma régua de lembretes gravava o degrau como "disparado" antes de o rascunho
existir. O caminho sem credencial não desfazia o registro, e a oferta se perdia em silêncio depois do
conserto. Os 5 porquês chegaram à causa ("o estado gravava por padrão"), mas a skill não oferecia o
contraveneno, e o reflexo seria remendar só aquele caminho — o próximo ramo novo repetiria o defeito.

- `references/kaizen-conceitos.md`, item **Poka-yoke**: o padrão "confirmar para manter" — o registro nasce
  desfeito e só o ramo que confirmou a ação o mantém (gravar depois do efeito, ou `try/finally` que desfaz
  por padrão), com uma sonda de invariante que fique vermelha no código antigo.
- Evidência na sessão: a sonda de invariante falhou no código anterior ("degrau gravado sem rascunho") e
  passou depois da inversão.

## [1.3.0] — 2026-09-03

Pergunta do usuário, logo depois da 1.2.0: "além do poka-yoke, algum outro conceito do Kaizen está
sendo ignorado no fluxo? Cada passo é útil em qualquer área, inclusive resolução de problemas de TI."

### Medição, não opinião

`grep` de cada conceito do cânone em `SKILL.md` × references separou três estados: **passo no
fluxo** (Gemba, PDCA, SDCA, jidoka, 5 Porquês, 5S, poka-yoke, retrospectiva), **só verbete**
(mura/muri, kaikaku, blitz, genchi genbutsu) e **ausente** (yokoten, andon, Ishikawa, o 8º
desperdício, hansei, kata, A3, kanban, VSM). Nas seis respostas da sonda A/B da 1.2.0, o modelo
não usou yokoten, Ishikawa nem o 8º desperdício uma vez sequer; mura/muri e kaikaku só apareceram
quando o subagente leu a referência inteira. Mesmo defeito do poka-yoke: verbete não vira ação.

### Sete conceitos ganham um lugar no fluxo (+16 linhas, description intacta)

- **Yokoten** — Fase 3, bugs, passo 4 novo: a causa raiz achada aqui existe onde mais (servidores,
  repositórios, clientes, skills)? Campo `Yokoten` no template do Kaizen Log. Padronizar é vertical;
  yokoten é lateral — sem ele o mesmo incidente é resolvido N vezes, uma por equipe.
- **Andon** — princípio 5 e Fase 2: parar **visivelmente**; "pare, avise, conserte". Conserto
  silencioso não vira contagem nem padrão — e é a raiz do "tudo falha em silêncio".
- **Ishikawa** — Fase 3, bugs, passo 2 e nota no template dos 5 Porquês: quando um "por quê" tem
  duas respostas verdadeiras, siga cada ramo (processo, ferramenta, ambiente, medição,
  conhecimento) com contramedida própria. Incidente de TI raramente tem uma causa só.
- **Mura/Muri** — Fase 1, caça de desperdícios: o plano empilha tudo no fim? sobrecarrega alguém?
- **Kaikaku** — Fase 1, sinal de alerta: quando nem refatiando dá, nomear, exigir ADR com a
  alternativa kaizen medida, e fatiar o próprio kaikaku (strangler, feature flag).
- **8º desperdício** — seção nova em `desperdicios.md` (sem renumerar os 7): talento e conhecimento
  não usados — quem já resolveu não é consultado, runbook inexistente, bus factor.
- **Gemba sem ticket** — Fase 3, intro: olhar logs, alertas, métricas e as oportunidades do log
  periodicamente; o problema achado antes do usuário custa uma fração.

`kaizen-conceitos.md` ganha os verbetes de andon, Ishikawa e yokoten, para o ensino acompanhar o
corpo — e o corpo aponta para o verbete em vez de duplicá-lo. Ficam de fora, de propósito: hansei
(a retrospectiva cobre), kanban/WIP ("um incremento por vez" já é WIP 1), A3 (Plano PDCA + 5
Porquês já é um A3), kata, VSM, takt, hoshin — superprocessamento para uma skill de código.

## [1.2.0] — 2026-09-03

Duas fontes, uma mudança. **Relato do usuário:** "a skill tem acionado pouco o poka-yoke, na
verdade quase nunca." **Auditoria de prompt** (`/claude-api prompt-audit`, modelo-alvo Claude Fable
5.1) sobre os 4 arquivos da skill e os espelhos da description.

### Poka-yoke entra no fluxo operacional

Gemba antes de opinar: `grep -rni poka` na skill → duas ocorrências, e as duas no caminho de
**ensino** (`SKILL.md` L79, lista de vocabulário; `kaizen-conceitos.md` L36, o verbete). Zero nos
princípios, nas três fases e nos templates. O corpo pedia como contramedida "teste que teria pegado"
e "padronize em convenção/doc/CLAUDE.md" — teste e regra escrita; nunca "torne o erro impossível".

5 Porquês, encurtados: o modelo não propunha poka-yoke porque o fluxo não pedia; não pedia porque,
na 1.0.0, jidoka, 5 porquês, 5S e SDCA viraram **passos** e poka-yoke ficou **verbete**; ninguém
notou porque a ausência falha em silêncio — plano e log saem "corretos" sem ele. Causa raiz: não
havia, no fluxo, um ponto onde a pergunta "dá para tornar esse erro impossível ou óbvio?" fosse
feita, nem sensor que mostrasse a ausência.

Contramedida em seis hunks curtos, sem caps:

- **Princípio 6 (SDCA)** ganha a escada de padronização: poka-yoke (tipo, validador na borda,
  lint, hook, gate de CI, script que recusa) > template ou script > convenção escrita — e o porquê:
  regra escrita depende de alguém lembrar. Aponta para o verbete em vez de duplicá-lo.
- **Fase 1, caça de desperdícios:** "passo que só funciona se alguém lembrar de fazer X — e que um
  poka-yoke dispensaria?"
- **Fase 2, Check explícito:** sonda nova só merece confiança depois de vermelha num caso sabotado
  e verde num caso bom.
- **Fase 3, bugs:** padronizar **começando** pelo poka-yoke, nomeando o mecanismo; regra escrita só
  quando nenhum couber, e o registro diz por quê.
- **`templates.md`, 5 Porquês:** o campo Contramedida pede o poka-yoke — ou o motivo de não haver.
- **`desperdicios.md`, #7 Defeitos:** "qual poka-yoke teria impedido este defeito?"

Verificado por sonda A/B antes de aplicar (3 cenários, 1.1.0 × nova, subagentes com contexto
limpo): 14/14 asserções passam nas duas versões — sem regressão — e a diferença aparece onde a
1.1.0 fechava com regra escrita. Planejar uma feature: 0 → 4 menções, o Act vira uma tabela de
poka-yokes. Apagar uma branch: 1 → 4, o Act vira escada (auto-delete na plataforma > `fetch.prune`
> script sabotado > regra por último). Custo: +5 % de tokens.

### Auditoria de prompt — o que mudou e o que ficou

A skill é a mais limpa do marketplace em todos os sinais do guia (zero caps, zero `STEP n`, zero
datas/tickets/modelos). Três achados de confiança média aplicados: a **description** passou de 9
para 8 gatilhos (pares `kaizen log/retrospectiva` e `desperdício/dívida técnica`), ganhou
`poka-yoke` como capacidade e gatilho, e perdeu "respeitando as convenções do repo" (é
comportamento, coberto pela seção própria; não é gatilho) — 483 chars, agora entre aspas como o
`CLAUDE.md` pede; `ANTES` em caps virou `antes` (a razão já estava na frase seguinte); a pergunta
do desperdício #1 trocou "cotação" por "usuário" — vazamento do projeto `sales_quote`, onde a skill
nasceu. De brinde, "Caçe" → "Cace".

Ficou de propósito (keep list do guia): o script exato das ações irreversíveis, a redundância
funcional do "Padronizado em" em três arquivos (os textos concordam), os exemplos ilustrativos, e o
negrito de abertura dos itens — estrutura, não ênfase.

## [1.1.0] — 2026-08-07

Uso real da skill numa sessão de revisão + limpeza de repositório expôs quatro lacunas.
Três delas são a mesma ideia aparecendo em lugares diferentes, e ela agora tem nome.

### `Rótulo ≠ artefato` entra no vocabulário

Duas vezes na mesma sessão, em domínios sem relação, uma ferramenta disse que estava tudo
bem enquanto a coisa que deveria existir não existia:

- um `postgres-backup` respondia `healthy` **antes de qualquer ciclo** — o endpoint de
  status nasce com `Exit_status: 0`, que é valor inicial, não resultado de dump. Um deploy
  com senha errada passaria pelo gate de saúde e só falharia às 06:00 do dia seguinte;
- `PR MERGED` no GitHub descreve o que a PR **consumiu**, não o que a branch contém agora.
  Duas branches "seguras para apagar" tinham commits que nenhum `refs/pull` protegia.

A skill já mandava "ir ao Gemba", mas Gemba genérico não distingue *olhar o sistema* de
*olhar a coisa certa do sistema*. O verbete novo em `kaizen-conceitos.md` nomeia a
distinção e diz o que perguntar: qual artefato deveria existir, e ele está lá? A Fase 2
(Check explícito) passa a apontar para ele — "testes verdes" e "deploy succeeded" são
rótulos sobre o processo.

### O campo `Padronizado em` do kaizen log precisa de sensor

Numa entrada escrita nessa mesma sessão, o campo dizia `este log + .claude/napkin.md` e o
napkin não tinha uma linha a respeito. O log afirmava uma convenção inexistente, e ninguém
teria notado.

É o defeito acima aplicado ao próprio registro da melhoria: aquele campo é a **única** linha
do log que afirma algo sobre o mundo fora do log, e escrever o caminho dá a sensação de ter
padronizado. O template e o princípio 6 (SDCA) passam a mandar abrir o arquivo citado e
confirmar — ou escrever `pendente`, que é informação honesta e acionável.

### Poka-yoke: a sonda caseira que alarma à toa

Uma sonda escrita na hora (`git merge-tree` contra a branch principal) acusou 4 de 6 casos.
Ela media um **proxy** — a idade da branch — quando a pergunta era se havia trabalho a
perder. Sonda que erra em 4 de 6 ensina o operador a ignorá-la, e aí ele também não vê o
alarme verdadeiro. O verbete de poka-yoke ganha esse modo de falha e a contramedida:
sabotar de propósito para ver a sonda vermelha, e rodá-la num caso bom para vê-la verde.
Sonda conferida num estado só não é sonda.

### Fase 3 ganha "Ações irreversíveis"

A skill prega incrementos "pequenos e reversíveis"; apagar branch, rodar migration
destrutiva, revogar acesso ou publicar perdem o segundo adjetivo — e é justamente aí que
faltava orientação. Quatro regras curtas, sendo a central: **fatie de modo que o passo
reversível venha primeiro**. Na sessão, apagar as cópias locais antes das remotas fez uma
divergência inesperada aparecer quando ainda custava uma verificação; num laço único sobre
tudo, teria custado um commit órfão.

### Descrição

Enxugada, não só somada (390 → 474 chars). Entra o diferencial novo (verificar pelo
artefato) e o gatilho que a sessão provou faltar: a skill foi invocada para **confirmar uma
remoção destrutiva**, uso que nenhuma palavra da descrição anterior cobria.

## [1.0.0] — 2026-08-03

Empacotamento inicial da skill local `kaizen-software` no marketplace. A skill guia as três
fases da vida de um software — planejamento, implementação e manutenção — pelo ciclo PDCA, e
também ensina Kaizen (história, vocabulário, roteiro de treinamento).

### Por que empacotar agora

A skill vivia apenas em `<projeto>/.claude/skills/kaizen-software/`, um diretório que o
`.gitignore` do projeto ignora. Ou seja: existia numa única máquina, sem versão, sem
histórico e sem distribuição — um `git clean -xfd` a apagaria sem deixar rastro. Publicar é
o que lhe dá as três coisas, e é o próprio princípio de padronização (SDCA) que a skill
prega: melhoria que não vira padrão evapora.

### Added

- `SKILL.md` — 10 princípios (incrementos pequenos, PDCA, gemba, muda, jidoka, SDCA, 5
  porquês, kaizen log, anti-perfeccionismo, todos melhoram) e as três fases operacionais.
- `references/desperdicios.md` — os 7 desperdícios traduzidos para software, com perguntas
  de detecção, mais mura/muri.
- `references/kaizen-conceitos.md` — história, vocabulário e roteiro de ensino, para
  onboarding do time ou apresentação à diretoria.
- `references/templates.md` — Plano PDCA, Kaizen Log, 5 Porquês e Retrospectiva.

### Changed — description reescrita para caber no orçamento de trigger

A description original tinha ~1000 caracteres, abria com "Use esta skill SEMPRE" e repetia
os gatilhos duas vezes (em prosa e em lista). Isso viola o padrão do marketplace (≤ 350
caracteres, teto 500) e o efeito não é cosmético: quando o conjunto de skills estoura o
`skillListingBudgetFraction`, as descriptions são **descartadas silenciosamente** e a skill
perde justamente o texto que a faz disparar. A nova tem ~385 caracteres, um idioma só e uma
linha `Gatilhos —` com 8 termos. Mesmo texto espelhado em `SKILL.md`, `plugin.json` e
`marketplace.json`.

### Changed — o template do Kaizen Log passou a refletir o uso real

O uso da skill no projeto `sales_quote` (feature SQ-62) produziu entradas de log com duas
subseções que o template não previa, e ambas se provaram as mais consultadas depois:

- **Desperdícios evitados (cortes conscientes)** — o que ficou fora do escopo e por quê.
  Sem isso, o corte deliberado é lido como esquecimento seis meses depois, e alguém reabre
  um escopo que já havia sido rejeitado com razão. Também fecha o laço com
  `references/desperdicios.md`, até então consultado só na entrada do ciclo.
- **O que aprendemos** — a pegadinha técnica que custou tempo (no caso real: o `tsconfig`
  que exclui `__tests__` do typecheck, e o glob de rota que não casa `/`). Sem registro, a
  próxima pessoa paga o mesmo custo de descoberta.

Ambas entram como **opcionais** — a skill rejeita preencher formulário sem conteúdo real.
