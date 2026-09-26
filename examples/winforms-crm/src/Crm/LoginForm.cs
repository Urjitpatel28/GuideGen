namespace Crm;

public class LoginForm : Form
{
    // Demo-only account; documented in README.md.
    private const string DemoUser = "demo";
    private const string DemoPassword = "clientdesk";

    private readonly TextBox _user;
    private readonly TextBox _password;
    private readonly Label _error;

    public LoginForm()
    {
        Text = "ClientDesk - Sign in";
        Name = "LoginForm";
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = MinimizeBox = false;
        StartPosition = FormStartPosition.CenterScreen;
        ClientSize = new Size(380, 230);
        Font = new Font("Segoe UI", 9.5f);

        var heading = new Label { Text = "Sign in to ClientDesk", Name = "LoginHeading", Dock = DockStyle.Top, Height = 44,
            Font = new Font("Segoe UI", 14f, FontStyle.Bold), ForeColor = Ui.Brand, Padding = new Padding(16, 12, 0, 0) };
        var grid = Ui.FieldGrid();
        _user = Ui.AddField(grid, "&User name", "UserNameTextBox", new TextBox());
        _password = Ui.AddField(grid, "&Password", "PasswordTextBox", new TextBox { UseSystemPasswordChar = true });
        _error = new Label { Name = "LoginErrorLabel", ForeColor = Color.Firebrick, AutoSize = true, Visible = false };
        grid.Controls.Add(new Label());
        grid.Controls.Add(_error);

        var ok = Ui.Button("Sign in", "SignInButton", primary: true);
        var cancel = Ui.Button("Cancel", "CancelButton");
        cancel.DialogResult = DialogResult.Cancel;
        ok.Click += (_, _) => SignIn();
        AcceptButton = ok;
        CancelButton = cancel;

        Controls.Add(grid);
        Controls.Add(Ui.ButtonRow(cancel, ok));
        Controls.Add(heading);
    }

    public string UserName { get; private set; } = "";

    private void SignIn()
    {
        if (_user.Text.Trim().Equals(DemoUser, StringComparison.OrdinalIgnoreCase) && _password.Text == DemoPassword)
        {
            UserName = _user.Text.Trim();
            DialogResult = DialogResult.OK;
            return;
        }
        _error.Text = Messages.LoginFailed;
        _error.Visible = true;
    }
}
