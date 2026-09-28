# Cookbook — receitas completas

Receitas do indice "Cookbook" do SKILL.md que nao tem casa em outra reference: exemplos XAML/C#
completos, errado vs correto, e o porque de cada correcao. Leia a secao do ID quando for aplicar a
correcao que o indice apontou. As receitas LAYOUT-001/002/003, FORM-003, BRAND-001, CTRL-004 a
CTRL-007 e RES-001 vivem em `layout-patterns.md`, `form-design.md` e `wpfui-theming-overrides.md`
(o SKILL.md roteia cada uma). "Anti-padrao #N" e "Detalhe Critico #N" apontam para as listas
numeradas do SKILL.md.

## Sumario

- [FORM-001: Espacamento entre campos de formulario](#form-001-espacamento-entre-campos-de-formulario)
- [FORM-002: Sizing minimo de controles](#form-002-sizing-minimo-de-controles)
- [FORM-004: Separador sutil entre grupos de campos em Grid](#form-004-separador-sutil-entre-grupos-de-campos-em-grid)
- [THEME-001: DynamicResource brushes vs cores hardcoded](#theme-001-dynamicresource-brushes-vs-cores-hardcoded)
- [TYPO-001: Tipografia consistente com Type Ramp](#typo-001-tipografia-consistente-com-type-ramp)
- [CTRL-001: Catalogo de controles WPF-UI](#ctrl-001-catalogo-de-controles-wpf-ui)
- [CTRL-002: ControlAppearance — semantica de cores em botoes](#ctrl-002-controlappearance--semantica-de-cores-em-botoes)
- [CTRL-003: SymbolIcon sharing bug em DataGrid](#ctrl-003-symbolicon-sharing-bug-em-datagrid)
- [CTRL-008: ContentDialog para confirmar acoes destrutivas (guard before mutate)](#ctrl-008-contentdialog-para-confirmar-acoes-destrutivas-guard-before-mutate)
- [DRY-001: Estilo compartilhado para aba ativa (toolbars/tabs)](#dry-001-estilo-compartilhado-para-aba-ativa-toolbarstabs)

---

## FORM-001: Espacamento entre campos de formulario

**Problema:** Campos de formulario muito juntos, sem respiro visual.

**Solucao Fluent Design:**

| Contexto | Margin recomendado |
|----------|--------------------|
| Entre campos (row margin) | `Margin="0,12,0,0"` (compacto) ou `Margin="0,24,0,0"` (padrao) |
| Entre grupos/secoes | `Margin="0,32,0,0"` ou `Margin="0,48,0,0"` |
| Padding de secao (Border) | `Padding="16,12,16,16"` |
| Entre botoes | `Margin="0,0,8,0"` |
| Entre label e campo (vertical) | `Margin="0,0,0,8"` no label |

**Antes (apertado):**
```xml
<RowDefinition Height="Auto" />  <!-- Margin="0,4" = 4px, muito pouco -->
<TextBlock Margin="0,4" />
```

**Depois (confortavel):**
```xml
<RowDefinition Height="Auto" />  <!-- Margin="0,12" = 12px compacto -->
<TextBlock Margin="0,12,0,0" />  <!-- ou Margin="0,8" para 8px simetrico -->
```

Detalhes em `form-design.md` (roteado pelo SKILL.md).

---

## FORM-002: Sizing minimo de controles

**Problema:** TextBox, ComboBox ou controles customizados muito pequenos,
texto cortado ou ilegivel.

**Valores minimos recomendados:**

| Controle | MinHeight | MinWidth | FontSize |
|----------|-----------|----------|----------|
| TextBox | 32px | — | 14px (Body) |
| ComboBox | 32px | 100px | 14px |
| ToggleButton | 28px | 48px | 12px (Caption) |
| UserControl (date/time) | 32px | — | 13-14px |
| ComboBox (mes abreviado) | 32px | 80px | 13px |
| TextBox (2 digitos) | 32px | 40px | 13px |
| TextBox (4 digitos) | 32px | 55px | 13px |

**Exemplo — controle de data (Day / Month / Year):**

```xml
<!-- ✅ Auto-tamanho: o UserControl cresce conforme o filho mais alto -->
<UserControl>
    <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
        <TextBox  Width="40" FontSize="13" />
        <TextBlock Text="/" Margin="4,0" FontSize="13" />
        <!-- Height>=36 para FontSize=13 nao clipar texto Fluent verticalmente -->
        <ComboBox Width="80" FontSize="13" Height="36" />
        <TextBlock Text="/" Margin="4,0" FontSize="13" />
        <TextBox  Width="55" FontSize="13" />
    </StackPanel>
</UserControl>
```

⚠️ **Armadilha frequente:** colocar `Height="32"` no `<UserControl>` parece "padronizar" a
altura, mas a `FontSize="13"` o `ComboBox` Fluent (WPF-UI) precisa de **~36px** para
renderizar abreviacoes como "Jan."/"Feb."/"Mar." sem cortar o caractere final. Resultado:
o texto fica visualmente clipado e o instinto e aumentar `Width` — que NAO resolve, porque
o problema e altura, nao largura. Veja Anti-padrao #8 e Detalhe Critico #9 no SKILL.md.

Recomendado:
- **Nao** definir `Height` no `<UserControl>` (deixar auto-tamanho); ou
- Definir `MinHeight` (nao `Height`) no UserControl, e/ou
- Garantir que o filho problematico (geralmente o `ComboBox`) tenha `Height` explicito
  suficiente para o `FontSize` em uso.

Detalhes em `controls-sizing.md` (roteado pelo SKILL.md).

---

## FORM-004: Separador sutil entre grupos de campos em Grid

**Problema:** Em formularios densos com muitos campos dentro de um unico `SectionBorder`,
grupos logicos de campos (ex: dados de identificacao vs datas de validade) ficam colados
sem distincao visual. Usar um `Border` com `BorderThickness="1"` e `CornerRadius="4"`
(estilo "box") envolve o grupo inteiro e destoa do design flat/clean do resto do formulario.

**Solucao:** Usar um `Border` fino em sua **propria RowDefinition dedicada** dentro do Grid,
com apenas a borda bottom (`BorderThickness="0,0,0,1"`) e `Margin="0,8"` para respiro
simetrico. Isso cria uma linha horizontal sutil que separa grupos sem "encaixotar".

```xml
<Grid>
    <Grid.RowDefinitions>
        <RowDefinition Height="Auto" />  <!-- Row N: ultimo campo do grupo A -->
        <RowDefinition Height="Auto" />  <!-- Row N+1: SEPARADOR (row dedicada) -->
        <RowDefinition Height="Auto" />  <!-- Row N+2: primeiro campo do grupo B -->
    </Grid.RowDefinitions>

    <!-- ... campos do grupo A ... -->

    <!-- Row N+1: Separador sutil -->
    <Border Grid.Row="N+1" Grid.Column="0" Grid.ColumnSpan="3"
            BorderBrush="{DynamicResource DividerStrokeColorDefaultBrush}"
            BorderThickness="0,0,0,1" Margin="0,8" />

    <!-- ... campos do grupo B ... -->
</Grid>
```

**Regras:**
- **Sempre use row dedicada** para o separador — nunca compartilhe a row com conteudo.
  Compartilhar causa sobreposicao porque o `Margin` do Border compete com o conteudo da
  mesma row.
- `Margin="0,8"` da 8px acima e abaixo da linha — respiro confortavel sem exagero.
  Aumente para `Margin="0,12"` se precisar de mais respiro.
- Use `DividerStrokeColorDefaultBrush` (nao `ControlStrokeColorDefaultBrush`) — e mais
  sutil, projetado para separadores.
- `ColumnSpan` deve cobrir todas as colunas do Grid.

**Anti-padrao: Border na mesma row que conteudo**

```xml
<!-- ❌ ERRADO: Border na mesma row que o TextBlock — sobrepoe o texto -->
<TextBlock Grid.Row="6" Grid.Column="1" Text="Descricao..." />
<Border Grid.Row="6" Grid.Column="0" Grid.ColumnSpan="3"
        BorderThickness="0,0,0,1" Margin="0,16,0,16" />
<!-- O Margin do Border expande a row e o texto fica atras da linha -->

<!-- ✅ CORRETO: Border em row propria -->
<TextBlock Grid.Row="6" Grid.Column="1" Text="Descricao..." />
<Border Grid.Row="7" Grid.Column="0" Grid.ColumnSpan="3"
        BorderThickness="0,0,0,1" Margin="0,8" />
<TextBlock Grid.Row="8" Grid.Column="0" Text="Proximo campo..." />
```

---

## THEME-001: DynamicResource brushes vs cores hardcoded

**Problema:** Cores como `#B0B0B0`, `#555`, `#444` hardcoded no XAML nao acompanham
mudancas de tema e podem ter contraste inadequado.

**Solucao:** Usar DynamicResource com brushes do WPF-UI:

```xml
<!-- Antes (hardcoded) -->
<TextBlock Foreground="#B0B0B0" />
<Border BorderBrush="#555" />

<!-- Depois (theme-aware) -->
<TextBlock Foreground="{DynamicResource TextFillColorSecondaryBrush}" />
<Border BorderBrush="{DynamicResource ControlStrokeColorDefaultBrush}" />
```

**Mapeamento de cores comuns:**

| Hardcoded | DynamicResource equivalente |
|-----------|-----------------------------|
| `#B0B0B0` (label) | `TextFillColorSecondaryBrush` |
| `#555` (borda) | `ControlStrokeColorDefaultBrush` |
| `#444` (separador) | `DividerStrokeColorDefaultBrush` |
| `White` (texto) | `TextFillColorPrimaryBrush` |
| `#2D2D30` (card bg) | `CardBackgroundFillColorDefaultBrush` |

Detalhes em `wpfui-components.md` (roteado pelo SKILL.md).

---

## TYPO-001: Tipografia consistente com Type Ramp

**Problema:** FontSize inconsistente entre controles, headers, labels.

**Solucao:** Seguir o type ramp do Windows 11:

```xml
<!-- Titulo da pagina -->
<TextBlock FontSize="28" FontWeight="SemiBold" />  <!-- Title -->

<!-- Header de secao -->
<TextBlock FontSize="14" FontWeight="SemiBold" />  <!-- Body Strong -->

<!-- Label de campo -->
<TextBlock FontSize="14" />  <!-- Body -->

<!-- Texto auxiliar / hint -->
<TextBlock FontSize="12" />  <!-- Caption -->
```

**Com WPF-UI (preferivel):**
```xml
<ui:TextBlock FontTypography="Title" Text="Titulo" />
<ui:TextBlock FontTypography="BodyStrong" Text="Secao" />
<ui:TextBlock FontTypography="Body" Text="Label" />
<ui:TextBlock FontTypography="Caption" Text="Hint" />
```

Detalhes em `typography-colors.md` (roteado pelo SKILL.md).

---

## CTRL-001: Catalogo de controles WPF-UI

**Problema:** O projeto usa controles WPF padrao (TextBox, ComboBox) quando existem
equivalentes WPF-UI com funcionalidades extras (PlaceholderText, Icon, ClearButton).

**Controles mais uteis para formularios:**

| Controle WPF-UI | Substitui | Vantagem |
|------------------|-----------|----------|
| `ui:TextBox` | TextBox | PlaceholderText, Icon, ClearButtonEnabled |
| `ui:NumberBox` | TextBox (numerico) | Validacao, Min/Max, SpinButtons, MaxDecimalPlaces |
| `ui:AutoSuggestBox` | TextBox + filtro | Dropdown de sugestoes, busca integrada |
| `ui:ToggleSwitch` | CheckBox/ToggleButton | On/Off semantico, OnContent/OffContent |
| `ui:CalendarDatePicker` | UserControl custom | Calendario popup nativo |
| `ui:ContentDialog` | MessageBox.Show() | Modal async, DI-friendly, Fluent styled |
| `ui:Snackbar` | — | Toast temporario para feedback (sucesso/erro) |

Catalogo completo com exemplos XAML em `wpfui-controls-catalog.md` (roteado pelo SKILL.md).

---

## CTRL-002: ControlAppearance — semantica de cores em botoes

**Problema:** Botoes importantes (Export PDF, Delete) nao se distinguem visualmente.

**Solucao:** Usar `Appearance` nos `ui:Button`:

```xml
<ui:Button Content="Export PDF" Appearance="Primary" />   <!-- Accent color -->
<ui:Button Content="Delete" Appearance="Danger" />        <!-- Vermelho -->
<ui:Button Content="Save" Appearance="Success" />         <!-- Verde -->
<ui:Button Content="Warning" Appearance="Caution" />      <!-- Laranja -->
<ui:Button Content="Cancel" Appearance="Secondary" />     <!-- Neutro -->
```

Valores disponiveis: Primary, Secondary, Info, Dark, Light, Danger, Success, Caution, Transparent.

---

## CTRL-003: SymbolIcon sharing bug em DataGrid

**Problema:** Em um `DataGridTemplateColumn`, usar `SymbolIcon` dentro de `Style.Setter.Value`
com `DataTrigger` faz o icone aparecer em apenas UMA linha (a ultima renderizada). As demais
linhas ficam vazias.

**Causa raiz:** WPF cria uma unica instancia de `SymbolIcon` no `Setter.Value`. Como um
UIElement so pode ter um pai visual, cada nova linha "rouba" o icone da anterior.

**Errado (icone compartilhado):**
```xml
<DataGridTemplateColumn Header="Level">
    <DataGridTemplateColumn.CellTemplate>
        <DataTemplate>
            <ContentControl>
                <ContentControl.Style>
                    <Style TargetType="ContentControl">
                        <Setter Property="Content">
                            <Setter.Value>
                                <!-- UMA instancia para TODAS as linhas! -->
                                <ui:SymbolIcon Symbol="Info24" Foreground="#3B82F6" />
                            </Setter.Value>
                        </Setter>
                        <Style.Triggers>
                            <DataTrigger Binding="{Binding Type}" Value="Warning">
                                <Setter Property="Content">
                                    <Setter.Value>
                                        <ui:SymbolIcon Symbol="Warning24" Foreground="#F59E0B" />
                                    </Setter.Value>
                                </Setter>
                            </DataTrigger>
                        </Style.Triggers>
                    </Style>
                </ContentControl.Style>
            </ContentControl>
        </DataTemplate>
    </DataGridTemplateColumn.CellTemplate>
</DataGridTemplateColumn>
```

**Correto (icones por linha com Visibility):**
```xml
<DataGridTemplateColumn Header="Level" Width="70">
    <DataGridTemplateColumn.CellTemplate>
        <DataTemplate>
            <Grid HorizontalAlignment="Center" VerticalAlignment="Center">
                <ui:SymbolIcon x:Name="InfoIcon" Symbol="Info24"
                               FontSize="16" Foreground="#3B82F6" Visibility="Visible" />
                <ui:SymbolIcon x:Name="WarningIcon" Symbol="Warning24"
                               FontSize="16" Foreground="#F59E0B" Visibility="Collapsed" />
                <ui:SymbolIcon x:Name="SevereIcon" Symbol="ErrorCircle24"
                               FontSize="16" Foreground="#EF4444" Visibility="Collapsed" />
            </Grid>
            <DataTemplate.Triggers>
                <DataTrigger Binding="{Binding Type}" Value="Warning">
                    <Setter TargetName="InfoIcon" Property="Visibility" Value="Collapsed" />
                    <Setter TargetName="WarningIcon" Property="Visibility" Value="Visible" />
                </DataTrigger>
                <DataTrigger Binding="{Binding Type}" Value="Severe">
                    <Setter TargetName="InfoIcon" Property="Visibility" Value="Collapsed" />
                    <Setter TargetName="SevereIcon" Property="Visibility" Value="Visible" />
                </DataTrigger>
            </DataTemplate.Triggers>
        </DataTemplate>
    </DataGridTemplateColumn.CellTemplate>
</DataGridTemplateColumn>
```

**Por que funciona:** Cada linha recebe sua propria instancia do DataTemplate. Os 3 icones
sao criados por linha, empilhados em Grid, e `DataTemplate.Triggers` alterna `Visibility`.
Sem compartilhamento de UIElement.

**Regra geral:** Nunca coloque UIElements (SymbolIcon, Image, Border, etc.) em `Setter.Value`
de um Style dentro de DataTemplate. Use `DataTemplate.Triggers` com `Visibility` ou
`ContentTemplate` (que cria instancias por uso).

---

## CTRL-008: ContentDialog para confirmar acoes destrutivas (guard before mutate)

**Problema:** Botoes que sobrescrevem o estado da UI (Load Last Export, Reset Form,
Restore Defaults, Discard Changes) executam direto. Um clique acidental apaga
trabalho do usuario sem chance de desfazer — snackbar de "sucesso" depois nao ajuda.

**Solucao:** Mostrar `ContentDialog` Fluent **antes** de qualquer leitura de I/O ou
mutacao do view-model. Se o usuario cancelar, retornar imediatamente — nada e
tocado, nada e lido. O custo e um clique extra; o ganho e que a acao vira reversivel
por padrao.

```csharp
private async void BtnLoadLastExport_Handler()
{
    // Guard antes de qualquer leitura/mutacao. Cancelar => preserva o trabalho atual.
    var confirm = await _contentDialogService.ShowSimpleDialogAsync(new SimpleContentDialogCreateOptions
    {
        Title = "Load Last Export",
        Content = "This will replace the current form data with the last exported report. "
                + "Any unsaved changes will be lost.\n\nDo you want to continue?",
        PrimaryButtonText = "Replace data",
        CloseButtonText = "Cancel"
    });
    if (confirm != ContentDialogResult.Primary) return;

    // ... so agora le do disco e chama _viewModel.SetSharedData(...) etc.
}
```

**Regras do padrao:**

1. **Confirmar antes de qualquer side-effect.** A chamada do diálogo é a primeira
   linha do handler. Não leia arquivo, nem chame service, nem mude flag — se o
   usuário cancelar, o estado anterior tem que estar 100% intacto.
2. **`ContentDialogResult.Primary` = confirmou; qualquer outro valor = cancelou.**
   `Close` (botão Cancel ou tecla Esc) e `None` (clique fora, se permitido) caem no
   mesmo `return`. Não tente diferenciar — o usuário não confirmou, ponto.
3. **Texto do botão Primary descreve a ação, não "OK".** "Replace data", "Discard
   changes", "Delete report" — o usuário precisa ler o botão e saber o que vai
   acontecer. Evite "Yes/No" genérico (Fluent guidance).
4. **Use `Appearance="Danger"` no Primary se a ação for irreversível** (delete,
   force-overwrite de arquivo). Para overwrite de UI in-memory (caso acima), o
   default já basta — não precisa pintar de vermelho.

**Sempre confirmar vs. so quando "dirty":** dirty-tracking parece a solucao limpa,
mas exige snapshot do estado original + comparacao confiavel a cada interacao —
escopo grande, alto risco de false-negatives (que recriam o bug original). Se o
estado raramente esta vazio (formulario auto-preenchido apos analise, lista
populada por API, etc.), **sempre confirmar** e o trade-off correto: 1 clique
extra contra trabalho perdido. Implementar dirty-tracking so se a confirmacao
realmente cria friccao mensuravel no fluxo principal.

**Onde mora:** code-behind da Page (`*Page.xaml.cs`), nao no ViewModel. Pelas
regras de UI decoupling, dialogs vivem na camada UI — o command do ViewModel
dispara um evento, o code-behind escuta, mostra o diálogo e só chama de volta o
`viewModel.DoTheThing()` se confirmado.

**`using` necessario:** o tipo `ContentDialogResult` mora em `Wpf.Ui.Controls` e
quase sempre conflita com `System.Windows.Controls`. Adicione um alias seguindo o
padrão dos outros tipos da WPF-UI no arquivo (veja Detalhe Critico #7 no SKILL.md):
```csharp
using ContentDialogResult = Wpf.Ui.Controls.ContentDialogResult;
```

---

## DRY-001: Estilo compartilhado para aba ativa (toolbars/tabs)

**Problema:** Paginas com toolbar de 3-5 botoes que destacam a aba ativa acabam
com `<ui:Button.Style>` inline duplicado. Cada botao tem 9 linhas de XAML identicas
variando so o Binding path — multiplicado pelo numero de abas e de paginas.

```xml
<!-- ❌ ANTES: 9 linhas de Style inline por botao, repetido em cada aba -->
<ui:Button Content="VDR Form" Command="{Binding ShowVDRFormCommand}">
    <ui:Button.Style>
        <Style TargetType="ui:Button" BasedOn="{StaticResource {x:Type ui:Button}}">
            <Setter Property="Appearance" Value="Secondary" />
            <Style.Triggers>
                <DataTrigger Binding="{Binding IsTestReportVisible}" Value="True">
                    <Setter Property="Appearance" Value="Primary" />
                </DataTrigger>
            </Style.Triggers>
        </Style>
    </ui:Button.Style>
</ui:Button>
```

**Solucao:** Um Style compartilhado em `App.xaml` + `Tag` binding:

```xml
<!-- App.xaml -->
<Style x:Key="ActiveTabButton" TargetType="ui:Button"
       BasedOn="{StaticResource {x:Type ui:Button}}">
    <Setter Property="Appearance" Value="Secondary" />
    <Style.Triggers>
        <DataTrigger Binding="{Binding RelativeSource={RelativeSource Self}, Path=Tag}"
                     Value="True">
            <Setter Property="Appearance" Value="Primary" />
        </DataTrigger>
    </Style.Triggers>
</Style>
```

Cada botao vira uma unica linha:

```xml
<!-- ✅ DEPOIS: 1 linha por botao -->
<ui:Button Content="VDR Form"
           Style="{StaticResource ActiveTabButton}"
           Tag="{Binding IsTestReportVisible}"
           Command="{Binding ShowVDRFormCommand}" />
```

**Por que `Tag` funciona:** `Tag` e uma `DependencyProperty` herdada de
`FrameworkElement` (tipo `object`). Bindar a uma prop bool a deixa boxed true/false.
O `DataTrigger` sobre `Self.Tag` converte "True"/"False" string ao tipo correto via
type coercion. Padrao WPF standard e estavel.

**Funciona em qualquer DRY com N botoes compartilhando logica** — nao so abas.
