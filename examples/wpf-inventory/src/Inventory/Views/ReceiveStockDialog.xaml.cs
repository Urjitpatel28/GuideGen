using System.Windows;
using Inventory.Models;
using Inventory.ViewModels;

namespace Inventory.Views;

public partial class ReceiveStockDialog : Window
{
    public ReceiveStockDialog(Item item)
    {
        InitializeComponent();
        ItemText.Text = $"{item.Sku} - {item.Name} (now {item.Quantity} in stock)";
    }

    public int Received { get; private set; }

    private void Ok_Click(object sender, RoutedEventArgs e)
    {
        if (!int.TryParse(ReceivedBox.Text, out var n) || n <= 0)
        {
            ErrorText.Text = "Quantity received must be greater than 0.";
            return;
        }
        Received = n;
        DialogResult = true;
    }
}
