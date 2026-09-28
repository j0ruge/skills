---
name: dotnet-wpf-mvvm
metadata:
  version: 1.8.0
description: WinForms→WPF MVVM migration plus new WPF screens — CommunityToolkit.Mvvm, WPF-UI, ViewModels, data binding, Commands, navigation, DI via Microsoft.Extensions.Hosting. Setup and E2E live in sibling skills. Triggers — MVVM, WinForms to WPF, CommunityToolkit, data binding, RelayCommand.
---

# dotnet-wpf-mvvm

Skill para migrar projetos WinForms para WPF com MVVM e para construir novas telas WPF
seguindo o padrao MVVM moderno com CommunityToolkit.Mvvm + WPF-UI.

Este arquivo contem o workflow, as decisoes e as armadilhas. Templates, exemplos de codigo e
guias detalhados ficam em `references/` (a tabela no fim diz quando ler cada um).

---

## Stack Recomendada

| Componente | Pacote NuGet | Funcao |
|-----------|-------------|--------|
| MVVM Framework | `CommunityToolkit.Mvvm` | ObservableObject, source generators |
| DI + Lifecycle | `Microsoft.Extensions.Hosting` | IHost, IServiceProvider |
| UI Framework | `WPF-UI` (Wpf.Ui) | Fluent Design, NavigationView, Theming |
| Navegacao | Wpf.Ui.INavigationService | MVVM-friendly page navigation |
| Dialogs | Wpf.Ui.IContentDialogService | Substitui MessageBox |

---

## Quando usar

- Migrar um Form WinForms para WPF com MVVM
- Adicionar MVVM a projeto WPF que usa code-behind
- Criar nova tela/pagina WPF com ViewModel
- Configurar navegacao entre paginas com DI
- Substituir event handlers por Commands
- Configurar DI em App.xaml.cs

---

## Pre-requisitos

Antes de aplicar MVVM, o projeto deve ter:

1. **Services desacoplados** — logica de negocio em classes `*Service.cs`, nao em Forms/code-behind
2. **Sem MessageBox em services** — services retornam `Result<T>` ou lancam excecoes
3. **Target framework .NET 8+** — source generators exigem .NET moderno

Se nao atende, use a skill `dotnet-desktop-setup` primeiro para desacoplar e configurar: o
ViewModel so orquestra chamadas a services que ja existem e expoe dados para a View.

---

## Workflow: 6 Passos

Execute os passos em ordem. Cada passo verifica o estado atual antes de agir.

### Passo 1: Diagnostico do Estado Atual

Avalie o projeto para entender o ponto de partida:

```bash
grep -r "UseWPF\|UseWindowsForms" *.csproj            # framework UI
grep -r "CommunityToolkit.Mvvm" *.csproj              # toolkit ja instalado?
grep -rn "_Click\|_Changed\|_Loaded\|_SelectionChanged" *.xaml.cs *.cs   # handlers a migrar
find . -name "*Service.cs" -type f                    # services existentes
grep -rn "MessageBox" --include="*Service.cs"         # MessageBox em service (anti-padrao)
```

Apresente o relatorio ao usuario:
- "Projeto X: WPF com WPF-UI, **sem MVVM**. 5 event handlers para migrar. 2 services existentes."
- "Pre-requisitos: OK" ou "Pre-requisitos: MessageBox encontrado em LicenseService.cs — desacoplar primeiro"

### Passo 2: Instalar Pacotes

```bash
dotnet add <projeto>.csproj package CommunityToolkit.Mvvm
dotnet add <projeto>.csproj package Microsoft.Extensions.Hosting
dotnet add <projeto>.csproj package WPF-UI   # so se WPF-UI ainda nao estiver instalado
```

Verifique que o `.csproj` tem `<UseWPF>true</UseWPF>`.

### Passo 3: Configurar App.xaml.cs como Composition Root

Leia `references/wpfui-integration.md` para o template completo de App.xaml.cs.

O App.xaml.cs cria o `IHost` com `Host.CreateDefaultBuilder()`; registra **todos** os services,
**todos** os ViewModels (Singleton com NavigationView — Detalhe #27), **todas** as Pages/Windows
(Transient ou Singleton conforme necessidade) e os services WPF-UI (INavigationService,
IContentDialogService, IThemeService); inicia o host em `OnStartup` e para em `OnExit`.

Padrao de registro:
```csharp
services.AddSingleton<ILicenseService, LicenseService>();  // services de negocio
services.AddSingleton<MainWindowViewModel>();  // VM Singleton: evita o leak do Detalhe #27
services.AddTransient<MainWindow>();           // Windows/Pages
```

App simples (1 janela, sem navegacao entre paginas): registro minimo e MainWindow +
MainWindowViewModel + services de negocio, sem INavigationService/IPageService.

### Passo 4: Criar ViewModels

Para cada tela, crie um ViewModel `partial` que herda `ObservableObject`, recebe os services
por injecao no construtor, expoe estado com `[ObservableProperty]` e acoes com `[RelayCommand]`
(o async com `try/finally` em volta de um `IsProcessando`). Leia
`references/communitytoolkit-patterns.md` antes de escrever o primeiro: o template base desta
etapa abre o arquivo, seguido dos patterns detalhados.

**Regras do source generator:**
- A classe deve ser `partial` — source generators precisam disso
- Campos `[ObservableProperty]` devem ser `private` — `_name` gera propriedade `Name`
- Metodos `[RelayCommand]` geram propriedade com sufixo `Command` — `Salvar()` gera `SalvarCommand`
- Metodos async geram `IAsyncRelayCommand` com cancelamento automatico

### Passo 5: Refatorar Views (XAML)

Substitua event handlers por bindings e commands:

```xml
<!-- Antes: Click="BtnCarregar_Click" + x:Name="txtNome", e no code-behind
     txtNome.Text = _service.Carregar(); -->
<Button Content="Carregar" Click="BtnCarregar_Click" />
<TextBox x:Name="txtNome" />

<!-- Depois (MVVM) -->
<Button Content="Carregar" Command="{Binding CarregarDadosCommand}" />
<TextBox Text="{Binding Titulo, UpdateSourceTrigger=PropertyChanged}" />
```
```csharp
// Code-behind fica so com DI wiring
public MainWindow(MainWindowViewModel viewModel) { InitializeComponent(); DataContext = viewModel; }
```

**Mapeamento rapido de controles:**

| WinForms / Code-behind | WPF MVVM |
|------------------------|----------|
| `button.Click += handler` | `Command="{Binding XCommand}"` |
| `textBox.Text = valor` | `Text="{Binding Propriedade}"` |
| `listBox.Items.Add(x)` | `ItemsSource="{Binding Lista}"` + `ObservableCollection<T>` |
| `checkBox.Checked += handler` | `IsChecked="{Binding Flag}"` |
| `comboBox.SelectedItem` | `SelectedItem="{Binding ItemSelecionado}"` |
| `label.Content = texto` | `Content="{Binding Texto}"` |
| `progressBar.Value` | `Value="{Binding Progresso}"` |
| `control.Enabled = false` | `IsEnabled="{Binding PodeExecutar}"` ou `CanExecute` no Command |
| `element.Visibility = Visible/Collapsed` | `Visibility="{Binding IsXxx, Converter={StaticResource BoolToVis}}"` |
| `comboBox.SelectedItem` (ComboBoxItem) | `SelectionChanged` handler ou `SelectedValue="{Binding Prop}"` com `SelectedValuePath` |
| `scrollViewer.ScrollToTop()` | `PropertyChanged` handler no code-behind (excecao MVVM documentada) |
| `Mouse.OverrideCursor = Wait` | `[ObservableProperty] bool IsLoading` + trigger ou converter no XAML |

**Dialogs MVVM-friendly:** em vez de `MessageBox.Show("Erro")`, file dialog com
`new Microsoft.Win32.OpenFileDialog { Filter = "HID files|*.hid" }` e
`if (dialog.ShowDialog() == true) CaminhoArquivo = dialog.FileName;`. Para dialogs complexos,
`IContentDialogService` do WPF-UI: leia `references/wpfui-integration.md` para registrar.

### Passo 6: Verificacao

1. **Build:** `dotnet build` sem erros nem warnings de source generators
2. **Testes:** `dotnet test` — os existentes passam (MVVM nao muda services)
3. **Code-behind limpo:** cada `.xaml.cs` so com `InitializeComponent()`, `DataContext = viewModel`
   (ou atribuicao via DI) e handlers UI-only (ex: Window closing, drag behavior)
4. **CLAUDE.md:** atualizar descricao do stack e arquitetura do projeto
5. **Funcionalidade:** testar manualmente que a UI funciona como antes
6. **Testes de ViewModel:** criar testes xUnit para o novo ViewModel (secao abaixo)

---

## Testes de ViewModel (Recomendacao)

Cada migracao MVVM inclui testes de ViewModel: blindam contra regressoes em refatoracoes,
testam a logica de apresentacao sem abrir janelas, rapidos e confiaveis no CI.

- **Commands com dialogs** — Command que abre `OpenFileDialog` nao e testavel unitariamente: ele
  chama o dialog e delega a um metodo publico testavel (`PopularCampos(HardwareInfo)`).
- **Reflection** — `typeof(Page).GetMethod("NomeMetodo", BindingFlags.NonPublic)` quebra quando o
  metodo vai para o ViewModel (`typeof(MinhaPage)` vira `typeof(MinhaPageViewModel)`).
  Identifique esses testes ANTES de mover codigo.
- Leia `references/viewmodel-testing.md` quando for escrever esses testes (o que testar, com
  exemplos, e o codigo do Command, do metodo testavel e do teste xUnit).
- **E2E** — smoke tests visuais em projetos com muitas telas: skill irma `dotnet-wpf-e2e-testing`
  (FlaUI + xUnit: setup, AutomationId, Page Objects e CI). Testes de ViewModel continuam aqui.

---

## Cenarios Comuns

- **WPF com code-behind (sem MVVM)** — o mais comum. Os 6 passos; o Passo 4 (extrair logica dos handlers para ViewModels) e o mais trabalhoso.
- **WinForms** — leia `references/migration-winforms-to-wpf.md` antes de comecar. Fase A: Form vira Window/Page (XAML equivalente ao layout); Fase B: MVVM (Passos 3-6). Form-a-form (Strangler Fig), nunca tudo de uma vez.
- **Novo projeto do zero** — leia `references/project-structure.md` para a estrutura de pastas; crie Models/Views/ViewModels/Services antes de codar. Passo 2, Passo 3 (DI), depois ViewModels e Views.
- **Navegacao entre paginas** — `INavigationService` + `IPageService` do WPF-UI; leia a secao NavigationView de `references/wpfui-integration.md` para configurar.

---

## Detalhes Criticos (armadilhas)

| # | Armadilha | Regra |
|---|-----------|-------|
| 1 | Classe sem `partial` | `[ObservableProperty]` e `[RelayCommand]` nao geram codigo e o build falha |
| 2 | Campo `[ObservableProperty]` publico | O campo e `private`: `_nomeDoNavio` gera `NomeDoNavio`; publico conflita |
| 3 | Dialog WinForms em projeto WPF | `Microsoft.Win32.OpenFileDialog`/`SaveFileDialog`, nao os de System.Windows.Forms |
| 4 | `[ObservableProperty]` em `ObservableCollection<T>` | Desnecessario: `public ObservableCollection<Item> Items { get; } = new();` ja implementa `INotifyCollectionChanged` |
| 5 | CLAUDE.md desatualizado apos migrar | Referencias a Form*.cs envelhecem: atualize stack, nomes de arquivos UI e tabela de projetos |
| 6 | CanExecute | `[RelayCommand(CanExecute = nameof(PodeSalvar))]` + `SalvarCommand.NotifyCanExecuteChanged()` quando a condicao mudar |
| 7 | Async command | Metodo que retorna `Task` gera `IAsyncRelayCommand`: desabilita o botao durante a execucao e suporta cancelamento |
| 8 | String sem inicializar | `private string _nome = string.Empty;`; sem isso bindings podem receber null (warnings ou comportamento inesperado) |
| 9 | MessageBox em app simples | Em 1-2 telas, `StatusMessage` na barra de status e mais simples e testavel que `IDialogService`; `IContentDialogService` fica para multiplas telas ou dialogs complexos |
| 10 | Icone pixelado em FluentWindow | `Icon=` no XAML e `BitmapImage` carregam o menor frame do .ico; use `BitmapDecoder` (maior resolucao) e declare o .ico como `<ApplicationIcon>` E `<Resource>` no .csproj |

Leia a secao "Icone da Aplicacao" de `references/wpfui-integration.md` para aplicar o #10.

| # | WPF-UI 4.2.0 | Regra |
|---|--------------|-------|
| 11 | `ui:Page` NAO existe | `<Page>` padrao (`System.Windows.Controls`); code-behind herda `Page`, NAO `INavigableView<T>` |
| 12 | `INavigationViewPageProvider` | Esta em `Wpf.Ui.Abstractions` (NAO em `Wpf.Ui` nem `Wpf.Ui.Controls`); `GetPage(Type pageType)` retorna `object?` |
| 13 | `MessageBoxButton` conflita | `using MessageBoxButton = System.Windows.MessageBoxButton;` e `using MessageBoxImage = System.Windows.MessageBoxImage;` |
| 14 | `Wpf.Ui.Controls` global | Conflita com `System.Windows.Controls` (TextBox, ComboBox, Page, Button, `MessageBoxButton`). Qualifique (`: Wpf.Ui.Controls.FluentWindow`) ou use alias (`using ControlAppearance = Wpf.Ui.Controls.ControlAppearance;`) |
| 15 | PageService e manual | Sem implementacao built-in: `PageService(IServiceProvider sp)` com `GetPage(Type) => sp.GetService(pageType)`; setup `RootNavigation.SetPageProviderService(pageProvider)` (NAO `SetPageService()`) |
| 16 | Action items do NavigationView | Sem `TargetPageType` (Browse/Upload), nem `ItemInvoked` nem `SelectionChanged` disparam: `PreviewMouseLeftButtonUp` no item, com `e.Handled = true` |

**17 a 26 — listas grandes, performance e UI.** Leia `references/performance-patterns.md` quando a
Page tiver lista grande, filtro digitado ou WindowsFormsHost (texto completo e codigo): **17**
DataGrid com `AutoGenerateColumns="False"`, coluna oculta nao e declarada; **18** o NavigationView
da altura infinita a Page e ListBox/DataGrid/ListView renderiza TODOS os items: `MaxHeight` +
`Page_SizeChanged`; **19** Page pesada como `Singleton` (a `Transient` e reconstruida a cada
navegacao), com `ReloadData()`; **20** `WindowBackdropType="None"` com WindowsFormsHost (`Mica`
deixa controles WinForms **invisiveis**, bug documentado pela Microsoft); **21** `Page.Resources`
antes do conteudo, senao `StaticResource` falha em runtime ("StaticResourceExtension"); **22**
`SolidColorBrush.Freeze()` em brushes estaticos (thread-safety); **23** 100K+ linhas: `List<T>`
tipado + LINQ em background, nao `DataView.RowFilter` (reflexao, NAO thread-safe; se usar, copie o
DataTable antes; `DefaultView` compartilhado entre consumidores causa race conditions); **24**
debounce de 300ms com `CancellationTokenSource` no filtro; **25** cache `??=` em propriedade
formatada lida a cada frame; **26** caches estaticos como `IReadOnlyList<T>`, nao `List<T>`.

27. **Lifecycle mismatch: Transient VM + Singleton Service = memory leak** — VM `Transient` que
    assina `PropertyChanged` de servico Singleton (ex: IAppStateService) ganha instancia nova a
    cada navegacao, nunca dessubscrita: o Singleton guarda delegates de instancias mortas e o GC
    nao as coleta. Com NavigationView (paginas recriadas a cada navegacao) o leak e cumulativo.
    **Fix preferido:** ViewModels como Singleton (consistente com #19). Alternativas:
    `IDisposable` com unsubscribe, ou `WeakEventManager` (requer `System.Windows`, o que viola a
    separacao ViewModel/UI).
28. **Visibility bindings esquecidos ao migrar handlers** — ao trocar Click handlers que
    alternavam `Visibility` por Commands, e comum criar `IsXxxVisible` no VM e esquecer
    `Visibility="{Binding IsXxxVisible, Converter={StaticResource BoolToVis}}"` no XAML: o Command
    executa e nada muda na tela. Audite o XAML depois de converter handlers de visibilidade.

---

## Anti-padroes desta Skill

| Anti-padrao | Por que e o que fazer |
|-------------|-----------------------|
| ViewModel referenciando UI | Nao importa `System.Windows` nem acessa controles da View: e isso que o mantem testavel sem abrir janela. Use bindings, Messenger (eventos pontuais) ou `IAppStateService` (secao abaixo) |
| Logica de negocio no ViewModel | ViewModel orquestra, Service executa: IO, parsing ou calculo complexo vao para um Service |
| `new ViewModel()` no XAML | Funciona, mas impede DI; injete via construtor |
| Ignorar UpdateSourceTrigger | O default do `TextBox` e `LostFocus`; use `UpdateSourceTrigger=PropertyChanged` para validacao em tempo real |
| `List<T>` em vez de `ObservableCollection<T>` | `List` nao notifica a View quando itens sao adicionados/removidos |
| DataGrid/ListView para listas grandes (>5K items) | Travam dentro de NavigationView mesmo com virtualizacao. ListBox com paginacao (500 items/pagina) ou Page Singleton; nunca confie so na virtualizacao sem testar |
| DataView.RowFilter em background thread | DataView NAO e thread-safe (Detalhe #23) |
| SymbolIcons inexistentes | Nem todo icone da documentacao existe no WPF-UI 4.2.0 (ex.: `SignalStrength24`, `PlugConnected24`); teste em runtime antes de commitar |
| `async void` fora de event handler | Fora de handlers UI (Click, Loaded) a excecao nao e observada e pode crashar a app. Use `async Task` e `await` no chamador; `[RelayCommand]` ja gera `IAsyncRelayCommand` com `async Task`, nunca converta para `async void` |
| ContentDialogPresenter no XAML | O elemento correto e `<ui:ContentDialogHost>`, nao `<ui:ContentPresenter>` ou `<ui:ContentDialogPresenter>`; erro comum que causa crash |
| ShowSimpleDialogAsync sem using | E extension method em `Wpf.Ui.Extensions`: requer `using Wpf.Ui.Extensions;` |
| `new Service()` dentro do ViewModel | Impede mocking e viola inversao de dependencias; injete via construtor. Thin wrapper (ex: `new UsuariosServicos(repo)`): injete a interface subjacente (`IUsuariosRepositorio`) e chame `_repo.Salvar()` |
| Remover error handling ao migrar handlers | O `try/catch` com `MessageBox.Show()` do Click handler some na migracao para `[RelayCommand]` e a falha e engolida sem feedback. Preserve o error path: `StatusMessage` ou `IContentDialogService` no catch |

---

## Checklist Pre-Migracao de Pagina

Antes de migrar cada Page para MVVM, audite o code-behind:

1. **Event handlers** — listar todos (Click, Loaded, TextChanged, SelectionChanged, KeyDown).
2. **Visibilidade por codigo** — `element.Visibility = Visible/Collapsed` pede binding com
   `BooleanToVisibilityConverter`. Facil de esquecer (Detalhe #28).
3. **ComboBox com selecao logica** — se a selecao afeta comportamento (ex: tipo de filtro),
   precisa de binding ou `SelectionChanged` handler que atualiza o ViewModel.
4. **Error handling em handlers** — `try/catch` com MessageBox vira `StatusMessage` ou
   `IContentDialogService` no ViewModel, nunca remocao silenciosa.
5. **Custom controls imperativos** — API `GetValue()/SetValue()/SetDate()` sem
   DependencyProperties nao suporta binding (secao "Estado Compartilhado e Custom Controls").
6. **Operacoes visuais** — `ScrollToTop()`, `Focus()`, `Mouse.OverrideCursor` ficam no
   code-behind como excecao MVVM documentada (a mesma da tabela do Passo 5).
7. **Testes com reflection** — `typeof(Page).GetMethod()` em metodo privado quebra quando o
   metodo vai para o ViewModel; atualize o `typeof` apos mover.

---

## Estado Compartilhado e Custom Controls

- **Estado compartilhado** — estado central que varios VMs leem (dados carregados, modo, filtros,
  usuario logado) vai num `IAppStateService` Singleton com `INotifyPropertyChanged`; evento
  pontual entre VMs ou notificacao de navegacao vai no `IMessenger` (WeakReferenceMessenger).
  VMs que assinam o `PropertyChanged` dele tambem sao Singleton (Detalhe #27). Leia a secao
  "Estado Compartilhado (IAppStateService)" de `references/mvvm-fundamentals.md` quando for
  desenhar o estado.
- **Custom Controls** — UserControl custom sem `DependencyProperty` para o valor principal (API
  imperativa `GetValue()/SetValue()/SetDate()/GetDay()`) nao aceita binding bidirecional. Leia
  `references/custom-controls-binding.md` antes de planejar a migracao de Page que os usa.

---

## Guias de Referencia (progressive disclosure level 3)

Leia estes arquivos **somente quando necessario** no passo correspondente:

| Arquivo | Leia quando... |
|---------|----------------|
| `references/mvvm-fundamentals.md` | Quando o usuario for novo em MVVM ou for usar Messenger/IAppStateService |
| `references/communitytoolkit-patterns.md` | No Passo 4, para criar ViewModels com source generators |
| `references/wpfui-integration.md` | No Passo 3, para configurar DI, navegacao, dialogs e theming com WPF-UI |
| `references/migration-winforms-to-wpf.md` | Quando o projeto for WinForms e precisar migrar para WPF |
| `references/project-structure.md` | Quando criar projeto do zero ou reorganizar pastas |
| `references/viewmodel-testing.md` | Ao escrever testes de ViewModel (Command com dialog, reflection) |
| `references/custom-controls-binding.md` | Antes de migrar Page com UserControls custom sem DependencyProperty |
| `references/performance-patterns.md` | Quando houver lista grande, filtro digitado ou WindowsFormsHost (Detalhes #17-#26) |
