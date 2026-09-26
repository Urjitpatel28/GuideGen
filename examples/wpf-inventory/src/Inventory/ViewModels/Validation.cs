namespace Inventory.ViewModels;

/// <summary>User-facing messages. GuideGen collects these for the Troubleshooting chapter.</summary>
public static class Messages
{
    public const string NameRequired = "Name is required.";
    public const string SkuRequired = "SKU is required.";
    public const string SkuNotUnique = "Another item already uses this SKU.";
    public const string QuantityNegative = "Quantity cannot be negative.";
    public const string QuantityNotNumber = "Quantity must be a whole number.";
    public const string PriceInvalid = "Unit price must be greater than 0.";
    public const string SelectItemFirst = "Select an item in the list first.";
    public const string CategoryExists = "That category already exists.";
    public const string ThresholdInvalid = "Low-stock threshold must be between 0 and 1000.";
    public const string LoginFailed = "Invalid user name or password.";
}
