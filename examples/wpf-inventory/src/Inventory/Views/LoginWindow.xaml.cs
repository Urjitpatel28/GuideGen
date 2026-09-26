using System.Windows;
using Inventory.ViewModels;

namespace Inventory.Views;

public partial class LoginWindow : Window
{
    // Demo-only account; documented in README.md. Never real credentials.
    private const string DemoUser = "demo";
    private const string DemoPassword = "stockroom";

    public LoginWindow() => InitializeComponent();

    public string SignedInUser { get; private set; } = "";

    private void SignIn_Click(object sender, RoutedEventArgs e)
    {
        if (UserNameBox.Text.Trim().Equals(DemoUser, StringComparison.OrdinalIgnoreCase) && PasswordBox.Password == DemoPassword)
        {
            SignedInUser = UserNameBox.Text.Trim();
            DialogResult = true;
            return;
        }
        ErrorText.Text = Messages.LoginFailed;
        ErrorText.Visibility = Visibility.Visible;
    }
}
