using FlaUI.Core;
using FlaUI.Core.AutomationElements;
using FlaUI.Core.Tools;
using FlaUI.UIA3;
using Xunit;

namespace Inventory.UiTests;

/// <summary>
/// End-to-end UI tests (FlaUI / UI Automation). Build src/Inventory first.
/// GuideGen reads these as evidence for which tasks matter most.
/// </summary>
public sealed class InventoryTests : IDisposable
{
    private static readonly string Exe = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory,
        "..", "..", "..", "..", "..", "src", "Inventory", "bin", "Debug", "net9.0-windows", "Inventory.exe"));

    private readonly Application _app;
    private readonly UIA3Automation _automation = new();

    public InventoryTests() => _app = Application.Launch(Exe);

    public void Dispose()
    {
        _app.Close();
        _app.Dispose();
        _automation.Dispose();
    }

    private Window SignIn()
    {
        var login = _app.GetMainWindow(_automation);
        login.FindFirstDescendant(cf => cf.ByAutomationId("UserNameBox")).AsTextBox().Text = "demo";
        login.FindFirstDescendant(cf => cf.ByAutomationId("PasswordBox")).AsTextBox().Text = "stockroom";
        login.FindFirstDescendant(cf => cf.ByAutomationId("SignInButton")).AsButton().Invoke();
        return Retry.WhileNull(() => _app.GetAllTopLevelWindows(_automation).FirstOrDefault(w => w.AutomationId == "MainWindow"),
            TimeSpan.FromSeconds(10)).Result!;
    }

    [Fact]
    public void Sign_in_opens_main_window()
    {
        var main = SignIn();
        Assert.Equal("Stockroom Inventory", main.Title);
    }

    [Fact]
    public void Add_new_item()
    {
        var main = SignIn();
        main.FindFirstDescendant(cf => cf.ByAutomationId("NewItemButton")).AsButton().Click();
        var dlg = Retry.WhileNull(() => main.ModalWindows.FirstOrDefault(), TimeSpan.FromSeconds(5)).Result!;
        dlg.FindFirstDescendant(cf => cf.ByAutomationId("SkuBox")).AsTextBox().Text = "HW-1003";
        dlg.FindFirstDescendant(cf => cf.ByAutomationId("NameBox")).AsTextBox().Text = "Wall plugs 6mm (box)";
        dlg.FindFirstDescendant(cf => cf.ByAutomationId("QuantityBox")).AsTextBox().Text = "40";
        dlg.FindFirstDescendant(cf => cf.ByAutomationId("PriceBox")).AsTextBox().Text = "4.50";
        dlg.FindFirstDescendant(cf => cf.ByAutomationId("SaveItemButton")).AsButton().Click();
        var grid = main.FindFirstDescendant(cf => cf.ByAutomationId("ItemsGrid")).AsDataGridView();
        Assert.Contains(grid.Rows, r => r.Cells[0].Value == "HW-1003");
    }

    [Fact]
    public void Receive_stock_adds_to_quantity()
    {
        var main = SignIn();
        var grid = main.FindFirstDescendant(cf => cf.ByAutomationId("ItemsGrid")).AsDataGridView();
        grid.Rows[1].Click();
        main.FindFirstDescendant(cf => cf.ByAutomationId("ReceiveStockButton")).AsButton().Click();
        var dlg = Retry.WhileNull(() => main.ModalWindows.FirstOrDefault(), TimeSpan.FromSeconds(5)).Result!;
        dlg.FindFirstDescendant(cf => cf.ByAutomationId("ReceivedBox")).AsTextBox().Text = "24";
        dlg.FindFirstDescendant(cf => cf.ByAutomationId("AddToStockButton")).AsButton().Click();
        Assert.Equal("30", grid.Rows[1].Cells[3].Value);
    }

    [Fact]
    public void Search_filters_items()
    {
        var main = SignIn();
        main.FindFirstDescendant(cf => cf.ByAutomationId("SearchBox")).AsTextBox().Text = "cable";
        var grid = main.FindFirstDescendant(cf => cf.ByAutomationId("ItemsGrid")).AsDataGridView();
        Assert.Single(grid.Rows);
    }
}
