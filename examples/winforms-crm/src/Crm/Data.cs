using System.ComponentModel;

namespace Crm;

public class Customer
{
    public string Name { get; set; } = "";
    public string Company { get; set; } = "";
    public string Email { get; set; } = "";
    public string Phone { get; set; } = "";
    public string Status { get; set; } = "Lead";
    public decimal AnnualValue { get; set; }
    public override string ToString() => Name;
}

public class Activity
{
    public DateTime Date { get; set; }
    public string Customer { get; set; } = "";
    public string Type { get; set; } = "Call";
    public string Notes { get; set; } = "";
}

public class CrmOptions
{
    public string DefaultStatus { get; set; } = "Lead";
    public string SignatureEmail { get; set; } = "sales@fabrikam.example";
    public bool ShowInactive { get; set; } = true;
}

/// <summary>Fake data, seeded in memory on every start.</summary>
public class CrmData
{
    public static readonly string[] Statuses = { "Lead", "Prospect", "Customer", "Inactive" };
    public static readonly string[] ActivityTypes = { "Call", "Email", "Meeting", "Note" };

    public BindingList<Customer> Customers { get; } = new();
    public BindingList<Activity> Activities { get; } = new();
    public CrmOptions Options { get; } = new();

    public static CrmData CreateSeeded()
    {
        var d = new CrmData();
        d.Customers.Add(new Customer { Name = "Avery Chen", Company = "Northwind Traders", Email = "avery.chen@northwind.example", Phone = "555-0141", Status = "Customer", AnnualValue = 48000 });
        d.Customers.Add(new Customer { Name = "Blake Diaz", Company = "Contoso Ltd", Email = "blake@contoso.example", Phone = "555-0142", Status = "Prospect", AnnualValue = 22000 });
        d.Customers.Add(new Customer { Name = "Casey Patel", Company = "Tailspin Toys", Email = "casey.patel@tailspin.example", Phone = "555-0143", Status = "Lead", AnnualValue = 9000 });
        d.Customers.Add(new Customer { Name = "Devon Brooks", Company = "Wide World Importers", Email = "devon@wideworld.example", Phone = "555-0144", Status = "Customer", AnnualValue = 61000 });
        d.Customers.Add(new Customer { Name = "Emery Novak", Company = "Litware Inc", Email = "emery@litware.example", Phone = "555-0145", Status = "Inactive", AnnualValue = 0 });
        d.Activities.Add(new Activity { Date = new DateTime(2026, 9, 2), Customer = "Avery Chen", Type = "Meeting", Notes = "Quarterly review. Renewal likely." });
        d.Activities.Add(new Activity { Date = new DateTime(2026, 9, 9), Customer = "Blake Diaz", Type = "Call", Notes = "Asked for pricing on the premium plan." });
        d.Activities.Add(new Activity { Date = new DateTime(2026, 9, 15), Customer = "Casey Patel", Type = "Email", Notes = "Sent product brochure." });
        return d;
    }
}

/// <summary>User-facing messages. GuideGen collects these for the Troubleshooting chapter.</summary>
public static class Messages
{
    public const string LoginFailed = "The user name or password is incorrect.";
    public const string NameRequired = "Enter the customer's name.";
    public const string EmailInvalid = "Enter a valid email address.";
    public const string ValueInvalid = "Annual value must be a number of 0 or more.";
    public const string SelectCustomerFirst = "Select a customer first.";
    public const string ChooseCustomer = "Choose a customer for this activity.";
    public const string NotesTooLong = "Notes cannot be longer than 500 characters.";
    public const string DuplicateEmail = "A customer with this email address already exists.";
}
