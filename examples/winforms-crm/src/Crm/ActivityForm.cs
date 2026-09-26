namespace Crm;

public class ActivityForm : Form
{
    private readonly CrmData _data;
    private readonly ComboBox _customer, _type;
    private readonly DateTimePicker _date;
    private readonly TextBox _notes;
    private readonly Label _message;

    public ActivityForm(CrmData data, string? customer)
    {
        _data = data;
        Text = "Log activity";
        Name = "ActivityForm";
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = MinimizeBox = false;
        ShowInTaskbar = false;
        StartPosition = FormStartPosition.CenterParent;
        ClientSize = new Size(460, 340);
        Font = new Font("Segoe UI", 9.5f);

        var grid = Ui.FieldGrid();
        _customer = Ui.AddField(grid, "&Customer", "ActivityCustomerComboBox", new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList });
        _customer.Items.AddRange(data.Customers.Select(c => (object)c.Name).ToArray());
        if (customer is not null) _customer.SelectedItem = customer;
        _type = Ui.AddField(grid, "&Type", "ActivityTypeComboBox", new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList });
        _type.Items.AddRange(CrmData.ActivityTypes);
        _type.SelectedIndex = 0;
        _date = Ui.AddField(grid, "&Date", "ActivityDatePicker", new DateTimePicker { Format = DateTimePickerFormat.Short, Value = new DateTime(2026, 9, 24) });
        _notes = Ui.AddField(grid, "&Notes", "ActivityNotesTextBox", new TextBox { Multiline = true, Height = 90, ScrollBars = ScrollBars.Vertical });
        _message = new Label { Name = "ActivityValidationLabel", ForeColor = Color.Firebrick, AutoSize = true };
        grid.Controls.Add(new Label());
        grid.Controls.Add(_message);

        var save = Ui.Button("Save activity", "SaveActivityButton", primary: true);
        var cancel = Ui.Button("Cancel", "CancelActivityButton");
        cancel.DialogResult = DialogResult.Cancel;
        save.Click += (_, _) => Save();
        CancelButton = cancel;
        Controls.Add(grid);
        Controls.Add(Ui.ButtonRow(cancel, save));
    }

    private void Save()
    {
        if (_customer.SelectedItem is not string customer) { _message.Text = Messages.ChooseCustomer; return; }
        if (_notes.Text.Length > 500) { _message.Text = Messages.NotesTooLong; return; }
        _data.Activities.Add(new Activity { Date = _date.Value.Date, Customer = customer, Type = (string)_type.SelectedItem!, Notes = _notes.Text.Trim() });
        DialogResult = DialogResult.OK;
    }
}
