# Compatibilidade Codex

Inventário dos 32 plugins: 31 auditados em 2026-10-22; `windows-games-linux` entrou em 2026-10-23 sem avaliação Codex (`not_checked`). Apenas `supported` entra no catálogo.
Os smokes cobrem instalação, descoberta, leitura no cache e entrada de cada workflow;
operações integrais de domínio e dependências autenticadas não fazem parte do smoke.
Ubuntu 24.04/CLI 0.163.0 é a cobertura medida (o `hook-builder` 0.2.0, em 2026-10-27, na 0.164.0); desktop, macOS e Windows permanecem
`not_checked`. Isso inclui a execução Windows de WPF/limpeza/WSL, mesmo quando o pacote carrega.
Versão mínima ainda não estabelecida. Veja [verification.md](verification.md).

| Plugin | Estado | Workflows canônicos | Recursos | Requisitos e motivo |
|---|---|---|---|---|
| ansible-docker-backup-restore | `supported` | `skills/ansible-docker-backup-restore/SKILL.md` | 11 arquivos de scripts/referências/templates/assets | Ansible, Docker, SSH; Bash/Linux no alvo. Operações exigem inventário e acesso próprios. |
| cicd | `supported` | `skills/cicd/SKILL.md` | 15 arquivos de scripts/referências/templates/assets | Git, gh autenticado, Docker conforme a stack. Sensores/CI reais são do projeto consumidor. |
| codereview | `partial` | `skills/coderabbit-pr/SKILL.md`<br>`skills/codereview/SKILL.md` | 17 arquivos de scripts/referências/templates/assets | Git, Python; gh para PR; roteamento de modelos/agentes. As duas entradas carregam, mas o corpo exige Agent/model sonnet; equivalência completa não comprovada. |
| cors | `supported` | `skills/cors/SKILL.md` | 4 arquivos de scripts/referências/templates/assets | Browser/DevTools para diagnóstico; stack HTTP para correções. Entrada segura pede mensagem literal do Console; não faz chamadas de rede. |
| criar-prd | `supported` | `commands/criar-prd.md` | 1 arquivos de scripts/referências/templates/assets | Leitura/escrita de Markdown; pesquisa web condicional. Adaptador preserva template do projeto e fallback em assets/. |
| criar-task | `supported` | `commands/criar-task.md` | 2 arquivos de scripts/referências/templates/assets | PRD e Tech Spec locais. Dois templates empacotados; aprovação antes de gerar arquivos. |
| criar-techspec | `supported` | `commands/criar-techspec.md` | 1 arquivos de scripts/referências/templates/assets | PRD local aprovado; leitura do repo. Template empacotado; não exige acesso externo no smoke. |
| ddd | `supported` | `skills/ddd/SKILL.md` | 19 arquivos de scripts/referências/templates/assets | Leitura de código/documentos; ferramentas de agente do host quando disponíveis. Referências Agent descrevem delegação; smoke cobre entrada e leitura, sem acionar delegação. |
| deploy | `supported` | `skills/staging/SKILL.md` | 5 arquivos de scripts/referências/templates/assets | Git, gh ou acesso ao host, pipeline do projeto. Skill publicada como deploy:staging; smoke não promove ambientes. |
| dev-script | `supported` | `skills/dev-script/SKILL.md` | 9 arquivos de scripts/referências/templates/assets | Bash/PowerShell e ferramentas da stack do consumidor. Gera scripts para os sistemas do projeto; smoke não executa os scripts gerados. |
| dotnet-wpf | `partial` | `skills/dotnet-desktop-setup/SKILL.md`<br>`skills/dotnet-wpf-design/SKILL.md`<br>`skills/dotnet-wpf-e2e-testing/SKILL.md`<br>`skills/dotnet-wpf-mvvm/SKILL.md` | 28 arquivos de scripts/referências/templates/assets | Windows, .NET, ferramentas WPF/FlaUI. Agrupamento preservado: setup exige regras, hooks e configuração Claude; três skills isoladas não autorizam publicar o pacote inteiro. |
| executar-task | `supported` | `commands/executar-task.md` | 0 arquivos de scripts/referências/templates/assets | Projeto com tarefas e ferramentas da stack. Testes e convenções dependem do projeto consumidor. |
| git-housekeeping | `supported` | `skills/git-housekeeping/SKILL.md` | 4 arquivos de scripts/referências/templates/assets | Python 3, Git; gh opcional para comprovar squash. Planejamento/análise são separados da aplicação autorizada. |
| hook-builder | `supported` | `skills/hook-builder/SKILL.md` | 29 arquivos de scripts/referências/templates/assets | Python 3 (stdlib); Claude Code e/ou Codex CLI, conforme o host do hook. Contrato Codex conferido no código da tag rust-v0.164.0 e em probe com `codex exec` (`references/codex.md`); smoke de 2026-10-27 no codex-cli 0.164.0: instalação, descoberta `hook-builder:hook-builder`, leitura de `references/codex.md` pelo cache e fixtures Codex no `hook_test.py`. |
| html-presentation | `supported` | `skills/html-presentation/SKILL.md` | 7 arquivos de scripts/referências/templates/assets | Python, navegador/Playwright, ferramentas de PDF conforme a origem. Reviewer deck-reviewer é específico do Claude; no Codex use revisor nativo de contexto independente conforme references/review.md. |
| kaizen-software | `supported` | `skills/kaizen-software/SKILL.md` | 4 arquivos de scripts/referências/templates/assets | Leitura/escrita de Markdown e ferramentas do projeto. Referências e templates PDCA locais; sem dependência de runtime Claude. |
| n8n-ops | `supported` | `skills/n8n-ops/SKILL.md` | 4 arquivos de scripts/referências/templates/assets | n8n, ferramentas do projeto, API/autenticação quando usada. MCP é opcional; o alvo precisa de URL/credenciais próprias. |
| pdf-generation | `supported` | `skills/pdf-generation/SKILL.md` | 3 arquivos de scripts/referências/templates/assets | Biblioteca PDF escolhida por stack; navegador quando necessário. Comparação de bibliotecas é recurso empacotado; geração/exportação integral não testada. |
| release | `supported` | `skills/release/SKILL.md` | 0 arquivos de scripts/referências/templates/assets | Git e gh autenticado; versão informada explicitamente. Somente $release:release; agents/openai.yaml impede ativação implícita no Codex. |
| retrofit-skill | `partial` | `commands/retrofit-skill.md` | 3 arquivos de scripts/referências/templates/assets | Clone deste marketplace, Python, Git e auditor irmão. O comando depende de <REPO>/plugins/ e caminhos de instalação do Claude; autocontenção no cache e integração com outros plugins não comprovadas. |
| retrofit-watch | `partial` | `skills/retrofit-watch/SKILL.md` | 2 arquivos de scripts/referências/templates/assets | Adaptação local Codex em funcionamento nesta sessão. O plugin da loja ainda contém hooks/transcript Claude e não empacota a camada Codex; instalação nativa dessa camada pelo catálogo não comprovada. |
| skill-quality-audit | `supported` | `skills/skill-claim-check/SKILL.md`<br>`skills/skill-quality-audit/SKILL.md`<br>`skills/skill-refactoring/SKILL.md`<br>`skills/skill-self-containment/SKILL.md` | 15 arquivos de scripts/referências/templates/assets | Python 3; validadores externos opcionais. Quatro skills mantidas juntas; resolução por diretórios irmãos, sem instalar outro plugin. |
| statusline | `unsupported` | `commands/setup.md` | 0 arquivos de scripts/referências/templates/assets | Runtime e status-line API do Claude Code. Comando setup escreve configurações e script exclusivos do Claude. |
| ticket | `supported` | `skills/ticket/SKILL.md` | 7 arquivos de scripts/referências/templates/assets | acli, Git, Jira; JIRA_EMAIL/JIRA_API_TOKEN para REST; MCP opcional. Sem credenciais no pacote. argument-hint permanece para Claude e é ignorado no Codex; configure as variáveis no seu ambiente. |
| todo-to-github-issues | `supported` | `skills/todo-to-github-issues/SKILL.md` | 10 arquivos de scripts/referências/templates/assets | Python, Git, gh autenticado e kit sdd instalado. O kit externo é dependência declarada; scripts empacotados são conferidos sem criar issues. |
| ts-library | `supported` | `skills/ts-library/SKILL.md` | 6 arquivos de scripts/referências/templates/assets | Node/gerenciador do projeto, TypeScript, Git. Ferramentas da biblioteca dependem do projeto consumidor. |
| unlovable | `supported` | `skills/unlovable/SKILL.md` | 0 arquivos de scripts/referências/templates/assets | Node e ferramentas React/Vite do projeto. Workflow específico para migrar projetos Lovable. |
| whisper-preprocess | `supported` | `skills/whisper-preprocess/SKILL.md` | 2 arquivos de scripts/referências/templates/assets | Python, ffmpeg, Whisper e modelos locais; hardware adequado. Dependências e processamento de áudio não executados pelo smoke. |
| windows-disk-cleanup | `supported` | `skills/windows-disk-cleanup/SKILL.md` | 18 arquivos de scripts/referências/templates/assets | Windows, PowerShell, ferramentas de disco; Bash/WSL conforme o caso. Operações Windows e exclusão de dados não executadas no smoke Linux. |
| windows-games-linux | `not_checked` | `skills/windows-games-linux/SKILL.md` | 6 arquivos de scripts/referências/templates/assets | Linux com Lutris/umu/Proton ou Wine, bash e python3; pkexec ou sudo para instalar pacotes. Lança jogos na tela do usuário. Não avaliado no Codex nesta publicação. |
| wsl-windows-onboarding | `supported` | `skills/wsl-windows-onboarding/SKILL.md` | 6 arquivos de scripts/referências/templates/assets | Windows/WSL2, PowerShell, Bash, rsync, ferramentas do guia. O alvo é WSL/Claude; smoke de leitura no Linux não prova operações Windows. |
| zitadel-idp | `supported` | `skills/zitadel-idp/SKILL.md` | 15 arquivos de scripts/referências/templates/assets | Zitadel, Docker, curl/jq, credenciais do projeto. Versões/APIs exigem conferência nas referências; nenhum acesso ao IdP no smoke. |

`$plugin:skill` é o nome qualificado mostrado pelo host. Instalações avulsas em
`~/.agents/skills` ou outros marketplaces podem oferecer nomes semelhantes; confira
a origem em `/skills` e remova duplicatas pela instalação que as criou.
Comandos adaptados não recebem a cópia automática `source-command-*` porque o
manifesto derivado fixa `commands: []`.

O campo `platforms` dos manifestos é uma declaração deste repositório. A filtragem
real vem do catálogo Codex próprio, cuja precedência foi provada no CLI.
Campos de frontmatter exclusivos de Claude/Cursor geram `A4 AVISO` no auditor local
e avisos em `validate-versions.py`. Com o validador externo disponível
(`--external auto`, via skills-ref/agentskills/uvx), release e ticket recebem
`G2 ERRO` e o auditor retorna 1 por esses campos fora da spec. Esse limite de
portabilidade é explícito: Codex não os herda, e a regra de interseção não foi
relaxada. A política explícita de release é validada separadamente.

As skills ddd, pdf-generation e release usam o texto da mensagem de invocação
quando `$ARGUMENTS` permanece literal; os hosts que substituem o bloco continuam
usando essa substituição. Comandos derivados já traduzem o placeholder.

Nenhuma credencial é distribuída; os requisitos citam apenas nomes de variáveis.

## Retrofit-watch local no Codex

Classificação corrigida em 2026-10-23: `unsupported` não representava a adaptação
local já funcional no CLI. `partial` registra o suporte local observado e a
lacuna de distribuição do pacote desta loja.

O hook ativo em `~/.codex/hooks.json` chama
`~/.agents/skills/retrofit-watch/scripts/codex_retrofit_watch.py`, pelos eventos
SessionStart e Stop. O symlink observado resolve para a skill local em
`~/.hermes/skills/software-development/retrofit-watch/`; sua camada Codex é
separada do motor upstream. Os prompts de retro recebidos nesta sessão comprovam
o disparo; a leitura da configuração confirma qual implementação os produziu.

Já `plugins/retrofit-watch/hooks/hooks.json` usa `${CLAUDE_PLUGIN_ROOT}` e o
motor `retrofit_watch.py`; o plugin 0.3.3 declara apenas `claude-code`. A camada
`codex_retrofit_watch.py` e seu template `assets/hooks.json` existem na instalação
local, sem fazer parte desse pacote. O catálogo Codex tem 26 plugins desde a entrada do `hook-builder` 0.2.0 (2026-10-27), e o watcher continua fora:
publicar o watcher nele exige integrar essa camada e provar instalação/confiança
e execução pelo pacote instalado. Esta correção documental não certifica desktop,
macOS, Windows ou equivalência completa entre os dois watchers.
