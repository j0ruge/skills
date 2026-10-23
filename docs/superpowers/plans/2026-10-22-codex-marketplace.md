# Loja Codex — plano de implementação PDCA

> **Para execução por agentes:** usar `superpowers:executing-plans` em execução
> nativa, tarefa por tarefa, é a recomendação para este plano. Se o usuário
> escolher delegação na retomada, usar `superpowers:subagent-driven-development`.
> A implementação e a segunda retomada de revisão foram executadas. O Check da revisão está no final; R01 continua parcial.

**Goal:** permitir instalação individual dos plugins portáveis da Chewiesoft
no marketplace nativo do Codex CLI e desktop.

**Architecture:** catálogo Codex filtrado e derivado dos metadados existentes,
com conteúdo canônico compartilhado. Adaptar contratos de plataforma somente
onde a prova de carregamento e invocação exigir; conferir todos os derivados.

**Tech Stack:** Python, JSON, Markdown, formato Agent Skills e Codex CLI/desktop.
Manter `install.py` sem dependências externas; usar `unittest` para os novos
testes locais. A validação YAML existente usa PyYAML.

**Spec:** [desenho aprovado](../specs/2026-10-22-codex-marketplace-design.md).

**Data:** 2026-10-22 · **Responsável:** agente executor + usuário na validação de
superfícies não acessíveis ao executor · **Estado:** `implemented_with_gaps`

## Restrições globais

- Repositório `j0ruge/skills`; marca `Chewiesoft`; slug `chewiesoft-marketplace`.
- Branch base `main`, conforme `CLAUDE.md` deste repositório.
- Instalação por plugin, mantendo os agrupamentos atuais de skills.
- Oferecer apenas plugins no estado `supported`; documentar exclusões no README.
- Alvo: todos os ambientes oficialmente suportados pelo Codex; registrar a
  cobertura real sem converter ausência de teste em aprovação.
- `install.py` apenas mostra comandos para Codex; não instala nem altera a
  configuração pessoal. Claude Code e Cursor preservam os fluxos existentes.
- Comentários, docstrings e commits novos em português; identificadores,
  configuração e tokens de estado em inglês.
- Preservar autoria, licenças, nomes e regras de versão/CHANGELOG existentes.
- Conteúdo canônico em `plugins/`; nenhuma segunda árvore editada manualmente.
- Arquivos derivados necessários à instalação Git são versionados e verificados.
- Mudanças de comportamento seguem TDD; falha interrompe o incremento até ser
  explicada e corrigida. Não refatorar trechos vizinhos sem necessidade da missão.
- Os testes de distribuição usam fixtures e smokes seguros, sem executar
  operações de produção descritas pelas skills.
- A revisão final com `/goal` e `codereview:codereview` ocorre após outro `/clear`.

## Foco da revisão

| Risco | Resultado esperado | Teste que o cobre |
|---|---|---|
| Dois catálogos no mesmo repo fazem o cliente expor plugins excluídos. | O catálogo observado no Codex corresponde exatamente ao subconjunto publicado. | Tarefas 1 e 5: comparar nomes no JSON do CLI com as entradas Codex. |
| Comando convertido carrega, mas seu template só existe no clone fonte. | O fallback funciona com projeto consumidor vazio. | Tarefa 3: `criar-prd` com leitura do template no pacote instalado. |
| Fonte/versão muda e o catálogo ou adaptação fica antigo. | Conferência falha; atualização entrega o conteúdo novo no cache instalado. | Tarefa 2: mutação de fonte; tarefa 5: atualização entre duas revisões de teste. |
| Menu Codex executa processos, escreve arquivos ou anuncia sucesso sem catálogo. | Exibe instruções; erros de leitura são explícitos e falham. | Tarefa 4: processos e gravações proibidos por mocks; JSON ausente/inválido. |
| Cache de teste anterior esconde recurso ausente. | Cada cenário parte de estado limpo e inspeciona a cópia instalada. | Tarefa 5: fixtures independentes, hashes e caso com recurso removido. |

## Plan — Gemba e métrica

O [CONTEXT.md](../../../CONTEXT.md) contém o baseline: 31 plugins no catálogo,
32 diretórios de skills, 6 plugins somente de comandos e 4 declarados apenas
para Claude. O validador atual passou; `codex-cli 0.163.0` e os helps dos comandos
foram observados. Nenhuma instalação de prova foi realizada nesta fase.

Métrica de entrega: cada plugin publicado deve ter prova de seleção individual,
carregamento das skills esperadas, recursos disponíveis e smoke seguro da entrada
dos workflows. O catálogo e seus derivados devem passar nos checks; itens
excluídos devem ter motivo rastreável. R01–R12 da especificação devem ter evidência.

Desperdícios evitados: catálogo completo obrigatório, port de APIs exclusivas por
antecipação, cópias manuais das skills, auditoria de regras de negócio sem relação
com a distribuição e repetição de perguntas já respondidas.

## Mapa de arquivos

Os caminhos nesta tabela são entregáveis futuros, não arquivos já implementados.

| Arquivo | Responsabilidade |
|---|---|
| `.agents/plugins/marketplace.json` | Catálogo Codex derivado, versionado e filtrado. |
| `scripts/codex-marketplace.py` | Gerar ou conferir o catálogo a partir das fontes canônicas. |
| `tests/test_codex_marketplace.py` | Contratos do gerador, filtragem, integridade e erros. |
| `scripts/validate-versions.py` | Aceitar `codex` e integrar verificações de distribuição. |
| `scripts/pre-commit` | Acionar o gate quando fontes ou derivados relevantes mudam. |
| `tests/test_codex_validation.py` | Regressões das guardas e do acionamento do gate. |
| `plugins/<plugin>/.claude-plugin/plugin.json` | Declarar suporte somente após evidência e manter identidade canônica. |
| `.claude-plugin/marketplace.json` | Espelhar plataformas/versões conforme as regras atuais. |
| `plugins/<plugin>/.codex-plugin/plugin.json` | Manifesto derivado, somente onde a prova exigir adaptação do manifesto. |
| `plugins/<plugin>/codex-skills/<skill>/` | Conteúdo derivado de comandos, somente se o host não os carregar corretamente. |
| `scripts/codex-adapters.py` e `tests/test_codex_adapters.py` | Gerar e conferir adaptações necessárias; omitir ambos se o carregamento nativo resolver todos os casos. |
| `plugins/<plugin>/codex-adapter.json` | Mapeamento declarativo de comando e recursos, somente nos plugins que precisarem de adaptação gerada. |
| `install.py` e `tests/test_install_codex.py` | Menu e instruções de instalação individual. |
| `plugins/skill-quality-audit/skills/skill-quality-audit/scripts/audit_skill_quality.py` | Regras de plataforma do auditor alinhadas com o validador. |
| `plugins/skill-quality-audit/skills/skill-quality-audit/tests/test_audit_skill_quality.py` | Regressões das regras de plataforma do auditor. |
| `docs/codex/compatibility.md` | Inventário, motivos de exclusão, dependências e provas por plugin. |
| `docs/codex/verification.md` | Procedimento reproduzível e resultados de CLI/desktop por versão e ambiente. |
| `README.md`, `CLAUDE.md`, CHANGELOGs afetados e `KAIZEN_LOG.md` | Uso, manutenção, versões e fechamento do ciclo. |

## Do + Check — incrementos

### Tarefa 1 — provar o contrato de distribuição no host

**Arquivos:** criar `docs/codex/verification.md`; iniciar `docs/codex/compatibility.md`.
Fixtures ficam em diretório temporário; não declarar suporte em massa nesta tarefa.

**Interface consumida:** fontes atuais e os comandos do Codex instalados.
**Saída:** evidência de precedência de catálogos, manifestos aceitos, recursos
carregados e tratamento de comandos; decisões técnicas registradas com versão.

- [x] Ler especificação, contexto e regras do repo. Conferir branch, status e
  mudanças existentes; preservar os documentos desta fase. Criar isolamento de
  implementação pela skill de worktrees se a retomada não estiver isolada.
- [x] Revalidar o baseline e os comandos disponíveis:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-versions.py
  codex --version
  codex plugin marketplace add --help
  codex plugin add --help
  codex plugin list --help
  ```

- [x] Preparar um cliente de teste isolado, por exemplo um container ou usuário
  de teste. Seus dados e cache não devem compartilhar o perfil pessoal. Não
  substituir variáveis de diretórios do usuário na sessão principal. Usar cópias
  temporárias dos plugins `cors`, `codereview` e `criar-prd` para cobrir skill com
  referências, várias skills e comando com template.
- [x] Na cópia de teste, manter um catálogo Claude com os três plugins e criar
  um catálogo Codex que inicialmente ofereça só `cors`. Usar o formato da fonte
  oficial já pesquisada; os caminhos resolvem para arquivos da cópia de teste.
- [x] Dentro do cliente isolado, executar a sequência abaixo, substituindo
  `/work/marketplace` pelo caminho real da fixture naquele ambiente:

  ```bash
  codex plugin marketplace add /work/marketplace --json
  codex plugin list --marketplace chewiesoft-marketplace --available --json
  codex plugin add cors@chewiesoft-marketplace --json
  codex plugin list --marketplace chewiesoft-marketplace --json
  ```

- [x] Comparar os nomes estruturados, não procurar apenas ausência de erros.
  A loja deve oferecer exatamente `cors`, e só ele deve estar instalado. Ler
  seu `SKILL.md` e uma referência pela cópia instalada; iniciar uma sessão nova
  para conferir seleção e invocação. Não rodar comandos externos sugeridos pela
  skill como parte desta prova.
- [x] Repetir em fixtures limpas para `codereview` e `criar-prd`. Conferir todas
  as skills do plugin múltiplo; no comando, conferir o template de fallback.
- [x] Fixar o resultado técnico: usar manifestos existentes quando funcionarem;
  usar manifesto Codex apenas quando necessário; manter comandos nativos se o
  host preservar o workflow, ou seguir a adaptação da tarefa 3. Se a precedência
  dos catálogos falhar, investigar o formato documentado e corrigir a fixture
  antes de expandir a publicação.
- [x] Registrar versão e ambiente testados, resultados estruturados e arquivos
  lidos. Falta de autenticação ou acesso ao desktop fica como `not_checked`, com
  o procedimento exato para completar a prova. Não registrar credenciais.

**Check:** seleção individual, filtragem e recursos comprovados; decisões de
empacotamento têm evidência. **Reversão:** remover apenas fixtures e instalações
de teste identificadas, preservando o perfil pessoal.

### Tarefa 2 — catálogo derivado e guardas de consistência

**Arquivos:** catálogo, gerador, seus testes, validador, hook e testes de guardas.
**Interface consumida:** manifestos canônicos, localização dos plugins e
resultado da tarefa 1.
**Interface produzida:** `scripts/codex-marketplace.py --root DIR --check|--write`.
`--root` tem default na raiz do repo do script; o modo padrão é `--check`.
Retorno 0 significa artefato atual; retorno 1 significa erro ou divergência;
argumentos inválidos retornam 2. `--check` nunca escreve.

- [x] Criar testes de contrato por subprocesso usando `unittest` e diretórios
  temporários. A fixture mínima tem dois plugins válidos: `ready` declara
  `claude-code` e `codex`; `excluded` declara apenas `claude-code`. Cada plugin
  tem manifesto, pasta de skill e `SKILL.md` coerentes; o catálogo Claude lista
  ambos. O teste verifica estes comportamentos:

  ```python
  written = subprocess.run(
      [sys.executable, str(script), "--root", str(root), "--write"],
      capture_output=True, text=True, check=False,
  )
  self.assertEqual(written.returncode, 0, written.stderr)
  catalog_path = root / ".agents/plugins/marketplace.json"
  catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
  self.assertEqual(catalog["name"], "chewiesoft-marketplace")
  self.assertEqual([item["name"] for item in catalog["plugins"]], ["ready"])
  self.assertEqual(catalog["plugins"][0]["source"]["path"], "./plugins/ready")
  before = catalog_path.read_bytes()
  checked = subprocess.run(
      [sys.executable, str(script), "--root", str(root), "--check"],
      capture_output=True, text=True, check=False,
  )
  self.assertEqual(checked.returncode, 0, checked.stderr)
  self.assertEqual(catalog_path.read_bytes(), before)
  ```

  No teste, `script` é o caminho do gerador, `root` é a fixture e as bibliotecas
  `json`, `subprocess`, `sys` e `unittest` são importadas pelo módulo de testes.
  Criar a fixture no `setUp`, nunca aproveitar o checkout real como entrada.

- [x] Acrescentar casos independentes: catálogo derivado ausente; JSON inválido;
  inclusão indevida de `excluded`; fonte fora de `plugins/`; escape por symlink;
  nome duplicado; manifesto inexistente; plataforma divergente entre manifestos;
  escrita repetida idempotente; origem com versão ou descrição alterada.
  No caso de versão alterada, conferir o derivado que efetivamente carrega versão
  segundo o formato medido, sem inventar campo de versão no catálogo.
- [x] Executar os testes antes de implementar e observar as falhas esperadas:

  ```bash
  python3 -m unittest discover -s tests -p 'test_codex_marketplace.py' -v
  ```

- [x] Implementar leitura, validação, filtragem exata de `codex`, ordenação
  determinística e escrita atômica. Resolver caminhos dentro da raiz do repo;
  recusar escapes, metadados incoerentes e nomes duplicados antes de escrever.
  Comparar o documento derivado esperado com o existente, incluindo seus campos
  de políticas e fontes conforme o formato comprovado na tarefa 1.
- [x] Introduzir `codex` em `VALID_PLATFORMS`. Integrar a conferência do catálogo
  no validador, sem tornar PyYAML uma dependência do instalador. Se uma validação
  obrigatória depender de PyYAML ausente, informar a lacuna e falhar esse gate.
- [x] Estender o hook para disparar também quando mudarem o gerador, o próprio
  validador, `install.py`, metadados de invocação ou adaptações Codex. Testar o
  acionamento com repositório temporário. Um arquivo corrigido só no working tree
  não pode encobrir sua versão inválida já staged: validar o snapshot ou recusar
  divergência nos arquivos conferidos, indicando que precisam ser staged.
- [x] Executar os testes de guardas e o baseline completo:

  ```bash
  python3 -m unittest discover -s tests -p 'test_codex_validation.py' -v
  python3 scripts/codex-marketplace.py --check
  python3 scripts/validate-versions.py
  ```

**Check:** todos os casos negativos falham pelo motivo esperado, entradas válidas
passam e a conferência não escreve. **Reversão:** reverter este incremento e seus
derivados como unidade; não deixar `codex` declarado sem catálogo válido.

### Tarefa 3 — portabilidade dos plugins e comandos

**Arquivos:** fontes dos plugins afetados, manifestos, CHANGELOGs, auditor e seus
testes; relatório de compatibilidade; adaptadores e testes apenas se necessários.
**Interface consumida:** resultado de empacotamento da tarefa 1 e guardas da 2.
**Saída:** conjunto explícito de plugins `supported`, com nomes, recursos,
dependências e evidências por workflow.

- [x] Inventariar todos os plugins do catálogo. Para cada um, registrar skills,
  comandos, scripts, templates, ferramentas exigidas, invocação explícita,
  referências entre workflows e limitações de sistema operacional. Começar por
  `not_checked`, sem copiar a compatibilidade Cursor como prova de Codex.
- [x] Examinar especialmente `statusline`, `hook-builder`, `retrofit-watch` e
  `ticket`, hoje declarados apenas Claude, sem presumir exclusão ou suporte só
  pelo nome. A ausência de uma equivalência pequena e comprovada gera exclusão
  documentada, conforme o escopo aprovado.
- [x] Para cada plugin elegível, escrever o caso que reproduz a lacuna antes de
  adaptar. Corrigir somente o contrato que falhou: ferramenta, caminho,
  argumentos, nomes de skill ou política de invocação. Preservar a intenção e
  testar o workflow original na área modificada.
- [x] Se comandos forem carregados corretamente pelo host, conservar esse
  caminho e registrar a prova. Se exigirem conversão, implementar
  `scripts/codex-adapters.py --root DIR --check|--write`, com o mesmo contrato de
  retorno e ausência de escrita em `--check` do gerador do catálogo.
- [x] Na ramificação com conversão, usar `codex-adapter.json` no plugin para
  declarar as origens e recursos; o formato mínimo para o caso já observado é:

  ```json
  {
    "commands": [
      {
        "name": "criar-prd",
        "source": "./commands/criar-prd.md",
        "resources": [
          {
            "source": "./templates/prd-template.md",
            "target": "assets/prd-template.md"
          }
        ]
      }
    ]
  }
  ```

  Gerar `codex-skills/criar-prd/SKILL.md`, seus assets e, quando exigido,
  `.codex-plugin/plugin.json` a partir da identidade canônica. Usar a descrição
  canônica existente; traduzir apenas os contratos medidos. O conteúdo adaptado
  deve resolver seu template pelo diretório da skill instalada, mantendo a
  preferência pelo template do projeto consumidor. Não depender de expansão de
  variável de Claude sem uma prova de que ela existe nesse contexto.
- [x] Cobrir os adaptadores com fixtures de: `$ARGUMENTS`; caminho de template;
  recurso ausente; chamada entre skills; duas skills no mesmo plugin; e comando
  que exige invocação explícita. Usar `agents/openai.yaml` quando for necessário
  preservar a política de invocação demonstrada. Derivados inválidos ou antigos
  devem falhar no validador principal.
- [x] Alinhar os mapas `TOP_FIELDS_BY_PLATFORM` do validador e do auditor.
  Definir o conjunto Codex por fonte ou prova, sem copiar campos Claude/Cursor.
  Testar que declarar Codex não faz um campo exclusivo de outro host passar
  silenciosamente na interseção de plataformas.
- [x] Rodar os testes afetados:

  ```bash
  python3 plugins/skill-quality-audit/skills/skill-quality-audit/tests/test_audit_skill_quality.py
  python3 -m unittest discover -s tests -p 'test_codex_*.py' -v
  python3 scripts/validate-versions.py
  ```

- [x] Executar o smoke seguro de cada workflow publicado, no pacote instalado.
  Só então declarar `codex`, atualizar versão/CHANGELOG quando aplicável e gerar
  o catálogo. `partial`, `unsupported` e `not_checked` ficam fora dele.

**Check:** o relatório cobre todo o catálogo; cada inclusão tem prova e recursos
disponíveis. **Reversão:** remover suporte Codex do plugin afetado, regenerar os
derivados e preservar o histórico; não apagar fontes compartilhadas.

### Tarefa 4 — opção Codex no instalador e documentação de uso

**Arquivos:** `install.py`, `tests/test_install_codex.py`, `README.md` e `CLAUDE.md`.
**Interface consumida:** `.agents/plugins/marketplace.json` validado.
**Interfaces produzidas:** `_codex_install_flow() -> None` apresenta instruções;
erros de leitura/formato chegam ao tratamento de erro do CLI com retorno 1.

- [x] Testar a escolha Codex antes de implementar. Importar `install.py` com
  `importlib.util`, como o validador atual faz; redirecionar `REPO_ROOT` para uma
  fixture e capturar stdout. Usar mocks de gravação e execução externa que falham
  se forem chamados. Casos: um plugin, vários plugins, catálogo vazio, ausente e
  inválido. Catálogo vazio deve informar que não há plugins publicados e não
  apresentar uma instalação como concluída.
- [x] Testar a seleção dos fluxos já existentes por nome da opção, sem fixar
  índices que mudam quando Codex é acrescentado. A opção combinada deve chamar
  somente os fluxos Claude Code e Cursor, com rótulo explícito.
- [x] Implementar a opção Codex lendo o catálogo validado. A saída deve mostrar
  estes comandos, com uma linha por plugin realmente publicado:

  ```text
  codex plugin marketplace add j0ruge/skills
  codex plugin add cors@chewiesoft-marketplace
  ```

  `cors` é o exemplo de apresentação, não uma inclusão incondicional. A lista
  real deve vir do catálogo. Informar que a pessoa escolhe os comandos que deseja
  executar. A existência do binário Codex não é requisito para mostrar orientação.
- [x] Rodar:

  ```bash
  python3 -m unittest discover -s tests -p 'test_install_codex.py' -v
  python3 scripts/validate-versions.py
  ```

- [x] Atualizar README: plataformas, instalação, seleção individual, requisitos,
  atualização, remoção e matriz com motivos de exclusão. Manter as referências
  oficiais já adicionadas. Atualizar CLAUDE.md: plataforma `codex`, fontes
  canônicas, geração/check e procedimento para habilitar um novo plugin.

**Check:** apenas plugins publicados aparecem; nenhum processo de instalação é
executado pelo menu Codex; erros não simulam sucesso; fluxos anteriores passam.
**Reversão:** reverter a opção e a documentação do mesmo incremento.

### Tarefa 5 — verificar a distribuição entregue e fechar o PDCA

**Arquivos:** relatórios em `docs/codex/`, documentação e logs afetados.
**Interface consumida:** candidato completo produzido pelas tarefas anteriores.
**Saída:** tabela R01–R12 com resultado, evidência e lacunas, mais handoff de revisão.

- [x] Preparar uma cópia Git do candidato com todos os arquivos necessários,
  incluindo os derivados versionados. Registrar a revisão testada; não usar a
  publicação remota antiga como se já contivesse o trabalho local.
- [x] Em perfil limpo, registrar a loja e comparar o conjunto disponível com o
  catálogo. Instalar um plugin múltiplo e confirmar todas as skills previstas e
  ausência de instalação automática dos outros plugins.
- [x] Ler arquivos pela cópia instalada e comparar hashes com os artefatos da
  revisão candidata. Em outro cenário independente, remover um recurso exigido
  da fixture e comprovar que a verificação correspondente falha.
- [x] Verificar atualização usando duas revisões de uma origem Git de teste, com
  uma alteração observável de versão/conteúdo. `marketplace upgrade` atualiza o
  snapshot Git; medir separadamente quando a cópia do plugin instalado muda.
  Documentar a sequência que realmente atualiza o pacote, sem presumir que o
  nome do comando prova a atualização. Os helps consultados oferecem:

  ```bash
  codex plugin marketplace upgrade chewiesoft-marketplace --json
  codex plugin remove cors@chewiesoft-marketplace --json
  codex plugin marketplace remove chewiesoft-marketplace --json
  ```

  Executar remoções somente no perfil de teste e verificar os efeitos. Não
  tratar upgrade de origem local como prova de upgrade de origem Git.
- [ ] Conferir descoberta, instalação e invocação no desktop, registrando versão
  e sistema. Registrar separadamente o que foi observado em cada ambiente; se o
  executor não tiver acesso a uma superfície, entregar o procedimento e marcar
  `not_checked`, sem atribuir conclusão a esse requisito.
- [x] Rodar uma vez os checks completos após o último ajuste; repetir somente
  se uma nova mudança, falha ou dúvida concreta justificar:

  ```bash
  python3 -m unittest discover -s tests -p 'test_*.py' -v
  python3 plugins/skill-quality-audit/skills/skill-quality-audit/tests/test_audit_skill_quality.py
  python3 scripts/codex-marketplace.py --check
  python3 scripts/validate-versions.py
  git diff --check
  ```

- [x] Confrontar os resultados com R01–R12, atualizar CONTEXT e o relatório de
  compatibilidade. Uma lacuna de acesso ou teste continua visível no resultado.
- [x] Registrar no KAIZEN_LOG o antes/depois observado, quais guardas foram
  provadas com casos vermelhos/verdes e onde ficaram padronizadas. Reabrir os
  arquivos citados para confirmar que os mecanismos existem.
- [x] Preparar handoff com revisão base/final, diff, comandos, resultados e
  lacunas para o novo `/clear`. A etapa seguinte é o `/goal` de codereview até
  todos os grades A, com correção e nova evidência para cada achado.

**Check:** relatório corresponde ao pacote entregue, não apenas ao checkout;
falhas e lacunas permanecem explícitas. **Reversão:** reverter incrementos
afetados e remover apenas instalações de teste identificadas.

## Rastreabilidade e fechamento

| Requisitos | Tarefas |
|---|---|
| R01, R02, R04, R09, R11 | 1, 2, 5 |
| R03, R05, R10 | 2, 3, 5 |
| R06, R07 | 2, 3, 4 |
| R08 | 3, 4, 5 |
| R12 | Handoff e condição de início de todas as tarefas |

**Act:** o padrão alvo é publicar apenas o que foi medido, regenerar os derivados
pela ferramenta e impedir divergências pelo gate. A execução preencherá as
evidências; este plano não declara testes futuros como aprovados.

Cada incremento deve ser revisado e commitado separadamente, com mensagem em
português explicando o motivo. Preparação de documentação não autoriza push,
merge ou publicação remota. A integração final seguirá o escopo autorizado pelo
usuário na retomada.


## Check observado — execução nativa

Base `cff1494c17c21774885e2a58ae6a5eb42cdd95d9`, branch
`feat/codex-marketplace`. Candidato exportado e testado:
`f98c06d34f06ee86cc64c5a1e60419e806e73d8f`; o fechamento seguinte altera
somente documentação e evidências.

| Incremento | Check observado | Commit(s) |
|---|---|---|
| 1 | Catálogo Codex teve precedência; instalação individual, nomes e leituras no cache comprovados. Comando nativo mostrou lacuna de nome/fallback. | `1bb9dff` |
| 2 | RED/GREEN de filtragem, metadados, symlinks, conferência sem escrita e snapshot staged. | `09eb3ef` |
| 3 | 25 plugins / 28 workflows com smokes reais; quatro comandos adaptados; release explícita; seis exclusões documentadas. Hook 100755 comprovado com commit inválido bloqueado. | `98a207d`, `8f865d0` |
| 4 | 8 testes do instalador, sem execução/escrita no fluxo Codex; menu anterior preservado; 31 versões do README conferidas. | `6a6dbf3`, `7ff889a`, `d9d7c47` |
| 5 | 44 testes gerais e 55 do auditor passaram; 25 pacotes / 289 arquivos conferidos no candidato Git; família de quatro skills sem erro; sabotagem detectada; refresh Git, reinstalação e remoção comprovados. | `f98c06d` + fechamento documental |

`marketplace upgrade` no CLI 0.163.0 atualizou também a cópia instalada:
versão 1.1.1 → 99.0.0, marcador novo lido e cache antigo removido na fixture Git.
A hipótese inicial de cache preservado foi rejeitada pela medição.

Evidências, comandos reproduzíveis e R01–R12:
[verification.md](../../codex/verification.md),
[smokes.json](../../codex/smokes.json),
[distribution-evidence.json](../../codex/distribution-evidence.json).
Desktop, macOS e Windows continuam `not_checked`; versão mínima não estabelecida.
R01 está `partial`. Na execução acima, a revisão independente ainda aguardava
o novo `/clear`. Push e publicação não foram executados em nenhuma etapa.

## Check da segunda retomada — revisão

`codereview:codereview` v2.26.8 revisou o diff desde `cff1494`, incluindo o
retrofit CORS; candidato inicial `bad6ebd`, correções `7df2ea7`. Cinco regressões
novas reproduziram dois defeitos no adaptador e duas causas de desvio do gate;
ficaram GREEN após mudanças pontuais. A revisão das correções não encontrou
novos achados. Docstrings públicas e dois trechos do README foram alinhados.

49 testes gerais e 55 do auditor passaram; exportação de `7df2ea7` repetiu os
três cenários reais de distribuição, incluindo 25 pacotes / 289 arquivos.
Grade A em todos os critérios da revisão; régua e limites preservados em
[verification.md](../../codex/verification.md#segunda-retomada--revisão-e-correções).
Desktop/macOS/Windows e versão mínima continuam sem comprovação; a tarefa de
desktop acima permanece desmarcada e R01 `partial`. A revisão não autoriza
integração ou publicação. O [handoff](../../handoffs/2026-10-22-codex-marketplace.md)
registra o estado atual sem reiniciar o planejamento.

## Check da integração autorizada no PR #6

Após revisão do Claude Code, quatro achados foram corrigidos em `2511ba8` e a
base main `0d2e56d` foi integrada em `cb7f95c`. O usuário autorizou o conjunto,
incluindo retrofit codereview 2.27.0, commit e envio à branch do PR. Os 53 testes
gerais, 55 do auditor e 15 do scanner passaram; a exportação do commit integrado
repetiu os três cenários reais com 25 pacotes / 289 arquivos. Os limites de R01 e
a tarefa desktop desmarcada acima permanecem. A evidência atual está no
[relatório](../../codex/verification.md#check-do-commit-integrado).
