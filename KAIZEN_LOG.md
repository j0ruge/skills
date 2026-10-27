# Kaizen Log — skills

Registro de melhorias: o que mudou, por quê, e onde o aprendizado foi padronizado
para não se perder. Complementa os `CHANGELOG.md` de cada plugin — eles contam o
**o quê** por versão; aqui fica o **porquê de processo**.

---

## 2026-10-27 — env-docs-sync 0.1.0: hook que documenta segredo, provado nos dois hosts antes de publicar

- **Antes:** a loja não tinha plugin que mantivesse uma página de documentação a partir de arquivos
  vigiados. No Codex, um hook de plugin só rodava depois de aprovado à mão em `/hooks`.
- **Depois:**
  - **Publicação:** env-docs-sync 0.1.0 (`cfdcb44..d3d812b`), com o hook nos dois hosts e o
    `install --codex`, que grava o trust conferido contra o `hooks/list` do próprio Codex.
  - **Testes:** 310 (rodados de novo em `d3d812b` no fechamento), 43/43 mutantes (`tests/mutantes.py`)
    e o oráculo do Codex 9/9 no 0.165.0 (`tests/oraculo_codex.py`).
  - **Primeiro consumidor:** um repositório privado, com 9 arquivos locais e 2 remotos `ok` e a
    SessionStart calada quando nada muda.
- **Check:**
  - **codereview:** 6 rodadas (F, B, A, A, A e A sem achado);
  - **gates:** `validate-versions`, catálogo Codex, `check_release_sync` e `claude plugin validate` com
    rc 0;
  - **sensor anti-marca:** vermelho com a fixture sabotada;
  - **CA9:** pela cópia instalada nos dois hosts.
- **O que aprendemos:**
  - **O trust do Codex é preso ao conteúdo do pacote.** Um byte mudado deixa o hook `modified` até o
    `install --codex` rodar de novo, e o `remove` não apaga o `[hooks.state]`. Por isso a seção CI/CD
    entrou antes da 0.1.0: cada update desliga o hook no Codex.
  - **Hook com efeito colateral visível é síncrono.** O C5 do plano pedia `async`. Mas num `async` o
    `systemMessage` vai para o Claude, e não para a pessoa, e o processo morre no fim de um `claude -p`.
  - **Um hook de Stop não pode sair 2 por acidente.** `python3 <script ausente>` sai 2, e um Stop com
    exit 2 entra em loop. O `command` confere o arquivo antes (`[ -f "$f" ] || exit 0`).
  - **Uma linha de carimbo cria uma revisão por gatilho.** A linha "sincronizado em" mudava a cada host
    ou estado perdido. Agora a escrita pula o bloco que a página já tem com o mesmo hash.
  - **O rodador de mutantes copia o plugin inteiro.** Com só a pasta da skill, o sensor anti-marca
    (`SKILL.parent.parent`) varreu a pasta temporária inteira, e o primeiro mutante travou 600 s.
- **Padronizado em:**
  - **no pacote:** `references/hosts.md` §4 (trust, com fonte e oráculo), `references/safety.md`
    (superfícies × testes × mutantes), `references/kb.md` §3 (pular o bloco igual), o `command` do
    `hooks/hooks.json`, os docstrings de
    `tests/mutantes.py` e o CHANGELOG [0.1.0];
  - **na loja:** a lição do `rc=` depois de um pipe, no codereview 2.27.13 (`cfdcb44`).
  - **Pendente:** as lições do trust e do `hooks/list` no `hook-builder`, ainda sem retrofit.
- **Oportunidades** (cada uma com o próximo passo pequeno):
  - **ACL incompleta:** a normalização dos ids `bkmrk-` do BookStack mora no núcleo
    (`env_docs_sync.py:1034-1053`), e não no adaptador kb. Próximo passo: movê-la quando entrar um
    segundo backend.
  - **`SKILL.md` com 19 861 caracteres,** a 139 do aviso do audit. Próximo passo: a próxima edição move
    texto para `references/` antes de acrescentar.
  - **Retrofit do `hook-builder`:** trust por conteúdo, o oráculo `hooks/list`, o `codex exec` que não
    mostra o `systemMessage`, o `PLUGIN_DATA` sem a pasta criada e `NumberOfPasswordPrompts` com
    `sshpass`.
  - **Retrofit do `skill-quality-audit`:** o F1 lê só a linha da referência e a anterior.
  - **Nenhum plugin da loja tem `LICENSE`** (`LICENSE_MISSING` no `claude plugin validate`).

---

## 2026-10-22 — Consolidar worktrees e integrar o Check incremental preservado

- **Antes:** a worktree Kaizen guardava `9e53c38`, não integrado, enquanto a loja
  evoluiu até 1.4.4. O procedimento de baseline estava ausente da versão atual;
  o exemplo antigo tratava redução de severidade como achado novo.
- **Depois:** Kaizen 1.4.5 preserva o texto atual e acrescenta a receita, com
  identidade independente da severidade e comparação por limiar. Não houve
  rebaixamento de versão ou remoção das lições posteriores ao commit antigo.
- **Check:** leitura independente confirmou a lacuna explícita; o texto anterior
  já permitia decisões corretas por inferência, sem falha de conduta reproduzida.
  O falso bloqueio do exemplo foi reproduzido em RED e corrigido; cinco controles
  mutados falharam, enquanto o exemplo correto passou. Re-revisão independente
  do ajuste sem novos achados. SQA antes/depois sem novos findings.
- **Preservação:** quatro branches e 2.714 arquivos da sessão foram reunidos em
  `/home/joruge/artefatos/skills-pr6-2026-10-22-1dspgoxp/`, com origem e hashes no
  manifesto e bundle Git verificado. Originais preservados; perfis temporários,
  caches, metadados Git e arquivos com nomes de credenciais/configuração local
  constam nas exclusões. A consolidação é local, sem publicar esses arquivos.
- **Padronizado em:** Fase 2 de Kaizen e `references/check-incremental.md`;
  metadados/README/CHANGELOG sincronizados em 1.4.5.

---

## 2026-10-22 — Diagnósticos e transporte na segunda revisão do PR #6

- **Antes:** YAML e mapas inválidos escapavam como traceback; a prova de
  descoberta misturava `select` com buffer de texto; o instalador duplicava o
  contrato gerado. Três skills dependiam de placeholder sem explicar a entrada
  no Codex. A documentação confundia aviso local com aprovação externa.
- **Depois:** erros de entrada normalizados na origem, JSONL acumulado em bytes,
  contrato do gerador reutilizado e entrada textual explícita. A interseção do
  auditor permanece estrita; a documentação registra `G2 ERRO` externo.
- **Check:** baseline 53 gerais/55 auditor; depois 61 gerais/55 auditor/15 scanner.
  Oito regressões e cinco mutantes detectados. SQA das três skills sem diferença
  de findings. Auditor externo real de release e ticket retornou 1, como agora
  documentado; esse resultado não é tratado como check verde.
- **Padronizado em:** adaptadores, instalador, testes de transporte e instruções
  canônicas das três skills; rastreabilidade em `docs/codex/verification.md`.

---

## 2026-10-22 — Origem da revisão separada da conta que publica

- **Tipo:** padronização de duas lições verificadas, autorizada pelo usuário.
- **Antes:** a detecção por logins perdia os achados do Claude Code publicados
  pela conta do operador; a passagem de sensores não explicitava o rename que
  esconde a origem monitorada.
- **Depois:** codereview 2.27.0 / coderabbit-pr 4.6.0 coleta candidatos pelo corpo
  do comentário, confirma a origem e compara o SHA completo antes de contar
  cobertura. O marcador sozinho não autentica a revisão. O passe 6.11 inclui
  remoções e renames nos limites do escopo, respeitando read-only e autorização.
- **Check:** 14 controles e consulta GitHub real preservaram os quatro achados;
  leitura fria conferiu roteamento, proveniência, contagem, cobertura, severidade
  e limite de atuação. SQA antes/depois: zero erros/avisos nas duas skills, sem
  NOVO ou SUMIU; descrições preservadas e ambas abaixo de 20.000 caracteres.
- **Padronizado em:** `plugins/codereview/skills/coderabbit-pr/references/reviewer-registry.md`,
  seu roteiro no SKILL.md e `plugins/codereview/skills/codereview/references/detection-passes.md`.
- **Yokoten:** candidatos sem origem ou com parse inconsistente permanecem
  pendentes, sem virar aprovação; revisão de commit antigo não cobre head novo.
  Tabela de logins duplicada fundida com o cadastro canônico, sem retirar logins.

---

## 2026-10-22 — Revisão externa cobre ordem e rename nos limites do pacote

- **Tipo:** correção de causa raiz e redução de duplicação apontada na revisão.
- **Antes:** o catálogo comparava plataformas pela ordem, divergindo do validador;
  o hook via somente o destino de renames para fora dos diretórios monitorados.
- **Depois:** comparação de plataformas independente da ordem, preservando tipos
  e conteúdo; `--no-renames` expõe a remoção da origem ao gate staged.
- **Check:** dois casos de ordem e um rename ficaram RED antes e GREEN depois.
  Remover as guardas fez as regressões falharem. Passaram 53 testes gerais, 55 do
  auditor e 15 do scanner. O preview combinado passou nos três cenários reais
  de distribuição, com 25 pacotes / 289 arquivos.
- **Padronizado em:** `scripts/codex-marketplace.py`, `scripts/pre-commit` e testes
  em `tests/test_codex_marketplace.py` / `tests/test_codex_validation.py`.
- **Yokoten:** catálogo e adaptador usam `skill_paths` e `atomic_write` comuns;
  mutantes foram detectados nos dois consumidores e na limpeza do temporário.
  Fallbacks mortos de PyYAML foram removidos; a dependência continua obrigatória.
- **Integração:** após autorização, `2511ba8` incorporou a resposta e `cb7f95c`
  integrou main `0d2e56d` conforme o preview aprovado. Os 53 testes gerais e os
  três cenários reais do commit integrado passaram; 25 pacotes / 289 arquivos
  conferidos, com CICD 2.39.1 e deploy 3.3.3.

---

## 2026-10-22 — Hash tipado preserva a varredura do manifesto

- **Tipo:** padronização de correção verificada.
- **Antes:** §6.10 de codereview reconhecia checksums sinalizados como credenciais,
  mas oferecia apenas allowlist do arquivo como remédio durável.
- **Depois:** codereview 2.26.10 oferece primeiro um registro com `sha256` quando
  o schema puder mudar, preservando a alternativa anterior para schema imutável.
- **Check:** 15 testes passaram, incluindo três fixtures independentes com
  gitleaks real: alerta original, hash tipado limpo e canário detectado no mesmo
  manifesto. SQA antes/depois sem erros/avisos; gate sem `NOVO` ou `SUMIU`.
- **Padronizado em:** `plugins/codereview/skills/codereview/references/detection-passes.md`
  §6.10 e `tests/test_scan_secrets.py:TestTypedHashManifest` da mesma skill.
- **Yokoten:** a referência exige conferir todos os hashes na revisão fixada,
  atualizar produtor e consumidores e repetir os mesmos scanners/regras. Nenhuma
  exceção de scanner foi adicionada. Versões e descrição conferidas nos espelhos.

---

## 2026-10-22 — Revisão impede perda de recursos e desvio do gate

- **Tipo:** correção de causa raiz e padronização.
- **Antes:** targets equivalentes podiam sobrescrever templates; o overlay podia
  omitir skills descobertas pelo diretório padrão. O hook podia aceitar commit
  sem validar quando o detector falhava ou Git colocava aspas no nome do arquivo.
- **Depois:** targets são comparados como caminhos; o overlay preserva `./skills`;
  o hook consome nomes delimitados por NUL, usa seleção Bash e falha se Git falhar.
- **Causa raiz:** a validação comparava representações textuais em vez dos
  caminhos resolvidos; dois consumidores divergiam no default de skills; o status
  da pipeline do detector confundia erro com ausência de arquivos relevantes.
- **Check:** cinco regressões novas falharam antes e passaram depois. A suíte
  geral passou em 49 testes, sem skips; os 55 testes do auditor também passaram.
  Geradores, validador e `git diff --check` passaram. A revisão das correções não
  encontrou novos defeitos. Evidência Git após o commit `7df2ea7` registrada em
  `docs/codex/verification.md`.
- **Padronizado em:** `scripts/codex-adapters.py`, `scripts/pre-commit`,
  `tests/test_codex_adapters.py` e `tests/test_codex_validation.py`.
- **Evidência tipada:** os 289 hashes foram conferidos contra a revisão registrada
  antes de receberem o campo `sha256`. Isso removeu três alertas indevidos de
  gitleaks sobre nomes de arquivos com `api`/`token`, sem mudar digest, scanner,
  regra ou whitelist; a mesma representação é emitida pelo teste de distribuição.
- **Yokoten:** defaults conferidos entre gerador e adaptador; filtro cobre todos
  os caminhos de distribuição, inclusive nomes não ASCII. A sonda de docstrings
  levou à documentação dos quatro `main()` tocados. README corrigido em dois
  trechos que ainda descreviam o menu e a implementação antigos.

---

## 2026-10-22 — Retrofit confirmado sem presumir falha por nome de ferramenta

- **Tipo:** correção de causa raiz e verificação de hipótese.
- **Antes:** a retro suspeitava de portabilidade em DDD/codereview e de duas
  referências inconsistentes em CORS.
- **Depois:** os controles de DDD/codereview adaptaram os planos às capacidades
  nativas, sem reproduzir a falha; fontes preservadas. CORS 1.1.2 corrige a seção
  de Vary e o aviso que descrevia como fixa uma sonda já parametrizada.
- **Causa raiz:** o comando da triagem mudou, mas explicação e encaminhamento
  continuaram descrevendo o estado anterior. A leitura do pacote pelo agente
  expôs a divergência; nome específico de outro host, isoladamente, não provou
  falha operacional nas outras skills.
- **Check:** cenário antigo reproduziu duas contradições; fixture corrigida e
  instalação final confirmaram a navegação e o método. SQA antes/depois: zero
  erros/avisos e nenhum achado novo. 44 testes gerais passaram; três provas reais
  repetidas após o commit confirmaram CORS 1.1.2 e os 289 arquivos distribuídos.
- **Padronizado em:** correções pontuais em `plugins/cors/skills/cors/SKILL.md` e
  `references/casos-limite.md`, bump/CHANGELOG e espelhos, conferidos pelo gate.
  Evidência e limites em `docs/codex/retrofits-2026-10-22.md`.
- **Yokoten:** outros achados de conteúdo permaneceram como dívida para tarefa
  própria; não foi inserida regra de portabilidade sem reprodução da falha.

---

## 2026-10-22 — Distribuição Codex medida no pacote instalado

- **Tipo:** melhoria incremental e padronização.
- **Antes:** somente Claude Code/Cursor; nenhuma prova de instalação Codex; hook
  conferia working tree e não tinha execução real pelo Git coberta.
- **Depois:** catálogo filtrado com 25 plugins / 28 workflows, quatro comandos
  adaptados por geração e menu orientativo sem instalação. No candidato Git,
  289 arquivos instalados foram comparados; 44 testes gerais e 55 do auditor
  passaram. Desktop/macOS/Windows continuam não verificados.
- **Check:** casos independentes vermelhos/verdes cobrem inclusão indevida,
  metadados divergentes, escapes por symlink, template ausente, fontes/derivados
  antigos, política de invocação e índice inválido encoberto pelo working tree.
  Git refresh foi comprovado por versão e conteúdo no cache; remoções observadas.
- **Padronizado em:** `scripts/codex-marketplace.py`, `scripts/codex-adapters.py`,
  `scripts/validate-versions.py`, `scripts/pre-commit` 100755, testes em `tests/`,
  mapas de plataforma do auditor, README e CLAUDE.md. Evidências em `docs/codex/`.
- **Yokoten:** auditor e validador usam conjunto Codex próprio; campos Claude
  continuam avisados, sem supor equivalência com a política do Codex.

### Causas verificadas nas guardas

- Hook atualizado herdou modo 100644 → Git ignorava sua execução → testes chamavam
  Bash diretamente e não verificavam um commit real. Contramedida: modo 100755
  versionado e teste que precisa bloquear um commit inválido.
- `rg -q` encerrava cedo com `pipefail` → Git recebia SIGPIPE em lista staged
  grande → condição pulava o gate. Contramedida: consumir a lista completa,
  comprovada com 2.500 arquivos staged.
- Guarda inicial exigia campo `skills`, mas `ticket` usa descoberta padrão já
  comprovada pelo host. Contramedida: aceitar o diretório padrão, com teste positivo
  e negativo para skill ausente.

### Desperdícios evitados e oportunidades

- Sem instalação obrigatória de catálogo inteiro, cópias manuais de skills,
  mudança de regras de negócio, push ou revisão antecipada. Seis pacotes ficaram
  excluídos com motivo, em vez de suporte presumido por compatibilidade Cursor.
- Os smokes sinalizaram referências antigas de CORS e exemplos específicos de
  Zitadel; oportunidade para o mantenedor em tarefa própria, sem alterar esta entrega.
- Próximo passo: novo `/clear` e revisão com `/goal` e codereview. Desktop requer
  acesso ao aplicativo para fechar R01; a lacuna não foi convertida em aprovação.

---

## 2026-10-22 — Planejamento da distribuição individual no Codex

- **Tipo:** planejamento de melhoria incremental.
- **Antes:** catálogo, instalador e validadores documentavam Claude Code e Cursor;
  a forma de distribuir no Codex ainda não tinha decisões registradas.
- **Depois:** pesquisa em fontes oficiais e no exemplo solicitado, entrevista
  concluída e desenho aprovado para catálogo Codex filtrado com fontes de skills
  compartilhadas. Especificação, plano com Check por incremento e handoff
  preparados para a execução em outra sessão.
- **Check da preparação:** validador existente passou; os comandos de CLI foram
  conferidos pelo help. Esses resultados não comprovam uma instalação Codex,
  que ainda não foi executada.
- **Padronizado em:** referências no README e critérios documentados em
  `CONTEXT.md` e `docs/superpowers/`. Os validadores e adaptadores previstos no
  plano permanecem pendentes de implementação e prova.
- **Yokoten:** a introdução de plataforma precisa alcançar o validador e o auditor
  de skills, ambos com mapas próprios; essa verificação foi incluída no plano.

### Desperdícios evitados

- O usuário escolheu instalação individual por plugin, preservando os
  agrupamentos existentes; um pacote obrigatório com todo o catálogo foi excluído.
- O exemplo externo usa catálogo compatível com Claude; aceitá-lo como prova de
  execução de todos os nossos workflows esconderia diferenças de ferramentas,
  argumentos e templates. O plano começa pela prova no artefato instalado.

---

## 2026-09-30 — Retro de skill puxada por hook (retrofit-watch) + skill de hooks (hook-builder)

- **Tipo:** poka-yoke (a retro deixa de depender de alguém lembrar) · padronização (como se
  escreve e se prova um hook).
- **Antes:** melhorar uma skill exigia que o usuário lembrasse, no fim da sessão, de pedir a
  análise e depois o `/retrofit-skill`. Sem o pedido, o pitfall da sessão se perdia. O
  marketplace não tinha nenhum hook. A única skill de hooks na máquina (`hooks-2-0-builder`,
  local e fora do git) tratava de uma proposta experimental.
- **Depois:**
  - `retrofit-watch` 0.1.0: um Stop hook percebe que uma skill nossa trabalhou (marketplace →
    retrofit full; skill versionada em repo nosso → lean) e pede a retro no próprio turno. Adia
    quando o turno espera o usuário, faz no máximo 2 retros por skill por sessão e cala em
    `claude -p`.
  - `hook-builder` 0.1.0: a skill de hooks com probe de payload, harness de fixture e lint de
    config.
- **Medição:**
  - `retrofit-watch`: 28 testes; 9 mutações pegas pelo teste certo; E2E ao vivo com
    `claude -p --plugin-dir` nos três casos (sem lição, lição real depois de adiar e retomar,
    skill de terceiro que não dispara).
  - `hook-builder`: a linha de base sem a skill errou 8 pontos (evento, canal, recarga, debug,
    estado, disparo, gate) e, com a skill, os dois cenários acertaram todos.
- **Causa raiz:** o processo de melhoria era puxado pela memória do usuário, não pelo fluxo de
  trabalho. Hooks escritos de memória erram exatamente onde o teste com pipe não enxerga (evento
  e canal de saída).
- **Lição que o E2E trouxe:** a primeira versão do filtro exigia "o que resolveu", e com isso
  descartava a lição mais importante, a skill com instrução quebrada que ninguém conseguiu
  consertar. O pitfall sem solução passou a entrar, marcado "sem correção verificada".
- **Padronizado em:**
  - `plugins/hook-builder` (workflow, gotchas, `outdated-sources.md` com a linha de base);
  - `plugins/retrofit-watch/skills/retrofit-watch/references/criteria.md`, adaptado da
    `self-learning` (kulaxyz, MIT) e do loop "Lições" de um agente de propostas de
    um projeto interno.

---

## 2026-09-28 — Skills no formato da spec aberta agentskills.io + check 7

- **Tipo:** correção de causa raiz (nada media o formato da skill) · melhoria (progressive
  disclosure em 11 skills).
- **Antes:** auditoria com a `skill-quality-audit` contra a spec e as boas práticas do
  agentskills.io: 1 `name` fora da spec (`coderabbit_pr`), 5 `SKILL.md` acima de 500 linhas
  (970, 769, 648, 610, 531), 8 acima de 20 mil chars (o `cicd` com 110.525, ~27k tokens),
  2 `B3` (path relativo saindo da skill), campos mortos `user_invocable`/`argument_description`
  em 2 skills e dezenas de avisos de reference órfã, cadeia de references e reference longa sem
  sumário.
- **Depois:** 0 ERRO do auditor em todas as skills do marketplace; todos os `SKILL.md` abaixo de
  500 linhas e de 20 mil chars; `validate-versions.py` verde com 1 aviso justificado
  (`argument-hint` do `ticket`). 12 plugins com bump e entrada no CHANGELOG.
- **Causa raiz:** os checks 1–6 só olhavam versão, plataforma e description; o formato da skill
  não tinha sensor, e retrofit só soma texto.
- **Padronizado em:** check 7 no `validate-versions.py` (erro: `name`, description, flow style,
  mais de 500 linhas; aviso: campo de topo fora da spec, mais de 20 mil chars); `scripts/pre-commit`
  passa a disparar também em `SKILL.md`; `CLAUDE.md` § *Skill format*; `retrofit-skill` 0.5.0
  com a seção "Mantenha a skill no formato da spec".
- **Autoria preservada:** os plugins `criar-prd`, `criar-task`, `criar-techspec` e
  `executar-task` (Alexandre Souza Pereira, PR #2) não foram tocados.

---

## 2026-09-03 — Prompt audit das 16 skills + poka-yoke na kaizen-software + custo do codereview

- **Tipo:** melhoria (16 skills re-lidas para o modelo atual) · correção de causa raiz (cruft
  acumulado por retrofit) · oportunidade (custo do `codereview` — mudança publicada, medição
  pós-mudança pendente)
- **Antes:** skills escritas para Opus 4.x carregavam ênfase em caps, narrativas de incidente com
  data/ticket/PR, nomes/hosts/e-mail do projeto de origem e modelos fixos em prosa; 10 plugins sem
  `metadata.version` no `SKILL.md`; a `kaizen-software` ensinava poka-yoke no verbete mas fechava
  o fluxo com regra escrita; uma invocação de `/codereview` custava **$11–16** (46–65% de cada
  sessão REVIEW do pipeline `sdd_agents`, medido em 16 sessões).
- **Depois:** 15 commits em `origin/main` (tabela abaixo), `validate-versions.py` verde em todos,
  `metadata.version` em todos os SKILL.md tocados; `kaizen-software` 1.3.0 com poka-yoke,
  yokoten, andon e Ishikawa no fluxo (sonda A/B: 14/14 sem regressão; menções a poka-yoke
  0→4 e 1→4 nos cenários em que a antiga fechava com regra escrita); `codereview` 1.19.0 com
  contrato dos agentes em arquivo, prompt de lançamento curto, `model` como poka-yoke, Bucket B
  opt-in e linha *Cost footprint* — medido em duas invocações headless sobre o mesmo diff:
  **$6,62 e $5,92 por revisão** (agentes $0,58–1,61 cada, 3–20 turnos, 8 de 8 leram as references)
  contra $11–16 e ≈45 turnos por agente no baseline; ver item (h).
- **Causa raiz (5 porquês abaixo):** sem eval nem sensor, a única evidência de que uma linha da
  skill "funciona" é o incidente que a gerou — ninguém tem base para removê-la, então só se
  acrescenta.
- **Padronizado em:** `CLAUDE.md` § *Prompt hygiene* (confirmado no arquivo após a edição):
  re-rodar `/claude-api prompt-audit` a cada retrofit e a cada release de modelo; brief
  reutilizável em `~/.claude/handoff/prompt-audit-2026-09-03/prompt-audit/BRIEF-auditoria.md`;
  o quê/porquê vai para o CHANGELOG do plugin, relatórios e diffs ficam fora do repo.
- **Yokoten:** a mesma causa existe fora do marketplace — `sdd_agents/agents/sdd-reviewer.md`
  ("Reproduce before you conclude" + "adversarial" = cauda de ≈ $5,4 e ~50 turnos por sessão
  REVIEW, e é o que empurra os agentes a construir sandboxes) e o `CLAUDE.md` + `.claude/rules`
  do `digital_service_report_api` (≈ 110 KB ≈ 28k tokens injetados em **cada** subagente).
  Registrados como oportunidades (f); não feitos nesta rodada.

### Antes → Depois (um commit por plugin, todos em `origin/main`)

| Commit | Plugin | Versão | O quê |
|---|---|---|---|
| `ac59240` | kaizen-software | 1.2.0 | poka-yoke entra no fluxo (escada de padronização, Fase 1/2/3, template dos 5 Porquês, desperdício #7, description com 8 gatilhos) |
| `7569ff9` | kaizen-software | 1.3.0 | yokoten, andon, Ishikawa, mura/muri, kaikaku, 8º desperdício, gemba sem ticket |
| `186948c` | codereview | 1.18.0 | Fase A inline (sem agente haiku), 28 de 32 linhas em caps voltam ao tom normal, registry de reviewers medido, "opus" fixo sai |
| `efbd550` | dotnet-wpf | 1.7.0 | hooks JSON inválido corrigido, VMs Singleton nas references, resíduos VDA/VDR fora |
| `cf9ab8e` | cicd | 2.26.0 | nomes JRC → placeholders, runner version → latest, lições alinhadas ao paths-ignore |
| `dfe3de7` | zitadel-idp | 0.12.0 | e-mail/IP/hosts fora, "47 quirks" → catálogo, quirks 38–45 viram gatilhos |
| `1647f39` | whisper-preprocess | 1.1.0 | copiar os 2 scripts (merge silencioso), lição 9 no presente, afftdn escopado |
| `fa90577` | pdf-generation | 1.6.1 | linha de downloads npm (falsa) fora, skill inexistente fora, NON-NEGOTIABLE/MUST |
| `4b58bf3` | ddd | 0.4.2 | e-mail do autor e marca → Acme/example.com, "fora de escopo" sem diff de versão |
| `8068660` | ansible-docker-backup-restore | 1.3.2 | nomes de uma instalação → placeholders; arqueologia fora |
| `df3f2c7` | dev-script | 0.5.3 | contagens de incidente fora, tetos numéricos viram qualitativos, 8 gatilhos |
| `174373f` | cors | 1.0.1 | hosts internos e data saem do caso medido; acentos na description |
| `2dc4881` | wsl-windows-onboarding | 0.4.2 | descoberta de caminho sem assumir o layout do autor; "current WSL" robusto |
| `6322d3b` | codereview | 1.19.0 | custo: contrato dos agentes em `references/`, prompt de ~12 linhas, `model: "sonnet"` como poka-yoke, Bucket B opt-in, Cost footprint |
| `50e814c` | ticket | 1.4.0 | PII e nome fora do corpo, changelog fora do workflow, tabela de sensores alinhada ao JQL, 13 narrativas viram regra, caps em tom normal, description 498 → 456 chars / 8 gatilhos — junto com as 3 lições do dono (issue links, estrutura do ADF, registrar sem começar) |

`ticket` entrou por último (`50e814c`, 2026-09-03 à noite): auditada sobre a edição não commitada do dono, a
pedido dele, e publicada junto com as três lições dele. Rodada das 16 skills fechada.

### 5 Porquês — por que as skills acumularam cruft
- **Sintoma:** 16 de 16 skills com achados de confiança alta/média no prompt audit — ênfase em
  caps que não previne mais nada, incidentes com data e ticket no corpo, nomes do projeto de
  origem virados regra, modelos fixos em prosa.
1. Por quê? O `retrofit-skill` soma **uma lição por sessão** ao texto que já existe.
2. Por quê somar em vez de reescrever? A lição chega com o nome, o host e o número do incidente
   que a gerou, e vira regra com eles dentro — reescrever custaria re-ler a skill inteira.
3. Por quê ninguém re-lê? Cada retrofit edita só o trecho da lição; não há passo que leia a skill
   **inteira contra o modelo novo**, e a release de modelo não dispara nada no repo.
4. Por quê nada dispara? Não existe eval nem sensor: nada mede se a ênfase ainda previne a falha
   para a qual foi escrita (a sonda do piloto foi a primeira medição desse tipo).
5. **Causa raiz (processo):** sem eval, a única evidência de que uma linha "funciona" é o
   incidente que a gerou; ninguém tem base para removê-la, então só se acrescenta.
- **Contramedida:** o audit periódico é regra escrita (`CLAUDE.md` § *Prompt hygiene*) — poka-yoke
  não coube: o único gate do repo (`validate-versions.py`) vê só a description. O sensor que
  nasceu nesta rodada é a linha *Cost footprint* do `codereview` — custo e turnos por agente
  passam a aparecer no próprio relatório, sem abrir log.
- **Teste que teria pegado:** nenhum existe; o mais perto é o grep de sinais do brief
  (caps, datas, tickets, e-mails, modelos fixos) — roda em segundos sobre `plugins/`.

### Desperdícios evitados (cortes conscientes)
- **Sem `docs/prompt-audit` no repo** — 16 relatórios + 20 diffs ficam em
  `~/.claude/handoff/prompt-audit-2026-09-03/`; o CHANGELOG de cada plugin carrega o quê e o
  porquê. Evitou superprocessamento e um diretório que envelheceria como as skills.
- **Sonda A/B só onde o diff muda comportamento** (kaizen-software). Nas outras, o diff é
  remoção; validação estática (`git apply --check` + validate) bastou.
- **Trade-offs do codereview fora até existir eval:** Haiku nos agentes, `effort: low`, agrupar
  5 arquivos por agente, sweep inteiro opt-in — cada um muda o que se analisa e não há como
  julgar achados perdidos hoje.

### O que aprendemos
- **O sensor pré-registrado do piloto não discriminou** (14/14 asserções passam nas duas versões
  da kaizen-software): o enunciado do cenário já apontava a falha da regra escrita, então a
  skill antiga também acertava. A métrica que separou as versões apareceu depois (menções a
  poka-yoke no Act). Cenário-sensor de comportamento novo tem de ser um em que o enunciado
  **não** empurre para a resposta.
- **A description cap é a única superfície com gate**; todo o resto do prompt audit é revisão
  humana — daí a regra escrita, e não um validador.
- **Agentes derrubados pelo 429 já tinham gravado os artefatos** em disco — conferir o disco
  antes de relançar; 4 relançamentos evitados.
- **No codereview o custo não era o tamanho das references** (1 de 66 agentes as leu) nem o
  prompt: era **turnos por agente** (~45 contra ~6 no desenho) — cache-read cresce com o
  quadrado dos turnos. Caminho relativo nas instruções + orquestrador que parafraseia o bloco
  `Agent(...)` = agente explorando livre.
- **O desenho "mesma missão, 2 rodadas" nunca ia medir nada:** `sdd retry` retenta a fase corrente
  (PR), a missão do baseline já estava mesclada em `main` (diff vazio → nenhum agente) e o seu revisor
  deixou de invocar o skill a partir da r3. A sessão forçada (`sdd run --phase REVIEW`, que ignora o
  teto de rodadas por desenho) fez checkout da branch da missão na árvore do usuário e commitou duas
  notas de intervenção — desfeitas por ele em um minuto. O que mediu foi `claude -p
  "/codereview:codereview"` num worktree destacado e, quando essa branch também foi mesclada, num
  clone descartável com `main` fixado no merge-base antigo: zero contato com o checkout de quem
  trabalha no repo em paralelo.
- **Job longo em Bash de fundo com timeout morre no prazo, com o grupo de processos inteiro**
  ($4,70 de sessão perdida): `setsid nohup … &` + Monitor. E um Monitor cujo comando contém o literal
  que ele procura com `pgrep -f` casa consigo mesmo e nunca sai.
- **Bucket B do sweep sem foco no prompt de lançamento é regra sem sensor**: o agente não tinha
  como saber o foco; o prompt agora leva `Focus area` e `Sweep`.

### Oportunidades registradas (dono: j0ruge — único mantenedor)
- (a) `scripts/validate-versions.py` não lê `metadata.version` do `SKILL.md` e o check 6 procura
  só `skills/<plugin>/SKILL.md` — plugins multi-skill (`codereview`, `dotnet-wpf`) ficam sem
  verificação de description e de versão por skill.
- (b) `README.md` com células-changelog na tabela de plugins (`kaizen-software`, `codereview` —
  a de codereview cresceu de novo nesta rodada); mover para os CHANGELOGs e deixar uma frase.
- (c) `coderabbit-review.md`, `copilot-review.md`, `gemini-review.md` soltos na raiz —
  ignorados por `.gitignore:4`, sobras de runs da `coderabbit_pr` anteriores à Fase 6 (1.17.0);
  apagar depois de confirmar que nenhum PR aberto os usa.
- (d) `create-readme` duplicado em `.claude/skills/` e `.agents/skills/`.
- (e) `ansible-docker-backup-restore`: a prova "há dados" conta blocos `COPY` — Postgres-only;
  `mysqldump` grava `INSERT INTO` (já anotado no CHANGELOG 1.3.2, sem diff).
- (f) Fora do repo: `sdd_agents/agents/sdd-reviewer.md` "Reproduce before you conclude" —
  reproduzir só CRITICAL/HIGH; `CLAUDE.md` + `.claude/rules` do DSR com ≈ 110 KB — cada
  subagente paga ≈ 28k tokens de prefixo.
- (g) `ticket` — **feita** (2026-09-03, `50e814c`, 1.4.0). O único tipo de achado que as outras 15 não tinham
  mostrado: uma **tabela de referência contradizendo a regra que a substituiu** (`sprint list-workitems` ainda
  listado como sensor, dois parágrafos depois de ser proibido) — duplicata que drifta é mais perigosa que
  arqueologia, porque o modelo lê a forma mais compacta.
- (h) Medição da 1.19.0 — **feita** (2026-09-03, ≈ $18 dos ≈ $40 aprovados; $4,70 deles numa sessão do
  runner morta pelo timeout do próprio agente): duas invocações headless sobre o mesmo diff de 18
  arquivos — $6,62 e $5,92 por revisão; agentes $0,58–1,61 (3–20 turnos) contra $2,0 (≈45 turnos);
  sweep $0,62–0,69 (6–8 turnos) contra $3,1–3,5 (63–66); references lidas por 8 de 8 agentes; nenhum
  CRITICAL/HIGH; os dois relatórios convergem no mesmo achado principal. **L1–L5 ficam.** Tabela no
  CHANGELOG do `codereview` (1.19.0); streams e relatórios em
  `~/.claude/handoff/prompt-audit-2026-09-03/prompt-audit/work/codereview-custo/medicao-1.19.0/`.

---

## 2026-08-26 — Descriptions acima do cap: da dívida ao gate

**Problema:** 7 dos 16 plugins tinham `description` acima do cap de 500 chars do
`CLAUDE.md` — o pior com **871**. A `description` é a única superfície de
triggering: é por ela que o Claude decide invocar a skill. Texto longo dilui o
sinal e pode ser **cortado em silêncio** na lista `/skills`, piorando exatamente
o que deveria melhorar.

**Métrica de sucesso:** `scripts/validate-versions.py` com zero erros e zero
warnings.

### Gemba

Não foi suposição. `git log` no `plugin.json` de cada plugin mostrou o padrão:
**`codereview` tem 21 commits** no arquivo, `zitadel-idp` 12, `wsl-windows-onboarding` 6.
Cada retrofit acrescentava sua lição ao texto existente.

### 5 Porquês

1. Por que 7 descriptions passaram do cap? Cada retrofit **somou** a lição nova.
2. Por que somar em vez de reescrever? É mais barato acrescentar uma cláusula do
   que reequilibrar o texto inteiro.
3. Por que nada barrou? O cap era **warning**, não erro — não reprovava o gate.
4. Por que warning? Quando o cap foi criado, as descriptions **já** estavam acima;
   torná-lo erro reprovaria o repositório inteiro de imediato.
5. **Causa raiz (processo, não pessoa):** o padrão nasceu depois da deriva e foi
   aplicado como aviso. Aviso que nunca reprova vira ruído de fundo — todo mundo
   aprende a rolar a tela. **O padrão só se sustenta quando a dívida é zerada
   primeiro e o gate é fechado logo em seguida.**

### Antes → Depois

| Plugin                          | Antes | Depois |
| ------------------------------- | ----- | ------ |
| `wsl-windows-onboarding`        | 871   | 468    |
| `codereview`                    | 686   | 489    |
| `zitadel-idp`                   | 670   | 476    |
| `ansible-docker-backup-restore` | 593   | 473    |
| `dev-script`                    | 578   | 434    |
| `whisper-preprocess`            | 578   | 406    |
| `cicd` (divergente + acima)     | 756   | 473    |

Todos os **16** plugins agora cabem no cap. O corte foi **encurtar, não resumir
mecanicamente**: saiu enumeração de detalhe (mensagens de erro literais, nomes de
ferramentas alternativas, exemplos), que continua no corpo da skill; ficaram o que
a skill faz e os diferenciais que a distinguem das vizinhas.

### Muda eliminado

Aplicar a mesma mudança em 6 plugins × 4 arquivos à mão é **retrabalho**. Virou
`aplica_desc.py`: recebe plugin + arquivo de descrição, aplica nos três arquivos,
faz bump de patch, atualiza o README e **recusa** texto acima do cap. Foi esse
poka-yoke que barrou a primeira tentativa do `wsl-windows-onboarding`, com 511
chars — o erro morreu antes de virar commit.

### Act — padronização

**Padronizado em `scripts/validate-versions.py`:** o cap deixou de ser warning e
virou **erro**. Verificado por injeção — 400 chars a mais num plugin e o gate
reprovou; teste revertido em seguida.

Agora que a dívida está zerada, o custo de manter o padrão é encurtar no ato de
cada retrofit, que é barato. Deixar acumular custou este mutirão.

**Oportunidade registrada (fora do escopo desta rodada):** o `retrofit-skill`
poderia lembrar de rodar o validador antes do commit — nesta sessão o erro do
`cicd` só apareceu porque um retrofit anterior alterou 2 dos 3 arquivos.
