namespace Crm;

public class AboutForm : Form
{
    public AboutForm()
    {
        Text = "About ClientDesk";
        Name = "AboutForm";
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = MinimizeBox = false;
        ShowInTaskbar = false;
        StartPosition = FormStartPosition.CenterParent;
        ClientSize = new Size(360, 200);
        Font = new Font("Segoe UI", 9.5f);

        var logoPath = Path.Combine(AppContext.BaseDirectory, "Assets", "logo.png");
        var pic = new PictureBox { Name = "AboutLogo", Size = new Size(64, 64), Location = new Point(20, 20), SizeMode = PictureBoxSizeMode.Zoom };
        if (File.Exists(logoPath)) pic.Image = Image.FromFile(logoPath);
        var title = new Label { Name = "AboutTitle", Text = "ClientDesk CRM", Font = new Font("Segoe UI", 14f, FontStyle.Bold), ForeColor = Ui.Brand, Location = new Point(100, 24), AutoSize = true };
        var version = new Label { Name = "AboutVersion", Text = "Version 1.8.2 · © Fabrikam Software", Location = new Point(102, 60), AutoSize = true };
        var ok = Ui.Button("OK", "AboutOkButton", primary: true);
        ok.DialogResult = DialogResult.OK;
        ok.Location = new Point(260, 150);
        AcceptButton = ok;
        Controls.AddRange(new Control[] { pic, title, version, ok });
    }
}
