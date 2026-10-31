# Changelog — `kaizen-software`

Formato: [Semantic Versioning](https://semver.org/)

## [1.4.8] — 2026-10-31

Patch: duas lições de uma sessão que pôs o controle de um projetor (interface web embarcada) num
módulo do Bitfocus Companion. O detalhe foi para `references/kaizen-conceitos.md` e
`references/templates.md`, e o `SKILL.md` ganhou só dois termos em frases que já roteiam para
lá, porque estava a 132 caracteres do teto de 20 mil.

- **Ação que derruba o próprio canal de volta é irreversível.** Um teste autorizado desligou o
  projetor pela web às 12:40:53. A web respondeu `pw:"0"` por cerca de 13 s, e a partir de 12:41:17
  as consultas deram timeout ou conexão recusada: no standby comum, a rede do aparelho desliga.
  O comando de religar dependia dessa rede, e o operador teve de religar pelo controle remoto
  (12:43:56). O plano tinha "desligar → religar após o cooldown" como passo reversível. A lista de
  ações irreversíveis (apagar, migration, revogar, publicar) não cobria esse caso.
  - `SKILL.md`: a lista entre parênteses das ações irreversíveis ganhou "desligar ou reconfigurar o
    que só se alcança pelo canal que a ação derruba".
  - `templates.md`: o Plano PDCA § Riscos e reversão pede o caminho de volta fora de banda (alguém
    no local, console, controle remoto). O item "Ação irreversível" do checklist de validação
    ganhou o mesmo caso.
- **Dublê de teste é sonda.** 26 testes passavam contra um servidor falso em `node:http`. No
  aparelho real, o cliente falhou com `Parse Error: Missing expected CR after response line`,
  porque o servidor embarcado termina as linhas do cabeçalho só com LF e o fake, feito com a
  biblioteca da norma, nunca mandaria isso. Refeito em TCP cru com os bytes capturados do fio, o
  fake reproduziu os 6 vermelhos do aparelho antes da correção. A skill pedia caso sabotado
  montado do zero e Check no artefato, mas não dizia que o dublê precisa imitar o artefato
  observado, e não a norma.
  - `SKILL.md`: "Sonda nova (script, check, healthcheck, dublê de teste)". O "ver *Poka-yoke*"
    que já estava na frase leva ao detalhe.
  - `kaizen-conceitos.md` § Poka-yoke: parágrafo "Dublê de teste é sonda", com o caso.

Dívida pré-existente, fora deste patch: o smoke do Codex (`docs/codex/smokes.json`) ainda é o da
1.4.3. Os INFO F1 (references sem "quando ler"), F4 (sem evals) e D1 (afirmações factuais) da
auditoria já vinham de antes.

## [1.4.7] — 2026-10-27

Patch: uma lição do planejamento de um sync automático de arquivos de segredo para uma wiki
interna, em `references/kaizen-conceitos.md` e `references/templates.md`. O `SKILL.md` ficou
igual, salvo a versão, porque está a 132 caracteres do teto de 20 mil, e já roteia as duas
referências.

- **Rótulo ≠ artefato vale para a premissa do pedido.** O pedido dizia que o destino era o lugar
  para dado sensível. A permissão lida pela API mostrou que a página herdava a leitura de todos
  os papéis com acesso geral (dezenas de contas), e o plano ia automatizar a exposição. O Gemba
  da skill mandava reler código, memória e thread, mas não conferir no artefato a premissa de
  acesso do próprio pedido.
  - Agora o verbete traz o caso.
  - O "Gemba — situação atual" do Plano PDCA pede essas premissas.
  - O checklist da Validação de plano ganhou o item.
  - O que resolveu na sessão: o primeiro incremento virou restringir o destino, e o script
    ganhou um poka-yoke que recusa destino mais exposto que a origem.

## [1.4.6] — 2026-10-25

Patch: duas lições de uma sessão no `magic_tutor` (um alvo do kit sdd), em
`references/kaizen-conceitos.md`. O `SKILL.md` já roteia as duas seções, e ficou
igual, salvo a versão, porque está a 132 caracteres do teto de 20 mil.

- **Poka-yoke:** a verificação que mora num comando opcional não protege a porta
  que gasta. O aviso de que nenhuma regra de leitura cobria a skill `codereview`
  existia só no `sdd preflight`. O `sdd run` pagou a REVIEW (US$ 5,61) sem
  repeti-lo, e as três missões de 2026-10-24 tiveram 5, 2 e 3 leituras negadas no
  `pipeline.log`. O 4º porquê parou aí. A contramedida no alvo foi o `READ_EXTRA`
  (j0ruge/magic_tutor#104), e no kit ficou o achado (j0ruge/sdd_agents#326).
- **Rótulo ≠ artefato, o inverso:** o Check feito numa cópia só vale para o
  artefato entregue com o mesmo hash de conteúdo. Os testes rodaram numa cópia
  descartável, o rebase de verdade gerou outros commits, e o `git rev-parse
  HEAD^{tree}` igual (`9937589`) levou os 952 testes ao PR (j0ruge/magic_tutor#103).

## [1.4.5] — 2026-10-22

Integra o Check incremental preservado na worktree `9e53c38`, sobre a versão
atual 1.4.4, sem rebaixar o plugin ou retirar as lições posteriores à 1.3.6.

- A Fase 2 direciona para `references/check-incremental.md` quando o critério é
  não introduzir regressão em artefato com legado. A receita preserva baseline,
  identidade, multiplicidade e severidade; dívida anterior e gates obrigatórios
  continuam separados. O exemplo sintético em memória cobre contagem igual com
  identidade diferente, duplicação, agravamento e desaparecimento.
- O controle com o texto anterior já tomou decisões corretas nos três cenários
  avaliados, por inferência. A integração torna o procedimento explícito; não é
  descrita como correção de uma falha de execução reproduzida.
- A revisão identificou falso bloqueio no exemplo antigo: severidade fazia
  parte da identidade e uma redução parecia achado novo. O exemplo adaptado
  compara identidade e limiares de severidade separadamente, com RED/GREEN para
  redução e controles de multiplicidade, agravamento e desaparecimento.
- Descrição e compatibilidade Claude/Cursor/Codex preservadas.

## [1.4.4] — 2026-10-22

Distribuição individual no catálogo Codex após instalação isolada, descoberta e smoke seguro de entrada dos workflows. Conteúdo canônico compartilhado com Claude Code/Cursor. Requisitos e limites em `docs/codex/compatibility.md` na raiz do marketplace.

## [1.4.3] — 2026-10-20

### Vocabulário válido não prova sentido igual

Lição de uma sessão real (TCC sobre classificação de telas de RADAR e ECDIS gravadas em VDR, rotulagem humana
já começada quando o campo corrigiu a taxonomia):

- **Armadilha nova "Vocabulário válido não prova sentido igual".** O código `radar_overlay` continuou na lista
  de classes, mas mudou de definição: deixou de ser o RADAR com carta e passou a ser a tela do ECDIS com o radar
  sobreposto, porque é o termo do campo. A ferramenta de rotulagem só conferia se o valor estava no vocabulário.
  Rótulos gravados pela definição antiga passariam com o sentido errado, e a exportação declararia o guia novo.
  Correção verificada:
  - o rótulo passou a carregar o guia sob o qual foi gravado (uma marca de versão ao lado do arquivo);
  - a ferramenta recusa misturar guias;
  - um modo de arquivamento renomeia o que é de outro guia, sem apagar.

  O caso sabotado ("rótulo antigo só com classes que continuam válidas") falhou nos cinco modos antes do código.
  No dado real, a ferramenta saiu 2 até o arquivamento das 22 linhas antigas.

### Analisada e não aplicada

- "Contradição na fonte resolvida por convenção, sem perguntar a quem opera" (o mesmo erro de domínio apareceu
  duas vezes no material e as duas foram resolvidas como "convenção deste trabalho"). A skill já cobre a
  família: Jidoka ("'deve ser normal' não é explicação… perguntar a quem tem acesso ao artefato") e a armadilha
  do handoff (regra sem origem vira pergunta). Não há correção verificável, porque é regra de conduta. Ficou
  no `CLAUDE.md` do projeto.

### Dívida pré-existente (não tratada aqui)

- `SKILL.md` com 19.404 caracteres (era 18.893), abaixo do teto de ~20 mil. **Correção da nota da 1.4.2:**
  pela `skill-refactoring`, numa skill de fluxo as armadilhas ficam no `SKILL.md`, onde evitam o erro antes de
  a reference ser lida. O próximo retrofit que passar do teto deve comprimir (Estratégia B: listas e blocos em
  tabela), e não extrair *Armadilhas* para `references/`.
- Auditoria sem mudança: F1 (`kaizen-conceitos.md` e `templates.md` citadas sem dizer quando ler), F4 (sem
  evals), D1 (afirmações sem sensor) e G1 (gate do Hermes ausente nesta máquina).

## [1.4.2] — 2026-10-20

### Sonda que não rodou e número que não veio da fonte

Lições de uma sessão real (kit para criptografar estações com BitLocker medindo o desempenho antes e depois,
planejado com esta skill e com o material destinado à diretoria):

- **Armadilha "Sonda verde porque não leu o artefato" estendida: a sonda precisa ter rodado.** O workflow do
  GitHub Actions que barra chave de recuperação no repositório não executou no push que criou o repo:
  `gh run list` voltou vazio. Ausência de vermelho foi lida, por um instante, como verde. Só o push seguinte
  (com `workflow_dispatch` acrescentado) gerou execução, conferida com `gh run watch` → `success`. A causa
  provável (repo criado pelo push antes de o workflow ser registrado) **não foi verificada**; a lição verificada
  é conferir que existe execução, não só que nenhuma falhou.
- **Armadilha nova "Número de pesquisa vem da fonte, não do resumo".** A pesquisa sobre o impacto do BitLocker
  veio de um agente que leu cobertura secundária. Reabrir as 26 fontes corrigiu 6 itens: a cópia de 50 GB e o
  PCMark 10 (−11% e −20%) eram comparados com a criptografia por hardware (OPAL), não com "sem criptografia"
  (−13% e −19%); e "forçar XTS-AES-128 desliga o BitLocker acelerado por hardware" era falso (só AES-CBC ou a
  política FIPS desligam). A regra da Fase 2 ("número copiado para prosa sai de um comando") cobria artefato
  local, não fonte externa resumida por terceiros — e era esse número que ia para a diretoria. A família é a de
  "Regra herdada de handoff": o resumo é o rótulo, a fonte é o artefato.

### Dívida pré-existente (não tratada aqui)

- `SKILL.md` com ~18,9 mil chars, perto do teto de ~20 mil da spec. O próximo retrofit deve antes passar pela
  `skill-refactoring` (candidato: mover *Armadilhas* para `references/armadilhas.md`, roteada do `SKILL.md`).
- Auditoria: F1 (`kaizen-conceitos.md` e `templates.md` citadas sem dizer quando ler), F4 (sem evals), D1
  (afirmações factuais sem sensor) — já existiam no baseline.

## [1.4.1] — 2026-10-17

### O render como unidade do Check, e Kaizen fora do código

Lições de uma sessão real (aula de Escola Bíblica montada como deck HTML para projetor, sem git nem testes,
organizada com esta skill):

- **Armadilha "Validador verde não prova que nada sumiu" estendida para asset visual.** Para "limpar" o SVG do
  logo extraído do PDF do manual de marca, removi os `<path>` sem `fill`; isso esvaziou os `<clipPath>` que
  desenhavam o logo. O build do deck saiu "ok", o logo sumiu de todas as lâminas e só a screenshot mostrou.
  A armadilha falava de conversão de texto e de contar unidades; em asset visual a unidade é o render.
  Padrão de falha: transformar um asset e confiar no gate de forma. Correção verificada no caso de origem:
  logo refeito a partir dos vetores (`get_drawings`), render de teste e segunda rodada de screenshots.
- **Item novo em "Respeite as convenções do projeto": projeto que não é software.** A skill fala em teste,
  commit e CI; num deck de aula foi preciso traduzir na hora: Check = artefato renderizado (screenshots,
  PDF) + revisor independente; poka-yoke = script que recusa a entrada errada (`contraste.py` sai 1 com par
  de cor abaixo do mínimo; `lacunas.py` acusa trecho pulado pelo Whisper, vermelho no caso real: uma
  citação bíblica de 11 s sumida); sem git, o registro vai para o plano e o `KAIZEN_LOG.md`. Antes de
  aplicar, conferido que nenhuma outra skill do marketplace cobre esse mapeamento (a `html-presentation`
  cobre a verificação do deck, não o Kaizen). Padrão de falha: largar o Check e o poka-yoke porque o
  projeto não tem teste nem CI. Usado uma vez; não testado em documento ou mídia.

## [1.4.0] — 2026-10-16

### Validar um plano que já chegou pronto, e a sabotagem que o cache engoliu

Lições de uma sessão real (planejamento da `@jrc/object-storage` como biblioteca da JRC: brainstorm,
grill de 13 perguntas e, a pedido do usuário, validação Kaizen da missão com checklist):

- **Template novo, § Validação de plano** (`references/templates.md`), roteado pela Fase 1 e pela
  tabela de artefatos. O usuário pediu "valide se a missão cumpre a skill e gere checklist"; a skill
  só tinha templates para *escrever* um plano (Plano PDCA), não para *validar* um já decidido, e a
  validação foi improvisada: tabela dos desperdícios contra o plano, ajustes K1–K6 que voltaram ao
  plano e um checklist. O template é esse formato, com o checklist tirado dos princípios e armadilhas
  desta skill. Padrão de falha: cada validação sai num formato, e a que vira só uma nota não muda o
  plano. Usado uma vez (`lighthouse_project`, `docs/superpowers/specs/2026-10-16-jrc-libs-object-storage-design.md`
  § 8); não testado em outro caso.
- **Armadilha nova, "Sabotagem que não chegou à ferramenta".** Para provar que o `npm ci` recusa um
  tarball trocado em `vendor/`, o caso sabotado deu rc=0 e instalou o conteúdo **antigo**: o npm
  serviu os bytes do cache global (`~/.npm`) pelo `integrity` do lockfile e nem leu o arquivo. Com
  `npm ci --cache <diretório vazio>`, o mesmo caso reprovou com `EINTEGRITY`. A Fase 2 e o
  *Poka-yoke* do `kaizen-conceitos.md` mandam montar os dois casos "do zero", mas os exemplos falam
  de pasta e fixture; o cache global da ferramenta fica fora da pasta e é estado de rodada anterior
  do mesmo jeito. Padrão de falha: ler o verde do caso sabotado como "a ferramenta não confere" e
  descartar o poka-yoke certo. Correção verificada no caso de origem (cache vazio → `EINTEGRITY`,
  rc=1).

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
