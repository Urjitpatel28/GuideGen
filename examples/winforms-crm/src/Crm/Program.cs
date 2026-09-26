namespace Crm;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        // Fixed culture so dates and currency look the same on every machine.
        System.Globalization.CultureInfo.DefaultThreadCurrentCulture = new System.Globalization.CultureInfo("en-US");
        System.Globalization.CultureInfo.DefaultThreadCurrentUICulture = new System.Globalization.CultureInfo("en-US");
        System.Threading.Thread.CurrentThread.CurrentCulture = new System.Globalization.CultureInfo("en-US");
        ApplicationConfiguration.Initialize();
        var data = CrmData.CreateSeeded();
        using var login = new LoginForm();
        if (login.ShowDialog() != DialogResult.OK) return;
        Application.Run(new MainForm(data, login.UserName));
    }
}
