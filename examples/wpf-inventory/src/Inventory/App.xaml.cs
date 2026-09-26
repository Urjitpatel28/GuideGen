using System.Windows;
using Inventory.Models;
using Inventory.ViewModels;
using Inventory.Views;

namespace Inventory;

public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        var store = DataStore.CreateSeeded();

        var login = new LoginWindow();
        if (login.ShowDialog() != true)
        {
            Shutdown();
            return;
        }

        var main = new MainWindow { DataContext = new MainViewModel(store, login.SignedInUser) };
        main.Closed += (_, _) => Shutdown();
        MainWindow = main;
        main.Show();
    }
}
