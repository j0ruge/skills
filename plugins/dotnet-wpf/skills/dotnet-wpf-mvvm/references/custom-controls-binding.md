# Custom Controls e Data Binding

Leia antes de planejar a migracao de uma Page que usa UserControls custom (controles de
formulario especializados): define se o controle aceita binding ou fica como excecao no code-behind.

---

Se o projeto usa UserControls custom (ex: controles de formulario especializados como
APTCheckBoxWPF, AptDateWPF), audite ANTES de planejar a migracao:

1. **Verificar DependencyProperties** — o controle expoe DP para seu valor principal?
   ```bash
   grep -r "DependencyProperty" <pasta-dos-controles-custom>/
   ```
   Se retorna vazio, o controle nao suporta data binding.

2. **API imperativa = sem binding** — se o controle usa `GetValue()/SetValue()/SetDate()/GetDay()`
   em vez de DependencyProperties, data binding bidirecional e impossivel.

3. **Abordagem pragmatica para migracao:**
   - ViewModel gerencia Commands e estado de visibilidade (funciona sem DP)
   - Code-behind mantem mapeamento imperativo (FillForm/GetForm) como excecao documentada
   - Planejar spec separada para adicionar DependencyProperties aos custom controls
   - Quando DPs estiverem prontas, substituir code-behind por binding no XAML

4. **Adicionar DependencyProperties** (spec separada) — cada controle precisa de pelo menos
   uma DP para seu valor principal. Exemplo para um checkbox custom:
   ```csharp
   public static readonly DependencyProperty ValueProperty =
       DependencyProperty.Register(nameof(Value), typeof(string), typeof(APTCheckBoxWPF),
           new FrameworkPropertyMetadata(string.Empty, FrameworkPropertyMetadataOptions.BindsTwoWayByDefault,
               OnValueChanged));
   ```
