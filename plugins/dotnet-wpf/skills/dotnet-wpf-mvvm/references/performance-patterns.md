# Performance, listas grandes e detalhes de UI

Texto completo, com codigo, dos Detalhes Criticos #17 a #26 do SKILL.md (a numeracao e a mesma).
Leia quando a Page tiver DataGrid/ListBox com muitos itens, filtro que trava a UI,
WindowsFormsHost, ou quando um desses detalhes do SKILL.md pedir o exemplo.

---

17. **DataGrid: usar `AutoGenerateColumns="False"`** — definir colunas explicitamente em XAML
    para controlar visibilidade, headers e formatacao. Colunas que nao devem aparecer simplesmente
    nao sao declaradas (mais limpo que `Visibility="Collapsed"` em cada coluna).

18. **NavigationView quebra virtualizacao** — o NavigationView do WPF-UI internamente usa layout
    que da **altura infinita** as paginas. Qualquer ListBox/DataGrid/ListView dentro de uma Page
    recebe ActualHeight infinito e renderiza TODOS os items (virtualizacao desabilitada).
    Fix: usar `MaxHeight` fixo + `Page_SizeChanged` para ajustar dinamicamente:
    ```csharp
    private void Page_SizeChanged(object sender, SizeChangedEventArgs e)
    {
        if (dgvLog != null && e.NewSize.Height > 100)
            dgvLog.MaxHeight = e.NewSize.Height - 120;
    }
    ```

19. **Singleton para paginas pesadas** — Pages registradas como `Transient` sao recriadas a cada
    navegacao (visual tree, bindings, tudo reconstruido). Para paginas com dados grandes, registrar
    como `Singleton` no DI evita reconstrucao e mantem estado de scroll/filtro. Adicionar metodo
    `ReloadData()` para resetar quando novos dados sao carregados.

20. **WindowBackdropType="None" com WindowsFormsHost** — `Mica` habilita transparencia
    internamente, o que torna controles WinForms (via WindowsFormsHost) **invisiveis**. Bug
    documentado pela Microsoft. Usar `WindowBackdropType="None"` se WindowsFormsHost for necessario.

21. **Page.Resources antes do conteudo** — declarar `<Page.Resources>` com Styles/converters
    antes do conteudo XAML (DockPanel, Grid, etc). Se declarado depois, `StaticResource` falha
    com erro "StaticResourceExtension" em runtime.

22. **SolidColorBrush.Freeze()** — brushes estaticos devem ser frozen para thread-safety:
    ```csharp
    private static SolidColorBrush CreateFrozenBrush(byte r, byte g, byte b)
    {
        var brush = new SolidColorBrush(Color.FromRgb(r, g, b));
        brush.Freeze();
        return brush;
    }
    ```

23. **LINQ filter em POCOs em vez de DataView.RowFilter** — para listas grandes (100K+),
    converter DataTable para `List<T>` tipado em background e filtrar com LINQ e mais rapido
    e thread-safe que DataView.RowFilter (que usa reflexao e nao e thread-safe).

24. **Debounce para filtros** — em TextBoxes de filtro, usar debounce de 300ms com
    `CancellationTokenSource` para filtrar enquanto o usuario digita sem travar a UI:
    ```csharp
    _filterCts?.Cancel();
    _filterCts?.Dispose();
    _filterCts = new CancellationTokenSource();
    _ = Task.Delay(300, _filterCts.Token).ContinueWith(t => {
        if (!t.IsCanceled) Dispatcher.Invoke(ApplyFilter);
    });
    ```

25. **Lazy property caching com ??=** — para propriedades formatadas chamadas repetidamente
    pelo binding (ex: DateTimeFormatted), usar lazy initialization para evitar ToString() em
    cada frame de renderizacao:
    ```csharp
    private string? _formatted;
    public string Formatted => _formatted ??= DateTime.ToString("dd/MM/yyyy HH:mm:ss");
    ```

26. **IReadOnlyList para caches** — expor caches estaticos como `IReadOnlyList<T>` em vez de
    `List<T>` para prevenir modificacao acidental por consumidores.
