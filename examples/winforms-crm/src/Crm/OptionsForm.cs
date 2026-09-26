namespace Crm;

public class OptionsForm : Form
{
    public OptionsForm(CrmOptions options)
    {
        Text = "Options";
        Name = "OptionsForm";
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = MinimizeBox = false;
        ShowInTaskbar = false;
        StartPosition = FormStartPosition.CenterParent;
        ClientSize = new Size(440, 230);
        Font = new Font("Segoe UI", 9.5f);

        var grid = Ui.FieldGrid();
        var status = Ui.AddField(grid, "Default &status", "DefaultStatusComboBox", new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList });
        status.Items.AddRange(CrmData.Statuses);
        status.SelectedItem = options.DefaultStatus;
        var email = Ui.AddField(grid, "&Reply-to email", "SignatureEmailTextBox", new TextBox { Text = options.SignatureEmail });
        var inactive = new CheckBox { Text = "Show &inactive customers", Name = "ShowInactiveCheckBox", Checked = options.ShowInactive, AutoSize = true };
        grid.Controls.Add(new Label());
        grid.Controls.Add(inactive);

        var ok = Ui.Button("OK", "SaveOptionsButton", primary: true);
        var cancel = Ui.Button("Cancel", "CancelOptionsButton");
        cancel.DialogResult = DialogResult.Cancel;
        ok.Click += (_, _) =>
        {
            options.DefaultStatus = status.SelectedItem as string ?? "Lead";
            options.SignatureEmail = email.Text.Trim();
            options.ShowInactive = inactive.Checked;
            DialogResult = DialogResult.OK;
        };
        AcceptButton = ok;
        CancelButton = cancel;
        Controls.Add(grid);
        Controls.Add(Ui.ButtonRow(cancel, ok));
    }
}
