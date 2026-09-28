---
name: dotnet-wpf-design
metadata:
  version: 1.8.0
description: Professional WPF/XAML design guide — Fluent Design (90+ controls, DataGrid icons, RowHeight), layout troubleshooting (ScrollViewer, toolbar, form spacing), control sizing, dark theme, branding. MVVM and E2E live in sibling skills. Triggers — WPF design, XAML layout, Fluent, DataGrid icon, form spacing, dark theme.
---

# dotnet-wpf-design

Skill para diagnosticar e corrigir problemas de design em interfaces WPF/XAML, aplicando
boas praticas do Microsoft Fluent Design System e WPF-UI.

Este arquivo tem o workflow, os tokens essenciais, o indice do cookbook e as armadilhas.
Receitas completas e guias por tema ficam em `references/` (tabela no fim diz quando ler cada um).

Historico de versoes em `CHANGELOG.md` (ao lado deste arquivo).

---

## Quando usar

- Campos de formulario muito pequenos ou com texto cortado
- Falta de espacamento/respiro entre campos, secoes ou controles
- Toolbar ou header que rola junto com o conteudo da pagina
- Labels desalinhados ou truncados
- Controles customizados (UserControl) com sizing inadequado
- Cores hardcoded em vez de theme brushes
- FontSize inconsistente entre controles
- Auditar qualidade visual de uma pagina XAML existente
- Planejar layout de nova pagina seguindo Fluent Design

---

## Fluent Design Quick Reference

Estes sao os valores mais usados. Para tabelas completas, leia `references/typography-colors.md`.

### Spacing Ramp (unidade base: 4px)

| Token | Valor | Uso comum |
|-------|-------|-----------|
| XS | 4px | Margem minima entre elementos inline |
| S | 8px | Entre botoes, controle e header |
| M | 12px | Entre controle e label, entre cards |
| L | 16px | Padding de superficie, margem de pagina |
| XL | 20px | Espacamento medio entre secoes |
| XXL | **24px** | **Entre campos de formulario** (padrao Fluent) |
| XXXL | 32px | Entre grupos de campos |

### Control Heights

| Controle | Altura padrao | Altura compacta |
|----------|---------------|-----------------|
| TextBox | 32px | 24px |
| ComboBox | 32-44px | 24px |
| Button | 32px | 24px |
| ToggleButton | 32px | 28px |
| Touch target minimo | 24x24 (WCAG AA) | — |
| Touch target recomendado | 40x40 | — |

### Type Ramp (Windows 11)

| Estilo | Tamanho | Peso | Uso |
|--------|---------|------|-----|
| Caption | 12px | Regular | Textos auxiliares, hints |
| Body | **14px** | Regular | **Labels, texto padrao** |
| Body Strong | 14px | SemiBold | Sub-headers de secao |
| Body Large | 18px | Regular | Subtitulos |
| Subtitle | 20px | SemiBold | Titulos de grupo |
| Title | 28px | SemiBold | Titulo de pagina |
| Title Large | 40px | SemiBold | Hero text, splash |
| Display | 68px | SemiBold | Numeros grandes, dashboards |

### Dark Theme — Cores Essenciais

| Elemento | Cor | Brush WPF-UI |
|----------|-----|-------------|
| Background app | `#202020` | `SolidBackgroundFillColorBaseBrush` |
| Card/secao | `#0DFFFFFF` | `CardBackgroundFillColorDefaultBrush` |
| Texto primario | `#FFFFFF` | `TextFillColorPrimaryBrush` |
| Texto secundario | `#C5FFFFFF` (~77%) | `TextFillColorSecondaryBrush` |
| Texto desabilitado | `#5DFFFFFF` (~36%) | `TextFillColorDisabledBrush` |
| Borda controle | `#12FFFFFF` | `ControlStrokeColorDefaultBrush` |
| Separador/divider | `#15FFFFFF` | `DividerStrokeColorDefaultBrush` |

---

## Workflow: 3 Passos

### Passo 1 — Auditar (diagnostico)

Leia o XAML da pagina e aplique este checklist:

**Layout:**
- [ ] Pagina com toolbar/header usa `ScrollViewer.CanContentScroll="False"`?
- [ ] ScrollViewer esta em Grid com `Height="*"`, nao dentro de StackPanel?
- [ ] Nenhum ScrollViewer aninhado desnecessario?
- [ ] Grid principal usa RowDefinitions adequadas (Auto + *)?

**Espacamento:**
- [ ] Rows de formulario tem Margin vertical >= 8px? (ideal: 24px Fluent)
- [ ] Secoes (Border/Card) tem Padding >= 16px?
- [ ] Separacao entre secoes >= 12px?
- [ ] Labels tem margem do campo >= 8px?

**Sizing:**
- [ ] TextBox/ComboBox tem MinHeight >= 32px (ou Height>=36 se FontSize=13)?
- [ ] ToggleButtons tem MinWidth >= 48px e MinHeight >= 28px?
- [ ] ComboBox tem Width suficiente para mostrar conteudo (minimo 80px para 4 chars)?
- [ ] Controles customizados (UserControl) NAO tem `Height` fixo restritivo? (preferir auto-tamanho ou `MinHeight`)
- [ ] DataGrid RowHeight >= 30px? (consistente entre paginas)
- [ ] Texto de ComboBox/TextBox visivel sem clip vertical em abreviacoes (Mar., Sep.) e descenders (g, p, q)?

**Estilos / escopo de Resources:**
- [ ] Nenhum estilo implicito (`<Style TargetType="...">` sem `x:Key`) em `Page.Resources`/`StackPanel.Resources` que afete inputs em layouts mistos? (use Margin cirurgico ou `x:Key` + `StaticResource` — veja FORM-003)

**DataGrid Icons:**
- [ ] SymbolIcon/Image em DataGridTemplateColumn usa DataTemplate.Triggers com Visibility?
      (NAO Style.Setter.Value — causa sharing bug, icone aparece so em 1 linha)

**Tipografia:**
- [ ] Body text usa FontSize >= 14px?
- [ ] Headers de secao usam FontSize >= 14px SemiBold?
- [ ] Labels usam Foreground com contraste >= 4.5:1 vs background?
- [ ] Nenhum FontSize < 12px (minimo legivel)?

**Theme:**
- [ ] Cores usam DynamicResource brushes em vez de valores hardcoded?
- [ ] BorderBrush usa theme brush em vez de `#555`?
- [ ] Foreground de labels usa `TextFillColorSecondaryBrush` em vez de `#B0B0B0`?

### Passo 2 — Corrigir

Para cada problema encontrado, localize o ID no indice do Cookbook abaixo e aplique o fix.
Quando o fix de uma linha nao bastar, leia a receita completa no arquivo da coluna "Receita"
(todos em `references/`) antes de editar o XAML.

### Passo 3 — Verificar

1. `dotnet build` — confirmar que compila sem erros
2. Teste visual — abrir a aplicacao e verificar:
   - Controles legiveis com texto completo visivel
   - Espacamento confortavel entre campos
   - Toolbar fixa ao rolar conteudo
   - Contraste adequado entre texto e fundo

> ⚠️ **XAML de UserControl numa biblioteca referenciada** (ex.: `MyControls.dll`): o
> `dotnet build` atualiza o DLL no disco, mas a app rodando mantem o antigo em memoria.
> **Instrua o usuario a fechar e reabrir a app** (Detalhe Critico #10).

---

## Cookbook — indice de solucoes

A coluna "Receita" nomeia o arquivo em `references/` com o recipe completo (XAML, errado vs
correto, causa raiz).

| ID | Sintoma | Fix | Receita |
|----|---------|-----|---------|
| LAYOUT-001 | Toolbar rola junto com a pagina dentro de `NavigationView` | `ScrollViewer.CanContentScroll="False"` no `<Page>` + Grid `Auto`/`*`; desliga o `DynamicScrollViewer` interno. Vale com DataGrid e ListBox virtualizado (WPF-UI Issue #1041, PR #1504) | `layout-patterns.md` |
| LAYOUT-002 | Formulario em StackPanel, campos nao expandem | Grid para formularios (alinha label e campo); StackPanel so para inline curto (toolbar, toggles); DockPanel para shell com `LastChildFill="True"` | `layout-patterns.md` |
| LAYOUT-003 | ScrollViewer nao rola, ou dois competem pelo scroll do mouse | ScrollViewer em Grid `Height="*"`, nunca em StackPanel; um ScrollViewer por eixo | `layout-patterns.md` |
| FORM-001 | Campos colados, sem respiro | Entre campos `0,12,0,0` (compacto) ou `0,24,0,0` (padrao); entre grupos `0,32,0,0`/`0,48,0,0`; Padding de secao `16,12,16,16` | `cookbook.md` |
| FORM-002 | Controle pequeno ou texto cortado | MinHeight 32px; ComboBox MinWidth 100px (80px para mes abreviado); sem `Height` fixo no `<UserControl>` (a FontSize 13 o ComboBox Fluent pede ~36px) | `cookbook.md` |
| FORM-003 | Linhas coladas; estilo implicito de Margin quebra toolbar | Margin cirurgico no input (nao no `RowDefinition`) ou `Style` com `x:Key` + `StaticResource` | `form-design.md` |
| FORM-004 | Grupos de campos sem separacao visual | `Border` com `BorderThickness="0,0,0,1"`, `Margin="0,8"` e `DividerStrokeColorDefaultBrush`, em row dedicada com `ColumnSpan` total | `cookbook.md` |
| THEME-001 | Cor hardcoded (`#B0B0B0`, `#555`, `#444`) | `DynamicResource` do WPF-UI (`TextFillColorSecondaryBrush`, `ControlStrokeColorDefaultBrush`, `DividerStrokeColorDefaultBrush`) | `cookbook.md` |
| TYPO-001 | FontSize inconsistente | Type ramp (Title 28 SemiBold, Body Strong 14 SemiBold, Body 14, Caption 12); com WPF-UI, `ui:TextBlock FontTypography="..."` | `cookbook.md` |
| CTRL-001 | Controle WPF padrao onde ha equivalente WPF-UI | `ui:TextBox`, `ui:NumberBox`, `ui:AutoSuggestBox`, `ui:ToggleSwitch`, `ui:CalendarDatePicker`, `ui:ContentDialog`, `ui:Snackbar` | `cookbook.md` |
| CTRL-002 | Botoes importantes sem destaque | `Appearance`: Primary, Secondary, Info, Dark, Light, Danger, Success, Caution, Transparent | `cookbook.md` |
| CTRL-003 | Icone do DataGrid aparece so em uma linha | Nunca UIElement em `Setter.Value`; icones empilhados por linha + `DataTemplate.Triggers` alternando `Visibility` | `cookbook.md` |
| CTRL-008 | Acao destrutiva executa sem confirmar | `ContentDialog` como primeira linha do handler; `confirm != ContentDialogResult.Primary` → `return` antes de qualquer I/O ou mutacao | `cookbook.md` |
| DRY-001 | `<ui:Button.Style>` inline repetido em cada aba | `Style x:Key="ActiveTabButton"` em `App.xaml` com `DataTrigger` sobre `Self.Tag` + `Tag="{Binding ...}"` no botao | `cookbook.md` |
| BRAND-001 | Primary com brand color volta ao cinza no hover | Override dos 7 resources `AccentButton*` em `App.xaml` (nao Style no Background) | `wpfui-theming-overrides.md` |
| CTRL-004 | ToggleButton checked com texto escuro; `Foreground` no code-behind nao pega | Override local de `ToggleButtonForegroundChecked` (+ `PointerOver`, `Pressed`) em `UserControl.Resources` | `wpfui-theming-overrides.md` |
| CTRL-005 | Cor do check ou do fundo do CheckBox | `CheckBoxCheckBackgroundFillChecked` (+ `PointerOver`, `Pressed`) e `CheckBoxCheckGlyphForeground` (singular, sem sufixo de estado) | `wpfui-theming-overrides.md` |
| CTRL-006 | X do `ui:TextBox` cobre o digito em campo curto | `ClearButtonEnabled="False"` em campos de 1-5 chars (dd, yyyy, HH, mm), nao em campos longos | `wpfui-theming-overrides.md` |
| CTRL-007 | ProgressRing na cor accent padrao | `ProgressRingForegroundThemeBrush` (arco) e `ProgressRingBackgroundThemeBrush` (circulo) em `App.xaml`; override global | `wpfui-theming-overrides.md` |
| RES-001 | Override de resource nao tem efeito | Extrair os nomes reais do `Wpf.Ui.dll` antes do override (comando abaixo) | `wpfui-theming-overrides.md` |

Comando rapido do RES-001 (Git Bash / WSL; o equivalente PowerShell esta na receita):

```bash
DLL="$HOME/.nuget/packages/wpf-ui/4.2.0/lib/net8.0-windows7.0/Wpf.Ui.dll"
grep -a "CheckBox" "$DLL" | tr '\0' '\n' | grep -oE "CheckBox[A-Za-z]+" | sort -u
```

---

## Armadilhas — anti-padroes

1. **StackPanel como container de formulario** — espaco infinito impede controles
   `Width="*"` de expandir. Use Grid com ColumnDefinitions (LAYOUT-002).
2. **ScrollViewer dentro de StackPanel** — recebe altura infinita e nunca rola. Coloque-o em
   Grid com `RowDefinition Height="*"` (LAYOUT-003).
3. **Cores hardcoded (#B0B0B0, #555)** — nao acompanham mudanca de tema. Use `DynamicResource`
   com brushes do WPF-UI (THEME-001).
4. **FontSize < 12px** — ilegivel. Minimo absoluto 12px (Caption); body text 14px.
5. **Controles sem MinHeight** — TextBox e ComboBox ficam microscopicos com conteudo vazio.
   Defina MinHeight >= 32px.
6. **Margin="0,4" entre campos** — 4px e pouco respiro. Minimo 8px; padrao Fluent 24px.
7. **Width fixo em ComboBox muito estreito** — `Width=65` nao mostra "Jun." completo com
   padding. Minimo 80px para meses abreviados.
8. **`Height` fixo em UserControl que envolve controles Fluent** — o pai capa o espaco dos
   filhos, e `MinHeight` nos filhos nao o recupera. A `FontSize="13"` o `ComboBox`/`TextBox`
   Fluent (WPF-UI) precisa de ~36px; `Height="32"` parece "padrao" mas corta "g", "p", ".",
   e o reflexo errado e aumentar `Width`. **Fix:** UserControl sem `Height` (auto-tamanho), ou
   `MinHeight` no proprio UserControl, ou `Height` explicito no filho problematico (FORM-002,
   Detalhe #9).
9. **SymbolIcon/Image em `Style` `Setter.Value` dentro de DataTemplate** — o UIElement e
   instanciado uma vez e compartilhado entre as linhas; so a ultima renderizada mostra o icone.
   Use `DataTemplate.Triggers` com Visibility, nao `Style.Triggers` com Content (CTRL-003).
10. **Estilo implicito em `<StackPanel.Resources>`/`<Page.Resources>` para Margin de inputs** —
    se a pagina mistura grid de formulario com qualquer `StackPanel Orientation="Horizontal"`
    (toolbar, campos inline, UserControl horizontal), um
    `<Style TargetType="{x:Type TextBox}"><Setter Property="Margin" Value="0,4"/></Style>`
    pega todos os TextBoxes filhos e a margem vertical desalinha a linha horizontal. Use Margin
    cirurgico ou `Style` com `x:Key` + `StaticResource` (FORM-003).
11. **Border separador na mesma `Grid.Row` que conteudo** — o Margin do Border expande a row e
    o texto fica atras da linha. Use `RowDefinition Height="Auto"` dedicada, sem outro elemento
    (FORM-004).
12. **`<Style TargetType="ui:Button">` sem `BasedOn`** — substitui o template padrao e perde o
    visual Fluent (padding, bordas arredondadas, hover suave, icones): o botao vira o retangulo
    cinza do `ButtonBase`. Em Style de controle WPF-UI, sempre
    `BasedOn="{StaticResource {x:Type ui:Button}}"`.
13. **Setar `control.Foreground`/`.Background` em controle WPF-UI com trigger de template
    ativo** — code-behind e Style externo perdem para o `Setter TargetName="X"` com
    `DynamicResource` no elemento interno; hover/pressed/checked ignoram a cor. Regra geral e
    recipes: Detalhe #11 (BRAND-001, CTRL-004, CTRL-005).
14. **Chutar nomes de DynamicResource do WPF-UI** — `ButtonBackgroundChecked`,
    `CheckBoxCheckGlyphForegroundChecked`, `AccentButtonBorderBrush` seguem a convencao
    WinUI/WinRT mas nao existem no WPF-UI 4.2.0. Override com nome errado e ignorado em
    silencio (sem erro, sem warning). Verifique no DLL antes (RES-001).

---

## Detalhes Criticos (armadilhas do WPF-UI 4.2.0)

1. **`ScrollViewer.CanContentScroll="False"` e a unica forma confiavel** de desabilitar o
   DynamicScrollViewer do NavigationView. `ScrollViewer.VerticalScrollBarVisibility="Disabled"`
   no Page NAO funciona: o `NavigationViewContentPresenter` ignora essa propriedade.
2. **WPF-UI herda do Frame** — o `NavigationViewContentPresenter` estende `Frame`, nao
   `ContentPresenter`, entao a pagina nao recebe constraints de tamanho automaticamente.
3. **DynamicResource vs StaticResource** — cor de tema usa `DynamicResource`; `StaticResource`
   nao atualiza quando o tema muda em runtime.
4. **ComboBox items com espacos iniciais** (`Content="   Good"`) — use `Padding`; espacos
   podem causar problemas ao comparar valores.
5. **`<ui:ContentDialogHost>` e o elemento XAML correto** — nao `ContentPresenter` nem
   `ContentDialogPresenter`.
6. **`using Wpf.Ui.Extensions;` necessario para ShowSimpleDialogAsync** — e extension method,
   nao metodo da interface. Sem o using, o codigo compila mas o metodo nao e encontrado.
7. **`using Wpf.Ui.Controls;` conflita com System.Windows.Controls** — TextBox, ComboBox, Page,
   Button existem nos dois namespaces. Use type aliases para os tipos do WPF-UI:
   ```csharp
   using ControlAppearance = Wpf.Ui.Controls.ControlAppearance;
   using SymbolIcon = Wpf.Ui.Controls.SymbolIcon;
   using SymbolRegular = Wpf.Ui.Controls.SymbolRegular;
   using SimpleContentDialogCreateOptions = Wpf.Ui.SimpleContentDialogCreateOptions;
   using ContentDialogResult = Wpf.Ui.Controls.ContentDialogResult;
   ```
   `ContentDialogResult` e o facil de esquecer: so aparece quando um `ShowSimpleDialogAsync`
   "single OK" ganha `PrimaryButtonText`+`CloseButtonText` (CTRL-008). Sem o alias, o codigo
   compila mas resolve para o tipo errado, ou da ambiguidade, conforme os outros usings.
8. **`async void` so em event handlers UI** — metodos como SaveFormDataJSON/LoadFormDataJSON
   que fazem `await _contentDialogService.ShowSimpleDialogAsync()` devem ser `async Task`.
   Excecoes em `async void` nao sao observaveis e podem crashar a app.
9. **Texto clipado em controle Fluent quase sempre e altura, nao largura** — "Mar." sem o
   ponto, "Sep." sem o "p.", descenders (`g`, `p`, `q`) cortados no rodape. Antes de mexer em
   `Width`, verifique nesta ordem:
   1. `Height` fixo no `<UserControl>` pai (mais comum — `Height="32"` e classico).
   2. `Height` fixo no proprio controle.
   3. `RowDefinition Height="..."` muito apertado no `Grid` pai.
   4. `MinHeight` < altura natural a essa `FontSize`.

   **Regra pratica:** a `FontSize="13"` o `ComboBox` Fluent precisa de **~36px** para
   abreviacoes com ponto sem clip; a `FontSize="14"` (Body), **~38-40px**; a `FontSize="12"`
   (Caption) suporta `Height="32"` na maioria dos casos.
10. **Mudancas em XAML de UserControl em DLL referenciada precisam de process restart** —
    `MyControl.xaml` em `MyControls.csproj` (DLL referenciada por `MyApp.exe`) vira BAML
    embutido no `MyControls.dll`, que o processo carregou no startup e nao recarrega.
    `dotnet build` atualiza o DLL no disco, nao o processo rodando. Sempre instruir o usuario:
    "feche e reabra a app para ver as mudancas".
11. **Hierarquia de precedencia WPF para triggers do template** — para customizar controle
    WPF-UI em estados (hover, pressed, checked), sobrescreva o `DynamicResource` que o template
    consulta, nao as properties do controle. `ControlTemplate.Triggers` com
    `Setter TargetName="X" Property="Y" Value="{DynamicResource Z}"` escreve no elemento
    INTERNO do template e vence: Setters de Style externo (mesmo com `BasedOn`), atribuicoes
    via code-behind (`button.Background = ...`) e TemplateBinding de outras properties.

    **Regra pratica:** se a cor "volta" no hover/pressed/checked, o problema nao e seu Style:
    ha um DynamicResource aplicado num elemento interno via `TargetName`. Identifique-o via
    RES-001 e sobrescreva no escopo certo (local = `UserControl.Resources`, global =
    `App.xaml`). Casos no cookbook: botao Primary com brand color voltando para azul no hover
    (BRAND-001), ToggleButton checked com texto escuro sobre fundo colorido (CTRL-004), glyph
    do CheckBox na cor errada (CTRL-005).

---

## Guias de Referencia (progressive disclosure level 3)

Leia estes arquivos **somente quando necessario** no passo correspondente:

| Arquivo | Leia quando... |
|---------|----------------|
| `references/cookbook.md` | For aplicar FORM-001/002/004, THEME-001, TYPO-001, CTRL-001/002/003/008 ou DRY-001 e precisar do XAML/C# completo |
| `references/layout-patterns.md` | Quando houver problema de ScrollViewer, toolbar fixa (LAYOUT-001), Grid vs StackPanel vs DockPanel |
| `references/form-design.md` | Quando o assunto for espacamento entre campos, label alignment, respiro ou FORM-003 |
| `references/typography-colors.md` | Quando precisar de FontSize, type ramp, cores dark theme completas ou contraste WCAG |
| `references/controls-sizing.md` | Quando dimensionar MinHeight/MinWidth, ComboBox, TextBox, touch targets, DataGrid |
| `references/wpfui-components.md` | Quando usar Card, CardExpander, InfoBar, DynamicResource brushes, theming setup, SymbolIcon ou header do NavigationView |
| `references/wpfui-controls-catalog.md` | Quando escolher entre os 90+ controles WPF-UI (XAML, enum ControlAppearance, `IContentDialogService`, `ISnackbarService`, gotchas do 4.2.0) |
| `references/wpfui-theming-overrides.md` | Quando aplicar BRAND-001, CTRL-004/5/6/7 ou RES-001 (brand color, ToggleButton, CheckBox, ProgressRing, nomes de resources) |
| `references/sources.md` | Quando precisar citar a documentacao oficial ou as fontes da pesquisa |
