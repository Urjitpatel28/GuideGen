namespace Crm;

public class MainForm : Form
{
    private readonly CrmData _data;
    private readonly DataGridView _customers;
    private readonly DataGridView _activities;
    private readonly TextBox _search;
    private readonly ToolStripStatusLabel _status;
    private readonly Label _summary;
    private readonly BindingSource _customerSource;

    public MainForm(CrmData data, string user)
    {
        _data = data;
        Text = "ClientDesk CRM";
        Name = "MainForm";
        var iconPath = Path.Combine(AppContext.BaseDirectory, "Assets", "crm.ico");
        if (File.Exists(iconPath)) Icon = new Icon(iconPath);
        StartPosition = FormStartPosition.CenterScreen;
        Size = new Size(1280, 800);
        Font = new Font("Segoe UI", 9.5f);

        // Menu
        var menu = new MenuStrip { Name = "MainMenu" };
        var file = new ToolStripMenuItem("&File") { Name = "FileMenu" };
        file.DropDownItems.Add(new ToolStripMenuItem("&Options...", null, (_, _) => ShowOptions()) { Name = "OptionsMenuItem" });
        file.DropDownItems.Add(new ToolStripSeparator());
        file.DropDownItems.Add(new ToolStripMenuItem("E&xit", null, (_, _) => Close()) { Name = "ExitMenuItem" });
        var cust = new ToolStripMenuItem("&Customers") { Name = "CustomersMenu" };
        cust.DropDownItems.Add(new ToolStripMenuItem("&New customer...", null, (_, _) => NewCustomer()) { Name = "NewCustomerMenuItem", ShortcutKeys = Keys.Control | Keys.N });
        cust.DropDownItems.Add(new ToolStripMenuItem("&Edit customer...", null, (_, _) => EditCustomer()) { Name = "EditCustomerMenuItem" });
        cust.DropDownItems.Add(new ToolStripMenuItem("&Log activity...", null, (_, _) => LogActivity()) { Name = "LogActivityMenuItem" });
        var help = new ToolStripMenuItem("&Help") { Name = "HelpMenu" };
        help.DropDownItems.Add(new ToolStripMenuItem("&About ClientDesk", null, (_, _) => { using var a = new AboutForm(); a.ShowDialog(this); }) { Name = "AboutMenuItem" });
        menu.Items.AddRange(new ToolStripItem[] { file, cust, help });
        MainMenuStrip = menu;

        // Status bar
        var statusStrip = new StatusStrip { Name = "StatusStrip" };
        _status = new ToolStripStatusLabel("Ready") { Name = "StatusLabel", Spring = true, TextAlign = ContentAlignment.MiddleLeft };
        statusStrip.Items.Add(_status);
        statusStrip.Items.Add(new ToolStripStatusLabel($"Signed in as {user}") { Name = "UserLabel" });

        var tabs = new TabControl { Name = "MainTabs", Dock = DockStyle.Fill, Padding = new Point(12, 5) };

        // Customers tab
        var customersTab = new TabPage("Customers") { Name = "CustomersTab", Padding = new Padding(10) };
        var toolbar = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(0, 0, 0, 8) };
        toolbar.Controls.Add(new Label { Text = "&Search", AutoSize = true, Margin = new Padding(0, 7, 6, 0), Name = "SearchLabel" });
        _search = new TextBox { Name = "SearchTextBox", Width = 240, AccessibleName = "Search", Margin = new Padding(0, 3, 16, 0) };
        _search.TextChanged += (_, _) => ApplyFilter();
        toolbar.Controls.Add(_search);
        var newBtn = Ui.Button("New customer", "NewCustomerButton", primary: true);
        newBtn.Click += (_, _) => NewCustomer();
        var editBtn = Ui.Button("Edit", "EditCustomerButton");
        editBtn.Click += (_, _) => EditCustomer();
        var logBtn = Ui.Button("Log activity", "LogActivityButton");
        logBtn.Click += (_, _) => LogActivity();
        var delBtn = Ui.Button("Delete", "DeleteCustomerButton");
        delBtn.Click += (_, _) => DeleteCustomer();
        toolbar.Controls.AddRange(new Control[] { newBtn, editBtn, logBtn, delBtn });

        _customerSource = new BindingSource { DataSource = _data.Customers };
        _customers = MakeGrid("CustomersGrid", "Customers");
        _customers.DataSource = _customerSource;
        _customers.DataBindingComplete += (_, _) =>
        {
            if (_customers.Columns["AnnualValue"] is { } c) { c.HeaderText = "Annual value"; c.DefaultCellStyle.Format = "C0"; }
        };
        _customers.CellDoubleClick += (_, e) => { if (e.RowIndex >= 0) EditCustomer(); };
        customersTab.Controls.Add(_customers);
        customersTab.Controls.Add(toolbar);

        // Activities tab
        var activitiesTab = new TabPage("Activities") { Name = "ActivitiesTab", Padding = new Padding(10) };
        _activities = MakeGrid("ActivitiesGrid", "Activities");
        _activities.DataSource = _data.Activities;
        activitiesTab.Controls.Add(_activities);

        // Dashboard tab with a custom-drawn chart (no UI Automation children)
        var dashTab = new TabPage("Dashboard") { Name = "DashboardTab", Padding = new Padding(10) };
        _summary = new Label { Name = "SummaryLabel", Dock = DockStyle.Top, Height = 60, Font = new Font("Segoe UI", 12f), ForeColor = Ui.Brand };
        var chart = new SalesChart(_data) { Dock = DockStyle.Fill };
        dashTab.Controls.Add(chart);
        dashTab.Controls.Add(_summary);

        tabs.TabPages.AddRange(new[] { customersTab, activitiesTab, dashTab });
        Controls.Add(tabs);
        Controls.Add(statusStrip);
        Controls.Add(menu);
        RefreshSummary();
    }

    private static DataGridView MakeGrid(string name, string accessibleName) => new()
    {
        Name = name, AccessibleName = accessibleName, Dock = DockStyle.Fill, ReadOnly = true, AllowUserToAddRows = false,
        AllowUserToDeleteRows = false, SelectionMode = DataGridViewSelectionMode.FullRowSelect, MultiSelect = false,
        AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill, BackgroundColor = Color.White, RowHeadersVisible = false,
    };

    private Customer? Selected => _customers.CurrentRow?.DataBoundItem as Customer;

    private void ApplyFilter()
    {
        var q = _search.Text.Trim();
        _customerSource.DataSource = q.Length == 0 ? _data.Customers
            : new System.ComponentModel.BindingList<Customer>(_data.Customers.Where(c =>
                c.Name.Contains(q, StringComparison.OrdinalIgnoreCase) || c.Company.Contains(q, StringComparison.OrdinalIgnoreCase)).ToList());
    }

    private void NewCustomer()
    {
        using var f = new CustomerForm(_data, null);
        if (f.ShowDialog(this) == DialogResult.OK) { _status.Text = $"Added {f.Result!.Name}."; ApplyFilter(); RefreshSummary(); }
    }

    private void EditCustomer()
    {
        if (Selected is null) { MessageBox.Show(this, Messages.SelectCustomerFirst, "ClientDesk", MessageBoxButtons.OK, MessageBoxIcon.Information); return; }
        using var f = new CustomerForm(_data, Selected);
        if (f.ShowDialog(this) == DialogResult.OK) { _status.Text = $"Saved {Selected.Name}."; _customers.Refresh(); RefreshSummary(); }
    }

    private void LogActivity()
    {
        using var f = new ActivityForm(_data, Selected?.Name);
        if (f.ShowDialog(this) == DialogResult.OK) _status.Text = "Activity logged.";
    }

    private void DeleteCustomer()
    {
        if (Selected is null) { MessageBox.Show(this, Messages.SelectCustomerFirst, "ClientDesk", MessageBoxButtons.OK, MessageBoxIcon.Information); return; }
        if (MessageBox.Show(this, $"Delete {Selected.Name}? Their activities are kept.", "Delete customer",
                MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes) return;
        var name = Selected.Name;
        _data.Customers.Remove(Selected);
        _status.Text = $"Deleted {name}.";
        ApplyFilter();
        RefreshSummary();
    }

    private void ShowOptions()
    {
        using var f = new OptionsForm(_data.Options);
        f.ShowDialog(this);
    }

    private void RefreshSummary()
    {
        var active = _data.Customers.Count(c => c.Status != "Inactive");
        _summary.Text = $"{_data.Customers.Count} contacts · {active} active · pipeline {_data.Customers.Sum(c => c.AnnualValue):C0}";
    }
}
