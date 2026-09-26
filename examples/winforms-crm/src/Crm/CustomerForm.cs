using System.Globalization;
using System.Text.RegularExpressions;

namespace Crm;

public class CustomerForm : Form
{
    private readonly CrmData _data;
    private readonly Customer? _original;
    private readonly TextBox _name, _company, _email, _phone, _value;
    private readonly ComboBox _statusBox;
    private readonly ErrorProvider _errors = new() { BlinkStyle = ErrorBlinkStyle.NeverBlink };
    private readonly Label _message;

    public CustomerForm(CrmData data, Customer? original)
    {
        _data = data;
        _original = original;
        Text = original is null ? "New customer" : $"Edit customer - {original.Name}";
        Name = "CustomerForm";
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = MinimizeBox = false;
        ShowInTaskbar = false;
        StartPosition = FormStartPosition.CenterParent;
        ClientSize = new Size(460, 330);
        Font = new Font("Segoe UI", 9.5f);

        var grid = Ui.FieldGrid();
        _name = Ui.AddField(grid, "&Name", "NameTextBox", new TextBox());
        _company = Ui.AddField(grid, "&Company", "CompanyTextBox", new TextBox());
        _email = Ui.AddField(grid, "&Email", "EmailTextBox", new TextBox());
        _phone = Ui.AddField(grid, "&Phone", "PhoneTextBox", new TextBox());
        _statusBox = Ui.AddField(grid, "&Status", "StatusComboBox", new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList });
        _statusBox.Items.AddRange(CrmData.Statuses);
        _value = Ui.AddField(grid, "Annual &value", "AnnualValueTextBox", new TextBox());
        _message = new Label { Name = "ValidationLabel", ForeColor = Color.Firebrick, AutoSize = true };
        grid.Controls.Add(new Label());
        grid.Controls.Add(_message);

        var o = original ?? new Customer { Status = data.Options.DefaultStatus };
        _name.Text = o.Name; _company.Text = o.Company; _email.Text = o.Email; _phone.Text = o.Phone;
        _statusBox.SelectedItem = o.Status;
        _value.Text = o.AnnualValue.ToString("0", CultureInfo.InvariantCulture);

        var save = Ui.Button("Save", "SaveCustomerButton", primary: true);
        var cancel = Ui.Button("Cancel", "CancelCustomerButton");
        cancel.DialogResult = DialogResult.Cancel;
        save.Click += (_, _) => Save();
        AcceptButton = save;
        CancelButton = cancel;
        Controls.Add(grid);
        Controls.Add(Ui.ButtonRow(cancel, save));
    }

    public Customer? Result { get; private set; }

    private void Save()
    {
        _errors.Clear();
        string? error = null;
        if (string.IsNullOrWhiteSpace(_name.Text)) { error = Messages.NameRequired; _errors.SetError(_name, error); }
        else if (!Regex.IsMatch(_email.Text.Trim(), @"^[^@\s]+@[^@\s]+\.[^@\s]+$")) { error = Messages.EmailInvalid; _errors.SetError(_email, error); }
        else if (_data.Customers.Any(c => c != _original && c.Email.Equals(_email.Text.Trim(), StringComparison.OrdinalIgnoreCase))) { error = Messages.DuplicateEmail; _errors.SetError(_email, error); }
        else if (!decimal.TryParse(_value.Text, NumberStyles.Number, CultureInfo.InvariantCulture, out var v) || v < 0) { error = Messages.ValueInvalid; _errors.SetError(_value, error); }
        if (error is not null) { _message.Text = error; return; }

        var c = _original ?? new Customer();
        c.Name = _name.Text.Trim(); c.Company = _company.Text.Trim(); c.Email = _email.Text.Trim(); c.Phone = _phone.Text.Trim();
        c.Status = _statusBox.SelectedItem as string ?? "Lead";
        c.AnnualValue = decimal.Parse(_value.Text, CultureInfo.InvariantCulture);
        if (_original is null) _data.Customers.Add(c);
        Result = c;
        DialogResult = DialogResult.OK;
    }
}
