# Changelog — ansible-docker-backup-restore

Formato: [Semantic Versioning](https://semver.org/)

## [1.5.0] — 2026-11-12

Lições de um teste de DR no mesmo dia da 1.4.0: o conjunto de um servidor restaurado em stacks
isoladas num host de teste, com contagem igual nas duas pontas. Tudo medido nessa sessão. O que já
estava coberto (`manifest inspect` antes do restore, o ping que responde às duas fases do MySQL, a
forma `--all-databases` do dump) ganhou a borda nova no mesmo lugar, sem seção repetida.

- **Banco novo: quem é o root depende do init da imagem** (`restore-bancos.md` §4b). Sintoma que
  teria evitado: num `lscr.io/linuxserver/mariadb:11.4.8` novo, o `root@localhost` só entra por
  `unix_socket` e a senha da env vale para `root@'%'`; com `skip_name_resolve=0` até TCP em
  127.0.0.1 vira `localhost`. Um import com `-p<senha>` abortou a guarda com `ERROR 1045`. A
  origem, de um init antigo, só tinha `root@'%'` com senha. Sondar e ter modo socket.
- **`mysqladmin ping` sai 0 com Access denied** (§3). A espera por ping passou e a consulta
  seguinte levou `ERROR 1045`.
- **`--all-databases` traz os usuários de produção** (§5b). Os grants só trocam no `FLUSH`;
  depois dele o root do restore levou `ERROR 1045` pelo socket e pela senha (conferido), e a
  reexecução bateria na guarda. Contar e pré-checar pelo usuário da aplicação.
- **A config efetiva pode não ser a do volume** (`restore-volumes-e-guarda.md` §4). O `APP_KEY`
  do `.env` de um volume Laravel era outro; a produção usava o do compose (env vence `.env`).
  Comparar por hash. E o marcador de manutenção ficava na camada do container, fora do backup.
- **Pré-staging sem SSH entre os hosts e trava de isolamento da stack de teste** (§7). Fluxo pela
  máquina do operador com `.part`, manifesto e sha256; a corrupção do teste tem de manter o
  tamanho, senão o sha256 nunca é exercitado (a primeira versão do teste caiu nisso).
- **SQLite com WAL, contado numa cópia** (`provas-que-nao-mentem.md` §4c). Sabotagem sem o WAL:
  2 usuários onde havia 3.
- **Imagem por digest** (`levantamento-e-escopo.md` §4). `docker manifest inspect` com digest de
  índice falhou com `manifest verification failed`; o `docker pull` pelo mesmo digest baixou.
  O checklist do SKILL.md, que mandava só o `inspect`, agora diz isso.
- **Sensor de cobertura e exclusões** (`backup-pipeline-e-falha-silenciosa.md` §5, item 6). Uma
  matriz que ignorava o `container_dirs_exclude` dava 28,6 GB excluídos como cobertos.
- **Reset abrupto do cliente** (§2.5, depois da sessão órfã). "Sem reset" pela lista de boots,
  não pelo uptime (o uptime enganou); o Machine Check do boot seguinte apontou defeito de CPU.
- **Quatro armadilhas de Ansible** (`ambiente-e-armadilhas-ansible.md` §6): `fail_msg` renderizado
  com o assert verdadeiro, chave `copy` de dict virando método, aspas aninhadas em `$( )` no
  `shell:` livre, `regex_search` com barra dupla em bloco literal.
- Smoke do Codex: segue o da 1.3.3 (nenhum arquivo novo; a contagem de recursos não mudou).

## [1.4.0] — 2026-11-12

Lições de uma sessão de DR num servidor cujo hardware resetava sob carga. O que já estava coberto
(chave `rrsync -wo` com caminho relativo, a pergunta 3 do §1.1, `failed_when: false` que nunca
derruba a play, `manifest inspect` antes do restore, `compose_project` pelo prefixo do volume) não
foi reescrito.

- **A trava do `rrsync` presa por sessão órfã** (`backup-pipeline-e-falha-silenciosa.md` §2.5).
  Sintoma que teria evitado: o cliente resetou no meio do push, o TCP não fechou, e com
  `ClientAliveInterval 0` a sessão do servidor segurou o `flock` do `rrsync -wo` por 1h36; o push
  seguinte gerou o staging inteiro (~20 min de tar num host frágil) para cair no rsync com rc 12.
  Contramedidas: preflight que barra com `rrsync`/`rsync --server` vivo no destino, com fronteira
  de caminho, e `ClientAliveInterval` como raiz. A trava padrão foi conferida na ajuda do
  `rrsync` do rsync 3.2.7 (`-no-lock`; `-ro` o implica).
- **O valor conhecido também se supõe errado** (§1.1). Sintoma: dois registros de um handoff não
  existiam no dump real — o MediaWiki usa `$wgDBprefix` (`mw_page`) e o BookStack v26.09.2 não
  tem mais `pages` (páginas em `entity_page_data`); e o dump `--all-databases` trazia um `page`
  legado noutro banco, que um `grep` teria aceitado. Tirar o nome da config viva, preferir
  `INSERT INTO`, conferir o bloco `USE`, glob exato.
- **Imagem que saiu do registry, vista no backup** (§3.4 novo, checklist do `SKILL.md`). Sintoma:
  `bitnami/mariadb:10.5-debian-10` com `no such manifest` (também em `bitnamilegacy/`) rodando
  dois bancos vivos, fora do `docker save`; o §4 do levantamento só pergunta isso no restore,
  quando o host pode já ter morrido. `unauthorized` a partir do próprio host não prova nada e
  vira lacuna.
- **`failed_when: false` engole a falha da ação** (`provas-que-nao-mentem.md` §6). Sintoma: script
  não achado reaparecendo duas tarefas depois como `undefined variable`. `failed_when:
  <registro>.rc is not defined`.
- **`script:` relativo num arquivo incluído** (`ambiente-e-armadilhas-ansible.md` §6): a busca não
  vai à pasta acima de `tasks/` (medido com `-vv`).
- **Restore isolado com origem e destino diferentes** (`restore-volumes-e-guarda.md` §7 novo;
  comentário no topo de `assets/restore-volume-guard.yml`, sem mudar a lógica do asset).
- Dívida que já existia: o `metadata.version` do `SKILL.md` estava em 1.3.3 com o plugin em
  1.3.4; os dois vão a 1.4.0. O smoke Codex em `docs/codex/smokes.json` continua sendo da 1.3.3
  (a mudança é só de texto em references, checklist e um comentário de asset).
- Números: `SKILL.md` 200 → 202 linhas; `backup-pipeline-e-falha-silenciosa.md` 464 → 533 linhas.
- Como reverter: `git revert` do commit que traz esta entrada.

## [1.3.4] — 2026-10-22

Distribuição individual no catálogo Codex após instalação isolada, descoberta e smoke seguro de entrada dos workflows. Conteúdo canônico compartilhado com Claude Code/Cursor. Requisitos e limites em `docs/codex/compatibility.md` na raiz do marketplace.

## [1.3.3] — 2026-09-28

Conformidade com a spec e as boas práticas do agentskills.io, apontada pelo `skill-quality-audit`
v0.2.0: 2 avisos → 0. Sem mudança de comportamento; scripts e assets ficam byte-idênticos.

- **B1, assets órfãos.** O `SKILL.md` falava de "um contrato de variáveis, a guarda
  anti-sobrescrita comentada e um script de backup de volumes" sem nomear os arquivos, e os três
  contavam como órfãos. O parágrafo vira uma tabela "Arquivo | Use quando":
  `assets/restore-defaults.yml` (ao montar a role de restore), `assets/restore-volume-guard.yml`
  (ao escrever a task que grava num volume; a ordem das etapas só muda depois do §2 de
  `restore-volumes-e-guarda.md`), `assets/backup-volumes.sh` (host sem script de volumes, ou o
  `tar` rc=1 de banco vivo; exclusão só depois do §2.3 e do §5) e
  `scripts/check-backup-freshness.sh` (Gate 2, item 2).
- **C3, `backup-pipeline-e-falha-silenciosa.md` sem sumário.** Ganha `## Sumário` com âncoras
  para as 16 seções (`##` e `###`), logo depois da introdução.
- Números: `SKILL.md` 196 → 200 linhas (11.822 → 12.424 chars);
  `backup-pipeline-e-falha-silenciosa.md` 445 → 464 linhas.
- Como reverter: `git revert` do commit que traz esta entrada.

## [1.3.2] — 2026-09-03

Prompt audit (`/claude-api prompt-audit`, modelo-alvo Claude Fable 5.1); relatório completo fora do repo. Skill de operação frágil: scripts e assets ficam byte-idênticos (keep list #3).

- `backup-pipeline-e-falha-silenciosa.md`: o usuário `erp,zitadel` e "o IdP que autenticava todos
  os serviços" eram nomes de uma instalação usados como exemplo do mecanismo — a sonda do auditor
  mostrou o modelo repetindo `erp,zitadel` ao diagnosticar um host com outros nomes. Placeholders,
  gravidade generalizada.
- `provas-que-nao-mentem.md`: "vale contar como esta seção envelheceu / o parágrafo acima já
  existia" é diff contra a versão anterior do próprio arquivo; o caso real e a lição ficam, a
  arqueologia sai (está no CHANGELOG).
- Registrado como oportunidade (fora deste diff): a prova de "há dados" por blocos `COPY` é
  Postgres-only — `mysqldump` grava `INSERT INTO`, então o detector acusa todo dump MySQL como
  schema-only, e a skill promete `mysqldump`.
- `SKILL.md` ganha `metadata.version`.

## [1.3.1] — 2026-08-26

Higiene de `description`, sem mudança de comportamento: o texto tinha **593 chars**,
acima do cap de 500 do `CLAUDE.md`. A `description` é a superfície de triggering — é só
por ela que o Claude decide invocar a skill —, e descrição longa demais dilui o sinal e
pode ser **cortada em silêncio** na lista `/skills`, piorando justamente o que ela deveria
melhorar.

### Changed

- **Description encurtada de 593 para 473 chars**, espelhada nos três arquivos
  (`SKILL.md`, `plugin.json`, `marketplace.json`). Encurtada **em vez de somada**: o que
  saiu foi o detalhe de como a prova é feita (`gzip -t`, blocos COPY, registro conhecido) e a desconfiança do healthcheck do container de backup — detalhe que continua no corpo da skill, onde é útil de fato.
  Os sinais de disparo (o que a skill faz + os diferenciais que a distinguem das vizinhas)
  foram preservados.

## [1.3.0] — 2026-08-08

Sexta sessão, e o achado veio de fora: durante um deploy de produção **de outro
produto** no mesmo host, o container de backup do ERP e do IdP estava `unhealthy`
desde 06/05/2026 e **nunca havia gerado um único dump** — três meses.

### Adicionado

- **`backup-pipeline-e-falha-silenciosa.md` §1.1 — tamanho é proxy fraco.**
  **O quê**: três perguntas em ordem de custo — `gzip -t` (integridade), contar
  `^COPY public` (há dados?) e procurar **um registro conhecido** (é este banco?).
  **Por quê**: a skill parava na heurística de tamanho (`-size -1k`, "um dump que é só
  a mensagem de erro tem poucos bytes"), que pega o caso grosseiro e deixa passar o
  inverso — **um dump só com o schema é grande, bem formado e inútil para restaurar**.
  `CREATE TABLE` de cem tabelas dá dezenas de KB sem uma linha de dado. A terceira
  pergunta é a única que distingue "dump válido" de "dump **deste** banco": aponte o
  `pg_dump` para o cluster errado, ou para um homônimo vazio, e as duas primeiras
  passam. Fica no §1 e não no §2 de propósito — as quatro formas de morrer calado do
  §2 são falhas *do pipeline*; aqui a play saiu `failed=0`, o arquivo está no lugar e
  no horário certo, e não serve.
- **`backup-pipeline-e-falha-silenciosa.md` §1.2 — o healthcheck de um container de
  backup mede a coisa errada.** **O quê**: quando o backup é container dedicado
  (`prodrigestivill/postgres-backup-local` e parentes) em vez de play Ansible, forçar
  um ciclo e olhar o artefato; mais as duas armadilhas de configuração (lista CSV só
  faz fan-out em `POSTGRES_DB`; tag da imagem ≥ versão do servidor). **Por quê**: o
  healthcheck dessas imagens observa a **porta HTTP de status que elas expõem**, não o
  arquivo. O container fica genuinamente `healthy` — o servidorzinho dentro dele está
  no ar — enquanto o `pg_dump` falha todas as noites. No caso real a lista CSV estava
  em `POSTGRES_HOST`/`POSTGRES_USER`, onde o valor é literal, então o `pg_dump`
  autenticava com o usuário `erp,zitadel`. O banco desprotegido era o do IdP que
  autenticava todos os outros serviços do host.
- **`provas-que-nao-mentem.md` §4b — a ausência de sinal também não prova nada.**
  **O quê**: vazio é produzido por dois mundos indistinguíveis (nada aconteceu / o
  instrumento nunca esteve vivo), e a cura é provocar um positivo que você mesmo
  causou. **Por quê**: o arquivo cobria só o gêmeo oposto — sinal positivo enganoso
  (§1 "um 301 não prova nada", §4 "um 200 também pode mentir"). Falta que aplica às
  próprias verificações desta skill: `find … -size -1k` sem resultado prova que não há
  dump pequeno **ou** que o caminho está errado e não há dump nenhum. Pergunta única
  que resolve: *"isto teria me mostrado um positivo?"*

### Alterado

- **`scripts/check-backup-freshness.sh`** ganha `gzip -t` por dump e detecção de
  dumps **schema-only** (zero blocos `COPY`), ambos somente-leitura, mais uma nota
  sobre `pg_restore -l` para dumps em formato custom. A terceira prova (registro
  conhecido) fica como `note` deliberadamente: não é automatizável sem conhecer o
  domínio, e automatizá-la com um valor genérico daria falsa confiança.
- **Gate 2 ganha um passo** (o antigo 3 vira 4): "cada dump abre e contém dados",
  com o corolário do registro conhecido, e uma nota de que `healthy` de container de
  backup não é evidência. Quatro linhas novas na checklist rápida.
- `description`: acrescenta a prova por conteúdo e a desconfiança do healthcheck.

## [1.2.0] — 2026-07-29

### Adicionado

Quinta sessão. Um serviço que todos davam por restaurado havia quatro dias
estava, na verdade, quebrado em dois lugares — e **as duas falhas passaram por
um playbook verde**. As lições abaixo saem de descobrir por que a verificação
não pegou nenhuma das duas.

- **`restore-bancos.md` §5 — o datadir traz o PLUGIN de autenticação, não só a
  senha.** O §4 já cobria a senha de um volume MySQL pré-populado. Faltava o
  atributo que viaja junto: usuários vindos de um datadir restaurado num MySQL 8
  chegam com `caching_sha2_password`, e clientes antigos (`DBD::mysql`, `mysqli`
  velho, JDBC antigo) não fecham esse handshake sem TLS — a conexão é recusada
  **com a senha inteiramente correta**. Duas armadilhas específicas: a flag
  `--default-authentication-plugin` do compose *não* corrige (só vale para
  usuários criados depois dela, e os do datadir já chegam prontos), e o sintoma
  aparece em um cliente e não em outro — a interface web seguia no ar porque o
  driver do PHP fala `caching_sha2`, enquanto o endpoint dos agentes, em Perl,
  não conectava. Corrigir só o plugin, preservando a mesma senha, e confirmar
  antes **de onde** a aplicação lê usuário e senha: num caso real o usuário
  efetivo vinha de outro arquivo, carregado depois na ordem alfabética do
  diretório de configs. Corrigir a credencial do usuário errado não produz erro
  nenhum — só continua sem funcionar.

- **`provas-que-nao-mentem.md` §4 — promova a prova de conteúdo a contrato da
  role.** Esta seção já existia e já citava o domínio real que servia a página
  padrão do servidor web. Ele passou mais quatro dias servindo exatamente isso,
  num restore que terminou verde o tempo todo. A nota estava escrita, foi lida, e
  não impediu nada — quem roda o restore confia no que a role afirma, não no que
  um documento sugere conferir. Daí `verify_body_contains` (default vazio =
  comportamento anterior, sem efeito nos playbooks existentes), agora também no
  contrato em `assets/restore-defaults.yml`. Corolário na mesma seção: **verifique
  todos os planos de entrada** — interface humana e endpoint de máquina quebram
  de forma independente, e o que fica de pé mascara o que caiu.

- **`provas-que-nao-mentem.md` §7 — o erro do log pode ser o secundário.** Rastro
  apontando para rotina de encerramento (`rollback`, `finally`, destrutor) quase
  sempre é o handler de erro estourando sobre recursos que a falha real impediu
  de existir. Caso real: `Can't call method "rollback" on an undefined value`
  descrevia a segunda vítima; a causa era conexão recusada. Agravante: o erro
  primário costuma estar **desligado por padrão** (log de diagnóstico em nível
  zero, impressão de erro do driver desabilitada). Ligar a verbosidade antes de
  teorizar — e revertê-la no mesmo script, porque ela vaza dado sensível.

- **`ambiente-e-armadilhas-ansible.md` §6 — `lineinfile` com `regexp` que não
  casa.** Não é erro: o módulo acrescenta a linha no fim do arquivo e reporta
  `changed`. Num arquivo com blocos, ela cai fora de todo contexto, fica inerte,
  e a task fica verde. Provar que a diretiva existe (`grep -c` + `assert`) antes
  de reescrevê-la.

### Corrigido

- `SKILL.md` declarava `metadata.version: 1.0.0` enquanto o `plugin.json` estava
  em `1.1.0`. As duas passam a ser espelhadas.

## [1.1.0] — 2026-07-28

### Adicionado

Quarta sessão sobre o mesmo servidor e um segundo servidor irmão que **nunca
tinha tido backup**. Os bloqueadores dele estavam empilhados — três, cada um
escondendo o próximo — e três das lições abaixo saíram de desempilhá-los. Nada
que a 1.0.0 já cobria foi reescrito; estas são as bordas novas.

- **`backup-pipeline-e-falha-silenciosa.md` §2.5 — o caminho de push nunca foi
  estabelecido.** A etapa de rsync pressupõe que o cliente alcança o host de
  backup por SSH. Num host isso simplesmente não valia (`Host key verification
  failed` → `Permission denied`), e o engano que escondeu foi generalizar de
  *outro* cliente onde o push funcionava. A topologia de SSH é por par de hosts:
  verifique o push de **cada** cliente. E conceda o acesso com menor privilégio —
  chave dedicada confinada por `rrsync -wo`, **provada** sem poder de shell —
  porque autorizar a chave root ampla do cliente faz do host de backup um alvo de
  movimentação lateral para os backups de todos os servidores.
- **`backup-pipeline-e-falha-silenciosa.md` §2.1 (estendido) — preflight nos dois
  sentidos.** Além de "declarado e ausente falha", agora "em execução e **não
  declarado** avisa": um banco que nunca entrou no inventário não é dumpado por
  ninguém e nada dá erro. O preflight achou dois bancos de produção em execução e
  nunca dumpados.
- **`backup-pipeline-e-falha-silenciosa.md` §3.3 — bind mount escapa do
  `docker volume ls`.** O script de volumes itera `docker volume ls` e por isso
  **não** enxerga bind mount. Os dumps de banco presentes davam aparência de
  cobertura, mas dezenas de GB de mídia num bind mount ficavam de fora.
- **`ambiente-e-armadilhas-ansible.md` §6 — `delegate_to` num arquivo
  compartilhado corre.** Vários hosts delegando edição do mesmo `authorized_keys`
  se sobrescrevem; `throttle: 1` serializa.
- **`SKILL.md` Encerramento #5 (estendido) — reescrita de histórico.** Uma senha
  fraca igual a um identificador público (schema/container) não sai por
  substituição literal; só rotação resolve. Discriminador: o valor aparece na
  árvore do HEAD?

## [1.0.0] — 2026-07-27

### Adicionado

Primeira versão. Consolida o aprendizado de três sessões de recuperação de um
servidor Linux Dockerizado — a restauração em si e, na sequência, o conserto do
backup daquele mesmo servidor, que estava morto havia dias sem ninguém perceber.

**A skill cobre as duas metades de propósito.** Foi um restore que quebrou o
backup (um container renomeado, um inventário que não acompanhou), e foi uma
lacuna antiga do backup que decidiu o que o restore conseguiu recuperar.
Separá-las é como o incidente nasce.

- **`SKILL.md`** — espinha com 11 regras invioláveis, tabela de roteamento
  para as references, ordem de execução e **dois gates obrigatórios**: nenhum
  `VIRTUAL_HOST` antes de auditar o vhost do domínio, e nenhum restore dado por
  encerrado antes de o backup rodar ponta a ponta com `failed=0`.
- **`references/backup-pipeline-e-falha-silenciosa.md`** — as quatro formas de
  um backup morrer calado: `ignore_errors` + `no_log` na mesma task (esconde o
  erro *e* a mensagem); a mesma causa numa task sem `ignore_errors` (aborta a
  play e parece lentidão); `set -euo pipefail` com `tar` devolvendo rc=1 num
  datadir vivo (mata o script, e a ordem alfabética dos volumes faz parecer
  intermitente); caminho fixo ausente derrubando a play inteira. Mais a
  aritmética da retenção e o capítulo sobre exclusões.
- **`references/proxy-reverso-e-tls.md`** — montagens assimétricas de config do
  proxy criam referência órfã armada: o diretório que é volume sobrevive, o que
  não é morre, e `nginx -t` passa até alguém declarar o domínio. Nesse instante
  o proxy recusa a config inteira e o próximo restart derruba **todos** os
  domínios HTTPS do host. Mais: o PEM do certificado pode sobreviver sem o
  estado do cliente ACME, e a criação dos symlinks planos só acontece se a
  emissão der certo.
- **`references/restore-volumes-e-guarda.md`** — a armadilha do nome de projeto
  compose (silenciosa: cria volume vazio e o serviço sobe sem erro), a mesma
  armadilha na camada de rede (service key genérica vira alias DNS colidente), a
  guarda anti-sobrescrita em 8 passos, bind mount de arquivo único, e por que
  ler o entrypoint da imagem antes de montar volume pré-populado.
- **`references/levantamento-e-escopo.md`**, **`restore-bancos.md`**,
  **`ambiente-e-armadilhas-ansible.md`**, **`provas-que-nao-mentem.md`** — a
  metade de restore, incluindo a postura que ficou na espinha: *"não existe em
  backup" só é verdade dentro das origens que você enumerou por escrito*.
- **`assets/`** — contrato de variáveis, a guarda anti-sobrescrita comentada
  passo a passo, e um script de tar de volumes com o tratamento de rc=1.
- **`scripts/check-backup-freshness.sh`** — checagem somente-leitura de "o
  backup de hoje existe e está completo": buracos na sequência de datas, um dump
  por banco, dumps pequenos demais, cobertura de volumes e a conta da retenção
  contra o espaço livre real. Na primeira execução contra um host real ele achou
  um buraco de três dias que tinha passado despercebido.

### Notas

Todo o conteúdo é agnóstico: nenhum nome de servidor, domínio, container,
volume ou endereço de rede de qualquer ambiente específico. Os casos reais estão
descritos pelo mecanismo, com placeholders — o que faz a lição transferir, e
mantém fora deste repositório o que pertence ao repositório de infraestrutura de
onde ela veio.
