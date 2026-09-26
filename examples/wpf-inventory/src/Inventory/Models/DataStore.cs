using System.Collections.ObjectModel;

namespace Inventory.Models;

public class Item
{
    public string Sku { get; set; } = "";
    public string Name { get; set; } = "";
    public string Category { get; set; } = "";
    public int Quantity { get; set; }
    public decimal UnitPrice { get; set; }
    public string Supplier { get; set; } = "";
    public string Location { get; set; } = "";
    public decimal Value => Quantity * UnitPrice;

    // UI Automation uses this as the row name, so rows can be targeted by name.
    public override string ToString() => $"{Sku} {Name}";
}

public class Supplier
{
    public string Name { get; set; } = "";
    public string ContactEmail { get; set; } = "";
    public string Phone { get; set; } = "";
    public int LeadTimeDays { get; set; }

    public override string ToString() => Name;
}

public class AppSettings
{
    public int LowStockThreshold { get; set; } = 10;
    public string DefaultCategory { get; set; } = "Hardware";
    public string ReportEmail { get; set; } = "reports@stockroom.example";
    public bool ConfirmDeletes { get; set; } = true;
}

/// <summary>In-memory data seeded with fake records on every start, so every run looks the same.</summary>
public class DataStore
{
    public ObservableCollection<Item> Items { get; } = new();
    public ObservableCollection<Supplier> Suppliers { get; } = new();
    public ObservableCollection<string> Categories { get; } = new();
    public AppSettings Settings { get; } = new();

    public static DataStore CreateSeeded()
    {
        var s = new DataStore();
        foreach (var c in new[] { "Hardware", "Electrical", "Plumbing", "Safety" }) s.Categories.Add(c);
        s.Suppliers.Add(new Supplier { Name = "Northwind Traders", ContactEmail = "sales@northwind.example", Phone = "555-0110", LeadTimeDays = 5 });
        s.Suppliers.Add(new Supplier { Name = "Contoso Supply", ContactEmail = "orders@contoso.example", Phone = "555-0120", LeadTimeDays = 3 });
        s.Suppliers.Add(new Supplier { Name = "Fabrikam Parts", ContactEmail = "parts@fabrikam.example", Phone = "555-0130", LeadTimeDays = 10 });
        s.Items.Add(new Item { Sku = "HW-1001", Name = "Hex bolt M8 (box of 100)", Category = "Hardware", Quantity = 48, UnitPrice = 12.50m, Supplier = "Northwind Traders", Location = "A-01" });
        s.Items.Add(new Item { Sku = "HW-1002", Name = "Wood screws 4x40 (box)", Category = "Hardware", Quantity = 6, UnitPrice = 7.95m, Supplier = "Northwind Traders", Location = "A-02" });
        s.Items.Add(new Item { Sku = "EL-2001", Name = "Cable ties 300mm", Category = "Electrical", Quantity = 120, UnitPrice = 3.20m, Supplier = "Contoso Supply", Location = "B-04" });
        s.Items.Add(new Item { Sku = "EL-2002", Name = "Junction box IP65", Category = "Electrical", Quantity = 9, UnitPrice = 14.00m, Supplier = "Contoso Supply", Location = "B-07" });
        s.Items.Add(new Item { Sku = "PL-3001", Name = "PTFE thread tape", Category = "Plumbing", Quantity = 75, UnitPrice = 1.10m, Supplier = "Fabrikam Parts", Location = "C-02" });
        s.Items.Add(new Item { Sku = "SF-4001", Name = "Safety glasses", Category = "Safety", Quantity = 22, UnitPrice = 5.60m, Supplier = "Fabrikam Parts", Location = "D-01" });
        return s;
    }
}
