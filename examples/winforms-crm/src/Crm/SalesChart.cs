namespace Crm;

/// <summary>
/// Custom-drawn pipeline chart. It paints everything itself and exposes no UI Automation children,
/// so GuideGen can only capture it as part of the window (reported as a limitation).
/// </summary>
public class SalesChart : Control
{
    private readonly CrmData _data;

    public SalesChart(CrmData data)
    {
        _data = data;
        Name = "PipelineChart";
        AccessibleName = "Pipeline chart";
        DoubleBuffered = true;
        ResizeRedraw = true;
        _data.Customers.ListChanged += (_, _) => Invalidate();
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        var g = e.Graphics;
        g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
        g.Clear(Color.White);
        using var titleFont = new Font("Segoe UI", 11f, FontStyle.Bold);
        using var font = new Font("Segoe UI", 9f);
        g.DrawString("Pipeline value by status", titleFont, Brushes.Black, 12, 10);

        var groups = CrmData.Statuses.Select(s => (s, _data.Customers.Where(c => c.Status == s).Sum(c => c.AnnualValue))).ToList();
        var max = Math.Max(1m, groups.Max(x => x.Item2));
        int left = 110, top = 44, barH = 28, gap = 14, width = Math.Max(50, Width - left - 120);
        using var bar = new SolidBrush(Ui.Accent);
        for (int i = 0; i < groups.Count; i++)
        {
            var (status, value) = groups[i];
            var y = top + i * (barH + gap);
            g.DrawString(status, font, Brushes.DimGray, 12, y + 6);
            var w = (int)(width * (float)(value / max));
            g.FillRectangle(bar, left, y, Math.Max(2, w), barH);
            g.DrawString(value.ToString("C0"), font, Brushes.Black, left + w + 8, y + 6);
        }
    }
}
