using System.Windows;
using Inventory.ViewModels;

namespace Inventory.Views;

public partial class SettingsDialog : Window
{
    public SettingsDialog() => InitializeComponent();

    private void Ok_Click(object sender, RoutedEventArgs e)
    {
        if (DataContext is SettingsViewModel vm && vm.TrySave()) DialogResult = true;
    }
}
