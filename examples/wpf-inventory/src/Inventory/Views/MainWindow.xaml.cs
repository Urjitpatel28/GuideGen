using System.Windows;
using System.Windows.Input;
using Inventory.ViewModels;

namespace Inventory.Views;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        InputBindings.Add(new KeyBinding(new RelayCommand(_ => (DataContext as MainViewModel)?.NewItemCommand.Execute(null)), Key.N, ModifierKeys.Control));
    }
}
