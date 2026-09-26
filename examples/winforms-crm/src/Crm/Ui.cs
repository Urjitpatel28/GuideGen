namespace Crm;

/// <summary>Small layout helpers so forms can be built in code without designer files.
/// Every control gets a Name: WinForms exposes it as the UI Automation AutomationId.</summary>
internal static class Ui
{
    public static readonly Color Brand = ColorTranslator.FromHtml("#5B2C6F");
    public static readonly Color Accent = ColorTranslator.FromHtml("#00A896");

    public static TableLayoutPanel FieldGrid()
    {
        var t = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 2, AutoSize = true, Padding = new Padding(16) };
        t.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 130));
        t.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        return t;
    }

    public static T AddField<T>(TableLayoutPanel grid, string label, string name, T control) where T : Control
    {
        var l = new Label { Text = label, AutoSize = true, Anchor = AnchorStyles.Left, Name = name + "Label", Margin = new Padding(3, 8, 3, 3) };
        control.Name = name;
        control.AccessibleName = label.Replace("&", "");
        control.Dock = DockStyle.Fill;
        control.Margin = new Padding(3, 4, 3, 4);
        grid.Controls.Add(l);
        grid.Controls.Add(control);
        return control;
    }

    public static Button Button(string text, string name, bool primary = false)
    {
        var b = new Button { Text = text, Name = name, AutoSize = true, Padding = new Padding(10, 3, 10, 3), Margin = new Padding(0, 0, 8, 0) };
        if (primary) { b.BackColor = Brand; b.ForeColor = Color.White; b.FlatStyle = FlatStyle.Flat; }
        return b;
    }

    public static FlowLayoutPanel ButtonRow(params Button[] buttons)
    {
        var f = new FlowLayoutPanel { Dock = DockStyle.Bottom, FlowDirection = FlowDirection.RightToLeft, AutoSize = true, Padding = new Padding(12) };
        f.Controls.AddRange(buttons);
        return f;
    }
}
