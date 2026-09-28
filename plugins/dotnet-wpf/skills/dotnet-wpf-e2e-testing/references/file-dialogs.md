# File Dialogs em testes E2E (FlaUI)

Código completo do Passo 6 do SKILL.md. Leia quando o app abre `OpenFileDialog`/`SaveFileDialog`
num fluxo que o teste precisa cobrir: a Estratégia A troca o dialog por fake no ViewModel, a B
automatiza o dialog Win32 de verdade. O porquê dos `Thread.Sleep` está no SKILL.md, Passo 6.

---

## Estratégia A: Abstrair com IFileDialogService (Recomendado)

A melhor abordagem para testabilidade é abstrair dialogs atrás de uma interface, permitindo substituição por fake em testes.

```csharp
// Interface
public interface IFileDialogService
{
    string? OpenFile(string filter);
    string? SaveFile(string filter, string defaultFileName);
}

// Produção
public class WpfFileDialogService : IFileDialogService
{
    public string? OpenFile(string filter)
    {
        var dlg = new Microsoft.Win32.OpenFileDialog { Filter = filter };
        return dlg.ShowDialog() == true ? dlg.FileName : null;
    }

    public string? SaveFile(string filter, string defaultFileName)
    {
        var dlg = new Microsoft.Win32.SaveFileDialog
        {
            Filter = filter,
            FileName = defaultFileName
        };
        return dlg.ShowDialog() == true ? dlg.FileName : null;
    }
}
```

No ViewModel, injete `IFileDialogService` e separe a lógica testável do dialog:

```csharp
public partial class MainWindowViewModel(
    LicenseService licenseService,
    IFileDialogService fileDialog) : ObservableObject
{
    [RelayCommand]
    private void CarregarHardwareId()
    {
        var path = fileDialog.OpenFile("Hardware ID|*.hid");
        if (path is not null)
        {
            PopularCampos(licenseService.RecuperarDeArquivo(path));
        }
    }

    // Método testável separado — sem dependência de dialog
    public void PopularCampos(HardwareInfo info) { /* ... */ }
}
```

---

## Estratégia B: Automatizar o Dialog Diretamente

Para testes E2E reais que precisam testar o fluxo completo incluindo o dialog, automatize o dialog Win32 via FlaUI. A automação de file dialogs é significativamente mais complexa do que parece — requer múltiplas estratégias de fallback e waits explícitos porque o dialog Win32 varia entre versões do Windows e localizações.

```csharp
using System.IO;
using System.Threading;
using FlaUI.Core.AutomationElements;
using FlaUI.Core.Input;
using FlaUI.Core.Tools;
using FlaUI.Core.WindowsAPI;

namespace MyApp.E2ETests.Infrastructure;

public static class FileDialogHelper
{
    public static void SelectFile(Window parentWindow, string filePath,
        int timeoutMs = TestConstants.ElementTimeoutMs)
    {
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"Arquivo não existe: {filePath}");
        }

        InteractWithDialog(parentWindow, filePath, timeoutMs);
    }

    public static void SaveFile(Window parentWindow, string filePath,
        int timeoutMs = TestConstants.ElementTimeoutMs)
    {
        var dir = Path.GetDirectoryName(filePath);
        if (dir is not null) { Directory.CreateDirectory(dir); }

        InteractWithDialog(parentWindow, filePath, timeoutMs);
    }

    private static void InteractWithDialog(Window parentWindow, string filePath,
        int timeoutMs)
    {
        // 1. Esperar o dialog modal aparecer
        var dialog = Retry.WhileNull(
            () => parentWindow.ModalWindows.FirstOrDefault(),
            timeout: TimeSpan.FromMilliseconds(timeoutMs),
            interval: TimeSpan.FromMilliseconds(300)
        ).Result ?? throw new TimeoutException(
            $"File dialog não apareceu após {timeoutMs}ms");

        // 2. Esperar dialog renderizar completamente
        //    Thread.Sleep é necessário aqui — Retry não resolve porque o dialog
        //    aparece na árvore antes dos controles internos estarem prontos
        Thread.Sleep(TestConstants.DialogRenderDelayMs);
        dialog.SetForeground();
        Thread.Sleep(TestConstants.DialogFocusDelayMs);

        // 3. Encontrar campo filename (AutomationId "1148" no Win10/11)
        var fileNameEdit = dialog.FindFirstDescendant(
            cf => cf.ByAutomationId("1148"));

        if (fileNameEdit is not null)
        {
            // Click → Ctrl+A → Delete → Type caminho completo
            fileNameEdit.Click();
            Thread.Sleep(TestConstants.FieldActivationDelayMs);
            Keyboard.TypeSimultaneously(VirtualKeyShort.CONTROL, VirtualKeyShort.KEY_A);
            Thread.Sleep(TestConstants.KeystrokeDelayMs);
            Keyboard.Press(VirtualKeyShort.DELETE);
            Thread.Sleep(TestConstants.KeystrokeDelayMs);
            Keyboard.Type(filePath);
            Thread.Sleep(TestConstants.InputProcessingDelayMs);
        }
        else
        {
            // Fallback: Alt+D foca a barra de endereço, Alt+N foca filename
            Keyboard.TypeSimultaneously(VirtualKeyShort.ALT, VirtualKeyShort.KEY_D);
            Thread.Sleep(TestConstants.InputProcessingDelayMs);
            Keyboard.Type(Path.GetDirectoryName(filePath) ?? filePath);
            Thread.Sleep(TestConstants.FieldActivationDelayMs);
            Keyboard.Press(VirtualKeyShort.ENTER);
            Thread.Sleep(TestConstants.NavigationDelayMs);
            Keyboard.TypeSimultaneously(VirtualKeyShort.ALT, VirtualKeyShort.KEY_N);
            Thread.Sleep(TestConstants.FieldActivationDelayMs);
            Keyboard.Type(Path.GetFileName(filePath));
            Thread.Sleep(TestConstants.FieldActivationDelayMs);
        }

        // 4. Confirmar — tentar botão por AutomationId, por nome, ou Enter
        var confirmBtn = dialog.FindFirstDescendant(
            cf => cf.ByAutomationId("1"))?.AsButton();
        if (confirmBtn is not null)
        {
            confirmBtn.Invoke();
        }
        else
        {
            var namedBtn = dialog.FindFirstDescendant(
                cf => cf.ByName("Abrir"))?.AsButton()
                ?? dialog.FindFirstDescendant(cf => cf.ByName("Open"))?.AsButton()
                ?? dialog.FindFirstDescendant(cf => cf.ByName("Salvar"))?.AsButton();
            if (namedBtn is not null) { namedBtn.Invoke(); }
            else { Keyboard.Press(VirtualKeyShort.ENTER); }
        }

        // 5. Esperar dialog fechar
        Retry.WhileTrue(
            () => parentWindow.ModalWindows.Length > 0,
            timeout: TimeSpan.FromMilliseconds(timeoutMs + 5000),
            interval: TimeSpan.FromMilliseconds(500));
    }
}
```

---

## Extraindo helpers para reduzir duplicação

Quando múltiplos testes compartilham fluxos (ex: carregar arquivo, preencher campos, salvar), extraia métodos helpers privados na classe de teste. Isso centraliza screenshot on failure e evita copiar/colar blocos de 20+ linhas entre testes:

```csharp
// Helper reutilizado por todos os testes que carregam .hid
private void LoadHardwareId(MainWindowPage page)
{
    var hidPath = Path.GetFullPath(TestConstants.SampleHidPath);
    try
    {
        page.ClickLoadHardware();
        FileDialogHelper.SelectFile(MainWindow, hidPath);
    }
    catch (Exception ex)
    {
        CaptureScreenshot("LoadHardwareId_Error");
        throw new InvalidOperationException($"Dialog falhou: {ex.Message}", ex);
    }
    Retry.WhileTrue(
        () => string.IsNullOrEmpty(MainWindowPage.GetText(page.CompanyNameTextBox)),
        timeout: TimeSpan.FromSeconds(10));
}
```
