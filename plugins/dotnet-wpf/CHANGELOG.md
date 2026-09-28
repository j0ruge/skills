# Changelog — dotnet-wpf

Formato: [Semantic Versioning](https://semver.org/)

## [1.8.0] - 2026-09-28

Progressive disclosure nas quatro skills, pela spec aberta agentskills.io (SKILL.md abaixo de
500 linhas e de ~5.000 tokens, references a um nível do SKILL.md, reference longa com sumário) e
pelos achados do `skill-quality-audit` v0.2.0: C1 (tamanho do SKILL.md), C2 (reference que cita
outra por `references/`) e C3 (reference com mais de 300 linhas sem sumário). Nenhum conteúdo
saiu: o que deixou o SKILL.md foi movido para `references/` ou comprimido sem perder fato,
comando ou número.

| Skill | Antes (linhas / chars) | Depois |
|-------|------------------------|--------|
| dotnet-wpf-design | 970 / 43.298 | 313 / 19.700 |
| dotnet-wpf-e2e-testing | 610 / 23.508 | 434 / 18.723 |
| dotnet-wpf-mvvm | 648 / 28.379 | 317 / 19.756 |
| dotnet-desktop-setup | 250 | 250 (só a versão) |

- **dotnet-wpf-design** — o cookbook vira um índice (ID, sintoma, fix curto, arquivo da receita).
  As receitas que não tinham casa em outra reference (FORM-001, FORM-002, FORM-004, THEME-001,
  TYPO-001, CTRL-001, CTRL-002, CTRL-003, CTRL-008, DRY-001) foram movidas na íntegra para a nova
  `references/cookbook.md`, com sumário. LAYOUT-001/002/003, FORM-003, BRAND-001, CTRL-004 a 007
  e RES-001 já tinham o recipe completo em `layout-patterns.md`, `form-design.md` e
  `wpfui-theming-overrides.md`; o resumo duplicado saiu do SKILL.md. Anti-padrões (14) e
  Detalhes Críticos (11) ficam no SKILL.md, comprimidos e com a mesma numeração, que as
  references citam. `wpfui-components.md` deixa de citar `references/layout-patterns.md` (C2);
  `wpfui-controls-catalog.md` (425 linhas) ganha sumário (C3). A tabela de references passa a
  dizer quando ler cada uma.
- **dotnet-wpf-e2e-testing** — o código do Passo 6 (`IFileDialogService`, `WpfFileDialogService`,
  ViewModel, `FileDialogHelper`) e o exemplo `LoadHardwareId()` vão para a nova
  `references/file-dialogs.md`. O SKILL.md guarda as duas estratégias, os cinco passos do helper
  (AutomationId `1148` e `1`, fallback Alt+D/Alt+N, botões por nome, timeouts) e a nota sobre
  `Thread.Sleep`. `flaui-patterns.md` deixa de citar `references/xaml-automation.md` (C2). A seção
  dos linters vira "Armadilha".
- **dotnet-wpf-mvvm** — o template de ViewModel do Passo 4 passa a abrir
  `communitytoolkit-patterns.md`; o código dos testes de ViewModel vai para a nova
  `references/viewmodel-testing.md`; "Custom Controls e Data Binding" para a nova
  `references/custom-controls-binding.md`; "Estado Compartilhado (IAppStateService)" para
  `mvvm-fundamentals.md`, ao lado do Messenger; o texto completo, com código, dos Detalhes #17 a
  #26 para a nova `references/performance-patterns.md`. No SKILL.md os 28 Detalhes Críticos
  mantêm a numeração (as references citam o #27), em tabela e resumo; os anti-padrões viram
  tabela, e o de `DataView.RowFilter` aponta para o #23. `mvvm-fundamentals.md` deixa de citar
  `references/wpfui-integration.md` (C2); `communitytoolkit-patterns.md`,
  `migration-winforms-to-wpf.md` e `wpfui-integration.md` ganham sumário (C3).
- **dotnet-desktop-setup** — `scoped-rules-templates.md` (320 linhas) ganha sumário das seções de
  fora dos blocos de template (C3).

As quatro skills sobem `metadata.version` para 1.8.0, espelhando o plugin.

**Como reverter:** `git revert` do commit que traz esta entrada. Nenhum arquivo foi apagado: o
revert restaura os SKILL.md originais e remove as cinco references novas.

## [1.7.0] - 2026-09-03

Prompt audit (`/claude-api prompt-audit`, modelo-alvo Claude Fable 5.1); relatório completo fora do repo. Quatro skills auditadas; um commit por plugin.

- **dotnet-desktop-setup** — o JSON de hooks do Passo 8 usava um evento `PreCommit`, que não existe
  no Claude Code, e o shape `command`/`description` direto no matcher, que o schema não aceita: quem
  colava a config recebia um hook que nunca rodava. Corrigido para `hooks[] { type: command }`; o
  teste antes do commit vai para um git hook `pre-commit`. "Execute os passos em ordem" vira "duas
  ordens importam" (auditoria antes de tudo; CLAUDE.md antes das rules escopadas); caps sem razão
  rebaixados; o Detalhe #4 ganha o motivo real (o que é global vs. do projeto), no lugar de "o
  modelo sem skill não conhece a hierarquia"; templates gerados sem `NUNCA` e sem categorias de
  domínio de um projeto (`MMSI`).
- **dotnet-wpf-mvvm** — as references ainda registravam ViewModels como `Transient`, o que o
  próprio corpo (Detalhe #27) diz vazar memória: o exemplo reintroduzia o leak sem erro de build.
  Alinhadas a Singleton. O ponteiro para `TODO_SPECS/SPEC-Automated-UI-Testing.md` (inexistente)
  vira ponteiro para a skill irmã `dotnet-wpf-e2e-testing`. Resíduos do projeto de origem
  (`VDAControls/WPF/`, `SC-002`, "projeto VDRDataAnalyzer") saem; ~18 caps rebaixados.
- **dotnet-wpf-design** — o bloco "Versão e Changelog" sai do corpo (o CHANGELOG já existe);
  nomes de brushes corrigidos (faltava o sufixo `Brush`); receita da toolbar fixa vira ponteiro para
  `layout-patterns.md` em vez de duplicata; `VDAControls`/`VDRDataAnalyzer` → nomes genéricos; o
  XAML do AptDate deixa de fixar `Height=32` a FontSize 13 (contradizia o Detalhe #9, que diz que
  clipa); "aprendidos nos testes" e "Exemplos na sessão" saem dos títulos.
- **dotnet-wpf-e2e-testing** — "nunca use `Thread.Sleep()`" ganha a exceção que o próprio corpo
  já fazia (dialogs Win32); o incidente do linter que removeu `LoadHardwareId()` vira o princípio;
  "siga estes passos na ordem" diz onde a ordem importa e que os Passos 6–7 são condicionais.

As quatro skills ganham `metadata.version` espelhando o plugin (antes ausente).

## [1.6.1] - 2026-05-06

### Changed

- Patch-bump em conjunto com os demais plugins: descrições das skills enxugadas para caber
  no orçamento do `/doctor`, garantindo que `/plugin update` puxe as versões enxutas.

## [1.6.0] - 2026-04-16

### Added

- `dotnet-wpf-design` CTRL-008: padrao "guard before mutate" para `ContentDialog`. Acoes destrutivas (Load Last Export, Reset Form, Discard Changes) confirmam ANTES de qualquer leitura de I/O ou mutacao do view-model. Handler chama o dialogo como primeira linha e faz early-return em `confirm != ContentDialogResult.Primary` — preserva o estado anterior 100% intacto se o usuario cancelar.
- Decisao "sempre confirmar vs. dirty-tracking" documentada: dirty-tracking exige snapshot + comparacao confiavel (alto custo, alto risco de false-negatives). Quando o estado raramente esta vazio, sempre confirmar e o trade-off vencedor.
- Regras de UX para o dialogo: texto do Primary descreve a acao ("Replace data") em vez de "OK"; `Appearance="Danger"` apenas quando irreversivel; dialog mora em `*Page.xaml.cs`, nao no ViewModel (UI decoupling).
- Detalhe Critico #7 expandido com lista explicita de aliases para `Wpf.Ui.Controls` ↔ `System.Windows.Controls`, incluindo `ContentDialogResult` (facil de esquecer porque so aparece quando o handler evolui de "single OK" para "Primary + Close").

### Changed

- Plugin version bumped to 1.6.0.

## [1.5.0] - 2026-04-09

### Added

- `dotnet-wpf-design` FORM-004: separador sutil entre grupos de campos em Grid. Border com `BorderThickness="0,0,0,1"` e `DividerStrokeColorDefaultBrush` em row dedicada (`Margin="0,8"`). Inclui anti-padrao documentado: nunca compartilhar row do separador com conteudo (causa sobreposicao visual).
- Anti-pattern #11: Border separador na mesma Grid.Row que conteudo causa sobreposicao — usar row dedicada.

### Changed

- Plugin version bumped to 1.5.0.

## [1.4.0] - 2026-04-08

### Added

- `dotnet-wpf-design` FORM-003: estilos implicitos em `<StackPanel.Resources>` tem blast radius indesejado em layouts mistos. Recipe completo em `references/form-design.md`.
- Anti-pattern #10: estilos implicitos para Margin de inputs quebra toolbars e StackPanels horizontais.
- Detalhe Critico #9: texto clipado em controle Fluent quase sempre e altura, nao largura.
- Detalhe Critico #10: mudancas em XAML de UserControl em DLL referenciada precisam de process restart.

### Fixed

- `dotnet-wpf-design` FORM-002: exemplo com `Height="32"` no UserControl e ComboBox FontSize=13 causava clipping. Corrigido para auto-tamanho.

## [1.3.0] - 2026-04-07

### Added

- `dotnet-wpf-design` WPF-UI deep dive: catalogo completo de 90+ controles em `references/wpfui-controls-catalog.md`.
- ControlAppearance enum (Primary, Danger, Success, Caution) para semantica de cores.
- DI services: IContentDialogService, ISnackbarService pattern.
- Controles novos: NumberBox, AutoSuggestBox, ToggleSwitch, ContentDialog, Snackbar, Flyout, CalendarDatePicker, PassiveScrollViewer.
- FontTypography completado: TitleLarge (40px), Display (68px).

## [1.2.0] - 2026-04-06

### Added

- `dotnet-wpf-design` CTRL-003: SymbolIcon sharing bug in DataGrid — icons in Style.Setter.Value are shared across rows, only last row shows icon. Documented correct pattern using DataTemplate.Triggers with Visibility.
- `dotnet-wpf-design` LAYOUT-001 variant: toolbar fixa em paginas com DataGrid (sem ScrollViewer explicito). CanContentScroll="False" desabilita DynamicScrollViewer e DataGrid usa scroll interno.
- `dotnet-wpf-design` DataGrid RowHeight recommendation: 30px as sweet spot for readability. Updated controls-sizing.md with comparison table and ListBox equivalent.
- `dotnet-wpf-design` audit checklist: DataGrid RowHeight >= 30px + SymbolIcon Visibility pattern check.
- Anti-pattern #9: UIElements in Style Setter.Value inside DataTemplate.

## [1.0.0] - 2026-04-01

### Added

- `dotnet-desktop-setup` skill — configures and audits C#/.NET desktop projects for Claude Code (WinForms, WPF, Avalonia). Includes environment audit script, CLAUDE.md templates, .editorconfig template, scoped rules, and decoupling/testing guides.
- `dotnet-wpf-design` skill — professional WPF/XAML Fluent Design guide with WPF-UI. 90+ controls catalog, layout patterns, typography/colors, form design, and controls sizing references.
- `dotnet-wpf-e2e-testing` skill — FlaUI + xUnit E2E testing guide for WPF. AutomationId patterns, Page Objects, CI/CD setup for UI tests.
- `dotnet-wpf-mvvm` skill — WinForms-to-WPF migration with MVVM using CommunityToolkit.Mvvm and WPF-UI. ViewModels, DataBinding, Commands, navigation, and DI configuration.
