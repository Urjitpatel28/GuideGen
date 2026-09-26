using System.Windows;
using Inventory.ViewModels;

namespace Inventory.Views;

public partial class ItemDialog : Window
{
    public ItemDialog() => InitializeComponent();

    private void Save_Click(object sender, RoutedEventArgs e)
    {
        if (DataContext is ItemEditViewModel vm && vm.TrySave()) DialogResult = true;
    }
}
