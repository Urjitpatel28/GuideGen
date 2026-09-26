using System.Globalization;
using Inventory.Models;

namespace Inventory.ViewModels;

public class ItemEditViewModel : ObservableObject
{
    private readonly DataStore _store;
    private readonly Item? _original;
    private string _sku = "", _name = "", _category = "", _quantity = "0", _unitPrice = "", _supplier = "", _location = "";
    private string? _skuError, _nameError, _quantityError, _priceError;

    public ItemEditViewModel(DataStore store, Item? original)
    {
        _store = store;
        _original = original;
        Title = original is null ? "New item" : $"Edit item {original.Sku}";
        _category = store.Settings.DefaultCategory;
        if (original is not null)
        {
            _sku = original.Sku; _name = original.Name; _category = original.Category;
            _quantity = original.Quantity.ToString(CultureInfo.InvariantCulture);
            _unitPrice = original.UnitPrice.ToString("0.00", CultureInfo.InvariantCulture);
            _supplier = original.Supplier; _location = original.Location;
        }
    }

    public string Title { get; }
    public IEnumerable<string> Categories => _store.Categories;
    public IEnumerable<string> Suppliers => _store.Suppliers.Select(s => s.Name);

    public string Sku { get => _sku; set => Set(ref _sku, value); }
    public string Name { get => _name; set => Set(ref _name, value); }
    public string Category { get => _category; set => Set(ref _category, value); }
    public string Quantity { get => _quantity; set => Set(ref _quantity, value); }
    public string UnitPrice { get => _unitPrice; set => Set(ref _unitPrice, value); }
    public string Supplier { get => _supplier; set => Set(ref _supplier, value); }
    public string Location { get => _location; set => Set(ref _location, value); }

    public string? SkuError { get => _skuError; private set => Set(ref _skuError, value); }
    public string? NameError { get => _nameError; private set => Set(ref _nameError, value); }
    public string? QuantityError { get => _quantityError; private set => Set(ref _quantityError, value); }
    public string? PriceError { get => _priceError; private set => Set(ref _priceError, value); }

    /// <summary>Validates and, if valid, writes the item to the store.</summary>
    public bool TrySave()
    {
        SkuError = string.IsNullOrWhiteSpace(Sku) ? Messages.SkuRequired
            : _store.Items.Any(i => i != _original && string.Equals(i.Sku, Sku.Trim(), StringComparison.OrdinalIgnoreCase)) ? Messages.SkuNotUnique
            : null;
        NameError = string.IsNullOrWhiteSpace(Name) ? Messages.NameRequired : null;
        QuantityError = !int.TryParse(Quantity, NumberStyles.Integer, CultureInfo.InvariantCulture, out var qty) ? Messages.QuantityNotNumber
            : qty < 0 ? Messages.QuantityNegative : null;
        PriceError = !decimal.TryParse(UnitPrice, NumberStyles.Number, CultureInfo.InvariantCulture, out var price) || price <= 0 ? Messages.PriceInvalid : null;
        if (SkuError is not null || NameError is not null || QuantityError is not null || PriceError is not null) return false;

        var item = _original ?? new Item();
        item.Sku = Sku.Trim(); item.Name = Name.Trim(); item.Category = Category;
        item.Quantity = qty; item.UnitPrice = price; item.Supplier = Supplier; item.Location = Location.Trim();
        if (_original is null) _store.Items.Add(item);
        return true;
    }
}
