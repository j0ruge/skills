# Testes de ViewModel — padroes com codigo

Complemento da secao "Testes de ViewModel" do SKILL.md. Leia quando for escrever testes de
ViewModel: o que testar, o teste de um Command que abre dialog, e o cuidado antes de mover codigo
que testes acessam por reflection.

---

## O que testar

| Aspecto | Exemplo |
|---------|---------|
| Estado inicial | Propriedades iniciam com valores default corretos |
| Commands executam | `CarregarCommand.Execute()` popula propriedades |
| CanExecute | Botao desabilitado quando pre-condicao nao e atendida |
| Validacao | Dados invalidos mostram erro, nao executam acao |

---

## Padrao para Commands com Dialogs

Commands que abrem `OpenFileDialog` nao sao testaveis unitariamente. Extraia a logica
para um metodo publico testavel:

```csharp
// No ViewModel — o Command chama o dialog e depois o metodo testavel
[RelayCommand]
private void CarregarHardwareId()
{
    var dialog = new Microsoft.Win32.OpenFileDialog { Filter = "*.hid" };
    if (dialog.ShowDialog() == true)
        PopularCampos(_service.RecuperarDeArquivo(dialog.FileName));
}

// Metodo publico testavel (sem dialog)
public void PopularCampos(HardwareInfo hwInfo)
{
    CompanyName = hwInfo.CompanyName;
    ProcessorId = hwInfo.ProcessorID;
    // ...
    IsSaveEnabled = true;
}
```

```csharp
// No teste
[Fact]
public void PopularCampos_AtualizaPropriedadesEHabilitaSave()
{
    var vm = new MainWindowViewModel(service);
    vm.PopularCampos(new HardwareInfo { CompanyName = "JRC" });

    Assert.Equal("JRC", vm.CompanyName);
    Assert.True(vm.IsSaveEnabled);
}
```

---

## Cuidado com testes que usam reflection

Testes que acessam metodos privados via `typeof(Page).GetMethod("NomeMetodo", BindingFlags.NonPublic)`
quebrarao quando o metodo for movido do code-behind para o ViewModel. O `typeof` precisa ser
atualizado de `typeof(MinhaPage)` para `typeof(MinhaPageViewModel)`. Identifique esses testes
ANTES de mover codigo — consulte a "Checklist Pre-Migracao de Pagina" do SKILL.md.
