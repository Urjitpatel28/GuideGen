using System.ComponentModel;
using System.Windows;
using System.Windows.Data;
using System.Windows.Input;
using Inventory.Models;
using Inventory.Views;

namespace Inventory.ViewModels;

public class MainViewModel : ObservableObject
{
    private string _search = "";
    private Item? _selected;
    private string _status = "Ready";

    public MainViewModel(DataStore store, string user)
    {
        Store = store;
        SignedInAs = user;
        ItemsView = CollectionViewSource.GetDefaultView(store.Items);
        ItemsView.Filter = o => o is Item i && (Search.Length == 0
            || i.Name.Contains(Search, StringComparison.OrdinalIgnoreCase)
            || i.Sku.Contains(Search, StringComparison.OrdinalIgnoreCase));

        NewItemCommand = new RelayCommand(_ => EditItem(null));
        EditItemCommand = new RelayCommand(_ =>
        {
            if (Selected is null) { MessageBox.Show(Messages.SelectItemFirst, "Stockroom Inventory", MessageBoxButton.OK, MessageBoxImage.Information); return; }
            EditItem(Selected);
        });
        DeleteItemCommand = new RelayCommand(_ => DeleteSelected());
        ReceiveStockCommand = new RelayCommand(_ => ReceiveStock());
        CategoriesCommand = new RelayCommand(_ => Show(new CategoriesDialog { DataContext = new CategoriesViewModel(Store) }));
        SettingsCommand = new RelayCommand(_ => Show(new SettingsDialog { DataContext = new SettingsViewModel(Store.Settings) }, refresh: true));
        AboutCommand = new RelayCommand(_ => Show(new AboutDialog()));
        ExitCommand = new RelayCommand(_ => Application.Current.Shutdown());
    }

    public DataStore Store { get; }
    public string SignedInAs { get; }
    public ICollectionView ItemsView { get; }

    public string Search
    {
        get => _search;
        set { if (Set(ref _search, value ?? "")) ItemsView.Refresh(); }
    }

    public Item? Selected { get => _selected; set => Set(ref _selected, value); }
    public string Status { get => _status; set => Set(ref _status, value); }

    public int TotalItems => Store.Items.Count;
    public int TotalUnits => Store.Items.Sum(i => i.Quantity);
    public decimal StockValue => Store.Items.Sum(i => i.Value);
    public IEnumerable<Item> LowStock => Store.Items.Where(i => i.Quantity <= Store.Settings.LowStockThreshold).ToList();

    public ICommand NewItemCommand { get; }
    public ICommand EditItemCommand { get; }
    public ICommand DeleteItemCommand { get; }
    public ICommand ReceiveStockCommand { get; }
    public ICommand CategoriesCommand { get; }
    public ICommand SettingsCommand { get; }
    public ICommand AboutCommand { get; }
    public ICommand ExitCommand { get; }

    private void Show(Window dlg, bool refresh = false)
    {
        dlg.Owner = Application.Current.MainWindow;
        dlg.ShowDialog();
        if (refresh) RefreshSummary();
    }

    private void EditItem(Item? item)
    {
        var vm = new ItemEditViewModel(Store, item);
        var dlg = new ItemDialog { DataContext = vm, Owner = Application.Current.MainWindow };
        if (dlg.ShowDialog() == true)
        {
            ItemsView.Refresh();
            Status = item is null ? $"Added {vm.Name}." : $"Saved {vm.Name}.";
            RefreshSummary();
        }
    }

    private void ReceiveStock()
    {
        if (Selected is null) { MessageBox.Show(Messages.SelectItemFirst, "Stockroom Inventory", MessageBoxButton.OK, MessageBoxImage.Information); return; }
        var dlg = new ReceiveStockDialog(Selected) { Owner = Application.Current.MainWindow };
        if (dlg.ShowDialog() == true)
        {
            Selected.Quantity += dlg.Received;
            ItemsView.Refresh();
            Status = $"Received {dlg.Received} x {Selected.Name}.";
            RefreshSummary();
        }
    }

    private void DeleteSelected()
    {
        if (Selected is null) { MessageBox.Show(Messages.SelectItemFirst, "Stockroom Inventory", MessageBoxButton.OK, MessageBoxImage.Information); return; }
        if (Store.Settings.ConfirmDeletes &&
            MessageBox.Show($"Delete {Selected.Name}?", "Delete item", MessageBoxButton.YesNo, MessageBoxImage.Warning) != MessageBoxResult.Yes)
            return;
        var name = Selected.Name;
        Store.Items.Remove(Selected);
        Status = $"Deleted {name}.";
        RefreshSummary();
    }

    private void RefreshSummary()
    {
        Raise(nameof(TotalItems)); Raise(nameof(TotalUnits)); Raise(nameof(StockValue)); Raise(nameof(LowStock));
    }
}

public class CategoriesViewModel : ObservableObject
{
    private string _newCategory = "";
    private string? _error;

    public CategoriesViewModel(DataStore store)
    {
        Categories = store.Categories;
        AddCommand = new RelayCommand(_ =>
        {
            var name = NewCategory.Trim();
            if (name.Length == 0) { Error = Messages.NameRequired; return; }
            if (Categories.Any(c => string.Equals(c, name, StringComparison.OrdinalIgnoreCase))) { Error = Messages.CategoryExists; return; }
            Categories.Add(name);
            NewCategory = "";
            Error = null;
        });
    }

    public System.Collections.ObjectModel.ObservableCollection<string> Categories { get; }
    public string NewCategory { get => _newCategory; set => Set(ref _newCategory, value); }
    public string? Error { get => _error; set => Set(ref _error, value); }
    public ICommand AddCommand { get; }
}

public class SettingsViewModel : ObservableObject
{
    private readonly AppSettings _settings;
    private string _threshold;
    private string? _error;

    public SettingsViewModel(AppSettings settings)
    {
        _settings = settings;
        _threshold = settings.LowStockThreshold.ToString();
        DefaultCategory = settings.DefaultCategory;
        ReportEmail = settings.ReportEmail;
        ConfirmDeletes = settings.ConfirmDeletes;
    }

    public string Threshold { get => _threshold; set => Set(ref _threshold, value); }
    public string DefaultCategory { get; set; }
    public string ReportEmail { get; set; }
    public bool ConfirmDeletes { get; set; }
    public string? Error { get => _error; set => Set(ref _error, value); }

    public bool TrySave()
    {
        if (!int.TryParse(Threshold, out var t) || t < 0 || t > 1000) { Error = Messages.ThresholdInvalid; return false; }
        _settings.LowStockThreshold = t;
        _settings.DefaultCategory = DefaultCategory;
        _settings.ReportEmail = ReportEmail;
        _settings.ConfirmDeletes = ConfirmDeletes;
        return true;
    }
}
